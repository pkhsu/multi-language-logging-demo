import streamlit as st
import requests
import subprocess
import re
import json

def remove_ansi_codes(text: str) -> str:
    """
    移除字串中的 ANSI Escape Code (例如顏色碼)。
    """
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def format_logs(raw_logs: str) -> str:
    """
    將 Docker logs 做基本的格式化與過濾。
    - 去除 ANSI 顏色碼
    - 嘗試將 JSON 日誌做 pretty print
    - 過濾/略過無用的啟動訊息
    """
    lines = raw_logs.splitlines()
    formatted_lines = []

    # 可自行調整想要略過的特定關鍵字
    skip_phrases = [
        "Serving Flask app",
        "Debug mode: off",
        "WARNING: This is a development server",
        "Running on all addresses",
        "Press CTRL+C to quit"
    ]

    for line in lines:
        # 移除 ANSI 碼
        clean_line = remove_ansi_codes(line).strip()
        if not clean_line:
            continue  # 跳過空行

        # 若包含在想要略過的行，就直接跳過
        if any(phrase in clean_line for phrase in skip_phrases):
            continue

        # 嘗試將該行視為 JSON
        try:
            json_data = json.loads(clean_line)
            # JSON 轉成縮排格式
            pretty_json = json.dumps(json_data, indent=2)
            formatted_lines.append(pretty_json)
        except json.JSONDecodeError:
            # 若不是 JSON，就直接保留原文字
            formatted_lines.append(clean_line)

    # 重新組成多行字串
    return "\n".join(formatted_lines)

import uuid
from concurrent.futures import ThreadPoolExecutor

def call_python_service(url, correlation_id):
    try:
        resp = requests.get(url, headers={"X-Correlation-ID": correlation_id}, timeout=5)
        return resp
    except Exception as e:
        return {"error": str(e)}

def get_container_logs(container_name):
    try:
        raw_logs = subprocess.check_output(
            ["docker", "logs", container_name],
            stderr=subprocess.STDOUT
        ).decode("utf-8")
        return format_logs(raw_logs)
    except Exception as e:
        return f"Error retrieving logs: {e}"

def main():
    st.title("Microservices Logging - Workshop")
    st.write("Demo: A single click to call Python (standard & loguru) -> Node.js -> golang -> java, then see logs instantly.")

    # 按鈕：一鍵觸發所有服務
    if st.button("Call All Nodes"):
        correlation_id = str(uuid.uuid4())
        
        # 並行呼叫兩個Python服務
        with ThreadPoolExecutor() as executor:
            future_std = executor.submit(call_python_service, "http://python_app:5001/call_node", correlation_id)
            future_loguru = executor.submit(call_python_service, "http://python_loguru_app:5002/call_node", correlation_id)
            
            resp_std = future_std.result()
            resp_loguru = future_loguru.result()

            if isinstance(resp_std, dict) and "error" in resp_std:
                st.error(f"Error calling Python (standard): {resp_std['error']}")
            elif resp_std.status_code == 200:
                st.success(f"Standard Python call success! Response: {resp_std.json()}")
            else:
                st.error(f"Standard Python call failed, status code: {resp_std.status_code}")

            if isinstance(resp_loguru, dict) and "error" in resp_loguru:
                st.error(f"Error calling Python (loguru): {resp_loguru['error']}")
            elif resp_loguru.status_code == 200:
                st.success(f"Loguru Python call success! Response: {resp_loguru.json()}")
            else:
                st.error(f"Loguru Python call failed, status code: {resp_loguru.status_code}")

        # 收集並顯示所有日誌
        st.subheader("Standard Python Logs")
        st.text_area("Python (standard) Logs", get_container_logs("python_app_container"), height=200)

        st.subheader("Loguru Python Logs")
        st.text_area("Python (loguru) Logs", get_container_logs("python_loguru_container"), height=200)

        st.subheader("Node.js App Logs")
        st.text_area("Node.js App Logs", get_container_logs("nodejs_app_container"), height=200)

        st.subheader("Golang App Logs")
        st.text_area("Golang App Logs", get_container_logs("golang_app_container"), height=200)

        st.subheader("Java App Logs")
        st.text_area("Java App Logs", get_container_logs("java_app_container"), height=200)

if __name__ == "__main__":
    main()
