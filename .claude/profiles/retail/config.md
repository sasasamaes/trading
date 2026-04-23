# Profile: RETAIL (BingX Real)

**Capital actual:** $13.63 (iniciado en $10, +36% tras 3 wins)
**Exchange:** BingX (BTCUSDT.P perpetual)
**Leverage máximo:** 10x
**Plataforma análisis:** TradingView (plan Basic, 2 indicadores: Neptune Signals + Neptune Oscillator)

## Assets operables

- Único: `BTCUSDT.P` (BingX)

## Estrategia activa

Ver `strategy.md` en este directorio — **Mean Reversion 15m** (según régimen actual RANGE 73.5k–78.3k).

## Ventana operativa

- Inicio: MX 06:00
- Force exit: MX 23:59 (regla "no dormir con posición abierta")
- Cripto 24/7 pero el trader no duerme con trade abierto

## Reglas duras

1. Max 2% riesgo por trade (del capital actual, no del inicial)
2. Max 3 trades/día
3. 2 SLs consecutivos → STOP día
4. Nunca mover SL en contra (solo a BE tras TP1)
5. Nunca leverage >10x
6. 4/4 filtros obligatorios simultáneos

## Memorias específicas retail

Ver archivos en `./memory/`:
- `trading_log.md` — journal histórico
- `trading_strategy.md` — detalle Mean Reversion
- `entry_rules.md` — 4 filtros
- `market_regime.md` — niveles actuales BTC BingX
- `tradingview_setup.md` — config TV
- `liquidations_data.md` — fuentes datos BingX/Binance
- `backtest_findings.md` — aprendizajes de 144 configs
