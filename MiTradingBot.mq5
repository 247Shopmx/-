#include <Trade\Trade.mqh> // Librería estándar de MT5
#include "Include/Estrategia.mqh"
#include "Include/GestionOrdenes.mqh"

CTrade trade; // Objeto de operaciones

int OnInit() {
    Print("Bot inicializado correctamente.");
    return(INIT_SUCCEEDED);
}

void OnTick() {
    // 1. Obtener datos técnicos
    double rsi = CalcularRSI(_Symbol, _Period, 14);
    double ema50 = CalcularEMA(_Symbol, _Period, 50);
    double ema200 = CalcularEMA(_Symbol, _Period, 200);

    // 2. Lógica de Trading
    if(ema50 > ema200 && rsi < 30) {
        Print("Señal de COMPRA detectada.");
        // Ejecutar compra de 0.1 lotes
        trade.Buy(0.1, _Symbol, SymbolInfoDouble(_Symbol, SYMBOL_ASK), 0, 0, "Compra Robot");
    }
    else if(ema50 < ema200 && rsi > 70) {
        Print("Señal de VENTA detectada.");
        trade.Sell(0.1, _Symbol, SymbolInfoDouble(_Symbol, SYMBOL_BID), 0, 0, "Venta Robot");
    }
}
