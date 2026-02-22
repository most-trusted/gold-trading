import pandas as pd
import numpy as np

def run_backtest(df):

    df.columns = [c.lower() for c in df.columns]

    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)

    df_5m = df.resample('5T').agg({
        'open':'first',
        'high':'max',
        'low':'min',
        'close':'last'
    }).dropna()

    df_1h = df.resample('1H').agg({
        'open':'first',
        'high':'max',
        'low':'min',
        'close':'last'
    }).dropna()

    balance = 1000
    risk_per_trade = 20
    trades = []
    equity = []

    for i in range(20, len(df_5m)):

        current_time = df_5m.index[i]

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

        candle = df_5m.iloc[i]
        prev = df_5m.iloc[i-1]

        entry = None
        stop = None
        target = None

        if bias == "bullish":
            if candle['low'] < prev['low'] and candle['close'] > candle['open']:
                entry = candle['close']
                stop = candle['low']
                risk = entry - stop
                target = entry + 2 * risk

        elif bias == "bearish":
            if candle['high'] > prev['high'] and candle['close'] < candle['open']:
                entry = candle['close']
                stop = candle['high']
                risk = stop - entry
                target = entry - 2 * risk

        if entry:
            position_size = risk_per_trade / risk

            future = df_5m.iloc[i+1:i+20]

            for _, row in future.iterrows():
                if bias == "bullish":
                    if row['low'] <= stop:
                        balance -= risk_per_trade
                        trades.append(-risk_per_trade)
                        break
                    if row['high'] >= target:
                        balance += risk_per_trade * 2
                        trades.append(risk_per_trade * 2)
                        break

                elif bias == "bearish":
                    if row['high'] >= stop:
                        balance -= risk_per_trade
                        trades.append(-risk_per_trade)
                        break
                    if row['low'] <= target:
                        balance += risk_per_trade * 2
                        trades.append(risk_per_trade * 2)
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
