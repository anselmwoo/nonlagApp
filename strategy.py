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
        # 取价格源
        src = self.df[self.src_option].copy()
        src.index = self.df.index  # 保证索引一致
    
        # 计算滤波和非滞后均线
        std_filtered = self.std_filter(src)
        clutter_filtered = self.clutter_filter(std_filtered)
    
        nlma = self.nonlag_ma(clutter_filtered)
        nlma.index = self.df.index
    
        # 初始化结果表
        self.result['price'] = src
        self.result['nonlagma'] = nlma
        self.result['signal'] = 0
    
        # 计算买入信号 — 价格今天刚上穿非滞后均线，昨天价格在均线下
        buy_signal = (src > nlma) & (src.shift(1) <= nlma.shift(1))
        # 计算卖出信号 — 价格今天刚下穿非滞后均线，昨天价格在均线上
        sell_signal = (src < nlma) & (src.shift(1) >= nlma.shift(1))
    
        # 避免 NaN 干扰，填充为 False
        buy_signal = buy_signal.fillna(False)
        sell_signal = sell_signal.fillna(False)
    
        # 打印调试信息
        print("buy_signal count:", buy_signal.sum())
        print("sell_signal count:", sell_signal.sum())
        print("Sample buy_signal:\n", buy_signal[buy_signal].head())
        print("Sample sell_signal:\n", sell_signal[sell_signal].head())
    
        # 用索引定位赋值，避免索引不匹配错误
        self.result.loc[buy_signal[buy_signal].index, 'signal'] = 1
        self.result.loc[sell_signal[sell_signal].index, 'signal'] = -1
    
        return self.result
