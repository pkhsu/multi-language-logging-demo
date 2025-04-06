# python_app/app.py
from flask import Flask, jsonify, request
import logging
import requests
import json # Add json import

import logging
from pythonjsonlogger import jsonlogger
import logging
from pythonjsonlogger import jsonlogger
import datetime

DEFAULT_LOG_FORMAT = (
    "%(asctime)s "       # 時間
    "%(levelname)s "     # 日誌等級
    "%(message)s "       # 訊息
    "%(service)s "       # 服務名稱
    "%(correlationId)s " # 追蹤ID
    "%(context)s "       # context (可能是 dict)
)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def __init__(self, fmt=DEFAULT_LOG_FORMAT, *args, **kwargs):
        super().__init__(fmt=fmt, *args, **kwargs)
    
    def process_log_record(self, log_record):
        """
        在這邊把 asctime -> timestamp
        levelname -> level (全大寫)
        等等...
        """
        # 以下僅示範：
        if "asctime" in log_record:
            log_record["timestamp"] = log_record.pop("asctime") + "Z"  # 簡化附加 Z
        if "levelname" in log_record:
            log_record["level"] = log_record.pop("levelname").upper()
        if "instance" not in log_record:
            log_record["instance"] = "python-workshop-01"
        if "context" not in log_record:
            log_record["context"] = {}
        return super().process_log_record(log_record)


app = Flask(__name__)

# 建立 Logger
logger = logging.getLogger("python-workshop")
logger.setLevel(logging.INFO)

# 建立 Handler (輸出至 stdout)
handler = logging.StreamHandler()

# 使用自訂 Formatter
formatter = CustomJsonFormatter()
handler.setFormatter(formatter)

logger.addHandler(handler)


@app.route("/hello")
def hello():
    logger.info("Hello from Python App!",
                extra={
                    "service": "python-workshop",
                    "correlationId": "xyz123abc",
                    "context": {"foo": "bar"}
                })
    return "Hello from Python Docker App!"

@app.route("/call_node")
def call_node():
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    logger.info("Call from Python App!",
                extra={
                    "service": "python-workshop",
                    "correlationId": correlation_id,
                    "context": {"foo": "bar"}
                })

    try:
        # 在同一個 docker-compose network, Node.js 服務名稱為 nodejs_app, port=3000
        resp = requests.get("http://nodejs_app:3000/node-hello", 
                          headers={"X-Correlation-ID": correlation_id},
                          timeout=3)
        node_response = resp.json()
        logger.info("Node.js responded",
                    extra={
                        "service": "python-workshop", 
                        "correlationId": correlation_id,
                        "context": {"response": node_response}
                    })
        # Return new JSON structure
        return jsonify({
            "python_standard_app": "Hello from Python!", # Renamed key
            "downstream_response": node_response # Node.js response is already nested
        }), 200 # Explicitly return 200 OK

    except requests.exceptions.Timeout:
        error_message = "Request to Node.js App timed out"
        logger.error(error_message,
                     extra={
                         "service": "python-workshop",
                         "correlationId": correlation_id,
                         "context": {"error": "timeout"}
                     })
        return jsonify({"error": error_message}), 500

    except requests.exceptions.RequestException as e:
        # Catch connection errors, etc.
        error_message = f"Error connecting to Node.js App: {e}"
        logger.error(error_message,
                     extra={
                         "service": "python-workshop",
                         "correlationId": correlation_id,
                         "context": {"error": str(e)}
                     })
        return jsonify({"error": "Failed to connect to downstream service", "details": error_message}), 500

    except json.JSONDecodeError as e:
        # This might happen if Node.js returns non-JSON
        error_message = "Failed to decode JSON response from Node.js App"
        # Try to get response text if possible, handle potential errors
        response_text = ""
        try:
            response_text = resp.text[:500] if 'resp' in locals() and hasattr(resp, 'text') else "Response text not available"
        except Exception as read_err:
            response_text = f"Could not read response text: {read_err}"

        logger.error(error_message,
                     extra={
                         "service": "python-workshop",
                         "correlationId": correlation_id,
                         "context": {"error": str(e), "response_text": response_text}
                     })
        return jsonify({"error": "Invalid response from downstream service", "details": error_message}), 500

    except Exception as e:
        # Catch-all for other errors, including potential errors from resp.json() if status wasn't 200
        error_message = f"An unexpected error occurred: {e}"
        # Check if it's an error response from downstream
        response_details = ""
        status_code = 500 # Default to 500
        if 'resp' in locals() and hasattr(resp, 'status_code'):
             # If we have a response object, try to get status and text
             status_code = resp.status_code
             try:
                 # Attempt to parse downstream error JSON if possible
                 error_json = resp.json()
                 response_details = error_json
             except json.JSONDecodeError:
                 # Fallback to raw text if not JSON
                 try:
                     response_details = resp.text[:500]
                 except Exception as read_err:
                     response_details = f"Could not read response text: {read_err}"
             except Exception as parse_err:
                 response_details = f"Could not parse or read response: {parse_err}"

             # Log specific downstream error
             logger.error(f"Downstream Node.js service returned status {status_code}",
                          extra={
                              "service": "python-workshop",
                              "correlationId": correlation_id,
                              "context": {"error": str(e), "downstream_status": status_code, "downstream_response": response_details}
                          })
             # Return a generic 500 error as requested
             return jsonify({"error": "Downstream service error", "details": f"Node.js returned status {status_code}"}), 500
        else:
             # Log general unexpected error
             logger.error(error_message,
                          extra={
                              "service": "python-workshop",
                              "correlationId": correlation_id,
                              "context": {"error": str(e)}
                          })
             return jsonify({"error": "An internal server error occurred", "details": error_message}), 500


if __name__ == "__main__":
    # 監聽 0.0.0.0 才能在 Docker 容器中對外暴露
    app.run(host="0.0.0.0", port=5001)
