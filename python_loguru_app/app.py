from flask import Flask, jsonify, request
import requests
from loguru import logger
import sys
import json
import traceback

app = Flask(__name__)

def json_formatter(record):
    log_record = {
        "timestamp": record["time"].isoformat(timespec="milliseconds") + "Z",
        "level": record["level"].name,
        "service": record["extra"].get("service", "python-loguru"),
        "instance": record["extra"].get("instance", "python-loguru-01"),
        "correlationId": record["extra"].get("correlationId", "N/A"),
        "message": record["message"],
        "context": record["extra"].get("context", {})
    }
    return json.dumps(log_record) + "\n"


def patching(record):
    # 简化patching方法，直接添加serialized字段
    record["serialized"] = json_formatter(record)


logger.remove(0)

logger = logger.patch(patching)
logger.add(
    sys.stdout,
    format="{serialized}"
)
logger.debug("Happy logging with Loguru!")


@app.route("/hello")
def hello():
    logger.info(
        "Hello from Python Loguru App!",
        service="python-loguru",
        instance="python-loguru-01", 
        correlationId="xyz123abc",
        context={"foo": "bar"}
    )
    return "Hello from Python Loguru Docker App!"

@app.route("/call_python_standard")
def call_python_standard():
    correlation_id = request.headers.get("X-Correlation-Id") or request.headers.get("x-correlation-id") or "N/A"
    logger.info(
        "Calling Python Standard App",
        service="python-loguru",
        instance="python-loguru-01",
        correlationId=correlation_id,
        context={
            "incoming_headers": dict(request.headers)
        }
    )

    try:
        resp = requests.get(
            "http://python_app:5001/call_node",
            headers={"X-Correlation-ID": correlation_id},
            timeout=3
        )
        resp.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        python_response = resp.json()

        logger.info(
            "Python Standard responded successfully",
            service="python-loguru",
            instance="python-loguru-01",
            correlationId=correlation_id,
            context={
                "response": python_response,
                "status_code": resp.status_code
            }
        )
        # Return success response with status 200 using the new structure
        return jsonify({
            "python_loguru_app": "Hello from Python Loguru!",
            "downstream_response": python_response # Use the standardized key
        }), 200

    except requests.exceptions.Timeout:
        error_message = "Request to Python Standard App timed out"
        logger.error(
            error_message,
            service="python-loguru",
            instance="python-loguru-01",
            correlationId=correlation_id,
            context={"error": "timeout"}
        )
        return jsonify({"error": error_message}), 500

    except requests.exceptions.HTTPError as e:
        error_message = f"Python Standard App returned error: {e.response.status_code}"
        # Log the error with details
        logger.error(
            error_message,
            service="python-loguru",
            instance="python-loguru-01",
            correlationId=correlation_id,
            context={
                "error": str(e),
                "status_code": e.response.status_code,
                "response_text": e.response.text[:500] # Limit response text length
            }
        )
        # Return generic error response with status 500
        return jsonify({"error": "Downstream service error", "details": error_message}), 500

    except requests.exceptions.RequestException as e:
        # Catch other request-related errors (e.g., ConnectionError)
        error_message = f"Error connecting to Python Standard App: {e}"
        logger.error(
            error_message,
            service="python-loguru",
            instance="python-loguru-01",
            correlationId=correlation_id,
            context={"error": str(e)}
        )
        return jsonify({"error": "Failed to connect to downstream service", "details": error_message}), 500

    except json.JSONDecodeError as e:
        error_message = "Failed to decode JSON response from Python Standard App"
        # Log the error with details including part of the invalid response
        logger.error(
            error_message,
            service="python-loguru",
            instance="python-loguru-01",
            correlationId=correlation_id,
            context={
                "error": str(e),
                "response_text": resp.text[:500] if 'resp' in locals() else "Response object not available"
            }
        )
        return jsonify({"error": "Invalid response from downstream service", "details": error_message}), 500

    except Exception as e:
        # Catch any other unexpected errors
        error_message = f"An unexpected error occurred: {e}"
        tb_str = traceback.format_exc()
        logger.error(
            error_message,
            service="python-loguru",
            instance="python-loguru-01",
            correlationId=correlation_id,
            context={
                "error": str(e),
                "traceback": tb_str
            }
        )
        return jsonify({"error": "An internal server error occurred", "details": error_message}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
