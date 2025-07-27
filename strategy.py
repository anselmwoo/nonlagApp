import pandas as pd
import numpy as np

class NonLagMaStrategy:
    def __init__(self, df, period=25, src_option='Close', std_threshold=0.1, filter_strength=0.5):
        self.df = df.copy()
        self.period = period
        self.src_option = src_option
        self.std_threshold = std_threshold
        self.filter_strength = filter_strength
        self.result = pd.DataFrame(index=self.df.index)

    def std_filter(self, src):
        std = src.rolling(window=self.period).std()
        mean = src.rolling(window=self.period).mean()
        filt = (src - mean).abs() < self.std_threshold * std
        return src.where(filt, other=np.nan).fillna(method='ffill')

    def clutter_filter(self, series):
        # 用指数加权平均模拟clutter滤波，参数可调
        return series.ewm(span=int(self.period * self.filter_strength), adjust=False).mean()

    def nonlag_ma(self, src):
        alpha = 2 / (self.period + 1)
        ma = src.copy()
        for i in range(1, len(src)):
            ma.iloc[i] = (1 - alpha) * ma.iloc[i - 1] + alpha * src.iloc[i]
        return ma

    def generate_signals(self):
        src = self.df[self.src_option].copy()
    
        std_filtered = self.std_filter(src)
        clutter_filtered = self.clutter_filter(std_filtered)
    
        nlma = self.nonlag_ma(clutter_filtered)
    
        self.result['price'] = src
        self.result['nonlagma'] = nlma
        self.result['signal'] = 0
    
        buy_signal = (src > nlma) & (src.shift(1) <= nlma.shift(1))
        sell_signal = (src < nlma) & (src.shift(1) >= nlma.shift(1))
    
        # 转成bool ndarray，避免索引不匹配问题
        buy_mask = buy_signal.fillna(False).values
        sell_mask = sell_signal.fillna(False).values
    
        self.result.loc[buy_mask, 'signal'] = 1
        self.result.loc[sell_mask, 'signal'] = -1
    
        return self.result
    
