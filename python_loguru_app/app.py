from flask import Flask, jsonify, request
import requests
from loguru import logger
import sys

app = Flask(__name__)

def json_formatter(record):
    log_record = {
        "timestamp": record["time"].isoformat() + "Z",
        "level": record["level"].name,
        "service": record["extra"].get("service", "python-loguru"),
        "instance": record["extra"].get("instance", "python-loguru-01"),
        "correlationId": record["extra"].get("correlationId", "N/A"),
        "message": record["message"],
        "context": record["extra"].get("context", {})
    }
    return json.dumps(log_record) + "\n"

logger.remove()
logger.add(
    sys.stdout,
    format=json_formatter,
    level="INFO"
)

@app.route("/hello")
def hello():
    logger.info(
        "Hello from Python Loguru App!",
        extra={
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": "xyz123abc",
            "context": {"foo": "bar"}
        }
    )
    return "Hello from Python Loguru Docker App!"

@app.route("/call_node")
def call_node():
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    logger.info(
        "Call from Python Loguru App!",
        extra={
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": correlation_id,
            "context": {"foo": "bar"}
        }
    )
    try:
        resp = requests.get(
            "http://nodejs_app:3000/node-hello",
            headers={"X-Correlation-ID": correlation_id},
            timeout=3
        )
        node_response = resp.text
        logger.info(
            f"Node.js responded: {node_response}",
            extra={
                "service": "python-loguru",
                "instance": "python-loguru-01",
                "correlationId": correlation_id,
                "context": {}
            }
        )
        return jsonify({
            "python_loguru_app": "Hello from Python Loguru!",
            "node_app": node_response
        })
    except Exception as e:
        logger.error(
            f"Error calling Node.js: {e}",
            extra={
                "service": "python-loguru",
                "instance": "python-loguru-01",
                "correlationId": correlation_id,
                "context": {"error": str(e)}
            }
        )
        return jsonify({"error": str(e)}), 500

@app.route("/call_python_standard")
def call_python_standard():
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    logger.info(
        "Calling Python Standard App",
        extra={
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": correlation_id,
            "context": {}
        }
    )
    try:
        resp = requests.get(
            "http://python_app:5001/call_node",
            headers={"X-Correlation-ID": correlation_id},
            timeout=3
        )
        if resp.status_code != 200:
            raise Exception(f"Python Standard returned {resp.status_code}: {resp.text}")
        python_response = resp.json()
        logger.info(
            f"Python Standard responded: {json.dumps(python_response)}",
            extra={
                "service": "python-loguru",
                "instance": "python-loguru-01",
                "correlationId": correlation_id,
                "context": {}
            }
        )
        return jsonify({
            "python_loguru_app": "Hello from Python Loguru!",
            "python_standard_app": python_response
        })
    except Exception as e:
        logger.error(
            f"Error calling Python Standard: {e}",
            extra={
                "service": "python-loguru",
                "instance": "python-loguru-01",
                "correlationId": correlation_id,
                "context": {"error": str(e)}
            }
        )
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)