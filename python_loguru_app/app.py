from flask import Flask, jsonify, request
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
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "service": "python-loguru",
        "instance": "python-loguru-01",
        "correlationId": correlation_id,
        "message": "Call from Python Loguru App!",
        "context": {"foo": "bar"}
    }
    logger.info(json.dumps(log_data))

    try:
        resp = requests.get("http://nodejs_app:3000/node-hello", 
                          headers={"X-Correlation-ID": correlation_id},
                          timeout=3)
        node_response = resp.text
        
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": correlation_id,
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
            "correlationId": correlation_id,
            "message": f"Error calling Node.js: {e}",
            "context": {"error": str(e)}
        }
        logger.error(json.dumps(log_data))
        return jsonify({"error": str(e)}), 500

@app.route("/call_python_standard")
def call_python_standard():
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "service": "python-loguru",
        "instance": "python-loguru-01",
        "correlationId": correlation_id,
        "message": "Calling Python Standard App",
        "context": {}
    }
    logger.info(json.dumps(log_data))

    try:
        resp = requests.get("http://python_app:5001/call_node", 
                          headers={"X-Correlation-ID": correlation_id},
                          timeout=3)
        if resp.status_code != 200:
            raise Exception(f"Python Standard returned {resp.status_code}: {resp.text}")
        python_response = resp.json()
        
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": correlation_id,
            "message": f"Python Standard responded: {python_response}",
            "context": {}
        }
        logger.info(json.dumps(log_data))
        
        return jsonify({
            "python_loguru_app": "Hello from Python Loguru!",
            "python_standard_app": python_response
        })
    except Exception as e:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "service": "python-loguru",
            "instance": "python-loguru-01",
            "correlationId": correlation_id,
            "message": f"Error calling Python Standard: {e}",
            "context": {"error": str(e)}
        }
        logger.error(json.dumps(log_data))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
