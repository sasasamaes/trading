# Wally Trader — Agent Instructions

> Sistema de trading personal con capital real + challenge FTMO + bonus Fotmarkets.
> Bautizado en honor a Wally 🌭, perro salchicha y CEO mascota del proyecto.

Este archivo lo lee **OpenCode** automáticamente al iniciar sesión (igual que Claude Code lee `CLAUDE.md`). Para evitar duplicación, las instrucciones operativas completas viven en `CLAUDE.md` — léelas primero.

## Lectura obligatoria al iniciar sesión

1. **`CLAUDE.md`** — perfil del trader, profile system 4-way, estrategias, reglas duras, helpers Python.
2. **Profile activo:** `bash .claude/scripts/profile.sh get` → `retail` | `retail-bingx` | `ftmo` | `fotmarkets`.
3. **Memoria del usuario:** `~/.claude/projects/-Users-josecampos-Documents-wally-trader/memory/MEMORY.md` (Claude Code) o `.claude/memory/MEMORY.md` (project-local fallback).

## Convenciones del proyecto

- **Idioma:** español (mixto con términos técnicos de trading en inglés: SL, TP, long, short, leverage)
- **Zona horaria:** Costa Rica (CR, UTC-6 sin DST). Statusline labels horarios como `CR HH:MM`.
- **Moneda:** capital tracked en USD + equivalente en colones (`$18.09 ≈₡8,241`). FX vía `bash .claude/scripts/fx_rate.sh`.
- **Ejecución:** el sistema **NO ejecuta trades**. Solo recomienda. Toda ejecución es manual del usuario en su exchange/broker.
- **Honesty first:** si data es insuficiente o backtest no funciona, decirlo explícitamente.
- **Disclaimers obligatorios** en decisiones con leverage real.

## Subagents disponibles (`.opencode/agents/`)

Invocar con `@<name>`:

| Subagent | Cuándo usar |
|---|---|
| `@morning-analyst` | Análisis matutino retail (17 fases). Profile retail-only. |
| `@morning-analyst-ftmo` | Análisis multi-asset FTMO/fotmarkets. |
| `@regime-detector` | Clasificación rápida del régimen (RANGE/TRENDING/VOLATILE). |
| `@trade-validator` | Validar 4/4 filtros antes de ejecutar entry. |
| `@risk-manager` | Position sizing 2% según profile activo. |
| `@journal-keeper` | Cerrar día + actualizar trading log. |
| `@chart-drafter` | Dibujar niveles en TradingView vía MCP. |
| `@backtest-runner` | Backtest de configs sobre data histórica. |
| `@signal-validator` | Validar señal externa de comunidad (GO/NO-GO). |
| `@sentiment-analyst` | Sentiment NLP aggregator (F&G + Reddit + News + Funding). |
| `@ml-analyst` | Score XGBoost TP-first del setup actual. |
| `@technical-analyst` | TA profundo (ICT + armónicos + chartismo + Elliott + Fibonacci). |

## Slash commands principales (`.opencode/commands/`)

```
/morning [args]     — análisis matutino profile-aware
/profile [name]     — ver/cambiar profile activo
/validate           — validar entry actual (4 filtros)
/risk               — position sizing 2%
/regime             — detectar régimen
/journal            — cerrar día
/status             — estado completo del sistema
/chart              — limpiar y redibujar niveles en TV
/backtest           — backtest config
/signal             — validar señal externa
/sentiment          — score sentiment 0-100
/ml                 — ML score XGBoost
/order              — encolar orden limit virtual
/watch              — tick manual del watcher
/equity <valor>     — actualizar equity FTMO
/challenge          — dashboard FTMO
/trades             — dashboard MT5 fotmarkets
/levels             — niveles técnicos ahora
/macross            — señal MA Crossover
/trail <side> <ent> — calcular trailing stop EMA(20)
/ta                 — TA avanzado 5 metodologías
```

## Skills disponibles (`.opencode/skills/` → symlink a `system/skills/`)

Conocimiento técnico-operativo. Activar con `@skill-name` o instrucción contextual:

`btc-on-chain`, `divergence-analysis`, `trendlines-sr`, `smart-money-ict`, `trade-psychology`, `adx-trend-strength`, `harmonic-patterns`, `fibonacci-tools`, `btc-regime-analysis`, `elliott-waves`, `neptune-indicators`, `stochastic-oscillator`, `classic-chartism`, `bollinger-bands-advanced`.

## Reglas sagradas (no negociables)

1. **Max 2% riesgo por trade**
2. **Max 3 trades/día** (5 en retail single-asset)
3. **2 SLs consecutivos → STOP día**
4. **Nunca mover SL en contra** (solo a BE o profit)
5. **Nunca leverage > 10x**
6. **4/4 filtros obligatorios** para entry Mean Reversion (no 3/4)
7. **No mezclar profiles** el mismo día (retail/ftmo/fotmarkets)
8. **No cruzar memorias** entre profiles

## MCP servers configurados

- **`tradingview`** — 78 tools para leer/controlar TradingView Desktop. Ver `tradingview-mcp/CLAUDE.md`.

Activar con `mcp__tradingview__*` (Claude Code) o tools directas en OpenCode.

## Helpers Python (`.claude/scripts/`)

| Helper | Función |
|---|---|
| `adx_calc.py` | ADX(14) + DI + label_regime |
| `trailing_stop.py` | Eval EMA(20) trail |
| `backtest_split.py` | Split 70/30 + OOS report |
| `macross.py` | EMA(9/21) cross detector |
| `per_asset_backtest.py` | Backtest multi-asset comparativo |
| `fx_rate.sh` | USD↔CRC del día (cache 1h) |
| `profile.sh` | Switch/get profile activo |
| `guardian.py` | FTMO daily/trailing guardian |
| `fotmarkets_guard.sh` | Lite guardian fotmarkets |

## Disclaimer

Nada en este proyecto es consejo financiero. Futuros con leverage pueden liquidar capital
en minutos con un wick. Usa solo capital que puedas perder sin afectar tu vida.
