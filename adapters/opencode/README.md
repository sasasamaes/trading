# OpenCode adapter (v2 — soporte total)

Genera `.opencode/` + `opencode.json` raíz desde `system/` con translation del formato Claude Code al OpenCode.

## Primera vez

```bash
bash adapters/opencode/install.sh
```

Hace:
1. Genera `.opencode/commands/`, `.opencode/agents/`, `.opencode/config.json` (legacy)
2. Sincroniza `mcp` block en `opencode.json` raíz (preserva model/permissions/instructions del usuario)
3. Symlinks `.opencode/skills → ../system/skills/` (formato compatible, zero translation)
4. Instala git pre-commit hook v2 (auto-sync futuro)
5. Auto-upgrade v1 → v2 si detecta hook legacy

## Auto-sync via git hook

Cada commit que toca `system/commands/`, `system/agents/`, o `system/mcp/` auto-regenera `.opencode/` y lo agrega al mismo commit.

## Real-time sync (opcional, durante dev)

```bash
brew install fswatch
bash adapters/opencode/watch.sh
```

Corre un daemon que regenera `.opencode/` cada vez que modificas `system/`. Útil mientras editas + pruebas en OpenCode en otra terminal.

## Translations aplicadas

### Commands
- `allowed-tools:` removido (OC no lo usa — tools manejadas por agent)
- `argument-hint:` movido al body como `<!-- args: ... -->`
- `description:` preservado
- Body idéntico ($ARGUMENTS, $1, etc. funcionan igual)

### Agents
- `tools: A, B, C` → `permission: {A: allow, B: allow, C: allow}`
- Agrega `mode: subagent` default (todos los agents de este proyecto son subagents)
- `description:` preservado
- `name:` preservado (OC usa filename, pero no daña)
- Body idéntico

### Skills
- Symlink `.opencode/skills → ../system/skills/`
- Zero translation (OpenCode docs confirm mismo frontmatter `name, description`)

### MCP (doble destino)
- `system/mcp/servers.json` → merged en `.opencode/config.json` bajo key `mcp.servers` (legacy back-compat)
- También sincronizado en `opencode.json` raíz bajo key `mcp` (formato OC primary, sin nested `servers`)
- En el raíz preserva `model`, `default_agent`, `instructions`, `permission`, `watcher`, `compaction` si existen
- Filtra `$comment` y otras claves no-server

### Root `opencode.json` (OC primary config)
- Si no existe → scaffold con defaults (model sonnet-4-5, instructions=[CLAUDE.md, AGENTS.md], permission ask, watcher.ignore común)
- Si existe → solo `mcp` se reescribe; user overrides (model, default_agent, etc.) intactos

## Tests

```bash
python3 -m pytest adapters/opencode/test_transform.py -v
```

15 tests cubren commands, agents, MCP legacy, MCP root sync (scaffold/preserve/comment-filter/missing-source), edge cases.

## Troubleshooting

- `.opencode/` stale después de edit: `bash adapters/opencode/install.sh` re-genera
- Git hook no triggerea: verifica `ls .git/hooks/pre-commit` existe y tiene marker `opencode-adapter-v1`
- PyYAML not found: `pip3 install pyyaml`
- fswatch not found: `brew install fswatch`
