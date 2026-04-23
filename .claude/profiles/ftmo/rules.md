# FTMO 1-Step Rules — Formal Spec

Este documento es la fuente única de verdad sobre reglas FTMO que el guardian implementa.

## Regla 1 — Max Daily Loss 3%

**Definición:** En cualquier día calendario (reset 00:00 UTC), la pérdida neta no puede exceder 3% del equity del inicio del día.

**Cálculo:**
```
daily_pnl = equity_actual - equity_inicio_dia
daily_pct = daily_pnl / equity_inicio_dia * 100
if daily_pct <= -3.0 → BREACH
```

**Enforcement:** BLOCKING (guardian impide entrada que llevaría a breach).

**Nota:** FTMO usa hora de servidor (típicamente UTC+2). Guardian usa timestamp del equity_curve; la consistencia es responsabilidad del usuario.

## Regla 2 — Max Total Trailing Drawdown 10%

**Definición:** La pérdida total desde el peak de equity histórico no puede exceder 10% del capital inicial ($1,000 en $10k).

**Cálculo:**
```
peak = max(equity_curve.equity)
dd_actual = peak - equity_actual
dd_pct = dd_actual / 10000 * 100
if dd_pct >= 10.0 → BREACH
```

**Enforcement:** WARNING (guardian advierte pero no bloquea; el usuario tiene margen de días).

**Threshold de warning:** guardian alerta si dd_pct >= 8.0 (80% del límite).

## Regla 3 — Best Day Rule 50%

**Definición:** Ningún día puede representar más del 50% del profit total del challenge.

**Cálculo:**
```
days_positive = [(date, profit) for date, profit in day_profits if profit > 0]
total_profit = sum(p for _, p in days_positive)
best_day = max(p for _, p in days_positive)
ratio = best_day / total_profit
if ratio > 0.50 → INFO (no bloquea, se soluciona con más días)
```

**Enforcement:** INFO (visible en `/challenge` y al cierre de día). No bloquea entradas.

**Threshold de aviso:** guardian muestra info si ratio >= 0.45.

## Regla 4 — Max 2 Trades/Day (del config, no FTMO)

**Definición:** Límite autoimpuesto para evitar sobretrading.

**Cálculo:**
```
trades_today = count(trades where date == today)
if trades_today >= 2 → BLOCK
```

**Enforcement:** BLOCKING.

## Regla 5 — 2 SLs Consecutivos → STOP día (autoimpuesta)

**Definición:** Después de 2 SLs seguidos (sin TP ni BE entre medio) en el mismo día, STOP.

**Cálculo:**
```
last_two = last 2 trades of today, ordered by close_time
if both are SL → BLOCK
```

**Enforcement:** BLOCKING.

## Override escape hatch

Usuario puede escribir literalmente `OVERRIDE GUARDIAN` en respuesta a un BLOCK. El guardian:
1. Registra evento en `memory/overrides.log` con timestamp, rule, equity, trade propuesto
2. Permite proceder

Usar solo en casos extremos; cada override es material de post-mortem.
