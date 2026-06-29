import os
import requests
import pandas as pd
import yfinance as yf

# 1. Configuración de variables de entorno para Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def enviar_alerta_telegram(mensaje):
    """Envía un mensaje de texto a través del bot de Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Error: Credenciales de Telegram no encontradas en las variables de entorno.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Alerta enviada a Telegram con éxito.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al enviar el mensaje de Telegram: {e}")

def calcular_rsi(data, periodos=14):
    """Calcula el Índice de Fuerza Relativa (RSI)."""
    delta = data['Close'].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodos).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodos).mean()
    
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analizar_accion(ticker):
    """Descarga datos, aplica estrategia de EMA/RSI y retorna una señal."""
    print(f"Analizando {ticker}...")
    
    # Descargamos 1 año de datos para tener suficiente histórico para la EMA 200
    accion = yf.Ticker(ticker)
    df = accion.history(period="1y")
    
    if df.empty:
        return f"⚠️ {ticker}: No se pudieron obtener datos."

    # 2. Cálculo de Indicadores
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = calcular_rsi(df)

    # Obtenemos los valores del último día de cotización
    ultimo_cierre = df.iloc[-1]['Close']
    ema_50_actual = df.iloc[-1]['EMA_50']
    ema_200_actual = df.iloc[-1]['EMA_200']
    rsi_actual = df.iloc[-1]['RSI']

    # 3. Lógica de la Estrategia (Cruces y Sobrecompra/Sobreventa)
    senal = f"⚪ **MANTENER** en {ticker}\nPrecio: ${ultimo_cierre:.2f} | RSI: {rsi_actual:.1f}"

    # Condición de COMPRA: Tendencia general alcista (EMA50 > EMA200) + Retroceso/Sobreventa (RSI < 30)
    if (ema_50_actual > ema_200_actual) and (rsi_actual < 30):
        senal = f"🟢 **SEÑAL DE COMPRA** en {ticker}\nPrecio: ${ultimo_cierre:.2f}\nRSI: {rsi_actual:.1f} (Sobreventa)\nTendencia: Alcista (EMA50 > EMA200)"
    
    # Condición de VENTA: Tendencia general bajista (EMA50 < EMA200) + Rebote/Sobrecompra (RSI > 70)
    elif (ema_50_actual < ema_200_actual) and (rsi_actual > 70):
        senal = f"🔴 **SEÑAL DE VENTA** en {ticker}\nPrecio: ${ultimo_cierre:.2f}\nRSI: {rsi_actual:.1f} (Sobrecompra)\nTendencia: Bajista (EMA50 < EMA200)"

    return senal

def main():
    # Puedes modificar esta lista con los símbolos que quieras monitorear (Ej. SPY, META, TSLA)
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    mensajes_alerta = ["📊 **Reporte Diario de Trading Bot** 📊\n"]

    for ticker in tickers:
        resultado = analizar_accion(ticker)
        mensajes_alerta.append(resultado)

    # 4. Formatear y enviar el mensaje final
    mensaje_final = "\n\n".join(mensajes_alerta)
    print("\n" + mensaje_final)
    enviar_alerta_telegram(mensaje_final)

if __name__ == "__main__":
    main()
