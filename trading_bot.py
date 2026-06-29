import os
import logging
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

# Configuración
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET')
        self.broker = TradingClient(self.api_key, self.api_secret, paper=True)

    def obtener_datos(self, ticker):
        # Descargamos datos para calcular volatilidad (ATR)
        df = yf.Ticker(ticker).history(period="1mo")
        if df.empty: return None
        
        # Calcular ATR (Average True Range) - Mide la volatilidad
        high_low = df['High'] - df['Low']
        df['ATR'] = high_low.rolling(window=14).mean()
        
        # Indicadores base
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        return df.iloc[-1]

    def ejecutar_trade_profesional(self, ticker, lado, precio, atr):
        # Lógica de gestión de riesgo profesional
        # Stop Loss = 1.5 veces el ATR
        # Take Profit = 3 veces el ATR (Ratio Riesgo/Beneficio 1:2)
        sl_price = round(precio - (atr * 1.5) if lado == OrderSide.BUY else precio + (atr * 1.5), 2)
        tp_price = round(precio + (atr * 3) if lado == OrderSide.BUY else precio - (atr * 3), 2)

        try:
            # Creamos una ORDEN TIPO BRACKET (Automáticamente pone SL y TP)
            orden = MarketOrderRequest(
                symbol=ticker,
                qty=1,
                side=lado,
                time_in_force=TimeInForce.GTC,
                order_class=OrderClass.BRACKET,
                take_profit={"limit_price": tp_price},
                stop_loss={"stop_price": sl_price}
            )
            self.broker.submit_order(orden)
            logger.info(f"✅ Trade ejecutado: {lado.name} {ticker} | SL: {sl_price} | TP: {tp_price}")
        except Exception as e:
            logger.error(f"❌ Error en orden bracket: {e}")

    def run(self, tickers):
        for ticker in tickers:
            datos = self.obtener_datos(ticker)
            if datos is None: continue
            
            # Estrategia de entrada
            if datos['EMA_50'] > datos['EMA_200'] and datos['Close'] < datos['EMA_50']:
                self.ejecutar_trade_profesional(ticker, OrderSide.BUY, datos['Close'], datos['ATR'])
            
            elif datos['EMA_50'] < datos['EMA_200'] and datos['Close'] > datos['EMA_50']:
                self.ejecutar_trade_profesional(ticker, OrderSide.SELL, datos['Close'], datos['ATR'])

if __name__ == "__main__":
    bot = TradingBot()
    bot.run(["AAPL", "TSLA", "NVDA"])
