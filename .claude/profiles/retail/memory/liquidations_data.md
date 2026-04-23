---
name: Liquidations data sources
description: Fuentes y workflow para incorporar liquidaciones (forced orders / OI drops) al análisis diario
type: reference
originSessionId: 736207e7-88e4-4e2f-9d58-09d6fdb006f2
---
**Por qué importan las liquidaciones:**
Las liquidaciones son combustible para el siguiente movimiento. Wicks con $100M+ liquidados = blow-off; acumulación de liq levels arriba/abajo del spot = imán de precio (liquidity pools). Retail suele estar largo a 10-20x → liq cluster debajo del spot = soporte falso que se come y rebota.

**Fuentes de datos (testeadas 2026-04-21, orden de preferencia):**

1. **Binance Futures Data API — PÚBLICA SIN KEY** ✅ FUENTE PRIMARIA
   - **OI history hourly:**
     `https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=24`
     Response: `sumOpenInterest` (BTC) y `sumOpenInterestValue` (USD). Caídas súbitas de OI = liq event.
   - **Long/Short ratio global (retail):**
     `https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=24`
   - **Top traders L/S ratio (smart money cuentas grandes):**
     `https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=24`
   - **Top traders L/S position ratio (peso de posición, no cuentas):**
     `https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=BTCUSDT&period=1h&limit=24`
   - **Taker buy/sell volume:**
     `https://fapi.binance.com/futures/data/takerlongshortRatio?symbol=BTCUSDT&period=1h&limit=24`

2. **Coinglass (requiere API key free)** — útil para cross-exchange agregado
   - Sign up: https://www.coinglass.com/pricing — free tier
   - Header: `coinglassSecret: <key>`
   - Endpoint: `https://open-api-v3.coinglass.com/api/futures/liquidation/v2/history?symbol=BTC&interval=h1`
   - UI heatmap: https://www.coinglass.com/LiquidationData

3. **Binance forced orders WebSocket** (real-time, requiere proceso colector)
   - WS: `wss://fstream.binance.com/ws/btcusdt@forceOrder`

4. **BingX (exchange del usuario)**
   - Verificar doc: `https://bingx-api.github.io/docs/` (API liquidaciones puede estar en endpoints v2)

**Métricas clave para cada sesión:**

| Métrica | Fuente | Lectura |
|---|---|---|
| OI 24h change (USD) | Binance openInterestHist | >+3% acumulación / <-3% distribución / drop súbito >$100M en 1h = liq event |
| Biggest OI drop 1h (últimas 24h) | Binance openInterestHist | -$50M normal / -$100M+ liq event / -$300M+ cascada |
| Long/Short ratio global (retail) | Binance globalLongShortAccountRatio | <0.8 shorts crowded (bullish setup) / >1.5 longs crowded (bearish setup) |
| Top trader L/S (smart money) | Binance topLongShortAccountRatio | Divergencia vs retail = señal (smart money opuesto a retail = edge) |
| Top trader L/S position ratio | Binance topLongShortPositionRatio | Más preciso — refleja tamaño real de posiciones grandes |
| Total liq 24h BTC (USD) | Coinglass (key requerida) | <$50M silencioso / $50-200M normal / >$500M evento grande |

**Cómo usar en el análisis matutino (nueva FASE):**

Insertar entre FASE 2 (contexto global) y FASE 3 (correlaciones):

> **FASE 2.5 — Liquidaciones últimas 24h**
> - Total liq USD (long + short)
> - Ratio L/S
> - Evento reciente (última hora): sí/no
> - Liq cluster arriba del spot (resistencia magnética)
> - Liq cluster debajo del spot (soporte magnético / trampa)

**Reglas prácticas:**

- Si liq 24h >$500M → día volátil, reducir size o NO operar
- Si short liquidations dominan (>70%) + F&G bajo → posible techo (cover rally agotado)
- Si long liquidations dominan (>70%) + F&G alto → posible piso (retail sacudido)
- Liq cluster a ~1-2% del spot = precio tiende a visitarlo (stop hunt)

**Limitaciones:**

- Coinglass free tier: rate limit bajo, historial limitado
- Free APIs retrasan 1-5 min (no real-time para scalping 15m)
- Binance WS es real-time pero requiere script colector local corriendo
- Datos de un solo exchange pueden subestimar si altcoins o contratos USDC también están liquidando

**Workflow acordado 2026-04-21 — Coinglass free tier NO sirve por API:**

- Probado: la API key free (`CG-API-KEY`) devuelve 401 "Upgrade plan" en TODOS los endpoints útiles (liquidation/history, OI history, funding, L/S, etc.). Requiere plan Hobbyist+ ($29/mo). No vale la pena con capital $11-100.
- **Workflow adoptado:** el usuario manda screenshot del **header superior de coinglass.com** que siempre muestra los 4 datos clave en barra horizontal:
  1. Volumen 24h total crypto (+ %change)
  2. Interés Abierto total (+ %change)
  3. **Liquidación 24h** (+ %change) ← el número clave
  4. Ratio Largo/Corto 24h
- Con esos 4 números + Binance Futures Data API (OI y L/S por par via API pública) tengo suficiente para FASE 2.5 del morning protocol.
- Para el heatmap visual (imanes de precio arriba/abajo del spot), usuario reporta clusters desde `/BitcoinLiquidationHeatMap`.

**Workflow visual / programático:**

- **Usuario visual (navegador):** Coinglass liq map es SPA JS, no scrapeable via WebFetch. Usuario abre una de las URLs y reporta 3 datos:
  1. Cluster de liquidaciones **arriba** del spot (precio + magnitud relativa)
  2. Cluster **debajo** del spot (precio + magnitud relativa)
  3. ¿Arriba o abajo es más grande? (el más grande es el imán de precio)
- URLs útiles:
  - https://www.coinglass.com/pro/futures/LiquidationMap (Pro, requiere suscripción)
  - https://www.coinglass.com/LiquidationData (Free, totales 24h)
  - https://www.coinglass.com/BitcoinLiquidationHeatMap (Free, heatmap visual por leverage)
- **Claude programático:** Binance Futures Data API (OI + L/S ratio) en FASE 2.5 del morning protocol. Coinglass v3 API con key free opcional si se quiere agregar más cross-exchange.
- **Cruce en el análisis:** imanes visuales (coinglass) + OI/L-S programático (binance) = mapa completo de posicionamiento.

**TradingView (Plan Basic, 2 indicador max):**

- **No hay indicador nativo de liquidaciones reales** en TV
- El MCP NO puede añadir "Open Interest" ni indicadores comunitarios automáticamente (probado 2026-04-21). Solo built-ins fijos (Volume, RSI, MACD, BB, EMA, etc.).
- **Workflow elegido:** Volume en TV (ya añadido) + liquidaciones/OI/L-S via Binance API en cada análisis matutino. Coinglass heatmap en ventana separada del navegador para visualizar liq clusters.
- Si el usuario quiere añadir OI o un script de liquidaciones manualmente desde la UI de TV: buscar "Open Interest" en indicadores (es data series, hay que seleccionar símbolo fuente como `BINANCE:BTCUSDTPERP_OI`).
