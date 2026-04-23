# Phase Progress — Fotmarkets

Fuente de verdad del capital y fase activa del profile `fotmarkets`.
Actualizado por `/journal` al cierre de cada día.

## Estado actual

```yaml
capital_current: 27.09
capital_previous: 30.00
phase: 1
phase_since: "2026-04-23"
trades_total: 1
trades_wins: 0
trades_losses: 1
pnl_total_usd: -2.91
last_updated: "2026-04-23T15:30:00Z"
sls_today: 1
sls_today_cap: 1
trades_today: 1
trades_today_cap: 1
day_locked: true  # 1 SL → stop día fase 1
day_locked_until: "2026-04-24T07:00:00Z"
```

## Historial de migraciones

| Fecha | Capital | Fase | Evento |
|---|---|---|---|
| 2026-04-23 | $30.00 | 1 | Profile creado, bonus inicial |
| 2026-04-23 | $27.09 | 1 | Trade #1 EURUSD LONG SL (-$2.91, -0.97R). 1/1 trade y 1/1 SL fase 1. STOP día. Sizing 0.03 respetado ✅. |

## Thresholds recordatorio

- Fase 1 → 2: capital ≥ $100 (assets desbloqueados: USDJPY, XAUUSD, NAS100)
- Fase 2 → 3: capital ≥ $300 (assets desbloqueados: SPX500, BTCUSD, ETHUSD)
