import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class NonLagMaStrategy:
    def __init__(self, df, period=25, src_option='Close',
                 std_threshold=0.1, filter_strength=0.5,
                 enable_std_filter=True, enable_clutter_filter=True):
        self.df = df.copy()
        self.period = period
        self.src_option = src_option
        self.std_threshold = std_threshold
        self.filter_strength = filter_strength
        self.enable_std_filter = enable_std_filter
        self.enable_clutter_filter = enable_clutter_filter
        self.result = pd.DataFrame(index=self.df.index)

    def std_filter(self, src):
        std = src.rolling(window=self.period, min_periods=1).std()
        mean = src.rolling(window=self.period, min_periods=1).mean()
        filt = (src - mean).abs() < self.std_threshold * std
        filtered = src.where(filt, other=np.nan)
        # 用前值填充NaN，避免断点（也可以注释掉试试）
        filtered = filtered.fillna(method='ffill')
        return filtered

    def clutter_filter(self, series):
        span = max(1, int(self.period * self.filter_strength))
        return series.ewm(span=span, adjust=False).mean()

    def nonlag_ma(self, src):
        alpha = 2 / (self.period + 1)
        ma = src.copy()
        for i in range(1, len(src)):
            ma.iloc[i] = (1 - alpha) * ma.iloc[i - 1] + alpha * src.iloc[i]
        return ma

    def generate_signals(self):
        # 取价格源
        src = self.df[self.src_option].copy()

        # 选择是否启用 std_filter
        if self.enable_std_filter:
            std_filtered = self.std_filter(src)
        else:
            std_filtered = src.copy()

        # 选择是否启用 clutter_filter
        if self.enable_clutter_filter:
            clutter_filtered = self.clutter_filter(std_filtered)
        else:
            clutter_filtered = std_filtered.copy()

        nlma = self.nonlag_ma(clutter_filtered)

        self.result['price'] = src
        self.result['std_filtered'] = std_filtered
        self.result['clutter_filtered'] = clutter_filtered
        self.result['nonlagma'] = nlma
        self.result['signal'] = 0

        # 买入信号：今日价格刚上穿非滞后均线，昨日价格在均线下
        buy_signal = (src > nlma) & (src.shift(1) <= nlma.shift(1))
        # 卖出信号：今日价格刚下穿非滞后均线，昨日价格在均线上
        sell_signal = (src < nlma) & (src.shift(1) >= nlma.shift(1))

        # 填充NaN为False，防止赋值错误
        buy_signal = buy_signal.fillna(False)
        sell_signal = sell_signal.fillna(False)

        # 打印调试信息
        print(f"买入信号数量: {buy_signal.sum()}")
        print(f"卖出信号数量: {sell_signal.sum()}")
        print("买入信号索引示例:", buy_signal[buy_signal].index[:5])
        print("卖出信号索引示例:", sell_signal[sell_signal].index[:5])

        self.result.loc[buy_signal[buy_signal].index, 'signal'] = 1
        self.result.loc[sell_signal[sell_signal].index, 'signal'] = -1

        return self.result

    def plot(self):
        plt.figure(figsize=(14, 7))
        plt.plot(self.result.index, self.result['price'], label='Price', color='blue')
        plt.plot(self.result.index, self.result['nonlagma'], label='NonLagMA', color='orange')
        plt.scatter(self.result.index[self.result['signal'] == 1],
                    self.result['price'][self.result['signal'] == 1],
                    label='买入信号', marker='^', color='green', s=100)
        plt.scatter(self.result.index[self.result['signal'] == -1],
                    self.result['price'][self.result['signal'] == -1],
                    label='卖出信号', marker='v', color='red', s=100)
        plt.title("NonLagMA 策略信号图")
        plt.legend()
        plt.grid(True)
        plt.show()
