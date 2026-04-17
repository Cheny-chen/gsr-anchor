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
        # 1. 抓取報價 (使用 history 確保穩定性)
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        silver_comex = yf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
        
        # 印度白銀 (每股價格，約代表 1克)
        india_history = yf.Ticker("SILVERBEES.NS").history(period="1d")
        silver_bees_inr = india_history['Close'].iloc[-1] 

        # 2. 抓取匯率
        usdinr = yf.Ticker("USDINR=X").info.get('regularMarketPrice')
        if not usdinr: # 防呆：如果 info 抓不到，改用 history
            usdinr = yf.Ticker("USDINR=X").history(period="1d")['Close'].iloc[-1]

        # 3. 換算邏輯
        # 印度白銀(每盎司盧比) = 每股價格 * 31.1035
        silver_mcx_inr_oz = silver_bees_inr * 31.1035
        
        # 印度白銀(每盎司美金) = 盧比總價 / 匯率
        silver_mcx_usd_oz = silver_mcx_inr_oz / usdinr

        # 這裡回傳 4 個值，確保與外面接收端完全對應
        return (round(gold, 2), 
                round(silver_comex, 2), 
                round(silver_mcx_inr_oz, 2), 
                round(silver_mcx_usd_oz, 2))
                
    except Exception as e:
        st.error(f"數據更新失敗: {e}")
        # 必須也回傳 4 個值，否則會變數錯位
        return 0.0, 0.0, 0.0, 0.0

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
g_live, s_comex_live, s_mcx_inr_oz, s_mcx_usd_oz = get_live_prices()

if g_live > 0:
    # 全球 GSR = 黃金(USD) / 白銀(USD)
    current_gsr = round(g_live / s_comex_live, 2)
    
    # 印度 GSR = 黃金(USD) / 印度白銀(USD)
    # 這裡必須用 s_mcx_usd_oz，算出來才會是 60.94
    india_gsr = round(g_live / s_mcx_usd_oz, 2)


    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("黃金 COMEX", f"${g_live}")
    col2.metric("白銀 COMEX", f"${s_comex_live}")
    col3.metric("印度 Silver BEES", f"₹{s_mcx_inr_oz}",
                delta=f"{round(s_mcx_usd_oz, 2)} (USD)",
                delta_color="normal")

    # 顯示 COMEX GSR (基準 60)
    col4.metric("COMEX GSR", current_gsr, 
                delta=f"{round(current_gsr - 60, 2)} (vs 60)", 
                delta_color="inverse")
    
    # 顯示 India GSR (對比 COMEX 的差值)
    col5.metric("India GSR", india_gsr, 
                delta=f"{round(india_gsr - 60, 2)} (vs 60)",
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

# --- 區塊 C: 歷史區間分析 ---
if hist_df is not None and "Silver_COMEX" in hist_df.columns:
    st.subheader("📊 全球 vs. 印度白銀 (GSR對比)")

    fig_compare = go.Figure()

    # 1. COMEX GSR 軌跡 (藍色)
    fig_compare.add_trace(go.Scatter(
        x=hist_df["Date"], 
        y=hist_df["GSR_COMEX"],
        name="COMEX GSR", 
        mode='lines+markers',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=10, opacity=0.8),
        hovertemplate="COMEX GSR: %{y:.2f}<extra></extra>"
    ))

    # 2. 印度 GSR 軌跡 (綠色) - X 軸完全對齊，確保 Unified Hover 觸發
    fig_compare.add_trace(go.Scatter(
        x=hist_df["Date"], 
        y=hist_df["GSR_MCX"],
        name="India GSR", 
        mode='lines+markers',
        line=dict(color='#2ca02c', width=2),
        marker=dict(size=6, symbol='diamond'), # 用不同形狀區分，但滑鼠指過去會一起出
        hovertemplate="India GSR: %{y:.2f}<extra></extra>"
    ))

    # 3. 強制 Unified Hover：滑鼠指過去，兩個數據同時顯示在一個框裡
    fig_compare.update_layout(
        title="全球與印度金銀比同步監控 (GSR)",
        xaxis=dict(title="日期", type='date'),
        yaxis=dict(
            title="GSR 數值",
            gridcolor='lightgrey',
            # 讓 GSR 視窗集中在 55~65 之間 (或根據即時數據動態調整)
            range=[current_gsr - 5, current_gsr + 5]
        ),
        # 核心設定：x unified 會把同一個時間點的所有數據合併到一個 Tooltip
        hovermode="x unified",
        legend=dict(x=0, y=1.1, orientation="h"),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    # 處理單點縮放 (前後 12 小時，視圖更清楚)
    if len(hist_df) == 1:
        single_date = hist_df['Date'].iloc[0]
        fig_compare.update_xaxes(range=[single_date - timedelta(hours=12), single_date + timedelta(hours=12)])

    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.info("⌛ 尚未發現符合格式的歷史資料。")