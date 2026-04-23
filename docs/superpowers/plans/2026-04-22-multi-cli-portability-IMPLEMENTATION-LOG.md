# Multi-CLI Portability — Implementation Log

**Fecha:** 2026-04-22 (noche tardía)
**Branch:** `feature/multi-cli`
**Commits:** 14 (update at finalization)
**Tests:** 54 total (24 guardian + 19 mt5_bridge + 11 transform)
**Status:** Claude Code adapter validated, OpenCode adapter code-complete pending user install, Codex adapter UNTESTED.

## Entregables

### Canonical source
- `system/commands/` (23 archivos migrados)
- `system/agents/` (12 archivos migrados)
- `system/skills/` (14 skills migrados)
- `system/mcp/servers.json` (seed desde tradingview MCP actual)
- `system/hooks/` (placeholder)
- `system/README.md`

### Adapters
- `adapters/claude-code/install.sh` + README (symlinks, validated)
- `adapters/opencode/transform.py` + tests (11 passing)
- `adapters/opencode/install.sh` (+ git pre-commit hook)
- `adapters/opencode/watch.sh` (fswatch daemon)
- `adapters/opencode/README.md`
- `adapters/codex/*` (UNTESTED)

### Generated output
- `.claude/commands -> ../system/commands` (symlink)
- `.claude/agents -> ../system/agents` (symlink)
- `.claude/skills -> ../system/skills` (symlink)
- `.opencode/commands/` (23 translated)
- `.opencode/agents/` (12 translated)
- `.opencode/skills -> ../system/skills` (symlink)
- `.opencode/config.json` (con sección mcp.servers)
- `.git/hooks/pre-commit` (auto-regen on system/ changes)

## Validación pendiente

1. **OpenCode** — user instala `curl -fsSL https://opencode.ai/install | bash`, corre `opencode` en repo, prueba `/status`, reporta issues.
2. **Codex** — requiere OpenAI API key + `npm install -g @openai/codex`.

## Pasos para el usuario para validar OpenCode

1. `curl -fsSL https://opencode.ai/install | bash`
2. `cd ~/Documents/trading`
3. `opencode` (abre TUI)
4. Probar: `/status` → debe funcionar
5. Probar: despachar agent `morning-analyst-ftmo` → debería correr
6. Si algo falla: reportar output del error, iteramos transform.py

## Métricas

- Commits en branch: 14
- Tests nuevos: 11 (transform.py)
- Líneas de código nuevas: ~500 (transform.py ~300 + adapters ~200)
- Archivos migrados: 49 (23 commands + 12 agents + 14 skills)

## Riesgos conocidos

1. OpenCode format puede haber cambiado desde docs consultados (2026-04-22). Re-fetchar antes de validar.
2. Codex adapter: 100% especulativo sin test real.
3. Skills: OpenCode doc dice compatible, pero no se valida hasta que user corra `opencode` y lo pruebe.
