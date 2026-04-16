#!/bin/bash

# 1. 獲取 Docker 內部 Python 的絕對路徑
PYTHON_PATH=$(which python)

# 2. 寫入 crontab (注意：路徑改為 /app/...)
# 我們直接把任務寫入 /etc/crontab 或 cron.d
echo "10 5 * * * root $PYTHON_PATH /app/cron_save.py >> /var/log/cron.log 2>&1" > /etc/cron.d/gsr-cron

# 3. 修正權限
chmod 0644 /etc/cron.d/gsr-cron

# 4. 啟動 cron 服務
service cron start

# 5. 首次執行紀錄 (確保容器一啟動就有資料)
$PYTHON_PATH /app/cron_save.py

# 6. 啟動 Streamlit
streamlit run app.py --server.port 8080 --server.address 0.0.0.0