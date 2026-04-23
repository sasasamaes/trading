---
description: Cierra el día y actualiza el log del profile activo
allowed-tools: Agent
---

Cierra el día y actualiza el log del profile activo.

Pasos que ejecuta Claude:

1. Lee profile: `PROFILE=$(bash .claude/scripts/profile.sh get)`

2. Despacha `journal-keeper` agent con el profile explícito.

3. Agent escribe al log correspondiente:
   - retail → `.claude/profiles/retail/memory/trading_log.md`
   - ftmo   → `.claude/profiles/ftmo/memory/trading_log.md` + actualiza `challenge_progress.md`

4. SI profile == "ftmo":
   - Lee trades del día del user (input manual: pega texto o screenshot MT5)
   - Para cada trade, append row a `equity_curve.csv` vía guardian --action equity-update
   - Recalcula: WR, avg R, best day ratio, profit factor
   - Update `challenge_progress.md` con nuevas métricas
   - Si overrides.log tiene eventos del día → lista para revisión
   - Muestra al usuario:
     - Trades del día con resultado
     - PnL neto
     - Status rules post-cierre
     - "Brechas cerca: none / <rule>"
     - Próximo paso: "/profile retail para mañana" o "continuar FTMO"

5. SI profile == "retail":
   - Comportamiento actual (3 wins log pattern).
   - journal-keeper append a `.claude/profiles/retail/memory/trading_log.md`.

6. Auto-commit al final:
   `git add <archivos profile> && git commit -m "journal: auto-save sesión <profile> <YYYY-MM-DD>"`

Input (opcional):
$ARGUMENTS
