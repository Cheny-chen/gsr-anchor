import os
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 設定頁面與樣式
st.set_page_config(page_title="GSR Anchor Dashboard", layout="wide")

# 1. 路徑設定
db_path = os.getenv("GSR_DB_PATH", "data/gsr_history.csv")
DB_FILE = db_path

# --- 功能函式 ---
def get_live_prices():
    try:
        # 1. 抓取報價 (改用 history 確保穩定性)
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        silver_comex = yf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
        
        # 抓取印度白銀 (改用 history 抓取最新收盤價，避免 2.55 這種異常值)
        india_ticker = yf.Ticker("SILVERBEES.NS")
        india_history = india_ticker.history(period="1d")
        silver_mcx_inr = india_history['Close'].iloc[-1]
        
        # 2. 抓取匯率 (USD/INR)
        usdinr = yf.Ticker("USDINR=X").info.get('regularMarketPrice')

        # 3. 換算印度銀價回美金 (對齊天秤)
        silver_mcx_usd = silver_mcx_inr * 31.1035

        # Get current price info
        print('---', usdinr, silver_mcx_usd)
        
        return round(gold, 2), round(silver_comex, 2), round(silver_mcx_usd, 2), usdinr
    except Exception as e:
        st.error(f"數據更新失敗: {e}")
        return 0.0, 0.0, 0.0

def load_history():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except:
            return None
    return None

# 執行讀取
hist_df = load_history()

# --- UI 介面 ---
st.title("🥇 GSR Anchor | 全球白銀戰情室")

# 區塊 A: 即時看板
g_live, s_comex_live, s_mcx_live, usdinr = get_live_prices()

if g_live > 0:
    current_gsr = round(g_live / s_comex_live, 2)
    india_gsr = round(g_live / s_mcx_live, 2) 
    
    # 計算印度相對於全球的溢價差
    gsr_diff = round(india_gsr - current_gsr, 2)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("黃金 COMEX", f"${g_live}")
    col2.metric("白銀 COMEX", f"${s_comex_live}")
    col3.metric("印度 Silver BEES", f"₹{s_mcx_live}",
                delta=f"{round(s_mcx_live / usdinr, 2)} (USD)",
                delta_color="normal")

    # 顯示 COMEX GSR (基準 60)
    col4.metric("COMEX GSR", current_gsr, 
                delta=f"{round(current_gsr - 60, 2)} (vs 60)", 
                delta_color="inverse")
    
    # 顯示 India GSR (對比 COMEX 的差值)
    col5.metric("India GSR", india_gsr, 
                delta=f"{gsr_diff} (vs 60)",
                delta_color="inverse")
else:
    st.warning("⚠️ 無法獲取即時報價，請檢查網路。")
    current_gsr = 60.0

# 區塊 B: 實體資產轉換計算
st.divider()
st.subheader("📦 實體資產轉換計算")
c1, c2, c3 = st.columns(3)
qty = c1.number_input("您的白銀持有量", value=1.0, step=0.1)
unit = c2.selectbox("單位", ["kg", "oz", "g"])

silver_oz = qty * 32.1507 if unit == "kg" else (qty / 31.1035 if unit == "g" else qty)
gold_g = (silver_oz / current_gsr) * 31.1035

with c3:
    st.write("") 
    st.info(f"💡 等值黃金: **{gold_g:.2f} g** (約 **{gold_g/37.5:.2f} 兩**)")

# 區塊 C: 歷史區間分析
st.divider()

if hist_df is not None and "Silver_COMEX" in hist_df.columns:
    st.subheader("📊 COMEX vs. 印度 MCX 白銀趨勢對比")

    fig_compare = go.Figure()

    # COMEX 軌跡
    fig_compare.add_trace(go.Scatter(
        x=hist_df["Date"], 
        y=hist_df["Silver_COMEX"],
        name="COMEX Silver (USD)", mode='lines+markers',
        line=dict(color='#1f77b4'), marker=dict(size=8),
        yaxis="y1"
    ))

    # 印度軌跡
    fig_compare.add_trace(go.Scatter(
        x=hist_df["Date"] + pd.Timedelta(hours=2), # 往後移 2 小時，視覺上會並排
        y=hist_df["Silver_MCX"],
        name="India MCX (INR)", mode='lines+markers',
        line=dict(color='#2ca02c'), marker=dict(size=8),
        yaxis="y2"
    ))

    # 修正後的 update_layout
    fig_compare.update_layout(
        title="全球與印度白銀同步率監控",
        xaxis=dict(title="日期"),
        # 左側 Y 軸
        yaxis=dict(
            title=dict(
                text="COMEX 價格 (USD)",
                font=dict(color="#1f77b4")
            ),
            tickfont=dict(color="#1f77b4")
        ),
        # 右側 Y 軸
        yaxis2=dict(
            title=dict(
                text="印度價格 (INR)",
                font=dict(color="#2ca02c")
            ),
            tickfont=dict(color="#2ca02c"),
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0, y=1.1, orientation="h"),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    if len(hist_df) == 1:
        single_date = hist_df['Date'].iloc[0]
        fig_compare.update_xaxes(range=[single_date - timedelta(days=3), single_date + timedelta(days=3)])

    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.info("⌛ 尚未發現符合格式的歷史資料。")