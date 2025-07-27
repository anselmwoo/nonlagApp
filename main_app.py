import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from strategy import non_lag_ma_strategy

st.set_page_config(page_title="Heikin-Ashi NonLagMA Strategy", layout="wide")
st.title("📈 Heikin-Ashi + STD/Clutter Filtered NonLagMA Strategy")

# Sidebar parameters
st.sidebar.header("🔧 策略参数")
symbol = st.sidebar.text_input("股票代码（Yahoo Finance）", value="AAPL")
start = st.sidebar.date_input("开始日期", pd.to_datetime("2023-01-01"))
end = st.sidebar.date_input("结束日期", pd.to_datetime("today"))
interval = st.sidebar.selectbox("K线周期", ["1d", "1h", "15m"], index=0)

per = st.sidebar.slider("Period", 5, 100, 25)
srcoption = st.sidebar.selectbox("价格源", ["Close", "Open", "High", "Low", "HL2", "HLC3", "OHLC4"], index=0)
stdFilter = st.sidebar.checkbox("启用 STD Filter", value=True)
clutterFilt = st.sidebar.checkbox("启用 Clutter Filter", value=True)
sigtype = st.sidebar.selectbox("信号类型", ["both", "buy", "sell"], index=0)

# Load data
data_load_state = st.text("加载数据中...")
data = yf.download(symbol, start=start, end=end, interval=interval)
data.dropna(inplace=True)
data_load_state.text("数据加载完成 ✅")

# Apply strategy
df = non_lag_ma_strategy(
    data,
    per=per,
    srcoption=srcoption,
    stdFilter=stdFilter,
    clutterFilt=clutterFilt,
    sigtype=sigtype
)

# Plot Heikin Ashi chart
st.subheader("📊 K线图 + 策略信号")
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['HA_Open'],
    high=df['HA_High'],
    low=df['HA_Low'],
    close=df['HA_Close'],
    name="Heikin-Ashi"
))

fig.add_trace(go.Scatter(x=df.index, y=df['nonlagma'], line=dict(color='orange'), name="NonLagMA"))
fig.add_trace(go.Scatter(x=df[df['signal'] == 1].index, y=df[df['signal'] == 1]['HA_Close'],
                         mode='markers', name='Buy Signal', marker=dict(color='green', size=10, symbol='triangle-up')))
fig.add_trace(go.Scatter(x=df[df['signal'] == -1].index, y=df[df['signal'] == -1]['HA_Close'],
                         mode='markers', name='Sell Signal', marker=dict(color='red', size=10, symbol='triangle-down')))

fig.update_layout(height=600, width=1000, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# Backtest summary
st.subheader("📈 回测结果")
capital = 10000
position = 0
cash = capital
trade_log = []

for i in range(1, len(df)):
    row = df.iloc[i]
    prev = df.iloc[i - 1]

    if row['signal'] == 1 and cash > row['HA_Close']:
        position = cash // row['HA_Close']
        cash -= position * row['HA_Close']
        trade_log.append([row.name, 'Buy', row['HA_Close'], position, cash])

    elif row['signal'] == -1 and position > 0:
        cash += position * row['HA_Close']
        trade_log.append([row.name, 'Sell', row['HA_Close'], position, cash])
        position = 0

final_value = cash + position * df['HA_Close'].iloc[-1]
profit = final_value - capital

st.metric("最终资产", f"${final_value:,.2f}", delta=f"${profit:,.2f}")

# Trade log table
st.subheader("📋 交易明细表")
if trade_log:
    df_log = pd.DataFrame(trade_log, columns=["时间", "操作", "价格", "股数", "现金余额"])
    st.dataframe(df_log)
else:
    st.write("无交易记录。")
