#include <Trade\Trade.mqh>

CTrade trade;

// ---------- INPUTS ----------
input double RiskPercent = 1.0;     // riesgo por trade %
input int RSI_Period = 14;
input int EMA_Fast = 50;
input int EMA_Slow = 200;

// ---------- INDICADORES ----------
double GetEMA(int period, int shift)
{
    return iMA(_Symbol, _Period, period, 0, MODE_EMA, PRICE_CLOSE, shift);
}

double GetRSI(int period, int shift)
{
    return iRSI(_Symbol, _Period, period, PRICE_CLOSE, shift);
}

// ---------- RISK MANAGEMENT ----------
double CalculateLot(double stopLossPoints)
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double risk = balance * (RiskPercent / 100.0);

    double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);

    double lot = risk / (stopLossPoints * tickValue);

    if(lot < 0.01) lot = 0.01;
    return NormalizeDouble(lot, 2);
}

// ---------- CHECK POSITIONS ----------
bool HasOpenPosition()
{
    return PositionSelect(_Symbol);
}

// ---------- INIT ----------
int OnInit()
{
    Print("EA iniciado correctamente");
    return INIT_SUCCEEDED;
}

// ---------- MAIN LOOP ----------
void OnTick()
{
    if(HasOpenPosition())
        return; // evita sobretrading

    double emaFast = GetEMA(EMA_Fast, 0);
    double emaSlow = GetEMA(EMA_Slow, 0);
    double rsi = GetRSI(RSI_Period, 0);

    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    double atr = iATR(_Symbol, _Period, 14, 0);
    double stopLoss = atr * 1.5;
    double takeProfit = atr * 3.0;

    double lot = CalculateLot(stopLoss / _Point);

    // ---------- BUY ----------
    if(emaFast > emaSlow && rsi < 30)
    {
        double sl = ask - stopLoss;
        double tp = ask + takeProfit;

        trade.Buy(lot, _Symbol, ask, sl, tp, "BUY EMA+RSI");
        Print("BUY ejecutado");
    }

    // ---------- SELL ----------
    else if(emaFast < emaSlow && rsi > 70)
    {
        double sl = bid + stopLoss;
        double tp = bid - takeProfit;

        trade.Sell(lot, _Symbol, bid, sl, tp, "SELL EMA+RSI");
        Print("SELL ejecutado");
    }
}
