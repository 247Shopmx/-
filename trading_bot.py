import os
import logging
import requests
import pandas as pd
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Configuración de Logging para tener un registro exacto en GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBotProfesional:
    def __init__(self):
        """Inicializa las conexiones a las APIs y valida credenciales."""
        # Credenciales de Alpaca (Broker)
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        # Credenciales de Telegram
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        self.validar_credenciales()

        # Conexión al Broker en modo DEMO (paper=True)
        try:
            self.broker = TradingClient(self.api_key, self.api_secret, paper=True)
            cuenta = self.broker.get_account()
            logger.info(f"✅ Conectado a Alpaca Demo. Poder de compra: ${cuenta.buying_power}")
        except Exception as e:
            logger.error(f"❌ Error crítico al conectar con Alpaca: {e}")
            self.enviar_telegram("🚨 *ERROR CRÍTICO:* No se pudo conectar al Broker Alpaca.")
            raise

    def validar_credenciales(self):
        """Verifica que todos los secretos de GitHub estén configurados."""
        if not all([self.api_key, self.api_secret, self.telegram_token, self.telegram_chat_id]):
            logger.error("Faltan variables de entorno (Secrets). Verifica tu configuración en GitHub.")
            raise ValueError("Credenciales incompletas.")

    def enviar_telegram(self, mensaje):
        """Envía notificaciones al chat de Telegram de forma segura."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo al enviar mensaje de Telegram: {e}")

    def calcular_rsi(self, data, periodos=14):
        """Cálculo matemático del Índice de Fuerza Relativa (RSI)."""
        delta = data['Close'].diff()
        ganancia = (delta.where(delta > 0, 0)).rolling(window=periodos).mean()
        perdida = (-delta.where(delta < 0, 0)).rolling(window=periodos).mean()
        rs = ganancia / perdida
        return 100 - (100 / (1 + rs))

    def ejecutar_orden(self, ticker, cantidad, lado):
        """Envía la orden de compra/venta al mercado de Alpaca."""
        try:
            orden = MarketOrderRequest(
                symbol=ticker,
                qty=cantidad,
                side=lado,
                time_in_force=TimeInForce.GTC
            )
            resultado = self.broker.submit_order(orden)
            
            accion = "COMPRA" if lado == OrderSide.BUY else "VENTA"
            mensaje = f"✅ *ORDEN EJECUTADA EN DEMO*\nAcción: {accion} {cantidad} x {ticker}\nID: `{resultado.id}`"
            logger.info(f"Orden ejecutada: {accion} {ticker}")
            self.enviar_telegram(mensaje)
            
        except Exception as e:
            error_msg = f"❌ *Fallo al ejecutar orden en {ticker}*\nDetalle: {e}"
            logger.error(error_msg)
            self.enviar_telegram(error_msg)

    def analizar_y_operar(self, tickers):
        """Descarga datos, calcula estrategia y decide si operar."""
        logger.info(f"Iniciando análisis de {len(tickers)} activos...")
        resumen_diario = ["📊 *Resumen del Análisis de Mercado* 📊\n"]

        for ticker in tickers:
            try:
                # 1. Obtener datos históricos
                df = yf.Ticker(ticker).history(period="1y")
                if df.empty:
                    logger.warning(f"Sin datos para {ticker}")
                    continue

                # 2. Calcular Indicadores (EMA 50, EMA 200, RSI)
                df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
                df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
                df['RSI'] = self.calcular_rsi(df)

                ultimo_precio = df.iloc[-1]['Close']
                ema_50 = df.iloc[-1]['EMA_50']
                ema_200 = df.iloc[-1]['EMA_200']
                rsi = df.iloc[-1]['RSI']

                # 3. Evaluar Estrategia y Operar
                # COMPRA: Tendencia alcista y RSI sobrevendido
                if (ema_50 > ema_200) and (rsi < 30):
                    resumen_diario.append(f"🟢 *{ticker}*: SEÑAL DE COMPRA detectada (${ultimo_precio:.2f})")
                    self.ejecutar_orden(ticker, cantidad=1, lado=OrderSide.BUY)
                
                # VENTA: Tendencia bajista y RSI sobrecomprado
                elif (ema_50 < ema_200) and (rsi > 70):
                    resumen_diario.append(f"🔴 *{ticker}*: SEÑAL DE VENTA detectada (${ultimo_precio:.2f})")
                    self.ejecutar_orden(ticker, cantidad=1, lado=OrderSide.SELL)
                
                # MANTENER: Sin condiciones claras
                else:
                    resumen_diario.append(f"⚪ *{ticker}*: Mantener (RSI: {rsi:.1f})")

            except Exception as e:
                logger.error(f"Error analizando {ticker}: {e}")

        # Enviar resumen final al terminar el bucle
        mensaje_final = "\n".join(resumen_diario)
        self.enviar_telegram(mensaje_final)
        logger.info("Análisis finalizado con éxito.")

if __name__ == "__main__":
    # Activos a operar (Puedes añadir los que soporte Alpaca)
    activos = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    
    bot = TradingBotProfesional()
    bot.analizar_y_operar(activos)
