import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import os

# 設定頁面與樣式
st.set_page_config(page_title="GSR Anchor Dashboard", layout="wide")

# 與 cron_save.py 共用同一個檔名
DB_FILE = "gsr_history.csv"

# --- 核心函式 ---
@st.cache_data(ttl=300) # 網頁打開時，每 5 分鐘快取一次最新報價
def get_live_prices():
    try:
        g = yf.Ticker("GC=F").fast_info['last_price']
        s = yf.Ticker("SI=F").fast_info['last_price']
        return round(g, 2), round(s, 2)
    except:
        return 4800.0, 80.0 # 抓取失敗時的保底值

def load_history():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return None

# --- UI 介面 ---
st.title("🥇 GSR Anchor | 金銀比監測站")

# 區塊 A: 即時看板
g_price, s_price = get_live_prices()
current_gsr = round(g_price / s_price, 2)

col1, col2, col3 = st.columns(3)
col1.metric("Gold Price (oz)", f"${g_price}")
col2.metric("Silver Price (oz)", f"${s_price}")
col3.metric("Current GSR", current_gsr, delta=f"{round(current_gsr - 60, 2)} (vs 基準 60)")

# 區塊 B: 實體資產轉換計算
st.divider()
st.subheader("📦 實體資產轉換計算")
c1, c2, c3 = st.columns(3)
qty = c1.number_input("您的白銀持有量", value=1.0, step=0.1)
unit = c2.selectbox("單位", ["kg", "oz", "g"])

# 換算邏輯 (1kg = 32.1507 oz)
silver_oz = qty * 32.1507 if unit == "kg" else (qty / 31.1035 if unit == "g" else qty)
# 換算回黃金公克 (1oz = 31.1035g)
gold_g = (silver_oz / current_gsr) * 31.1035

st.info(f"💡 目前您的 {qty} {unit} 白銀等值於 **{gold_g:.2f} 公克** 黃金 (約 **{gold_g/37.5:.2f} 台兩**)")

# 區塊 C: 歷史區間分析 (自動讀取 CSV)
st.divider()
st.subheader("📊 歷史趨勢分析 (無人值守自動紀錄)")

hist_df = load_history()

if hist_df is not None:
    # 畫圖
    fig = px.line(hist_df, x="Date", y="GSR", title="金銀比歷史波動曲線")
    fig.add_hline(y=30, line_dash="dot", line_color="red", annotation_text="收割目標 30:1")
    st.plotly_chart(fig, use_container_width=True)
    
    # 狀態提醒
    if current_gsr > 80:
        st.warning("⚠️ 目前白銀被嚴重低估，是「累積白銀」的好時機。")
    elif current_gsr < 40:
        st.error("🚨 白銀進入狂熱區間，請準備執行「換金計畫」。")
else:
    st.info("系統正在等待今日收盤後的第一次自動紀錄...")