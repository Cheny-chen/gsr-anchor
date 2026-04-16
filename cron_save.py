import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 環境設定
db_path = os.getenv("GSR_DB_PATH", "data/gsr_history.csv")
DB_FILE = db_path

def ensure_db_exists(csv_path):
    """確保 CSV 檔案存在，新增 GSR_COMEX 與 GSR_MCX 欄位"""
    if not os.path.exists(csv_path):
        # 這裡新增了 GSR_MCX 欄位
        df = pd.DataFrame(columns=["Date", "Gold", "Silver_COMEX", "Silver_MCX", "GSR_COMEX", "GSR_MCX"])
        df.to_csv(csv_path, index=False)
        print(f"[{datetime.now()}] 初始資料庫已建立: {csv_path}")

def run_auto_save():
    ensure_db_exists(DB_FILE)
    
    try:
        # 2. 抓取三項核心報價
        gold_ticker = yf.Ticker("GC=F")
        silver_comex_ticker = yf.Ticker("SI=F")
        silver_mcx_ticker = yf.Ticker("SILVERBEES.NS")
        
        g_price = round(gold_ticker.fast_info['last_price'], 2)
        s_comex_price = round(silver_comex_ticker.fast_info['last_price'], 2)
        s_mcx_price = round(silver_mcx_ticker.fast_info['last_price'], 2)

        # 3. 分別計算兩套 GSR
        gsr_comex = round(g_price / s_comex_price, 2)
        gsr_mcx = round(g_price / s_mcx_price, 2)
        
        today = datetime.now().strftime("%Y-%m-%d")

        # 4. 準備新數據列 (對應 6 個欄位)
        new_row = pd.DataFrame([[today, g_price, s_comex_price, s_mcx_price, gsr_comex, gsr_mcx]], 
                                columns=["Date", "Gold", "Silver_COMEX", "Silver_MCX", "GSR_COMEX", "GSR_MCX"])

        # 5. 讀取並合併 (Idempotency 檢查)
        df = pd.read_csv(DB_FILE)
        if today not in df["Date"].astype(str).values:
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            print(f"[{today}] 雙市場紀錄成功！")
        else:
            print(f"[{today}] 今日數據已存在。")

    except Exception as e:
        print(f"[{datetime.now()}] 存檔失敗: {str(e)}")

if __name__ == "__main__":
    run_auto_save()