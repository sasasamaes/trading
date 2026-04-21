---
description: Actualiza trading log + métricas del día / semana
allowed-tools: Agent
---

Invoca el agente `journal-keeper` para documentar tu actividad de trading.

Si es final del día (default):
- Registra trades ejecutados
- Calcula PnL, WR, disciplina
- Detecta patrones
- Actualiza `trading_log.md` y `DAILY_TRADING_JOURNAL.md`
- Sugiere 1 cosa a cambiar mañana

Si es domingo o especificas "semanal":
- Review completo semana (métricas, patrones, cambios)
- Calcula WR, PF, DD, avg win/loss
- Compara vs target (WR≥60%, PF≥1.8, DD≤15%)

Input (opcional):
$ARGUMENTS
