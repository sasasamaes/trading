#!/usr/bin/env python3
"""LSTM scaffold — NOT ACTIVE.

Este archivo contiene el esqueleto de un predictor LSTM para secuencias 15m.
Ver README.md para las precondiciones de activación.

Ejecutarlo directamente imprime un mensaje explicando por qué no corre.
"""
from __future__ import annotations

import sys


PRECONDITIONS = [
    ("capital_usd", 500, "Capital actual"),
    ("trades_executed", 100, "Trades ejecutados con sistema actual"),
    ("win_rate", 0.55, "Win rate del sistema actual"),
    ("supervised_auc_stable", 0.58, "XGBoost AUC estable 4+ semanas"),
    ("walk_forward_max_drop", 0.10, "Máximo deterioro entre folds walk-forward"),
    ("real_sharpe", 1.0, "Sharpe del sistema en real money"),
]


def _banner():
    print("═" * 60)
    print(" 🧠  DEEP LEARNING SUBSYSTEM — NOT ACTIVE")
    print("═" * 60)
    print()
    print("Este scaffold está intencionalmente apagado.")
    print("Ver deep/README.md para precondiciones de activación:")
    print()
    for k, v, desc in PRECONDITIONS:
        print(f"  [ ] {desc:<45} ≥ {v}")
    print()
    print("Cuando se cumplan TODAS, activar con: --force-activate")
    print("═" * 60)


# =========================================================================
# SCAFFOLD — código aquí NO se ejecuta por defecto, solo con --force-activate
# =========================================================================


def build_model(seq_len: int = 64, n_features: int = 12, hidden: int = 64):
    """Scaffold del LSTM bidireccional + attention."""
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise RuntimeError("torch no instalado. `pip install --user torch` primero.")

    class LSTMAttention(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=n_features,
                hidden_size=hidden,
                num_layers=2,
                dropout=0.2,
                bidirectional=True,
                batch_first=True,
            )
            self.attn_w = nn.Linear(hidden * 2, 1)
            self.head = nn.Sequential(
                nn.Linear(hidden * 2, 32),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(32, 2),
            )

        def forward(self, x):
            # x: (B, seq_len, n_features)
            out, _ = self.lstm(x)                      # (B, L, 2H)
            weights = torch.softmax(self.attn_w(out), dim=1)  # (B, L, 1)
            pooled = (out * weights).sum(dim=1)        # (B, 2H)
            return torch.sigmoid(self.head(pooled))    # (B, 2) = [P_long, P_short]

    return LSTMAttention()


def build_sequences(df, seq_len=64, feature_cols=None):
    """Construye tensores (B, seq_len, n_features) y targets.

    Scaffold — implementar cuando se active.
    """
    raise NotImplementedError("Scaffold — activar solo cuando se cumplan precondiciones.")


def train(args):
    """Loop de entrenamiento — scaffold."""
    raise NotImplementedError(
        "Training scaffold no implementado. "
        "Cuando se cumplan precondiciones, implementar con:\n"
        "  - AdamW + cosine annealing\n"
        "  - BCE ponderada por frecuencia de clase\n"
        "  - Early stopping sobre validation AUC\n"
        "  - Split temporal 70/15/15 (NUNCA random)\n"
    )


def main():
    if "--force-activate" not in sys.argv:
        _banner()
        sys.exit(0)

    print("⚠️  --force-activate recibido. Verificar precondiciones manualmente antes de continuar.")
    print("   Este scaffold NO tiene implementación de entrenamiento todavía.")
    print("   Implementar build_sequences() y train() con la arquitectura del README.")
    sys.exit(2)


if __name__ == "__main__":
    main()
