# backtest.py
import pandas as pd
import numpy as np

# 策略回测函数
def backtest_strategy(df, long_signals, short_signals):
    df = df.copy()
    df['Position'] = 0
    df.loc[long_signals, 'Position'] = 1
    df.loc[short_signals, 'Position'] = -1
    df['Position'] = df['Position'].ffill().fillna(0)

    df['Return'] = df['Close'].pct_change()
    df['Strategy'] = df['Position'].shift(1) * df['Return']

    df['Equity'] = (1 + df['Strategy']).cumprod()
    df['BuyHold'] = (1 + df['Return']).cumprod()
    df.dropna(inplace=True)
    return df

# 获取绩效指标
def get_performance_metrics(df):
    cumulative_return = df['Equity'].iloc[-1] - 1
    max_drawdown = ((df['Equity'].cummax() - df['Equity']) / df['Equity'].cummax()).max()
    sharpe = df['Strategy'].mean() / df['Strategy'].std() * np.sqrt(252) if df['Strategy'].std() != 0 else 0

    return {
        "Cumulative Return": round(cumulative_return, 4),
        "Max Drawdown": round(max_drawdown, 4),
        "Sharpe Ratio": round(sharpe, 2)
    }
