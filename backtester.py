# backtester.py

import pandas as pd
import numpy as np
import requests

API_KEY = "M369PH68TX0PTVYP"
SYMBOL = "XAU"
MARKET = "USD"

def max_drawdown(equity):
    peak = equity[0] if equity else 0
    max_dd = 0
    for x in equity:
        if x > peak:
            peak = x
        dd = peak - x
        if dd > max_dd:
            max_dd = dd
    return max_dd

def fetch_data(interval="5min", outputsize="full", start_date=None, end_date=None):
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={SYMBOL}&to_symbol={MARKET}&interval={interval}&apikey={API_KEY}&outputsize={outputsize}"
    r = requests.get(url)
    data = r.json()

    if 'Time Series FX (' not in data and 'Error Message' in data:
        raise Exception(data['Error Message'])

    key = [k for k in data.keys() if 'Time Series FX' in k][0]
    df = pd.DataFrame.from_dict(data[key], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.rename(columns={
        "1. open":"open",
        "2. high":"high",
        "3. low":"low",
        "4. close":"close"
    }).astype(float)

    # Filter by date if provided
    if start_date:
        df = df[df.index >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df.index <= pd.to_datetime(end_date)]

    return df

def run_backtest(interval="5min", start_date=None, end_date=None):
    df = fetch_data(interval=interval, start_date=start_date, end_date=end_date)
    df_1h = df.resample('1H').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()

    balance = 1000
    risk_per_trade = 20
    trades = []
    equity = []

    for i in range(20, len(df)):
        current_time = df.index[i]
        if current_time not in df_1h.index:
            continue

        htf = df_1h.loc[:current_time].iloc[-20:]
        if len(htf) < 20:
            continue

        bias = None
        if htf['close'].iloc[-1] > htf['high'].max():
            bias = "bullish"
        elif htf['close'].iloc[-1] < htf['low'].min():
            bias = "bearish"

        candle = df.iloc[i]
        prev = df.iloc[i-1]

        entry = stop = target = None

        if bias == "bullish":
            if candle['low'] < prev['low'] and candle['close'] > candle['open']:
                entry = candle['close']
                stop = candle['low']
                risk = entry - stop
                target = entry + 2*risk

        elif bias == "bearish":
            if candle['high'] > prev['high'] and candle['close'] < candle['open']:
                entry = candle['close']
                stop = candle['high']
                risk = stop - entry
                target = entry - 2*risk

        if entry:
            position_size = risk_per_trade / risk
            future = df.iloc[i+1:i+20]
            for _, row in future.iterrows():
                if bias == "bullish":
                    if row['low'] <= stop:
                        balance -= risk_per_trade
                        trades.append(-risk_per_trade)
                        break
                    if row['high'] >= target:
                        balance += risk_per_trade*2
                        trades.append(risk_per_trade*2)
                        break
                elif bias == "bearish":
                    if row['high'] >= stop:
                        balance -= risk_per_trade
                        trades.append(-risk_per_trade)
                        break
                    if row['low'] <= target:
                        balance += risk_per_trade*2
                        trades.append(risk_per_trade*2)
                        break
        equity.append(balance)

    win_rate = len([t for t in trades if t > 0]) / len(trades) * 100 if trades else 0
    max_dd = max_drawdown(equity)

    return {
        "final_balance": round(balance,2),
        "total_trades": len(trades),
        "win_rate": round(win_rate,2),
        "max_drawdown": round(max_dd,2)
    }
