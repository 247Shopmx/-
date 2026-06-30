import os
import logging
import numpy as np
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingBot:

    def __init__(self):
        self.api_key = os.getenv("ALPACA_KEY")
        self.api_secret = os.getenv("ALPACA_SECRET")

        self.client = TradingClient(
            self.api_key,
            self.api_secret,
            paper=True
        )

        self.max_risk_per_trade = 0.01  # 1%

    # ---------- DATA ----------
    def get_data(self, ticker):
        df = yf.download(ticker, period="3mo", interval="1d")
        if df.empty:
            return None

        # TRUE ATR
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())

        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        df["ATR"] = tr.rolling(14).mean()

        df["EMA50"] = df["Close"].ewm(span=50).mean()
        df["EMA200"] = df["Close"].ewm(span=200).mean()

        return df.iloc[-1]

    # ---------- POSITION SIZING ----------
    def position_size(self, price, atr):
        risk_dollars = 10000 * self.max_risk_per_trade
        stop_distance = atr * 1.5

        if stop_distance == 0:
            return 0

        qty = risk_dollars / stop_distance
        return max(1, int(qty))

    # ---------- EXECUTION ----------
    def execute_trade(self, ticker, side, price, atr):

        qty = self.position_size(price, atr)

        if qty <= 0:
            return

        sl = price - atr * 1.5 if side == OrderSide.BUY else price + atr * 1.5
        tp = price + atr * 3.0 if side == OrderSide.BUY else price - atr * 3.0

        try:
            order = MarketOrderRequest(
                symbol=ticker,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )

            self.client.submit_order(order)

            logger.info(
                f"TRADE {side.name} {ticker} | qty={qty} | SL={sl:.2f} | TP={tp:.2f}"
            )

        except Exception as e:
            logger.error(f"Order error: {e}")

    # ---------- STRATEGY ----------
    def signal(self, row):

        if row is None:
            return None

        if row["EMA50"] > row["EMA200"] and row["Close"] < row["EMA50"]:
            return OrderSide.BUY

        if row["EMA50"] < row["EMA200"] and row["Close"] > row["EMA50"]:
            return OrderSide.SELL

        return None

    # ---------- RUN ----------
    def run(self, tickers):

        for t in tickers:
            data = self.get_data(t)

            if data is None:
                continue

            side = self.signal(data)

            if side:
                self.execute_trade(t, side, data["Close"], data["ATR"])


if __name__ == "__main__":
    bot = TradingBot()
    bot.run(["AAPL", "TSLA", "NVDA"])
