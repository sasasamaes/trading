# Deep Learning — Scaffold (NO ACTIVO)

## Estado

**Este subsistema está intencionalmente NO-ACTIVO.** Hay código scaffold (`lstm_scaffold.py`) pero no se entrena ni se usa por defecto.

## Por qué está apagado

1. **Capital actual ($12) no justifica el costo de entrenamiento.** Un LSTM requiere:
   - PyTorch/TensorFlow instalado (~500MB)
   - GPU recomendada (Mac M-series tiene Metal backend pero limitado)
   - Horas a días de entrenamiento + validación
   - Framework de hyperparameter search

2. **Literatura académica: LSTMs sobre crypto price tienen Sharpe similar o peor a reglas simples.** Ver:
   - Sezer et al. (2020), *Financial time series forecasting with deep learning: A systematic literature review*
   - Chen et al. (2023), *Are Deep Learning models better for crypto forecasting?* — conclusión: no significativamente

3. **El XGBoost supervisado ya cubre el 90% del valor** de un LSTM para scoring de setups, con 100x menos costo y 10x más interpretabilidad (feature importance).

4. **Con n=2 trades ejecutados, el cuello de botella es disciplina**, no sofisticación de modelo.

## Precondiciones para ACTIVAR

Este scaffold se puede activar cuando TODAS estas condiciones se cumplan:

- [ ] Capital ≥ $500 (el gasto de compute no es trivial para $12)
- [ ] n ≥ 100 trades ejecutados con el sistema actual (ground truth real)
- [ ] WR > 55% con el sistema actual (el edge técnico ya existe, no inventarlo con ML)
- [ ] XGBoost supervisado tiene AUC > 0.58 estable por 4+ semanas
- [ ] Walk-forward validation del XGBoost no degrada >10% entre folds
- [ ] Sharpe ratio del sistema actual > 1.0 en real money

Si NO se cumplen todas, entrenar un LSTM es **cargo culting** — agregar complejidad sin evidencia de que aporta valor.

## Qué haría el LSTM cuando se active

Arquitectura propuesta (scaffold en `lstm_scaffold.py`):

```
Input: secuencia de 64 velas 15m × 12 features (mismas del supervisado)
  ↓
LSTM(hidden=64, layers=2, dropout=0.2, bidirectional=True)
  ↓
Attention pooling
  ↓
Dense(32) + ReLU + Dropout(0.3)
  ↓
Dense(2) + Sigmoid → [P(TP_first_long), P(TP_first_short)]
```

Entrenamiento:
- Dataset: 3+ años de BTC 15m (Binance)
- Split: 70% train, 15% validation, 15% test (temporal, NO aleatorio)
- Optimizer: AdamW con cosine annealing
- Loss: BCE ponderada por frecuencia de clase
- Early stopping sobre validation AUC
- Regularización: weight decay + label smoothing

## Cómo activar en el futuro

```bash
# Cuando precondiciones se cumplan:
pip install --user torch
python3 scripts/ml_system/deep/lstm_scaffold.py --train --days 1095
```

Y añadir `/dl` command + agente `dl-analyst` análogo a `ml-analyst`.

## Filosofía

> "No agregues complejidad al sistema hasta que el sistema simple demuestre que la necesita."
>
> — Jim Simons nunca arrancó con redes neuronales. Ni tú.
