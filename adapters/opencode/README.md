# OpenCode adapter

Genera `.opencode/` desde `system/` con translation del formato Claude Code al OpenCode.

## Primera vez

```bash
bash adapters/opencode/install.sh
```

Hace:
1. Genera `.opencode/commands/`, `.opencode/agents/`, `.opencode/config.json`
2. Symlinks `.opencode/skills → ../system/skills/` (formato compatible, zero translation)
3. Instala git pre-commit hook para auto-sync futuro

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

### MCP
- `system/mcp/servers.json` → merged en `.opencode/config.json` bajo key `mcp.servers`
- Preserva otros settings en config.json si existen

## Tests

```bash
python3 -m pytest adapters/opencode/test_transform.py -v
```

11 tests cubren commands, agents, MCP, edge cases.

## Troubleshooting

- `.opencode/` stale después de edit: `bash adapters/opencode/install.sh` re-genera
- Git hook no triggerea: verifica `ls .git/hooks/pre-commit` existe y tiene marker `opencode-adapter-v1`
- PyYAML not found: `pip3 install pyyaml`
- fswatch not found: `brew install fswatch`
