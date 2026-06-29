import os
import logging
import requests
import pandas as pd
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        # Carga credenciales desde variables de entorno
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET_KEY')
        self.tg_token = os.getenv('TELEGRAM_TOKEN')
        self.tg_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Conexión a Alpaca Paper Trading
        try:
            self.broker = TradingClient(self.api_key, self.api_secret, paper=True)
            logger.info("✅ Conectado a Alpaca Paper Trading")
        except Exception as e:
            logger.error(f"❌ Error al conectar a Alpaca: {e}")
            raise

    def enviar_telegram(self, mensaje):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": self.tg_chat_id, "text": mensaje, "parse_mode": "Markdown"})
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")

    def calcular_indicadores(self, ticker):
        data = yf.Ticker(ticker).history(period="1y")
        if data.empty: return None
        
        data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
        data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        return data.iloc[-1]

    def ejecutar_trade(self, ticker, lado):
        try:
            orden = MarketOrderRequest(symbol=ticker, qty=1, side=lado, time_in_force=TimeInForce.GTC)
            self.broker.submit_order(orden)
            self.enviar_telegram(f"🚀 Orden ejecutada: {lado.name} {ticker}")
        except Exception as e:
            logger.error(f"Error en ejecución: {e}")

    def run(self, tickers):
        resumen = ["📊 *Reporte Diario del Bot*"]
        for ticker in tickers:
            datos = self.calcular_indicadores(ticker)
            if datos is None: continue
            
            # Lógica: EMA 50 > 200 y RSI < 30 (Compra)
            if datos['EMA_50'] > datos['EMA_200'] and datos['RSI'] < 30:
                self.ejecutar_trade(ticker, OrderSide.BUY)
                resumen.append(f"🟢 {ticker}: COMPRA (RSI: {datos['RSI']:.1f})")
            # Lógica: EMA 50 < 200 y RSI > 70 (Venta)
            elif datos['EMA_50'] < datos['EMA_200'] and datos['RSI'] > 70:
                self.ejecutar_trade(ticker, OrderSide.SELL)
                resumen.append(f"🔴 {ticker}: VENTA (RSI: {datos['RSI']:.1f})")
        
        self.enviar_telegram("\n".join(resumen))

if __name__ == "__main__":
    bot = TradingBot()
    bot.run(["AAPL", "MSFT", "TSLA"])
