import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import os
import requests

# 1. Definimos la estrategia idéntica a la real
class EmaRsiStrategy(Strategy):
    def init(self):
        # Indicadores
        self.ema50 = self.I(lambda x: x.ewm(span=50, adjust=False).mean(), self.data.Close)
        self.ema200 = self.I(lambda x: x.ewm(span=200, adjust=False).mean(), self.data.Close)

    def next(self):
        # Reglas de entrada
        if self.ema50 > self.ema200 and self.data.Close < self.ema50:
            if not self.position: self.buy()
        elif self.ema50 < self.ema200 and self.data.Close > self.ema50:
            if self.position: self.position.close()

# 2. Descargar datos
ticker = "AAPL"
data = yf.Ticker(ticker).history(period="1y")

# 3. Correr Backtest
bt = Backtest(data, EmaRsiStrategy, cash=10000, commission=.002)
stats = bt.run()

# 4. Enviar resultado a Telegram
def enviar_reporte(stats):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    mensaje = f"📊 *Reporte de Backtesting - {ticker}*\n"
    mensaje += f"💰 Retorno Final: {stats['Return [%]']:.2f}%\n"
    mensaje += f"📈 Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%\n"
    mensaje += f"✅ Win Rate: {stats['Win Rate [%]']:.2f}%\n"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})

enviar_reporte(stats)
