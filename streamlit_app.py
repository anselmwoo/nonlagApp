import streamlit as st
from backtest import run_backtest

st.title("小盘股波动回测策略")
if st.button("运行策略"):
    run_backtest()