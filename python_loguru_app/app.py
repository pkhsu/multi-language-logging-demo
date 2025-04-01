from flask import Flask, jsonify
import requests
from loguru import logger
import datetime
import json

app = Flask(__name__)

# 配置loguru輸出JSON格式
logger.add(
    lambda msg: print(msg, end=''),
    format="{message}",
    serialize=True
)

@app.route("/hello")
def hello():
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "service": "python-loguru",
        "instance": "python-loguru-01",
        "correlationId": "xyz123abc",
        "message": "Hello from Python Loguru App!",
        "context": {"foo": "bar"}
    }
    logger.info(json.dumps(log_data))
    return "Hello from Python Loguru Docker App!"

@app.route("/call_node")
def call_node():
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "service": "python-loguru",
        "instance": "python-loguru-01",
        "correlationId": "xyz123abc",
        "message": "Call from Python Loguru App!",
        "context": {"foo": "bar"}
    }
    logger.info(json.dumps(log_data))

    try:
        resp = requests.get("http://nodejs_app:3000/node-hello", timeout=3)
        node_response = resp.text
        
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": "xyz123abc",
            "message": f"Node.js responded: {node_response}",
            "context": {}
        }
        logger.info(json.dumps(log_data))
        
        return jsonify({
            "python_loguru_app": "Hello from Python Loguru!",
            "node_app": node_response
        })
    except Exception as e:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": "xyz123abc",
            "message": f"Error calling Node.js: {e}",
            "context": {"error": str(e)}
        }
        logger.error(json.dumps(log_data))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
