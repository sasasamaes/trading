---
name: Bug report
about: Reporta un problema para que lo podamos corregir
title: "[BUG] "
labels: bug
assignees: sasasamaes
---

## Descripción del bug

<!-- Breve y concreto. ¿Qué pasa que no debería? -->

## Pasos para reproducir

1. En profile `<retail|ftmo>`
2. Corriendo comando `/...`
3. Con estado `<describir>`
4. Observo `<output no esperado>`

## Comportamiento esperado

<!-- ¿Qué debería haber pasado? -->

## Output real (pega logs/errores completos)

```
<pega aquí>
```

## Entorno

- **OS:** macOS / Linux / Windows (versión)
- **CLI:** Claude Code / OpenCode / Codex (versión)
- **Python:** `python3 --version`
- **Profile activo:** retail / ftmo
- **EA activo (si FTMO):** sí / no / N/A
- **Commit / branch:** `git rev-parse HEAD`

## Tests

- [ ] Corrí `python3 -m pytest .claude/scripts/ adapters/opencode/ -v` y pasan/fallan: **[cuál]**
- [ ] Corrí `bash .claude/scripts/test_integration.sh` y pasa/falla: **[cuál]**

## Contexto adicional

<!-- Screenshots, theory, links relacionados, etc. -->
