import os
import logging
import numpy as np
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ---------------- LOGGING ----------------
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

        self.risk_per_trade = 0.01  # 1%

    # ---------------- DATA ----------------
    def get_data(self, ticker):

        df = yf.download(ticker, period="3mo", interval="1d")

        if df is None or df.empty:
            logger.warning(f"No data for {ticker}")
            return None

        df = df.copy()

        # TRUE ATR
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())

        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        df["ATR"] = tr.rolling(14).mean()

        # INDICATORS
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

        last = df.iloc[-1]

        # 🔥 FORZAR ESCALARES (FIX CRÍTICO)
        return {
            "Close": float(last["Close"]),
            "EMA50": float(last["EMA50"]),
            "EMA200": float(last["EMA200"]),
            "ATR": float(last["ATR"]) if not np.isnan(last["ATR"]) else 0.0
        }

    # ---------------- SIGNAL ----------------
    def signal(self, row):

        if row is None:
            return None

        ema_fast = row["EMA50"]
        ema_slow = row["EMA200"]
        close = row["Close"]

        # BUY
        if ema_fast > ema_slow and close < ema_fast:
            return OrderSide.BUY

        # SELL
        if ema_fast < ema_slow and close > ema_slow:
            return OrderSide.SELL

        return None

    # ---------------- POSITION SIZE ----------------
    def position_size(self, atr):

        if atr <= 0:
            return 1

        balance = 10000
        risk_amount = balance * self.risk_per_trade

        stop_distance = atr * 1.5

        qty = risk_amount / stop_distance

        return max(1, int(qty))

    # ---------------- EXECUTION ----------------
    def execute(self, ticker, side, price, atr):

        qty = self.position_size(atr)

        try:
            order = MarketOrderRequest(
                symbol=ticker,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )

            self.client.submit_order(order)

            logger.info(
                f"TRADE {side.name} {ticker} | qty={qty} | price={price:.2f} | ATR={atr:.2f}"
            )

        except Exception as e:
            logger.error(f"Order error: {e}")

    # ---------------- RUN ----------------
    def run(self, tickers):

        for t in tickers:

            data = self.get_data(t)

            if data is None:
                continue

            side = self.signal(data)

            if side:
                self.execute(
                    t,
                    side,
                    data["Close"],
                    data["ATR"]
                )


# ---------------- MAIN ----------------
if __name__ == "__main__":

    bot = TradingBot()
    bot.run(["AAPL", "TSLA", "NVDA"])
