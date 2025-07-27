import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from strategy import NonLagMaStrategy

st.set_page_config(page_title="NonLagMA Strategy Demo", layout="wide")

st.title("📈 Heikin-Ashi + NonLag MA 策略回测")

# 侧边栏参数输入
symbol = st.sidebar.text_input("股票代码 (Yahoo Finance)", value="RCAT")
start_date = st.sidebar.date_input("开始日期", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("结束日期", pd.to_datetime("today"))
interval = st.sidebar.selectbox("K线周期", ["1d", "1h", "15m"], index=0)

period = st.sidebar.slider("NonLagMA周期", 5, 100, 25)
src_option = st.sidebar.selectbox("价格源", ["Open", "High", "Low", "Close"], index=3)
std_threshold = st.sidebar.slider("STD Filter阈值", 0.0, 1.0, 0.1, 0.01)
filter_strength = st.sidebar.slider("Clutter Filter 强度", 0.1, 1.0, 0.5, 0.01)

# 载入数据
data_load_state = st.text("加载数据中...")
df = yf.download(symbol, start=start_date, end=end_date, interval=interval)
if df.empty:
    st.error("未能获取数据，请检查股票代码或网络")
    st.stop()
data_load_state.text("数据加载完成 ✅")

# 执行策略
strategy = NonLagMaStrategy(
    df=df,
    period=period,
    src_option=src_option,
    std_threshold=std_threshold,
    filter_strength=filter_strength,
)

result_df = strategy.generate_signals()

# 绘制K线图与信号点
st.subheader("📊 策略与价格走势图")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name="Price"
))
fig.add_trace(go.Scatter(
    x=result_df.index,
    y=result_df['nonlagma'],
    line=dict(color='orange'),
    name='NonLagMA'
))
fig.add_trace(go.Scatter(
    x=result_df[result_df['signal'] == 1].index,
    y=result_df[result_df['signal'] == 1]['price'],
    mode='markers',
    name='买入信号',
    marker=dict(color='green', size=10, symbol='triangle-up')
))
fig.add_trace(go.Scatter(
    x=result_df[result_df['signal'] == -1].index,
    y=result_df[result_df['signal'] == -1]['price'],
    mode='markers',
    name='卖出信号',
    marker=dict(color='red', size=10, symbol='triangle-down')
))

fig.update_layout(height=600, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# 简单回测统计
st.subheader("📈 简单回测结果")

capital = 10000
position = 0
cash = capital
trade_log = []

for i in range(1, len(result_df)):
    row = result_df.iloc[i]
    prev = result_df.iloc[i - 1]

    if row['signal'] == 1 and cash > row['price']:
        # 买入全部仓位（可按需求修改为固定手数）
        position = cash // row['price']
        cash -= position * row['price']
        trade_log.append([row.name, '买入', row['price'], position, cash])

    elif row['signal'] == -1 and position > 0:
        # 卖出全部仓位
        cash += position * row['price']
        trade_log.append([row.name, '卖出', row['price'], position, cash])
        position = 0

final_value = cash + position * result_df['price'].iloc[-1]
profit = final_value - capital

st.metric("最终资产", f"${final_value:,.2f}", delta=f"${profit:,.2f}")

st.subheader("📋 交易明细")

if trade_log:
    trades_df = pd.DataFrame(trade_log, columns=["时间", "操作", "价格", "数量", "现金余额"])
    st.dataframe(trades_df)
else:
    st.write("无交易记录")

