# python_app/Dockerfile
FROM python:3.9-slim

# 建立工作目錄
WORKDIR /app

# 複製 requirements.txt
COPY requirements.txt .

# 安裝相依套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 容器啟動後執行的指令
CMD ["python", "app.py"]
