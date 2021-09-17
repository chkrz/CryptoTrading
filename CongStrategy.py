import os
from binance.client import Client
import math
from binance.enums import *
import time
import pandas as pd


def get_hl(left, right, candles):
    high = 0
    low = float("inf")
    for i in range(left, right):
        high = max(float(candles[i][2]), high)
        low = min(float(candles[i][3]), low)
    return high, low


top_pct = 0.1
interval = "1h"
# 单位为interval
period = 24   # 比较过去24h涨幅
period2 = 2   # 孕线的周期
symbol_table = ["BNBBTC", "ALICEBTC"]
trade_symbol = pd.DataFrame(index=symbol_table, columns=["change", "pattern"])

api_key = ''
api_secret = ''
client = Client(api_key=api_key, api_secret=api_secret)

all_candles = {}
for symbol in symbol_table:
    all_candles[symbol] = client.get_klines(symbol=symbol, interval=interval)

for symbol in all_candles:
    candles = all_candles[symbol]
    trade_symbol.loc[symbol, "change"] = float(candles[-1][4]) / float(candles[-period][1]) - 1

    high1, low1 = get_hl(0, period2, candles)
    high2, low2 = get_hl(period2, 2 * period2, candles)
    trade_symbol.loc[symbol, "pattern"] = (high1 < high2) and (low1 > low2)

trade_symbol.sort_values(["change"], ascending=False)
n = int(len(trade_symbol)*top_pct) + 1
final_symbol = trade_symbol.iloc[0:n]
final_symbol = final_symbol[final_symbol["pattern"] == True]
print(final_symbol)