FROM python:3.9-slim

# 安裝 cron 與基本工具 (清理 cache 以減少鏡像體積)
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# 設定容器內的根目錄
WORKDIR /app

# 1. 複製專案原始碼 (app.py, requirements.txt 等)
COPY . .

# 2. 將啟動腳本放入系統執行路徑，方便直接呼叫
COPY entrypoint.sh /usr/local/bin/

# 3. 在 Build 階段賦予執行權限，確保腳本可被執行
RUN chmod +x /usr/local/bin/entrypoint.sh

# 4. 安裝 Python 依賴套件
RUN pip install --no-cache-dir -r requirements.txt

# 5. 確保 /app 目錄下的檔案對所有使用者皆可讀取與執行 (針對 Streamlit 執行權限)
RUN chmod -R 755 /app

# 6. 宣告容器監聽的埠號 (僅供參考與對齊)
EXPOSE 8080

# 7. 使用 sh 直接執行絕對路徑腳本
CMD ["sh", "/usr/local/bin/entrypoint.sh"]