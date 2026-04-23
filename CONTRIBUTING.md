# Contributing

¡Gracias por tu interés! Este es un proyecto **personal de trading** mantenido por [Francisco Campos Diaz (@sasasamaes)](https://github.com/sasasamaes). PRs son bienvenidos pero con ciertas reglas — lee antes de proponer.

## Tipo de contribuciones que busco

### ✅ Bienvenidas

- **Fixes de bugs** en scripts (`guardian.py`, `mt5_bridge.py`, `statusline.sh`, etc.)
- **Mejoras al EA MQL5** (`ClaudeBridge.mq5`) — especialmente cross-platform compatibility
- **Nuevos adapters multi-CLI** (ej: Cursor, Windsurf) siguiendo el patrón en `adapters/opencode/`
- **Documentación clarificada** en README, CLAUDE.md, guías de setup
- **Tests adicionales** para código Python (`pytest`)
- **Nuevas skills analíticas** si aportan valor generalizable (no solo tu setup personal)
- **Traducciones** a inglés / portugués de las guías principales

### ⚠️ Requieren discusión previa (abre un issue primero)

- Cambios a la estrategia Mean Reversion o FTMO-Conservative (requieren evidencia de backtest)
- Cambios a reglas del guardian (3% daily, 10% trailing, Best Day Rule) — están ligadas a reglas reales de FTMO
- Refactors grandes de estructura (`system/`, `adapters/`)
- Nuevos profiles (ej: adicional a retail/ftmo)

### ❌ No aceptados

- Copies de estrategias propietarias sin atribución/evidencia
- Cambios que remuevan filtros/disclaimers de risk management
- Features que automaticen ejecución sin intervención humana (anti-filosofía del sistema)
- Código para operar sin MCP/EA reproducible (vendor lock-in)

## Antes de abrir un PR

1. **Fork + branch**:
   ```bash
   git checkout -b feature/mi-mejora
   ```

2. **Tests deben pasar:**
   ```bash
   python3 -m pytest .claude/scripts/ adapters/opencode/ -v
   bash .claude/scripts/test_integration.sh
   ```

3. **Follow el formato de commits** existente en el repo:
   - `feat:` nueva feature
   - `fix:` bug fix
   - `refactor:` cambios de estructura sin nuevas features
   - `docs:` cambios en documentación
   - `test:` tests añadidos/modificados
   - `chore:` mantenimiento (deps, gitignore, etc.)

4. **Si tocas el EA (`ClaudeBridge.mq5`)**, documenta en el PR:
   - Cómo lo probaste (MT5 version, OS, cuenta demo usada)
   - Si agregaste nuevos command types, actualiza el schema en `docs/superpowers/specs/`

5. **Si agregaste una nueva estrategia o filtro**, incluye:
   - Backtest ≥20 trades con evidencia (output CSV + métricas)
   - Comparación vs la estrategia actual
   - Criterios de invalidación explícitos

## Setup dev

Requisitos:
- Python 3.9+ con `pytest` y `pyyaml`
- Bash
- (Opcional) `fswatch` para watch de OpenCode adapter
- (Opcional) MT5 Desktop para Mac si vas a tocar el EA

```bash
git clone https://github.com/sasasamaes/trading.git
cd trading
bash adapters/claude-code/install.sh  # primera vez
python3 -m pytest .claude/scripts/ adapters/opencode/ -v  # debe pasar
```

## Reglas duras

- **Nunca commitees credenciales.** `.claude/.env` está gitignored. Si accidentalmente lo commiteas, pide ayuda inmediata para history rewrite.
- **Nunca hardcodes capital real, loginos FTMO, emails, API keys.** Usa `<placeholders>` o variables de entorno.
- **Nunca removas disclaimers** ("not financial advice") — son parte integral del código ético del proyecto.
- **Nunca agregues lógica que opere sin input humano** sobre dinero real. El sistema es asistido, no autónomo.

## Communication

- **Issues**: bugs, propuestas, preguntas técnicas
- **Discussions** (si se habilita): estrategia, trading philosophy, architecture decisions
- **PRs**: cambios de código concretos

Mantenedor: [@sasasamaes](https://github.com/sasasamaes). Respuesta típica: 1-7 días según carga personal.

## Code of Conduct (corto)

- Sé directo, sin ofensas personales.
- No spam de "gracias por tu repo" — valores tu tiempo y el mío.
- No pedir consejo financiero en issues — el proyecto es educativo.
- Crítica del código es bienvenida; crítica del trader no.
- En dudas sobre scope: pregunta antes de invertir tiempo.

## Licencia de contribuciones

Al contribuir, aceptas que tu código se licencia bajo la [MIT License](LICENSE) del proyecto.

---

**Gracias** — cada PR que valide mi sistema o agregue algo útil para otros traders retail hace el proyecto mejor.
