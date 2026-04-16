import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# 優先讀取環境變數裡的檔案路徑，如果沒有就用預設值
DB_FILE = os.getenv("GSR_DB_PATH", "gsr_history.csv")

def ensure_db_exists(csv_path):
    """確保 CSV 檔案存在，若不存在則初始化一個帶有 Header 的檔案"""
    if not os.path.exists(csv_path):
        df = pd.DataFrame(columns=["Date", "Gold", "Silver", "GSR"])
        df.to_csv(csv_path, index=False)
        print(f"[{datetime.now()}] 檢測到資料庫不存在，已自動建立: {csv_path}")

def run_auto_save():
    # 執行前置檢查
    ensure_db_exists(DB_FILE)
    
    try:
        # 2. 抓取即時報價 (yfinance)
        gold_ticker = yf.Ticker("GC=F")
        silver_ticker = yf.Ticker("SI=F")
        
        # 使用 fast_info 獲取最新成交價，這在 2026 年依然是最穩定的方式
        g_price = round(gold_ticker.fast_info['last_price'], 2)
        s_price = round(silver_ticker.fast_info['last_price'], 2)
        current_gsr = round(g_price / s_price, 2)
        today = datetime.now().strftime("%Y-%m-%d")

        # 3. 準備新數據
        new_row = pd.DataFrame([[today, g_price, s_price, current_gsr]], 
                                columns=["Date", "Gold", "Silver", "GSR"])

        # 4. 讀取現有資料並合併
        df = pd.read_csv(DB_FILE)
        
        # 5. 避免同一天重複紀錄 (Idempotency 冪等性)
        if today not in df["Date"].values:
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            print(f"[{today}] 紀錄成功: Gold {g_price}, Silver {s_price}, GSR {current_gsr}")
        else:
            print(f"[{today}] 今日數據已存在，跳過儲存。")

    except Exception as e:
        print(f"[{datetime.now()}] 自動紀錄過程發生錯誤: {str(e)}")

if __name__ == "__main__":
    run_auto_save()