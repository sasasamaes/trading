# Fotmarkets Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar `fotmarkets` como tercer profile operativo al sistema de trading — broker MT5 no-regulado, $30 bonus, operación real con risk escalation por fases ($30→$100→$300+).

**Architecture:** Reusar la infraestructura dual-profile existente (`retail`/`ftmo`). Agregar directorio `.claude/profiles/fotmarkets/` con config/strategy/rules + memory, dos scripts nuevos (`fotmarkets_phase.sh`, `fotmarkets_guard.sh`), y branches condicionales `if [[ $PROFILE == "fotmarkets" ]]` en los comandos profile-aware (`/status`, `/morning`, `/validate`, `/risk`, `/journal`, `/levels`, `/regime`).

**Tech Stack:** Bash (scripts), Markdown (configs/commands/docs), Python (opcional en guardian checks). Sin nuevas dependencias externas.

**Design spec:** `docs/superpowers/specs/2026-04-23-fotmarkets-profile-design.md`

---

## Task 1: Crear config.md del profile

**Files:**
- Create: `.claude/profiles/fotmarkets/config.md`

- [ ] **Step 1: Crear archivo config.md con identidad + constantes YAML**

```markdown
# Profile: FOTMARKETS (Bonus $30 no-deposit)

**Broker:** Fotmarkets (Mauritius, sin regulación tier-1)
**Plataforma:** MetaTrader 5 (cliente desktop)
**Tipo cuenta:** MT5 Standard
**Leverage:** 1:500 (forzado por bonus T&C)
**Capital inicial:** $30 USD (bonus no-deposit, no depositado)
**Moneda:** USD

## Constantes (YAML, consumidas por scripts + comandos)

```yaml
profile: fotmarkets
broker: fotmarkets
regulated: false
account_type: MT5_Standard
leverage: 500
initial_capital: 30.00
currency: USD
min_lot_broker: 0.01

# Assets operables (universo completo, filtrado por fase)
assets_universe:
  - EURUSD
  - GBPUSD
  - USDJPY
  - XAUUSD
  - NAS100
  - SPX500
  - BTCUSD
  - ETHUSD

# Ventana operativa
session_window_mx:
  start: "07:00"
  end: "11:00"
force_exit_mx: "10:55"
no_overnight: true
no_weekend: true

# Fases de escalation (ver rules.md para detalle)
phase_1:
  capital_min: 0
  capital_max: 100
  risk_per_trade_pct: 10
  risk_per_trade_usd_cap: 3.0
  max_trades_per_day: 1
  max_sl_consecutive: 1
  tp_r_multiple: 2.0
  allowed_assets: [EURUSD, GBPUSD]

phase_2:
  capital_min: 100
  capital_max: 300
  risk_per_trade_pct: 5
  max_trades_per_day: 2
  max_sl_consecutive: 2
  tp_r_multiple: 2.0
  break_even_trigger_r: 1.0
  allowed_assets: [EURUSD, GBPUSD, USDJPY, XAUUSD, NAS100]

phase_3:
  capital_min: 300
  capital_max: 999999
  risk_per_trade_pct: 2
  max_trades_per_day: 3
  max_sl_consecutive: 2
  tp_r_multiple: 2.5
  allowed_assets: [ALL]  # todos los del universo

# Strategy config global (todas las fases)
strategy:
  timeframe_primary: "5m"
  timeframe_confirmation: "15m"
  timeframe_context: "1H"
  stop_loss_atr_length: 14
  stop_loss_atr_mult: 1.2
  min_sl_pips:
    EURUSD: 8
    GBPUSD: 10
    USDJPY: 10
    XAUUSD: 20      # 20 pips = $2 en gold con 0.01 lot
    NAS100: 25      # 25 points
    SPX500: 4       # 4 points
    BTCUSD: 50      # 50 pips (CFD spread alto)
    ETHUSD: 40
```

## Estrategia activa

Ver `strategy.md` en este directorio — **Fotmarkets-Micro** (scalping reversal post-pullback).

## Memorias específicas

Ver archivos en `./memory/`:
- `trading_log.md` — journal de trades
- `phase_progress.md` — capital actual + fase vigente
- `session_notes.md` — notas operativas (spread anómalos, MT5 quirks, bonus T&C)

## Filosofía

Profile operativo REAL pero con capital de "casa de juego" ($30 bonus no depositado).
Disciplina estricta: reglas más tight que retail/ftmo por el capital micro.
NO depositar dinero propio en este broker bajo ninguna circunstancia.
```

- [ ] **Step 2: Verificar archivo creado**

Run: `cat .claude/profiles/fotmarkets/config.md | head -20`
Expected: Ver primeras líneas del archivo con "Profile: FOTMARKETS" en la línea 1.

- [ ] **Step 3: Commit**

```bash
git add .claude/profiles/fotmarkets/config.md
git commit -m "feat(fotmarkets): crear config.md del 3er profile"
```

---

## Task 2: Crear strategy.md — Fotmarkets-Micro

**Files:**
- Create: `.claude/profiles/fotmarkets/strategy.md`

- [ ] **Step 1: Crear strategy.md completo**

```markdown
# Estrategia: Fotmarkets-Micro

Scalping de reversión tras pullback, en dirección de tendencia 15m.
Sweet spot para overlap London/NY con capital micro y ventana 4h.

## 1. Filosofía

- **No somos trend-followers puros** (entraríamos tarde con capital insuficiente).
- **No somos mean-reverters contra-trend** (arriesgado en overlap London/NY).
- **Somos pullback traders**: entramos DESPUÉS de que el precio rebota levemente contra la tendencia, en dirección de la misma.

## 2. Timeframes

| Rol | TF | Para qué |
|---|---|---|
| Contexto | 1H | Ver estructura macro del día |
| Confirmación | 15m | Definir dirección de tendencia (EMA 50/200) |
| Entry | 5m | Timing de entrada exacta |

## 3. Filtros de entrada (4 obligatorios, todos simultáneos)

### LONG

1. **Trend:** `EMA50(15m) > EMA200(15m)` AND `close(15m) > EMA50(15m)`
2. **Momentum:** `RSI(14, 5m)` ∈ **[35, 55]** (rebote desde OS, no extremo)
3. **Estructura:** precio a **≤0.15%** de soporte clave:
   - Donchian Low(20) en 5m, O
   - Pivot clásico S1 del día, O
   - EMA50(15m) actuando como dynamic support
4. **Confirmación:** última vela 5m cerrada **verde** con cuerpo **>60%** del rango total (open-close vs high-low)

### SHORT

1. **Trend:** `EMA50(15m) < EMA200(15m)` AND `close(15m) < EMA50(15m)`
2. **Momentum:** `RSI(14, 5m)` ∈ **[45, 65]** (rebote desde OB)
3. **Estructura:** precio a ≤0.15% de resistencia clave (Donchian High 20, Pivot R1, o EMA50 dynamic resistance)
4. **Confirmación:** vela 5m cerrada **roja** con cuerpo >60%

## 4. Stop Loss

- **Método:** ATR-based
- **Cálculo:** `SL = entry ± (ATR(14, 5m) × 1.2)`
- **Floor por asset** (evita que el spread se coma el SL):

| Asset | Min SL pips |
|---|---|
| EURUSD | 8 |
| GBPUSD | 10 |
| USDJPY | 10 |
| XAUUSD | 20 (= $2) |
| NAS100 | 25 points |
| SPX500 | 4 points |
| BTCUSD | 50 pips |
| ETHUSD | 40 pips |

Si ATR × 1.2 < floor del asset → usar el floor.

## 5. Take Profit (phase-aware)

### Fase 1 ($30–$100): bala única
- TP único a **2.0R** del entry (cierre total 100% de la posición)
- Sin partials (complejidad innecesaria con 0.01 lote)

### Fase 2 ($100–$300): partials
- TP1 a **2.0R** (cierra 50%, mueve SL a BE)
- TP2 a **3.5R** (cierra 50% restante)

### Fase 3 ($300+): partials extendidos
- TP1 a **2.0R** (40%)
- TP2 a **3.5R** (40%, mueve SL a TP1)
- TP3 a **5.0R** (20%, SL trailing a TP2)

## 6. Position sizing (phase-aware)

```
risk_usd = capital × risk_per_trade_pct / 100
sl_pips = abs(entry - SL) en pips del asset
lots = risk_usd / (sl_pips × pip_value_per_lot)
lots = floor(lots, 2 decimales)  # MT5 rounding
if lots < 0.01 → ABORTAR (trade imposible con min lot)
```

**Ejemplo Fase 1, EURUSD:**
- Capital $30, risk 10% = $3
- SL = 10 pips
- pip_value(EURUSD, 0.01 lot) = $0.10 → pip_value por lote = $10
- lots = $3 / (10 × $10) = **0.03 lotes**
- Margin required @ 1:500: $30 × 0.03 × 100 / 500 = $1.80 (fácilmente cubierto)

## 7. Hard stops (invalidaciones)

1. `ATR(14, 5m) > 2× promedio 50 velas` → NO operar (régimen volatile)
2. Spread EURUSD > 3 pips → NO operar (condición anormal, probablemente pre-noticia)
3. 15 min antes de noticia roja (NFP, FOMC, CPI) → cierre preventivo + no reentrar 30 min
4. Jueves 07:00–09:00 MX si hay ECB meeting → NO operar en EUR pairs

## 8. Checklist pre-entry (siempre 4/4)

- [ ] Profile activo = fotmarkets (verificar statusline)
- [ ] Hora MX ∈ [07:00, 10:55]
- [ ] Asset ∈ allowed_assets de la fase actual
- [ ] Filtro 1: Trend ✓
- [ ] Filtro 2: Momentum ✓
- [ ] Filtro 3: Estructura ✓
- [ ] Filtro 4: Confirmación vela ✓
- [ ] Hard stops: ninguno activo
- [ ] Trades hoy < max_trades_per_day de la fase
- [ ] SL consecutivos < max_sl_consecutive de la fase
- [ ] Position sizing calculado con risk phase-aware
- [ ] Spread actual aceptable

11/11 → GO.
Menos → NO-GO.
```

- [ ] **Step 2: Verificar creación**

Run: `wc -l .claude/profiles/fotmarkets/strategy.md`
Expected: 90+ líneas.

- [ ] **Step 3: Commit**

```bash
git add .claude/profiles/fotmarkets/strategy.md
git commit -m "feat(fotmarkets): estrategia Fotmarkets-Micro (scalping reversal)"
```

---

## Task 3: Crear rules.md — fases + hard stops

**Files:**
- Create: `.claude/profiles/fotmarkets/rules.md`

- [ ] **Step 1: Crear rules.md**

```markdown
# Fotmarkets Rules — Formal Spec

Reglas de operación del profile `fotmarkets`. Este documento es fuente de verdad
para los scripts `fotmarkets_guard.sh` y `fotmarkets_phase.sh`.

## R1 — Phase Detection

**Definición:** La fase activa se determina por capital actual en `memory/phase_progress.md`.

```
phase_1: capital ∈ [0, 100)
phase_2: capital ∈ [100, 300)
phase_3: capital ∈ [300, ∞)
```

**Enforcement:** `fotmarkets_phase.sh` emite la fase; comandos profile-aware la leen.

## R2 — Risk per trade (phase-aware)

| Fase | Risk % | Cap USD |
|---|---|---|
| 1 | 10% | $3.00 fijo |
| 2 | 5% | dinámico |
| 3 | 2% | dinámico |

**Enforcement:** `/risk` aplica automáticamente según fase.

## R3 — Max trades/día (phase-aware)

| Fase | Max trades/día |
|---|---|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |

**Enforcement:** `fotmarkets_guard.sh` cuenta trades en `trading_log.md` del día
(líneas con fecha actual). Si trades_today >= max → BLOCK.

## R4 — Max SL consecutivos (phase-aware)

| Fase | Max SL consecutivos |
|---|---|
| 1 | 1 (cualquier SL → STOP día) |
| 2 | 2 |
| 3 | 2 |

**Enforcement:** `fotmarkets_guard.sh` lee últimos N trades del día (N = max + 1);
si todos son SL → BLOCK.

## R5 — Ventana operativa MX 07:00–11:00

**Definición:** Entries nuevos solo en [07:00, 10:55]. Force exit a 10:55.

**Enforcement:** `fotmarkets_guard.sh` chequea hora MX actual.

## R6 — No overnight / no weekend

**Definición:** Toda posición debe cerrarse antes de 10:55 MX del día. Nunca entrar
viernes si queda <1h para cierre de mercado (overnight implícito weekend).

**Enforcement:** Semi-automatizado — usuario cierra manualmente en MT5; `/journal`
detecta posiciones abiertas fuera de ventana y warninga.

## R7 — Asset whitelist por fase

Ver config.md (`phase_N.allowed_assets`). Intentar entry en asset fuera del
whitelist de la fase → BLOCK con mensaje "Asset X no desbloqueado hasta Fase Y".

## R8 — Hard stops operativos

Aplican en TODAS las fases:

1. ATR explotado (>2× promedio 50 velas en 5m) → NO operar
2. Spread anómalo (>3 pips EURUSD base, escalado para otros pairs) → NO operar
3. 15 min pre-noticia roja → cerrar posiciones abiertas + no reentrar 30 min post
4. ECB jueves 07:00–09:00 MX → no EUR pairs

**Enforcement:** Manual via checklist en strategy.md + recordatorio en `/morning`.

## R9 — Phase migration

Cuando capital cruza threshold ($100 o $300) durante el día:
1. `/journal` detecta cambio al cierre
2. Actualiza `phase_progress.md` con nueva fase
3. Emite mensaje explícito: "FASE NUEVA → assets desbloqueados: [...], risk baja a X%"
4. Usuario debe confirmar explícitamente antes de operar en fase nueva (al día siguiente)

## R10 — Override escape hatch

Usuario puede escribir literalmente `OVERRIDE FOTMARKETS` en respuesta a un BLOCK.
El guardian:
1. Registra evento en `memory/overrides.log` con timestamp, regla violada, capital, trade
2. Permite proceder

Usar solo en casos extremos. Cada override es material de post-mortem.

## Diferencias con retail y ftmo

| Aspecto | retail | ftmo | fotmarkets |
|---|---|---|---|
| Risk per trade | 2% fijo | 0.5% fijo | 10%/5%/2% por fase |
| Max trades/día | 3 | 2 | 1/2/3 por fase |
| Guardian DD rules | No | Sí (3% daily) | No (es bonus) |
| Override keyword | N/A | `OVERRIDE GUARDIAN` | `OVERRIDE FOTMARKETS` |
| Asset whitelist | BTC fijo | 6 fijos | 2/5/8 por fase |
```

- [ ] **Step 2: Verificar**

Run: `wc -l .claude/profiles/fotmarkets/rules.md`
Expected: 80+ líneas.

- [ ] **Step 3: Commit**

```bash
git add .claude/profiles/fotmarkets/rules.md
git commit -m "feat(fotmarkets): rules.md con escalation R1-R10"
```

---

## Task 4: Crear memory/ con archivos iniciales

**Files:**
- Create: `.claude/profiles/fotmarkets/memory/.gitkeep`
- Create: `.claude/profiles/fotmarkets/memory/phase_progress.md`
- Create: `.claude/profiles/fotmarkets/memory/trading_log.md`
- Create: `.claude/profiles/fotmarkets/memory/session_notes.md`

- [ ] **Step 1: Crear `.gitkeep`**

```bash
mkdir -p .claude/profiles/fotmarkets/memory
touch .claude/profiles/fotmarkets/memory/.gitkeep
```

- [ ] **Step 2: Crear `phase_progress.md`**

```markdown
# Phase Progress — Fotmarkets

Fuente de verdad del capital y fase activa del profile `fotmarkets`.
Actualizado por `/journal` al cierre de cada día.

## Estado actual

```yaml
capital_current: 30.00
capital_previous: null
phase: 1
phase_since: "2026-04-23"
trades_total: 0
trades_wins: 0
trades_losses: 0
pnl_total_usd: 0.00
last_updated: "2026-04-23T00:00:00Z"
```

## Historial de migraciones

| Fecha | Capital | Fase | Evento |
|---|---|---|---|
| 2026-04-23 | $30.00 | 1 | Profile creado, bonus inicial |

## Thresholds recordatorio

- Fase 1 → 2: capital ≥ $100 (assets desbloqueados: USDJPY, XAUUSD, NAS100)
- Fase 2 → 3: capital ≥ $300 (assets desbloqueados: SPX500, BTCUSD, ETHUSD)
```

- [ ] **Step 3: Crear `trading_log.md`**

```markdown
# Trading Log — Fotmarkets

Journal de trades ejecutados en el profile Fotmarkets.
Escrito automáticamente por `/journal`.

## Formato de tabla

| Fecha | Hora MX | Asset | Dir | Lots | Entry | SL | TP | Resultado | PnL $ | R | Fase | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Trades

(vacío — no hay trades ejecutados aún)
```

- [ ] **Step 4: Crear `session_notes.md`**

```markdown
# Session Notes — Fotmarkets

Notas operativas libres: spread anómalos, MT5 quirks, bonus T&C aclarados, aprendizajes.

## Bonus T&C (PENDIENTE VERIFICAR POR USUARIO)

Antes del primer trade, leer y documentar aquí:
- [ ] Volumen mínimo requerido para retirar profits del bonus
- [ ] Profit cap máximo del bonus (ej. $500)
- [ ] Ventana temporal (30/60/90 días)
- [ ] Requisitos KYC para retiro

## MT5 quirks

(vacío — rellenar durante operación)

## Spread observations

(vacío — documentar si ves spread anormal en algún par/hora)

## Bonus T&C confirmados

(vacío hasta leer T&C del broker)
```

- [ ] **Step 5: Verificar estructura**

Run: `ls -la .claude/profiles/fotmarkets/memory/`
Expected: ver `.gitkeep`, `phase_progress.md`, `trading_log.md`, `session_notes.md`.

- [ ] **Step 6: Commit**

```bash
git add .claude/profiles/fotmarkets/memory/
git commit -m "feat(fotmarkets): memory/ inicial con phase_progress + logs vacíos"
```

---

## Task 5: Crear script `fotmarkets_phase.sh`

**Files:**
- Create: `.claude/scripts/fotmarkets_phase.sh`
- Test: verificación manual con capital 30/100/300

- [ ] **Step 1: Crear el script**

```bash
#!/usr/bin/env bash
# .claude/scripts/fotmarkets_phase.sh
# Uso:
#   fotmarkets_phase.sh           — imprime fase actual (1|2|3) leyendo phase_progress.md
#   fotmarkets_phase.sh capital   — imprime capital actual
#   fotmarkets_phase.sh detail    — imprime fase + capital + rango de fase
#   fotmarkets_phase.sh check <N> — verifica que capital N cae en la fase actual

set -euo pipefail

PROGRESS_FILE="$(dirname "$0")/../profiles/fotmarkets/memory/phase_progress.md"

# Parse capital_current del YAML embebido en el markdown
get_capital() {
  if [[ ! -f "$PROGRESS_FILE" ]]; then
    echo "ERROR: phase_progress.md no encontrado" >&2
    exit 1
  fi
  grep -E '^capital_current:' "$PROGRESS_FILE" | awk '{print $2}' | tr -d ' '
}

# Determina fase según thresholds de config.md
phase_for_capital() {
  local cap="$1"
  # awk para comparación float-safe
  awk -v c="$cap" 'BEGIN {
    if (c < 100) print 1
    else if (c < 300) print 2
    else print 3
  }'
}

cmd="${1:-phase}"

case "$cmd" in
  phase|"")
    cap="$(get_capital)"
    phase_for_capital "$cap"
    ;;
  capital)
    get_capital
    ;;
  detail)
    cap="$(get_capital)"
    phase="$(phase_for_capital "$cap")"
    case "$phase" in
      1) echo "phase=1 capital=$cap range=[0,100) next_threshold=100" ;;
      2) echo "phase=2 capital=$cap range=[100,300) next_threshold=300" ;;
      3) echo "phase=3 capital=$cap range=[300,∞) next_threshold=none" ;;
    esac
    ;;
  check)
    test_cap="${2:-}"
    if [[ -z "$test_cap" ]]; then
      echo "ERROR: uso: fotmarkets_phase.sh check <capital>" >&2
      exit 2
    fi
    phase_for_capital "$test_cap"
    ;;
  *)
    echo "Uso: fotmarkets_phase.sh [phase|capital|detail|check <N>]" >&2
    exit 2
    ;;
esac
```

- [ ] **Step 2: Hacer ejecutable**

```bash
chmod +x .claude/scripts/fotmarkets_phase.sh
```

- [ ] **Step 3: Test manual fase 1**

Run: `bash .claude/scripts/fotmarkets_phase.sh`
Expected output: `1` (porque capital_current es 30.00).

- [ ] **Step 4: Test detail**

Run: `bash .claude/scripts/fotmarkets_phase.sh detail`
Expected: `phase=1 capital=30.00 range=[0,100) next_threshold=100`

- [ ] **Step 5: Test check con capital arbitrario**

Run: `bash .claude/scripts/fotmarkets_phase.sh check 150`
Expected: `2`

Run: `bash .claude/scripts/fotmarkets_phase.sh check 500`
Expected: `3`

Run: `bash .claude/scripts/fotmarkets_phase.sh check 50`
Expected: `1`

- [ ] **Step 6: Commit**

```bash
git add .claude/scripts/fotmarkets_phase.sh
git commit -m "feat(fotmarkets): script de phase detection"
```

---

## Task 6: Crear script `fotmarkets_guard.sh` (Lite Guardian)

**Files:**
- Create: `.claude/scripts/fotmarkets_guard.sh`

- [ ] **Step 1: Crear el script**

```bash
#!/usr/bin/env bash
# .claude/scripts/fotmarkets_guard.sh
# Lite Guardian — valida condiciones antes de entrada en profile fotmarkets
#
# Uso:
#   fotmarkets_guard.sh check
#     → imprime "PASS" y sale 0, O "BLOCK: <razón>" y sale 1
#
# Checks:
#   1. Hora MX ∈ [07:00, 10:55]
#   2. Trades hoy < max_trades_per_day de la fase
#   3. SLs consecutivos < max_sl_consecutive de la fase
#   4. No es weekend (sábado/domingo MX)

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
PROFILE_DIR="$SCRIPT_DIR/../profiles/fotmarkets"
PHASE_SCRIPT="$SCRIPT_DIR/fotmarkets_phase.sh"
LOG_FILE="$PROFILE_DIR/memory/trading_log.md"

fail() {
  echo "BLOCK: $1"
  exit 1
}

pass() {
  echo "PASS"
  exit 0
}

# Check 1: Ventana horaria MX
HORA_HHMM=$(TZ='America/Mexico_City' date +%H%M)
if [[ "$HORA_HHMM" -lt 700 || "$HORA_HHMM" -gt 1055 ]]; then
  fail "Fuera de ventana operativa MX 07:00-10:55 (hora actual: ${HORA_HHMM:0:2}:${HORA_HHMM:2:2})"
fi

# Check 2: Weekend
DOW=$(TZ='America/Mexico_City' date +%u)   # 1=Mon ... 7=Sun
if [[ "$DOW" -ge 6 ]]; then
  fail "Weekend: mercados Forex cerrados (día $DOW)"
fi

# Check 3: Phase detection
PHASE=$(bash "$PHASE_SCRIPT" 2>/dev/null || echo "1")

# Mapea fase → max_trades y max_sl_consecutive
case "$PHASE" in
  1) MAX_TRADES=1; MAX_SL_CONSEC=1 ;;
  2) MAX_TRADES=2; MAX_SL_CONSEC=2 ;;
  3) MAX_TRADES=3; MAX_SL_CONSEC=2 ;;
  *) fail "Fase desconocida: $PHASE" ;;
esac

# Check 4: Trades hoy
FECHA=$(TZ='America/Mexico_City' date +%Y-%m-%d)
TRADES_HOY=0
if [[ -f "$LOG_FILE" ]]; then
  TRADES_HOY=$(grep -c "^| $FECHA " "$LOG_FILE" 2>/dev/null || echo 0)
  TRADES_HOY=${TRADES_HOY:-0}
fi

if [[ "$TRADES_HOY" -ge "$MAX_TRADES" ]]; then
  fail "Max trades/día alcanzado en Fase $PHASE: $TRADES_HOY/$MAX_TRADES"
fi

# Check 5: SL consecutivos (últimos N trades hoy)
if [[ -f "$LOG_FILE" && "$TRADES_HOY" -ge "$MAX_SL_CONSEC" ]]; then
  # Extrae columna "Resultado" (8ª columna separada por |) de últimos N trades del día
  LAST_N_RESULTS=$(grep "^| $FECHA " "$LOG_FILE" | tail -n "$MAX_SL_CONSEC" \
    | awk -F'|' '{ gsub(/ /, "", $10); print tolower($10) }')

  CONSEC_SL=true
  while IFS= read -r line; do
    if [[ "$line" != "sl" ]]; then
      CONSEC_SL=false
      break
    fi
  done <<< "$LAST_N_RESULTS"

  if [[ "$CONSEC_SL" == "true" ]]; then
    fail "Stop día: $MAX_SL_CONSEC SL consecutivos en Fase $PHASE"
  fi
fi

pass
```

- [ ] **Step 2: Hacer ejecutable**

```bash
chmod +x .claude/scripts/fotmarkets_guard.sh
```

- [ ] **Step 3: Test durante ventana MX (si ejecutas entre 07:00–10:55 un día hábil)**

Run: `bash .claude/scripts/fotmarkets_guard.sh check`
Expected: `PASS` (exit 0) si:
- Hora MX está en ventana
- Es día hábil
- No hay trades hoy

Si no estás en ventana, esperar output: `BLOCK: Fuera de ventana operativa...`

- [ ] **Step 4: Test fuera de ventana (simulado con override de env — opcional)**

Si no estás en ventana naturalmente, el script debe decir BLOCK. Validar con:
Run: `bash .claude/scripts/fotmarkets_guard.sh check; echo "exit: $?"`
Expected: Si dice BLOCK → exit 1. Si dice PASS → exit 0.

- [ ] **Step 5: Commit**

```bash
git add .claude/scripts/fotmarkets_guard.sh
git commit -m "feat(fotmarkets): Lite Guardian (ventana/trades/SL consecutivos)"
```

---

## Task 7: Actualizar statusline.sh con rama fotmarkets

**Files:**
- Modify: `.claude/scripts/statusline.sh`

- [ ] **Step 1: Leer archivo actual completo**

Run: `cat .claude/scripts/statusline.sh | wc -l`
Expected: 110+ líneas.

- [ ] **Step 2: Agregar bloque de fotmarkets antes del bloque retail**

Localiza la línea exacta que empieza con `# RETAIL path (preserva comportamiento actual)` (aproximadamente línea 40–41) e inserta este bloque ANTES de esa línea:

```bash
# FOTMARKETS path
if [[ "$PROFILE" == "fotmarkets" ]]; then
  SCRIPT_DIR="$(dirname "$0")"
  PROGRESS="$SCRIPT_DIR/../profiles/fotmarkets/memory/phase_progress.md"
  LOG="$SCRIPT_DIR/../profiles/fotmarkets/memory/trading_log.md"

  CAP=$(grep -E '^capital_current:' "$PROGRESS" 2>/dev/null | awk '{print $2}' | tr -d ' ')
  CAP=${CAP:-30.00}

  PHASE=$(bash "$SCRIPT_DIR/fotmarkets_phase.sh" 2>/dev/null || echo "1")
  case "$PHASE" in
    1) NEXT_THRESHOLD="→\$100"; MAX_TRADES=1 ;;
    2) NEXT_THRESHOLD="→\$300"; MAX_TRADES=2 ;;
    3) NEXT_THRESHOLD="estándar"; MAX_TRADES=3 ;;
  esac

  HORA_MX=$(TZ='America/Mexico_City' date +%H:%M)
  FECHA=$(TZ='America/Mexico_City' date +%Y-%m-%d)

  TRADES_HOY=0
  if [[ -f "$LOG" ]]; then
    TRADES_HOY=$(grep -c "^| $FECHA " "$LOG" 2>/dev/null || echo 0)
    TRADES_HOY=${TRADES_HOY:-0}
  fi

  # Ventana 07:00-11:00
  HORA_HHMM=$(TZ='America/Mexico_City' date +%H%M)
  if [[ "$HORA_HHMM" -ge 700 && "$HORA_HHMM" -le 1055 ]]; then
    VENTANA="🟢 VENT"
  elif [[ "$HORA_HHMM" -gt 1055 && "$HORA_HHMM" -le 1100 ]]; then
    VENTANA="🟡 CLOSE"
  else
    VENTANA="🔴 OFF"
  fi

  echo "[FOTMARKETS] \$$CAP | Fase $PHASE ($NEXT_THRESHOLD) | $VENTANA MX $HORA_MX | $TRADES_HOY/$MAX_TRADES trades$NOTION_TAG"
  exit 0
fi
```

- [ ] **Step 3: Test statusline con profile fotmarkets**

```bash
bash .claude/scripts/profile.sh set fotmarkets
bash .claude/scripts/statusline.sh
```

Expected output (una línea): `[FOTMARKETS] $30.00 | Fase 1 (→$100) | 🟡 CLOSE MX HH:MM | 0/1 trades` (o 🟢/🔴 según hora).

- [ ] **Step 4: Test que retail sigue funcionando**

```bash
bash .claude/scripts/profile.sh set retail
bash .claude/scripts/statusline.sh
```

Expected: formato retail original intacto.

- [ ] **Step 5: Test que ftmo sigue funcionando**

```bash
bash .claude/scripts/profile.sh set ftmo
bash .claude/scripts/statusline.sh
```

Expected: formato FTMO intacto.

- [ ] **Step 6: Dejar profile en retail (default pre-setup)**

```bash
bash .claude/scripts/profile.sh set retail
```

- [ ] **Step 7: Commit**

```bash
git add .claude/scripts/statusline.sh
git commit -m "feat(fotmarkets): rama statusline para 3er profile"
```

---

## Task 8: Actualizar `/profile` command docs

**Files:**
- Modify: `.claude/commands/profile.md`

- [ ] **Step 1: Reemplazar contenido del archivo**

```markdown
# /profile

Muestra o cambia el profile activo del sistema.

Uso:
- `/profile` — muestra profile activo y timestamp
- `/profile ftmo` — switch a FTMO
- `/profile retail` — switch a retail
- `/profile fotmarkets` — switch a Fotmarkets (bonus $30)
- `/profile status` — resumen rápido de los 3 profiles

Pasos que ejecuta Claude:

1. Si el argumento es vacío:
   - Corre `bash .claude/scripts/profile.sh show`
   - Devuelve el profile actual + timestamp

2. Si el argumento es `status`:
   - Lee `.claude/profiles/retail/config.md` y resume (capital, strategy)
   - Lee `.claude/profiles/ftmo/config.md` y resume (challenge progress)
   - Lee `.claude/profiles/fotmarkets/config.md` y resume (capital, fase)
   - Si FTMO tiene `equity_curve.csv` no vacío, muestra equity + daily PnL
   - Si FOTMARKETS tiene `phase_progress.md` poblado, muestra capital + fase
   - Marca con ▶ el profile activo

3. Si el argumento es `ftmo`, `retail` o `fotmarkets`:
   - **Validación previa**: pregunta "¿tienes trade abierto en el profile actual?" — si sí, BLOCK switch con mensaje "cierra primero"
   - Corre `bash .claude/scripts/profile.sh set <arg>`
   - Confirma con el nuevo statusline
   - Si destino es `ftmo`: prompt "¿actualizar equity FTMO ahora? (último: $X @ <timestamp>)"
   - Si destino es `fotmarkets`: prompt "¿ya leíste bonus T&C? Ver memory/session_notes.md"

4. Si el argumento no es reconocido:
   - Devuelve error: "uso: /profile [ftmo|retail|fotmarkets|status]"

Reglas:
- NUNCA cambiar profile si hay trade abierto (evita cross-contamination)
- Después de switch, recordar al usuario que las memorias del otro profile quedan intactas
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/profile.md
git commit -m "docs(fotmarkets): extender /profile command para 3er profile"
```

---

## Task 9: Actualizar `/status` command

**Files:**
- Modify: `.claude/commands/status.md`

- [ ] **Step 1: Leer archivo actual para entender estructura**

Run: `cat .claude/commands/status.md`

- [ ] **Step 2: Reescribir completo con rama fotmarkets**

```markdown
Muestra el estado completo del sistema según el profile activo.

Pasos que ejecuta Claude:

1. Lee profile activo: `PROFILE=$(bash .claude/scripts/profile.sh get)`

2. SI profile == "retail":
   - Lee `.claude/profiles/retail/config.md` (capital, estrategia activa)
   - Lee `.claude/profiles/retail/memory/trading_log.md` (últimos trades)
   - Lee `.claude/profiles/retail/memory/market_regime.md` (niveles vigentes)
   - Muestra statusline retail expandido:
     ```
     [RETAIL $13.63]
     Estrategia: Mean Reversion 15m
     Régimen: <detecta vía regime-detector rápido o cachea>
     Hora MX: HH:MM
     Trades hoy: 0/3
     Último trade: <fecha> <resultado>
     ```

3. SI profile == "ftmo":
   - Invoca: `python3 .claude/scripts/guardian.py --profile ftmo --action status`
   - Lee `.claude/profiles/ftmo/memory/challenge_progress.md`
   - Muestra statusline FTMO expandido:
     ```
     [FTMO $10k]
     Equity: $X (+Y%)
     Daily PnL: $X (Y% / 3% limit)
     Trailing DD: $X (Y% / 10% limit)
     Best Day ratio: Y% (cap 50%)
     Trades hoy: N/2
     Estrategia: FTMO-Conservative
     Asset vigilancia: <top 1-2 del morning-analyst-ftmo>
     ```

4. SI profile == "fotmarkets":
   - Lee `.claude/profiles/fotmarkets/memory/phase_progress.md` (capital + fase)
   - Lee `.claude/profiles/fotmarkets/memory/trading_log.md` (trades hoy)
   - Invoca: `bash .claude/scripts/fotmarkets_phase.sh detail`
   - Invoca: `bash .claude/scripts/fotmarkets_guard.sh check` (captura PASS/BLOCK)
   - Muestra statusline fotmarkets expandido:
     ```
     [FOTMARKETS $30.00]
     Fase: 1 (rango [0, 100))
     Próximo threshold: $100 (desbloquea USDJPY, XAUUSD, NAS100)
     Risk por trade: 10% ($3.00)
     Max trades hoy: 1
     Estrategia: Fotmarkets-Micro
     Ventana MX: 07:00–11:00
     Guardian: PASS/BLOCK <razón>
     Trades hoy: 0/1
     Último trade: <fecha> <resultado>
     ```

5. SI profile no reconocido:
   - Muestra warning: "Profile desconocido: <X>. Corre /profile ftmo|retail|fotmarkets."

6. Al final de cualquier output, incluye: "Última actualización: <timestamp>. Cambiar profile: /profile ftmo|retail|fotmarkets"
```

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/status.md
git commit -m "feat(fotmarkets): /status con rama phase-aware"
```

---

## Task 10: Actualizar `/morning` command

**Files:**
- Modify: `.claude/commands/morning.md`

- [ ] **Step 1: Agregar rama fotmarkets al archivo existente**

Localiza la sección "3. SI profile == "ftmo":" e inserta DESPUÉS de ese bloque, ANTES de "4. Si argumento opcional":

```markdown
4. SI profile == "fotmarkets":
   - Ejecuta validación previa:
     ```
     bash .claude/scripts/fotmarkets_guard.sh check
     ```
     Si BLOCK por ventana u otras razones → muestra el BLOCK pero continúa con análisis "preparativo" (sin entry sugerida).
   - Lee `.claude/profiles/fotmarkets/config.md` para obtener `phase` actual y `allowed_assets`
   - Despacha `morning-analyst-ftmo` con instrucción especial:
     - "Analizar SOLO los siguientes assets: <allowed_assets de la fase actual>"
     - "Usar reglas de Fotmarkets-Micro (no FTMO-Conservative): filtros de strategy.md"
     - "Ventana operativa: MX 07:00-11:00 (no 06:00-16:00)"
     - "Risk per trade: <phase_risk_pct>% (phase-aware), cap $<phase_risk_usd_cap>"
     - "Max trades hoy: <phase_max_trades>"
   - El agente usa niveles/memoria de `profiles/fotmarkets/memory/`
   - Al final, recordatorio explícito:
     - "⚠️ Profile fotmarkets = bonus $30 en broker no regulado. Este no reemplaza tu profile FTMO/retail real."
     - "Verificar bonus T&C en memory/session_notes.md antes de ejecutar."
```

Renumera el paso "4. Si argumento opcional..." a "5." (ajuste automático).

- [ ] **Step 2: Verificar estructura**

Run: `grep -n "SI profile" .claude/commands/morning.md`
Expected: 3 líneas coincidentes (retail, ftmo, fotmarkets).

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/morning.md
git commit -m "feat(fotmarkets): /morning reusa morning-analyst-ftmo con asset filter"
```

---

## Task 11: Actualizar `/risk` command (phase-aware)

**Files:**
- Modify: `.claude/commands/risk.md`

- [ ] **Step 1: Agregar rama fotmarkets**

Inserta después de la sección "3. SI profile == "ftmo":" y antes de "4. Output:":

```markdown
3.5. SI profile == "fotmarkets":
   - Lee capital actual: `CAP=$(bash .claude/scripts/fotmarkets_phase.sh capital)`
   - Detecta fase: `PHASE=$(bash .claude/scripts/fotmarkets_phase.sh)`
   - Mapea fase → risk_pct y risk_usd_cap:
     - Fase 1: risk_pct=10, cap=$3.00
     - Fase 2: risk_pct=5, cap=null (dinámico)
     - Fase 3: risk_pct=2, cap=null (dinámico)
   - Fórmula:
     ```
     risk_usd = min(CAP * risk_pct / 100, risk_usd_cap if set else infinity)
     sl_pips = abs(entry - sl) en pips del asset
     
     # pip value por 0.01 lot (referencia):
     #   EURUSD, GBPUSD, USDJPY, etc: $0.10
     #   XAUUSD: $0.10 por pip (pip = 0.10 en gold, 1 pip = $0.10 con 0.01 lote)
     #   NAS100: $0.10 por punto
     #   SPX500: $0.10 por punto
     #   BTCUSD CFD: depende del broker, usar tamaño sugerido del broker
     
     lots = risk_usd / (sl_pips * pip_value_per_lot)
     lots = floor(lots * 100) / 100  # redondeo 2 decimales hacia abajo
     
     if lots < 0.01 → ABORTAR con mensaje:
       "Trade imposible: sizing calculado ${lots} < min lot 0.01. Amplia SL o espera Fase N."
     ```
   - Valida asset en whitelist de la fase:
     ```
     if asset NOT IN phase_N.allowed_assets → ERROR "Asset <X> no desbloqueado hasta Fase Y"
     ```
   - Valida que trade sea viable con el Lite Guardian:
     ```
     bash .claude/scripts/fotmarkets_guard.sh check
     ```
     Si BLOCK → comunicar razón y sugerir posponer.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/risk.md
git commit -m "feat(fotmarkets): /risk phase-aware con whitelist assets"
```

---

## Task 12: Actualizar `/validate` command

**Files:**
- Modify: `.claude/commands/validate.md`

- [ ] **Step 1: Insertar rama fotmarkets después de sección ftmo**

Localiza "3. SI profile == "ftmo":" (termina antes de "4. Formato de output estándar"). Inserta DESPUÉS del bloque ftmo y ANTES de "4. Formato de output":

```markdown
3.5. SI profile == "fotmarkets":
   - Invoca Lite Guardian primero:
     ```
     GUARD=$(bash .claude/scripts/fotmarkets_guard.sh check)
     ```
     Si `GUARD` empieza con `BLOCK`:
       - Muestra razón al usuario
       - Pregunta si quiere proceder con `OVERRIDE FOTMARKETS` (regla R10 de rules.md)
       - Si NO → abortar validación con NO-GO
       - Si OVERRIDE → continuar pero registrar en `memory/overrides.log`

   - Despacha agente `trade-validator` con contexto:
     - "Usar filtros de Fotmarkets-Micro (ver .claude/profiles/fotmarkets/strategy.md sección 3)"
     - 4 filtros obligatorios LONG o SHORT según dirección propuesta
   
   - Verifica que asset esté en whitelist de la fase actual:
     - `PHASE=$(bash .claude/scripts/fotmarkets_phase.sh)`
     - Cargar `phase_N.allowed_assets` de config.md
     - Si asset NO en whitelist → NO-GO con mensaje "Asset <X> desbloqueado en Fase Y+"
   
   - Si 4/4 filtros + asset whitelist OK:
     - Calcula sizing invocando `/risk` con datos del setup
     - Valida hard stops (ATR, spread, noticias) via strategy.md sección 7
     - Si algún hard stop activo → NO-GO con razón
     - Si todo OK → "GO" con mostrar:
       ```
       Asset:      <X>
       Fase:       <N>
       Entry:      <P>
       SL:         <P> (dist <D> pips / X%)
       TP:         <P> (R=2.0)
       Lots:       <lots>
       Risk USD:   $<X>
       Risk %:     <phase_risk_pct>% del capital actual ($<CAP>)
       Guardian:   PASS
       Filtros:    4/4 ✓
       ```
   
   - Si usuario escribe "OVERRIDE FOTMARKETS":
     - Append a `.claude/profiles/fotmarkets/memory/overrides.log`:
       `<timestamp>|fotmarkets|<rule_violated>|<capital>|<trade_json>|<user_reason>`
     - Procede con "GO" pero con warning
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/validate.md
git commit -m "feat(fotmarkets): /validate con 4 filtros + Lite Guardian + whitelist"
```

---

## Task 13: Actualizar `/journal` command (phase migration)

**Files:**
- Modify: `.claude/commands/journal.md`

- [ ] **Step 1: Insertar rama fotmarkets**

Localiza "5. SI profile == "retail":" e inserta ANTES de esa línea (después del bloque ftmo y su sub-secciones E/F/G):

```markdown
4.5. SI profile == "fotmarkets":

   **H. Actualizar phase_progress.md:**
   - Pregunta al usuario: "Capital actual en MT5 Fotmarkets (en USD, sin símbolo)?"
   - Lee `.claude/profiles/fotmarkets/memory/phase_progress.md` actual
   - Parse `capital_current` previo
   - Actualiza:
     ```yaml
     capital_previous: <valor anterior>
     capital_current: <valor nuevo del usuario>
     trades_total: <incremento según trades escritos>
     trades_wins / trades_losses: <incremento según resultado>
     pnl_total_usd: <acumulado>
     last_updated: "<timestamp ISO>"
     ```
   - Calcula fase nueva con `fotmarkets_phase.sh check <nuevo_capital>`
   - Si fase_nueva != fase_previa:
     - Actualiza campo `phase` y `phase_since` al timestamp actual
     - Append al historial:
       ```
       | <fecha> | $<nuevo> | <fase_nueva> | MIGRACIÓN: fase <previa>→<nueva> |
       ```
     - Muestra al usuario:
       ```
       ⚠️ MIGRACIÓN DE FASE DETECTADA
       De Fase <X> → Fase <Y>
       Nuevos assets desbloqueados: <list>
       Risk por trade: <old>% → <new>%
       Max trades/día: <old> → <new>
       
       Confirma que entendiste antes de operar mañana.
       ```
   - Si fase es la misma:
     - Solo append trades al log
   
   **I. Registrar trades del día:**
   - Pregunta al usuario: "Lista de trades de hoy, uno por línea, formato: asset,dir,entry,sl,tp,close,resultado,pnl_usd"
   - Parse cada línea y append a `trading_log.md` con formato de tabla
   - Ejemplo:
     ```
     | 2026-04-23 | 09:32 | EURUSD | LONG | 0.03 | 1.0830 | 1.0820 | 1.0850 | tp | +$6.00 | 2.0 | 1 | NY overlap clean break |
     ```

   **J. Verificar posiciones fuera de ventana:**
   - Pregunta: "¿Alguna posición sigue abierta ahora?"
   - Si sí → WARNING grande: "Profile fotmarkets prohíbe overnight. Cierra manualmente en MT5 YA."
   
   **K. Notion dual-write (si NOTION_FOTMARKETS_DB_ID configurado):**
   - Igual a ftmo/retail pero DB = NOTION_FOTMARKETS_DB_ID
   - Si no configurado → skip sin error
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/journal.md
git commit -m "feat(fotmarkets): /journal con phase migration + trade logging"
```

---

## Task 14: Actualizar `/levels` command (asset-agnostic)

**Files:**
- Modify: `.claude/commands/levels.md`

- [ ] **Step 1: Reescribir para ser profile-aware**

```markdown
---
description: Muestra niveles técnicos actuales (Donchian, BB, RSI, ATR) del asset activo del profile
allowed-tools: mcp__tradingview__quote_get, mcp__tradingview__chart_set_timeframe, mcp__tradingview__chart_set_symbol, mcp__tradingview__data_get_ohlcv, Bash
---

Niveles técnicos actuales del asset activo del profile.

Pasos que ejecuta Claude:

1. Lee profile: `PROFILE=$(bash .claude/scripts/profile.sh get)`

2. Determina símbolo a analizar:
   - retail → `BINGX:BTCUSDT.P` (único asset)
   - ftmo → pregunta al usuario cuál asset de los 6 del universo quiere (o usa el último analizado en morning)
   - fotmarkets → pregunta al usuario cuál asset de los allowed_assets de la fase actual

3. Determina timeframe primario del profile:
   - retail → 15m
   - ftmo → 15m
   - fotmarkets → 5m

4. Cambia TF al del profile y pull últimas 50 velas (excluir la forming)

5. Calcula:
   - **Donchian(20)** High y Low (en retail usa 15)
   - **Bollinger Bands(20, 2)** upper, mid, lower
   - **RSI(14)** actual
   - **ATR(14)** actual
   - **EMA 50** (si hay 50+ barras disponibles)
   - **EMA 200** (si hay 200+ barras)

6. Identifica:
   - Distancia del precio actual a cada nivel (%)
   - Cuál está más cerca (soporte o resistencia)
   - Si precio está dentro de zona de entrada (±0.15% de Donchian H/L para fotmarkets, ±0.1% para retail/ftmo)

7. Entrega:
   - Tabla con todos los niveles
   - Precio actual vs nivel más cercano
   - Recomendación rápida: ¿esperar, vigilar, o ya está en zona?

Formato compacto, máximo 20 líneas de output.

Si argumentos adicionales ($ARGUMENTS) → usar como símbolo override (ej: `/levels EURUSD`).
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/levels.md
git commit -m "feat(fotmarkets): /levels asset-agnostic profile-aware"
```

---

## Task 15: Actualizar `/regime` command (Forex ADX)

**Files:**
- Modify: `.claude/commands/regime.md`

- [ ] **Step 1: Leer archivo actual**

Run: `cat .claude/commands/regime.md`

- [ ] **Step 2: Agregar rama profile-aware**

Reescribir para que al final del archivo tenga esta lógica (estructura puede variar según archivo original):

```markdown
## Profile-aware logic

1. Lee profile: `PROFILE=$(bash .claude/scripts/profile.sh get)`

2. SI profile == "retail":
   - Lógica actual (BTC 4H + 1H)
   - Régimenes: RANGE / TRENDING UP / TRENDING DOWN / VOLATILE
   - Basado en ATR multiplier + distance from extremes

3. SI profile == "ftmo":
   - Misma lógica pero aplicable al asset pregun tado (no solo BTC)
   - Incluye ADX como métrica adicional

4. SI profile == "fotmarkets":
   - Forex/Indices requiere ADX principalmente (no BTC-style range detection)
   - Métricas:
     - ADX(14) en 15m:
       - ADX < 20 → RANGE (lateral, operable con strategy actual solo si hay soporte/resistencia tight)
       - ADX 20-30 → TREND leve (ideal para Fotmarkets-Micro pullback)
       - ADX > 30 → TREND fuerte (operar solo a favor, evitar reversiones)
       - ADX > 40 → TREND extremo (no operar scalping reversal)
     - +DI vs -DI: dirección del trend
   - Output:
     ```
     Asset: <X>
     ADX(15m): <val>
     Régimen: <RANGE|TREND_LEVE|TREND_FUERTE|TREND_EXTREMO>
     +DI: <val> | -DI: <val>
     Dirección: <LONG_BIAS|SHORT_BIAS|NEUTRAL>
     Recomendación Fotmarkets-Micro: <OPERAR|PAUSAR|SOLO_LONG|SOLO_SHORT>
     ```
```

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/regime.md
git commit -m "feat(fotmarkets): /regime con ADX para Forex/Índices"
```

---

## Task 16: Actualizar `CLAUDE.md` con 3er profile

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Localizar sección "Profile System (Dual)"**

Run: `grep -n "Profile System" CLAUDE.md`
Expected: una línea tipo `## Profile System (Dual)`

- [ ] **Step 2: Renombrar sección y agregar 3er profile**

Cambiar "Profile System (Dual)" a "Profile System (Triple)" y agregar después del bloque `### Profile `ftmo`` un nuevo bloque:

```markdown
### Profile `fotmarkets` (bonus $30)
- **Capital $30 USD** — bonus no-deposit de Fotmarkets (Mauritius, sin regulación tier-1)
- **MT5 Standard 1:500** (forzado por bonus T&C)
- Multi-asset (8 assets, desbloqueados por fase): EURUSD/GBPUSD → USDJPY/XAUUSD/NAS100 → SPX500/BTCUSD/ETHUSD
- Estrategia **Fotmarkets-Micro** (scalping reversal post-pullback 5m)
- Escalation risk: **10% → 5% → 2%** según fase ($30→$100→$300+)
- Ventana **MX 07:00–11:00** (London/NY overlap)
- Ejecución **manual en MT5** (sin EA bridge)
- Ver `.claude/profiles/fotmarkets/config.md`, `strategy.md`, `rules.md`

**⚠️ Filosofía Fotmarkets:** capital es bonus ("casa de juego"), NO depositar dinero propio,
no reemplaza el profile FTMO/retail real.
```

También, en la subsección "Reglas de operación dual", cambiar "dual" a "multi-profile":

```markdown
### Reglas de operación multi-profile
1. **No operar múltiples profiles el mismo día.** Switch al inicio de sesión.
2. **Nunca cruzar memorias** — trade FTMO no se escribe al log retail/fotmarkets y viceversa.
3. **Guardian** (`.claude/scripts/guardian.py`) obligatorio en FTMO antes de cada entry.
4. **Lite Guardian** (`.claude/scripts/fotmarkets_guard.sh`) obligatorio en fotmarkets antes de cada entry.
5. **Statusline** muestra `[PROFILE]` en todo momento para prevenir confusión.
```

En la subsección "Comandos específicos dual-profile", agregar:

```markdown
- `/profile fotmarkets` — switch al 3er profile
- `/risk` en fotmarkets → calcula sizing phase-aware (10%/5%/2%)
```

- [ ] **Step 3: Verificar cambios**

Run: `grep -c "fotmarkets" CLAUDE.md`
Expected: ≥5 (varias referencias).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: actualizar CLAUDE.md con 3er profile fotmarkets"
```

---

## Task 17: Smoke test end-to-end

**Files:**
- No modifications (solo verificación)

- [ ] **Step 1: Switch a fotmarkets**

```bash
bash .claude/scripts/profile.sh set fotmarkets
```

Expected: `switched to: fotmarkets | <timestamp>`

- [ ] **Step 2: Verificar statusline**

```bash
bash .claude/scripts/statusline.sh
```

Expected: una línea con `[FOTMARKETS] $30.00 | Fase 1 (→$100) | ... MX HH:MM | 0/1 trades`

- [ ] **Step 3: Verificar phase detection**

```bash
bash .claude/scripts/fotmarkets_phase.sh detail
```

Expected: `phase=1 capital=30.00 range=[0,100) next_threshold=100`

- [ ] **Step 4: Verificar Lite Guardian**

```bash
bash .claude/scripts/fotmarkets_guard.sh check
```

Expected: `PASS` si hora MX ∈ [07:00, 10:55] y es día hábil, o `BLOCK: <razón>` fuera de ventana.

- [ ] **Step 5: Verificar validación cruzada (estructura de archivos)**

```bash
ls .claude/profiles/fotmarkets/
ls .claude/profiles/fotmarkets/memory/
```

Expected:
```
config.md  memory  rules.md  strategy.md
```
y
```
.gitkeep  phase_progress.md  session_notes.md  trading_log.md
```

- [ ] **Step 6: Verificar profile.sh validate**

```bash
bash .claude/scripts/profile.sh validate
```

Expected: `OK: fotmarkets`

- [ ] **Step 7: Test migración simulada a fase 2**

```bash
bash .claude/scripts/fotmarkets_phase.sh check 150
bash .claude/scripts/fotmarkets_phase.sh check 400
```

Expected: `2` y `3` respectivamente.

- [ ] **Step 8: Rollback a profile de default**

```bash
bash .claude/scripts/profile.sh set retail
bash .claude/scripts/statusline.sh
```

Expected: statusline retail funciona intacta.

- [ ] **Step 9: Test final con ftmo**

```bash
bash .claude/scripts/profile.sh set ftmo
bash .claude/scripts/statusline.sh
```

Expected: statusline ftmo funciona intacta.

- [ ] **Step 10: Commit final "smoke test passed"**

```bash
git commit --allow-empty -m "test(fotmarkets): smoke test end-to-end PASS

- Profile switch funciona (retail ↔ ftmo ↔ fotmarkets)
- Statusline con 3 ramas correctas
- fotmarkets_phase.sh retorna fase correcta para capital variado
- fotmarkets_guard.sh valida ventana + weekend + trades/day
- Estructura de archivos completa
- CLAUDE.md documenta 3er profile"
```

---

## Self-Review checklist

**Spec coverage verification:**

- [x] Sec 3 (Identidad) → Task 1 (config.md)
- [x] Sec 4 (Risk model R1) → Task 1 (config.md) + Task 3 (rules.md) + Task 11 (/risk)
- [x] Sec 5 (Estrategia Fotmarkets-Micro) → Task 2 (strategy.md) + Task 12 (/validate)
- [x] Sec 6 (Integración comandos) → Tasks 7–15 (statusline + 7 comandos)
- [x] Sec 6 (Lite Guardian) → Task 6 (fotmarkets_guard.sh)
- [x] Sec 6 (Phase detection) → Task 5 (fotmarkets_phase.sh)
- [x] Sec 6 (Statusline) → Task 7
- [x] Sec 6 (CLAUDE.md) → Task 16
- [x] Sec 7 (Bonus T&C recordatorio) → Task 4 (session_notes.md template)
- [x] Sec 8 (Criterios de éxito) → Task 17 (smoke test)
- [x] Sec 9 (Fuera de scope) → respetado (no /backtest, no EA bridge, no ml)

**Placeholder scan:** ninguno detectado (todo tiene código completo).

**Type consistency:**
- `PROFILE` variable usada consistentemente en todos los commands.
- `phase_N.allowed_assets`, `phase_N.risk_per_trade_pct` nombres consistentes en config.md + rules.md + plan tasks.
- `fotmarkets_phase.sh` y `fotmarkets_guard.sh` nombres usados consistentemente en plan y commands.
- `OVERRIDE FOTMARKETS` (distinto a `OVERRIDE GUARDIAN` de FTMO) consistente en rules.md + /validate.

No hay gaps conocidos. Plan completo.
