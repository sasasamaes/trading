# 🎯 RISK CALCULATOR - BREAKOUT EDITION

## 📊 CALCULADORA DE GESTIÓN DE RIESGO

### 🔢 CÁLCULO AUTOMÁTICO DE POSICIÓN

```
═══════════════════════════════════════════════════
💰 BREAKOUT RISK CALCULATOR v3.3
═══════════════════════════════════════════════════

📅 FECHA: __/__/2025
⏰ HORA: __:__ UTC
```

---

## 📋 PASO 1 - VERIFICACIÓN DE LÍMITES

### 🔍 DATOS DE CUENTA ACTUALES:

```
💰 BALANCE BREAKOUT:
Balance Actual: $__________
Daily Limit (desde 00:30 UTC): $__________
Pérdidas Hoy: $__________
Daily Restante: $__________
Max DD Permitido: $__________ [STATIC/TRAILING]
Distancia al DD: $__________

🚦 ZONA DE RIESGO ACTUAL:
[ ] VERDE (>$500 del DD) → Riesgo 1%
[ ] AMARILLA ($300-500 DD) → Riesgo 0.5%  
[ ] ROJA (<$300 DD) → Riesgo 0.25%

✅ ESPACIO DISPONIBLE:
[ ] SUFICIENTE para operar
[ ] INSUFICIENTE → STOP OBLIGATORIO
```

---

## 📋 PASO 2 - CÁLCULO DE RIESGO

### 🎯 RIESGO PERMITIDO:

```
📊 RIESGO BASE:
Zona: [VERDE/AMARILLA/ROJA]
Porcentaje: [1% / 0.5% / 0.25%]
Balance: $__________
Riesgo Base: $__________

🔄 AJUSTES POR CONTEXTO:
Si ya perdí hoy: × 0.8 = $__________
Si 2 pérdidas seguidas: × 0.5 = $__________
Si racha ganadora 3+: × 1.0 = $__________

💰 RIESGO FINAL PERMITIDO: $__________
```

---

## 📋 PASO 3 - CÁLCULO DE TAMAÑO

### 📏 FÓRMULA DE POSICIÓN:

```
📊 DATOS DEL SETUP:
Par: [BTC/USDT / ETH/USDT / OTRO]
Entrada: $__________
Stop Loss: $__________
Distancia $: $__________
Distancia %: ____%

⚙️ PARÁMETROS DE LEVERAGE:
BTC/ETH: 5x máximo
Otros pares: 2x máximo
Leverage a usar: __x

🧮 CÁLCULO DE TAMAÑO:
Fórmula: Tamaño = Riesgo / (Distancia % × Precio Entrada)

Cálculo:
= $__________ / (___% × $__________)
= $__________ / $__________
= __________ [unidades]

💰 VALOR POSICIÓN:
__________ × $__________ = $__________
📈 MARGEN USADO: $__________ (con leverage __x)
⚠️ PÉRDIDA MÁXIMA: $__________ ✓
```

---

## 📋 PASO 4 - TAKE PROFITS

### 🎯 NIVELES DE SALIDA:

```
📈 TAKE PROFIT 1 (60% posición):
Nivel: $__________
Distancia: +___%
Ganancia: +$__________
R:R: 1:___

📈 TAKE PROFIT 2 (40% posición):
Nivel: $__________  
Distancia: +___%
Ganancia: +$__________
R:R: 1:___

📊 R:R BLENDED: 1:___
✅ MÍNIMO REQUERIDO: 1:3
```

---

## 📋 PASO 5 - CÁLCULO DE FEES

### 💸 FEES OFICIALES BREAKOUT:

```
📊 TRADING FEES:
Fee entrada: $__________ × 0.035% = $__________
Fee salida: $__________ × 0.035% = $__________
Fee total estimado: $__________

🔄 SWAP FEE (si mantiene >00:00 UTC):
Swap diario: $__________ × 0.05% = $__________
Días mantenidos: ___
Swap total: $__________

💰 FEES TOTALES: $__________
```

---

## 📋 PASO 6 - P&L AJUSTADO

### 📊 CÁLCULO NETO:

```
📈 P&L BRUTO:
TP1: +$__________
TP2: +$__________
Total: +$__________

💸 P&L NETO (después de fees):
TP1: $__________ - $__________ = $__________
TP2: $__________ - $__________ = $__________
Total Neto: +$__________

📊 R:R DESPUÉS DE FEES: 1:___
✅ ¿Cumple mínimo 1:3? [SÍ/NO]
```

---

## 📋 PASO 7 - VERIFICACIÓN FINAL

### ✅ CHECKLIST DE SEGURIDAD:

```
🔒 VERIFICACIONES CRÍTICAS:
[ ] Pérdida máxima < Daily restante
[ ] Pérdida máxima < Distancia DD  
[ ] R:R ≥ 1:3 después de fees
[ ] Confluencia suficiente (4+ factores)
[ ] Volumen confirma setup
[ ] Horario óptimo para operar
[ ] Mental estado OK
[ ] Screenshots completos recibidos
[ ] No contra tendencia 1D
[ ] Tamaño dentro de límites Breakout

🚦 DECISIÓN FINAL:
[ ] ✅ EJECUTAR TRADE
[ ] ⏸️ ESPERAR MEJOR OPORTUNIDAD  
[ ] ❌ NO OPERAR - DEMASIADO RIESGO
```

---

## 📊 ESCENARIOS DE RIESGO

### 📈 ANÁLISIS DE ESCENARIOS:

```
🎯 ESCENARIO 1 - TRADE GANADOR:
Si TP1: +$__________ neto
Si TP2: +$__________ neto
Si blended: +$__________ neto
Balance después: $__________
Daily restante después: $__________
Distancia DD después: $__________

📉 ESCENARIO 2 - TRADE PERDEDOR:
Pérdida máxima: -$__________
Balance después: $__________
Daily restante después: $__________
Distancia DD después: $__________
Zona después: [VERDE/AMARILLA/ROJA]

⚠️ ESCENARIO 3 - WORST CASE:
Si SL hit + gap adverso:
Pérdida estimada: -$__________
¿Causa breach? [SÍ/NO - CRÍTICO]
¿Suficiente espacio? [SÍ/NO]
```

---

## 📋 CALCULADORA RÁPIDA

### ⚡ CÁLCULO INSTANTÁNEO:

```
🔢 DATOS RÁPIDOS:
Balance: $__________
Zona: [V/A/R] → Riesgo: ___%
Riesgo permitido: $__________
Entrada: $__________
SL: $__________ (-___%)

💪 TAMAÑO RECOMENDADO:
__________ unidades ($__________)
Margen: $__________
R:R mínimo: 1:3

⚠️ ADVERTENCIA:
Si R:R < 1:3 → NO OPERAR
Si riesgo > daily restante → NO OPERAR
Si cerca DD → REDUCIR TAMAÑO
```

---

## 📊 HISTORIAL DE RIESGO

### 📈 REGISTRO DE POSICIONES:

```
📊 ÚLTIMAS 10 POSICIONES:

#1 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#2 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#3 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#4 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#5 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#6 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#7 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#8 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#9 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___
#10 [FECHA]: $__________ | [LONG/SHORT] | [GAN/PED] | $__________ | 1:___

📊 ESTADÍSTICAS DE RIESGO:
Tamaño promedio: $__________
Riesgo promedio: $__________
R:R promedio: 1:___
Tasa acierto: ___%
P&L acumulado: $__________
```

---

## 🎯 REGLAS DE ORO DE RIESGO

### ⚠️ PRINCIPIOS IRROMPIBLES:

```
🔒 REGLA #1 - PROTEGER CAPITAL:
NUNCA arriesgar > 1% del balance
NUNCA operar sin espacio suficiente
NUNCA ignorar límites Breakout

📊 REGLA #2 - R:R MÍNIMO:
SIEMPRE buscar R:R ≥ 1:3
INCLUIR fees en cálculo
PREFERIR setups con R:R ≥ 1:4

🎯 REGLA #3 - CONFLUENCIA:
MINIMO 4 factores en zona verde
MINIMO 6 factores en zona amarilla
MINIMO 9 factores en zona roja

⏰ REGLA #4 - TIMING:
Operar solo en horarios óptimos
Evitar dead zones
Respetar sesiones de alta liquidez

🧠 REGLA #5 - MENTAL:
NO operar en revenge
NO operar cansado o emocionado
SIEMPRE seguir el proceso
```

---

## 📊 PLANTILLAS DE CÁLCULO

### 📋 FÓRMULAS PREDEFINIDAS:

```
🔢 FÓRMULA 1 - TAMAÑO ESTÁNDAR:
Tamaño = (Balance × Riesgo%) / (Distancia% × Precio)

🔢 FÓRMULA 2 - AJUSTADA POR ZONA:
Si Verde: Tamaño × 1.0
Si Amarilla: Tamaño × 0.5  
Si Roja: Tamaño × 0.25

🔢 FÓRMULA 3 - CON FEES:
R:R Neto = (Ganancia - Fees) / (Pérdida + Fees)

🔢 FÓRMULA 4 - BREAKOUT:
Daily Restante = (Balance × 4/5/3%) - Pérdidas Hoy
Max DD = Balance - (6/5/3/8%)
Distancia DD = Balance - Max DD
```

---

## 🚀 ALERTAS DE RIESGO

### ⚠️ NOTIFICACIONES AUTOMÁTICAS:

```
🔴 ALERTA CRÍTICA:
Daily > 90% usado → STOP inmediato
Distancia DD < $200 → REDUCIR riesgo
3 pérdidas seguidas → STOP 24h

🟡 ALERTA PRECAUCIÓN:
Daily > 75% usado → Solo setups perfectos
Distancia DD < $500 → Reducir tamaño 50%
2 pérdidas seguidas → Esperar 2h

🟢 ESTADO ÓPTIMO:
Daily < 50% usado → Operar normal
Distancia DD > $1000 → Mantener estrategia
Racha ganadora → Mantener disciplina
```

---

## 📝 NOTAS FINALES

### 💡 CONSEJOS DE EXPERTO:

```
🎯 PACIENCIA > VELOCIDAD:
Es mejor esperar setup perfecto
Que forzar trade mediocre

📊 CONSISTENCIA > GANANCIAS:
Un trade bueno al día = $1500/mes
Disciplina = cuenta funded

🔒 SEGURIDAD > AMBICIÓN:
Proteger capital es prioridad #1
Cero breaches = éxito garantizado

📈 PROCESO > RESULTADO:
Seguir sistema = ganancias a largo plazo
Desviarse = pérdida segura
```

---

**📌 RECORDATORIO:** Esta calculadora es tu mejor amigo. Úsala SIEMPRE antes de operar. La precisión en los cálculos es la diferencia entre pasar evaluation y breach.

**🎯 MANTRA:** "Mejor perder oportunidad que perder cuenta"