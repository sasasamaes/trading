## Descripción

<!-- ¿Qué cambia? En 2-3 oraciones -->

## Tipo de cambio

- [ ] Bug fix (non-breaking, fixes an issue)
- [ ] Nueva feature (non-breaking, adds functionality)
- [ ] Breaking change (fix o feature que cambia comportamiento existente)
- [ ] Docs update
- [ ] Refactor (sin cambios de comportamiento)
- [ ] Test coverage
- [ ] Chore (deps, gitignore, CI, etc.)

## Cómo se probó

<!-- Comandos exactos que corriste + output relevante -->

```bash
# ejemplo
python3 -m pytest adapters/opencode/ -v
# 11 passed
```

## Issue relacionado

<!-- Closes #123, Refs #456, etc. -->

## Checklist

- [ ] Corrí `python3 -m pytest .claude/scripts/ adapters/opencode/ -v` y pasa (`54 passed`)
- [ ] Corrí `bash .claude/scripts/test_integration.sh` y pasa
- [ ] Si agregué código Python, agregué tests
- [ ] Si modifiqué `system/`, verifiqué que `.opencode/` se regenera correctamente (pre-commit hook)
- [ ] Si modifiqué `ClaudeBridge.mq5`, documenté cómo lo probé contra MT5
- [ ] Si es cambio de estrategia, incluí backtest evidencia (≥20 trades)
- [ ] Actualicé README/docs si aplica
- [ ] No committeé credenciales, paths hardcoded, capital personal

## Screenshots / evidencia

<!-- Si el cambio es visual (statusline, output de comando) o de backtest, pega evidencia -->
