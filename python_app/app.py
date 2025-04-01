# python_app/app.py
from flask import Flask, jsonify
import logging
import requests

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
    logger.info("Call from Python App!",
                extra={
                    "service": "python-workshop",
                    "correlationId": "xyz123abc",
                    "context": {"foo": "bar"}
                })

    try:
        # 在同一個 docker-compose network, Node.js 服務名稱為 nodejs_app, port=3000
        resp = requests.get("http://nodejs_app:3000/node-hello", timeout=3)
        node_response = resp.text
        logger.info("Node.js responded: %s" % node_response,
                    extra={"service": "python-workshop", "correlationId": "xyz123abc"})
        return jsonify({
            "python_app": "Hello from Python!",
            "node_app": node_response
        })
    except Exception as e:
        logger.error("Error calling Node.js: %s" % e,
                     extra={"service": "python-workshop", "correlationId": "xyz123abc"})
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 監聽 0.0.0.0 才能在 Docker 容器中對外暴露
    app.run(host="0.0.0.0", port=5001)
