FROM python:3.9-slim

# 安裝 cron 與基本工具
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. 安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. 【核心改動】直接把代碼複製進去，不要依賴外部掛載
COPY . .

# 3. 給予所有檔案讀取權限
RUN chmod -R 755 /app

# 4. 暴露埠
EXPOSE 80

# 5. 直接用命令列啟動 (捨棄 entrypoint.sh 避免格式問題)
CMD service cron start && python cron_save.py && streamlit run app.py --server.port 80 --server.address 0.0.0.0