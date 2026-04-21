---
description: Valida GO/NO-GO de entry actual según los 4 filtros
allowed-tools: Agent
---

Invoca el agente `trade-validator` para validar si es momento de entrar AHORA.

El agente chequea:
- **4 filtros obligatorios** (Donchian + BB + RSI + vela color)
- **Reglas duras de sesión** (max trades, 2 SLs stop, hora válida)
- **Correlaciones** (ETH en dirección)
- **Position sizing** (2% rule)

Output binario: GO o NO-GO con razón concreta.

Contexto adicional (opcional):
$ARGUMENTS
