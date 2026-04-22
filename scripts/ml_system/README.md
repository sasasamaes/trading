# ML System — Trading Intelligence Layer

Tres subsistemas que complementan (no reemplazan) las reglas mecánicas del sistema actual:

| Subsistema | Estado | Valor esperado | Costo |
|---|---|---|---|
| **Sentiment (NLP)** | Production | Filtra días extremos F&G/news/social | $0, ~1s por query |
| **Supervised (XGBoost)** | Production | Score 0-100 de probabilidad TP-first sobre setup 4/4 | $0, ~2 min entreno, ~50ms predict |
| **Deep Learning (LSTM)** | Scaffold only | Posible mejora marginal a escala. **NO ACTIVO.** | Decenas de horas; requiere n≥100 trades + capital >$500 |

## Filosofía

Estos componentes son **asistentes de decisión**, no reemplazos del sistema de 4 filtros. Si el setup técnico es NO-GO, ningún score ML convierte eso en GO. Su uso es:

1. **Sentiment** → pesa al iniciar la sesión (FASE 0 del morning protocol). F&G <20 o >80 = sesgo contrarian.
2. **ML Score** → 5° filtro opcional. Con setup 4/4 técnico, si ML predict <40 → reducir size 50% o esperar siguiente setup.
3. **DL** → no disponible hasta cumplir precondiciones (ver `deep/README.md`).

## Setup (primera vez)

```bash
cd scripts/ml_system
./setup.sh
```

Instala: `requests`, `feedparser`, `vaderSentiment`, `pandas`, `numpy`, `xgboost`, `scikit-learn`.

## Uso rápido

```bash
# Sentiment (instantáneo)
python3 scripts/ml_system/sentiment/aggregator.py

# ML: entrenar (primera vez, descarga ~100MB de Binance)
python3 scripts/ml_system/supervised/train.py

# ML: predecir sobre setup actual
python3 scripts/ml_system/supervised/predict.py --rsi 32 --bb-pos -0.95 --donchian-dist 0.001 --vol-z 1.2 --hour 9 --funding -0.01
```

## Integración con Claude

Tres nuevos agentes + slash commands:
- `/sentiment` → agente `sentiment-analyst`
- `/ml` → agente `ml-analyst` (predict sobre estado actual)
- `/ml-train` → re-entrenamiento

## Disclaimer

- Ningún modelo ML garantiza predicciones correctas en futuros. Backtest ≠ forward.
- El score ML se calibra sobre data histórica; en regímenes nuevos su precisión cae.
- Con capital <$100 y n<20 trades, la varianza de resultados supera la señal ML. Úsalo como un voto más, no como oráculo.
