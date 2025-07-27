# utils.py

import yfinance as yf
import pandas as pd
import pandas_ta as ta


def load_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Date"}, inplace=True)
    return df


def apply_indicators(df: pd.DataFrame, rsi_period: int = 14, ema_period: int = 20, atr_period: int = 14) -> pd.DataFrame:
    df.ta.rsi(length=rsi_period, append=True)
    df.ta.ema(length=ema_period, append=True)
    df.ta.atr(length=atr_period, append=True)
    return df
