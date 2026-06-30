import yfinance as yf
import numpy as np
import pandas as pd


def compute_indicators(df):
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())

    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    df["ATR"] = tr.rolling(14).mean()

    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    return df


def backtest(df):

    balance = 10000
    position = 0
    entry = 0
    equity = []

    for i in range(200, len(df)):

        row = df.iloc[i]

        if position == 0:
            if row["EMA50"] > row["EMA200"] and row["Close"] < row["EMA50"]:
                position = 1
                entry = row["Close"]

            elif row["EMA50"] < row["EMA200"] and row["Close"] > row["EMA50"]:
                position = -1
                entry = row["Close"]

        else:
            pnl = (row["Close"] - entry) * position

            if pnl < -2 * row["ATR"] or pnl > 3 * row["ATR"]:
                balance += pnl
                position = 0

        equity.append(balance)

    return equity


df = yf.download("AAPL", period="2y")
df = compute_indicators(df)

equity = backtest(df)

print("Final balance:", equity[-1])
