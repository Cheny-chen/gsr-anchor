# GSR Anchor - 金銀比自動監測系統

這是一個專門為了監測「1kg 實體白銀」價值錨定而設計的自動化工具。系統會每日自動紀錄金銀比 (GSR) 數據，並透過 Streamlit 視覺化圖表呈現，作為實體資產轉換（收割白銀換金子）的決策依據。

## 🚀 核心功能
- **自動化紀錄**：每日清晨 05:10 透過 Cron 抓取 `yfinance` 報價。
- **自癒能力**：自動檢查 `gsr_history.csv` 是否存在，若無則自動初始化。
- **數據視覺化**：動態展示金銀比走勢，輔助判斷白銀相對於黃金的價值水位。

## 🛠️ 開發與本地執行 (Local/SSH)

如果您要在 Ubuntu 伺服器上手動執行：

### 1. 環境初始化
```bash
# 更新系統並安裝 Python 環境
sudo apt update && sudo apt install -y python3-pip python3-venv

# 建立專案資料夾
mkdir -p ~/gsr-anchor && cd ~/gsr-anchor

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝必要的套件
pip install streamlit yfinance pandas plotly
```

2. 手動執行網頁
```Bash
./.venv/bin/python -m streamlit run app.py
```

## 📦 容器化部署 (Docker/docker)
這是目前最穩定、最推薦的部署方式，避開了權限與環境變數的衝突。

1. 構建鏡像 (Build)
```Bash
# 統一命名為 gsr-anchor
docker build -t gsr-anchor .
```

2. 啟動容器 (Run)
我們採用「指令注入」模式確保 Cron 服務啟動：

```Bash
docker run -d \
  --replace \
  -p 8080:80 \
  -v $(pwd):/app \
  --name gsr-anchor \
  localhost/gsr-anchor:latest \
  /bin/bash -c "service cron start && python cron_save.py && streamlit run app.py --server.port 80 --server.address 0.0.0.0"
```

## ☁️ Zeabur 雲端部署設定
若部署於 Zeabur，請選擇 github 安裝

## 📊 數據結構
gsr_history.csv: 儲存日期、金價、銀價及金銀比。

cron_save.py: 具備冪等性設計，同一天重複執行不會產生冗餘數據。