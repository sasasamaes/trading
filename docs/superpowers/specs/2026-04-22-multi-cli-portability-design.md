# Multi-CLI Portability — Design Spec

**Fecha:** 2026-04-22 (noche, 21:45 MX)
**Branch:** `feature/multi-cli` (worktree `.worktrees/multi-cli`)
**Context:** Después del merge del MT5 bridge, el usuario quiere hedge arquitectónico para poder usar OpenCode (o Codex eventualmente) como alternativa a Claude Code.

## Decisiones de scope aprobadas

| # | Decisión | Elegido |
|---|---|---|
| 1 | Motivación | **Hedge medio plazo** (B) — estructura portable ahora, no uso activo |
| 2 | Esfuerzo | **Phase 1+2 + adapter OpenCode validado + Codex blind** (degenerated B) |
| 3 | Stack | OpenAI API no disponible → solo OpenCode se valida en vivo |
| 4 | Canonical format | **Claude Code format** (primario, menos migración) |
| 5 | Skills | **Portables** — OpenCode docs confirmed same frontmatter schema |
| 6 | Auto-sync | **Git pre-commit hook + fswatch opcional** |
| 7 | `.opencode/` in git | **Commited** (facilita clone + CI) |
| 8 | MCP portable | **Incluido** — TradingView MCP config portable entre CLIs |
| 9 | Scripts/profiles | **No mover** (ya portables, referenciados por path) |

## Approach: Config System con transform adapters

```
system/             → canonical source (Claude Code format)
  ├── commands/     → 23 *.md files
  ├── agents/       → 12 *.md files
  ├── skills/       → skill dirs (format compatible con ambos CLIs)
  ├── mcp/          → servers.json (neutral schema, adapters translate)
  ├── hooks/        → reservado para futuro
  └── README.md

adapters/
  ├── claude-code/install.sh      → symlinks (zero transform)
  ├── opencode/
  │   ├── install.sh              → first-time setup + git hook install
  │   ├── transform.py            → CC → OC frontmatter translation
  │   └── watch.sh                → fswatch daemon (opcional)
  └── codex/
      ├── install.sh              → ⚠️ UNTESTED
      └── transform.py
```

## Sección 1 — Estructura + migración

### Estructura final

```
trading/
├── system/
│   ├── commands/ (23 files)
│   ├── agents/ (12 files)
│   ├── skills/ (copiados del ubicación actual)
│   ├── hooks/ (vacío)
│   └── README.md
│
├── adapters/
│   ├── claude-code/install.sh
│   ├── opencode/{install.sh, transform.py, watch.sh, test_transform.py}
│   └── codex/{install.sh, transform.py, README.md UNTESTED}
│
├── .claude/
│   ├── commands/ -> ../system/commands/   (symlink)
│   ├── agents/   -> ../system/agents/     (symlink)
│   ├── skills/   -> ../system/skills/     (symlink SI skills no son plugins)
│   ├── scripts/, profiles/, settings.json, .env (stay)
│
├── .opencode/                              (committed)
│   ├── commands/ (translated files, NOT symlinked)
│   ├── agents/   (translated files, NOT symlinked)
│   └── skills/ -> ../system/skills/       (symlink, formato idéntico)
│
└── .git/hooks/pre-commit                   (installed by OC adapter)
```

### Migración (Phase 1)

1. `git mv .claude/commands system/commands`
2. `ln -s ../system/commands .claude/commands`
3. `git mv .claude/agents system/agents`
4. `ln -s ../system/agents .claude/agents`
5. Decidir skills:
   - Si `.claude/skills/` existe con contenido de project → `git mv` + symlink
   - Si skills son plugins externos (`~/.claude/plugins/`) → no aplica, nada que mover
6. Verify Claude Code sigue funcionando sin cambios (regression test: `/status` sale igual)

### Canonical format

**Commands:** Claude Code format
```markdown
---
description: ...
allowed-tools: Bash, Read, ...  (opcional)
argument-hint: ...              (opcional)
---

Pasos: ...
$ARGUMENTS
```

**Agents:** Claude Code format
```markdown
---
name: my-agent
description: ...
tools: Bash, Read, mcp__...
---

Body prompt...
```

**Skills:** directorio `<name>/SKILL.md` con frontmatter `name, description`. Compatible nativo ambos CLIs.

## Sección 2 — Adapters

### 2.1 Claude Code adapter (`adapters/claude-code/install.sh`)

Idempotente:
- Si `.claude/commands` es dir real (no symlink): `mv` a `system/commands`, crea symlink
- Si symlink ya existe: no-op
- Mismo para agents y skills

**Zero translation.** Costo: cero.

### 2.2 OpenCode adapter

**`transform.py`** — convierte Claude Code → OpenCode format:

```python
# Commands translation
def translate_command(src, dst):
    # Remove `allowed-tools` (OC no lo usa)
    # Preserve `description`
    # Move `argument-hint` a comentario en body si presente
    # Body unchanged ($ARGUMENTS works same)

# Agents translation
def translate_agent(src, dst):
    # `tools: A, B, C` → `permission: {A: allow, B: allow, C: allow}`
    # Add `mode: subagent` default
    # Preserve `description`
    # Body unchanged

# Skills: symlink .opencode/skills -> ../system/skills
```

**Tests (pytest, TDD):**
- test_translate_command_removes_allowed_tools
- test_translate_command_preserves_description
- test_translate_command_argument_hint_to_comment
- test_translate_command_preserves_body_with_arguments
- test_translate_agent_tools_to_permission
- test_translate_agent_adds_mode_subagent
- test_translate_agent_preserves_body
- test_translate_skip_files_without_frontmatter

**`install.sh`** — primera generación + install git hook:
- Run transform.py
- Install `.git/hooks/pre-commit` (idempotent: detect if already installed)

**`watch.sh`** — fswatch daemon opcional:
- Requiere `brew install fswatch`
- Watch `system/commands` + `system/agents`
- On change: run transform.py

### 2.3 Codex adapter (UNTESTED)

Similar structure a OpenCode. Basado en docs actuales de Codex CLI de OpenAI. README.md con warning `⚠️ UNTESTED — may be broken until validated against live Codex install`.

Cuando el usuario obtenga OpenAI API key y lo pruebe: ~30 min para validar + fixes.

## Sección 3 — Auto-sync (pre-commit hook + watch)

### Pre-commit hook

Instalado por `adapters/opencode/install.sh`:
```bash
#!/usr/bin/env bash
REPO="$(git rev-parse --show-toplevel)"
CHANGED=$(git diff --cached --name-only | grep -E '^system/(commands|agents|skills)/' || true)
if [ -n "$CHANGED" ]; then
  python3 "$REPO/adapters/opencode/transform.py" || exit 1
  git add "$REPO/.opencode"
fi
```

**Comportamiento garantizado:**
- Cualquier commit tocando system/* regenera .opencode/ y lo stagea en el mismo commit
- Repo history siempre sincronizado
- `.opencode/` committed evita re-generation al clonar

### Watch daemon (opcional)

Para dev activo sin commit:
```bash
bash adapters/opencode/watch.sh
# fswatch -o system/ | xargs -n1 -I{} python3 transform.py
```

Requiere `brew install fswatch`. No instalado por default.

### Idempotencia

- `adapters/claude-code/install.sh`: detecta symlinks existentes, no-op
- `adapters/opencode/install.sh`: detecta hook existente, no reinstala
- `transform.py`: sobreescribe `.opencode/` cada run (idempotent por construcción)

## Sección 4 — Hooks, MCP, README

### Hooks: no se mueven

Scripts bash en `.claude/scripts/` son portables en contenido pero referenciados por path desde `.claude/settings.json`. Si el usuario configura hooks en OpenCode después, referenciará los mismos scripts.

**`system/hooks/` queda vacío** como placeholder para futuro shared hooks si surgen.

### MCP: portable (incluido)

**Canonical:** `system/mcp/servers.json` — schema neutral:
```json
{
  "servers": {
    "tradingview": {
      "command": "node",
      "args": ["/absolute/path/to/tradingview-mcp/server.js"],
      "env": {
        "TV_DEBUG_PORT": "9222"
      }
    }
  }
}
```

**Adapters:**
- `adapters/claude-code/install.sh` — genera `.claude/mcp.json` en formato Claude Code (similar/idéntico al canonical)
- `adapters/opencode/transform.py` — agrega sección `mcp.servers` dentro de `.opencode/config.json` (merge, no overwrite, preserva otros settings)
- `adapters/codex/transform.py` — genera sección equivalente (UNTESTED con docs actuales)

**Auto-sync:** pre-commit hook detecta cambios en `system/mcp/` y re-genera targets de cada CLI.

**Seed inicial:** script de migración lee la config actual de MCP de Claude Code (si existe) y la copia a `system/mcp/servers.json`. Si no existe (MCP manejado por plugin externo), deja un placeholder con comentario.

### `system/README.md`

Documento explicativo:
- "Edit only here"
- Flujo de sync (automático + manual)
- Cómo agregar nuevo command/agent/skill
- Troubleshooting

## Effort total tonight

| Fase | Tiempo | Entregable |
|---|---|---|
| 1. Migración | 20 min | git mv + symlinks + regression test |
| 2. Claude adapter | 15 min | install.sh idempotent |
| 3. OpenCode transform.py + tests | 45 min | TDD, 8 tests |
| 4. OpenCode install.sh + git hook | 20 min | script + hook install |
| 5. OpenCode watch.sh | 10 min | fswatch wrapper |
| 6. MCP portable + adapters | 45 min | seed servers.json desde config actual + translators |
| 7. Codex adapter (blind) | 30 min | transform.py + UNTESTED README |
| 8. system/README + adapter READMEs | 15 min | docs |
| 9. Validación OpenCode (tu install) | 30 min | user instala OC, corre /morning |

**Total: ~3.5h tonight.** Validación requiere tu participación activa en paso 9.

## Tests + verificación

**Unit tests:**
- `adapters/opencode/test_transform.py` — 8+ tests pytest

**Integration tests:**
- Post-migración: `/status` en Claude Code sale IDÉNTICO al estado pre-migración (regression)
- `adapters/claude-code/install.sh` idempotente: ejecutar 2x no rompe nada
- `adapters/opencode/install.sh` idempotente: ejecutar 2x no duplica hook

**Validation (user-driven, paso 8):**
- User ejecuta `curl -fsSL https://opencode.ai/install | bash`
- User ejecuta `cd trading; opencode` (o command equivalente)
- User corre `/status` → debe funcionar (o mostrar error útil)
- User reporta → iteramos adapter si hay issues

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Symlinks rompen en Windows | Usuario está en macOS, N/A |
| Claude Code no resuelve symlinks | Test inmediato post-migración |
| OpenCode format cambia antes de validar | Hoy validamos; si cambia después, 15 min fix del adapter |
| Git hook se borra al re-init | install.sh idempotent lo reinstala |
| User edita `.opencode/` directamente por error | README warning + comentario en archivos generados: "AUTO-GENERATED — edit system/ instead" |
| Codex adapter queda roto indefinidamente | README UNTESTED visible, user sabe que requiere validación |

## Skills: ubicación final

**Acción pendiente en Phase 1:** verificar dónde viven los skills del proyecto:

1. Si en `.claude/skills/<name>/SKILL.md` (project-local) → mover a `system/skills/`
2. Si son plugins externos (`~/.claude/plugins/...`) → no son portables por adapter, usuario instala plugins en OpenCode aparte
3. Si mezcla → portar los project-local, documentar que los plugin-based son per-CLI

## Próximo paso

Invocar `writing-plans` skill para traducir este spec a un plan de implementación ejecutable.
