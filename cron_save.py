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
        # 1. 抓取報價與匯率
        gold_ticker = yf.Ticker("GC=F")
        silver_comex_ticker = yf.Ticker("SI=F")
        silver_mcx_ticker = yf.Ticker("SILVERBEES.NS")
        usdinr_ticker = yf.Ticker("USDINR=X") # 必須抓匯率！

        g_price = round(gold_ticker.fast_info['last_price'], 2)
        s_comex_price = round(silver_comex_ticker.fast_info['last_price'], 2)
        s_mcx_raw = silver_mcx_ticker.fast_info['last_price'] # 這是印度每股(克)盧比
        
        # 取得最新匯率 (防呆：抓不到就設個常數)
        usdinr = usdinr_ticker.fast_info['last_price']
        if not usdinr: usdinr = 93.0 

        # 2. 【核心修正】將印度白銀換算為 USD/oz
        # 換算公式：(盧比單價 * 31.1035) / 匯率
        s_mcx_usd_oz = round((s_mcx_raw * 31.1035) / usdinr, 2)

        # 3. 分別計算兩套 GSR (這才是正確的對比！)
        gsr_comex = round(g_price / s_comex_price, 2)
        gsr_mcx = round(g_price / s_mcx_usd_oz, 2) # 美金金價 / 美金印度銀價
        
        today = datetime.now().strftime("%Y-%m-%d")

        # 4. 準備新數據列 (存入 CSV 時，Silver_MCX 存換算後的 USD 價格，圖表才會對齊)
        new_row = pd.DataFrame([[today, g_price, s_comex_price, s_mcx_usd_oz, gsr_comex, gsr_mcx]], 
                                columns=["Date", "Gold", "Silver_COMEX", "Silver_MCX", "GSR_COMEX", "GSR_MCX"])

        # ... (後續存檔邏輯不變))

    except Exception as e:
        print(f"[{datetime.now()}] 存檔失敗: {str(e)}")

if __name__ == "__main__":
    run_auto_save()