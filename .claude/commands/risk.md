---
description: Calcula position sizing con la regla del 2%
allowed-tools: Agent
---

Invoca el agente `risk-manager` para calcular el tamaño de posición correcto.

Necesita (si no proporcionas, te pregunta):
- Entry price
- SL price (o distance %)
- Leverage (default 10x)

Devuelve:
- Margen exacto a usar
- Qty BTC a comprar/vender
- PnL esperado si SL/TP1/TP2/TP3
- R:R ratio
- Validación vs reglas duras del día

Contexto del trade:
$ARGUMENTS
