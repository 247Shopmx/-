// Función para calcular RSI
double CalcularRSI(string symbol, ENUM_TIMEFRAMES period, int periodos) {
    int handle = iRSI(symbol, period, periodos, PRICE_CLOSE);
    double buffer[];
    CopyBuffer(handle, 0, 0, 1, buffer);
    return buffer[0];
}

// Función para calcular EMA
double CalcularEMA(string symbol, ENUM_TIMEFRAMES period, int periodos) {
    int handle = iMA(symbol, period, periodos, 0, MODE_EMA, PRICE_CLOSE);
    double buffer[];
    CopyBuffer(handle, 0, 0, 1, buffer);
    return buffer[0];
}
