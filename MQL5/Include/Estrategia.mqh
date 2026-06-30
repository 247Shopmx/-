#pragma once

class Estrategia
{
public:

    // 1 = BUY, -1 = SELL, 0 = NO TRADE
    static int Señal(double rsi, double emaFast, double emaSlow)
    {
        // Tendencia alcista + sobreventa
        if(emaFast > emaSlow && rsi < 30)
            return 1;

        // Tendencia bajista + sobrecompra
        if(emaFast < emaSlow && rsi > 70)
            return -1;

        return 0;
    }

    static bool EsMercadoValido(double spread, double maxSpread)
    {
        if(spread > maxSpread)
            return false;

        return true;
    }

    static bool EvitarChop(double emaFast, double emaSlow)
    {
        double diff = MathAbs(emaFast - emaSlow);

        // si EMAs muy juntas → mercado lateral
        if(diff < 0.0005)
            return false;

        return true;
    }
};
