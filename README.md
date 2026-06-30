# Trading Bot - Alpaca Paper Trading System

Sistema automatizado de trading en acciones usando Alpaca Paper API, estrategias basadas en indicadores técnicos (EMA + ATR), ejecutado vía GitHub Actions.

---

## 📌 Características

- Trading automático en acciones (AAPL, TSLA, NVDA)
- Estrategia basada en:
  - EMA 50 / EMA 200 (tendencia)
  - ATR (gestión de riesgo)
- Position sizing dinámico basado en riesgo (% del balance)
- Ejecución con órdenes market en Alpaca Paper Trading
- Compatible con GitHub Actions (ejecución programada o manual)

---

## 🧠 Estrategia

### Señales de entrada:

**BUY**
- EMA50 > EMA200
- Precio < EMA50

**SELL**
- EMA50 < EMA200
- Precio > EMA50
---

pip install -r requirements.txt

## 📊 Gestión de riesgo

- Riesgo por trade: 1% del balance
- Stop-loss implícito basado en ATR (1.5x)
- Take-profit implícito basado en lógica de volatilidad
- Tamaño de posición dinámico según ATR
- python trading_bot.py

---

## ⚙️ Instalación

### 1. Clonar repositorio
```bash
git clone <repo_url>
cd trading-bot
.
├── trading_bot.py
├── backtest.py
├── requirements.txt
├── .github/workflows/
│   ├── trading.yml
│   └── backtest.yml
└── README.md
