# 更新系統並安裝 Python 環境
sudo apt update && sudo apt install -y python3-pip python3-venv

# 建立專案資料夾
mkdir -p ~/gsr-anchor && cd ~/gsr-anchor

# 建立並進入虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝必要的套件
pip install streamlit yfinance pandas plotly

# 單純執行
./.venv/bin/python -m streamlit run app.py

# docker build
docker build .

# docker run
docker run -d \
  -p 8080:80 \
  -v $(pwd)/gsr_history.csv:/app/gsr_history.csv \
  --name gsr-monitor \
  f58a21786c49
