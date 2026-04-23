# Session Notes — Fotmarkets

Notas operativas libres: spread anómalos, MT5 quirks, bonus T&C aclarados, aprendizajes.

## Bonus T&C (PENDIENTE VERIFICAR POR USUARIO)

Antes del primer trade, leer y documentar aquí:
- [ ] Volumen mínimo requerido para retirar profits del bonus
- [ ] Profit cap máximo del bonus (ej. $500)
- [ ] Ventana temporal (30/60/90 días)
- [ ] Requisitos KYC para retiro

## MT5 quirks

**PENDIENTE VERIFICAR antes del primer trade:**
- [ ] **Pip value XAUUSD** con 0.01 lote (gold pip varía por broker: ¿$0.01, $0.10 o $1.00 por pip?). Abrir MT5 → Market Watch → right-click en XAUUSD → Specification → validar `Contract size` y `Tick size`.
- [ ] **Pip value BTCUSD CFD** con 0.01 lote (típicamente 1 pip = $0.01 USD por 0.01 lot, pero algunos brokers usan convención de "1 pip = $1.00").
- [ ] **Pip value ETHUSD CFD** idem.
- [ ] **Pip value NAS100 / SPX500** — CFDs de índices tienen convención "point" distinta de "pip". Validar en Specification.

Sin estos valores confirmados, el cálculo de sizing en `/risk` para assets no-Forex estará incorrecto. `config.md` asume convenciones estándar; si tu broker usa otras, actualizar `min_sl_pips` y hardcoded pip values en `/risk`.

(resto vacío — rellenar durante operación)

## Spread observations

(vacío — documentar si ves spread anormal en algún par/hora)

## Bonus T&C confirmados

(vacío hasta leer T&C del broker)
