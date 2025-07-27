import pandas as pd
import numpy as np
import ta

class NonLagMaStrategy:
    def __init__(self, df, period=25, src_option='close', std_threshold=1.0, filt_strength=0.5):
        self.df = df.copy()
        self.period = period
        self.src_option = src_option
        self.std_threshold = std_threshold
        self.filt_strength = filt_strength
        self.result = pd.DataFrame(index=self.df.index)

    def std_filter(self, src):
        std = src.rolling(window=self.period).std()
        mean = src.rolling(window=self.period).mean()
        filt = (src - mean).abs() < self.std_threshold * std
        return src.where(filt)

    def clutter_filter(self, series):
        return series.ewm(span=int(self.period * self.filt_strength), adjust=False).mean()

    def nonlag_ma(self, src):
        alpha = 2 / (self.period + 1)
        ma = src.copy()
        for i in range(1, len(src)):
            ma.iloc[i] = (1 - alpha) * ma.iloc[i - 1] + alpha * src.iloc[i]
        return ma

    def generate_signals(self):
        src = self.df[self.src_option]
        std_filtered = self.std_filter(src)
        clutter_filtered = self.clutter_filter(std_filtered)
        nlma = self.nonlag_ma(clutter_filtered)

        self.result['price'] = src
        self.result['nlma'] = nlma

        # Signal logic
        self.result['signal'] = 0
        self.result.loc[(src > nlma) & (src.shift(1) <= nlma.shift(1)), 'signal'] = 1  # buy
        self.result.loc[(src < nlma) & (src.shift(1) >= nlma.shift(1)), 'signal'] = -1  # stop loss/sell

        return self.result

    def backtest(self):
        df = self.result.copy()
        df['position'] = df['signal'].replace(to_replace=0, method='ffill').fillna(0)
        df['returns'] = self.df['close'].pct_change()
        df['strategy'] = df['position'].shift(1) * df['returns']
        df['cum_returns'] = (1 + df['returns']).cumprod()
        df['cum_strategy'] = (1 + df['strategy']).cumprod()
        self.result = df
        return df

    def get_trades(self):
        trades = self.result[self.result['signal'] != 0][['price', 'signal']]
        trades['timestamp'] = trades.index
        return trades.reset_index(drop=True)
