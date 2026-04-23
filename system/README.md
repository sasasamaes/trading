# system/ — Canonical source of truth

Este directorio es la fuente única de comandos, agentes, skills, y MCP config usados por el sistema de trading.

## Regla de oro

**Edita SOLO aquí.** Nunca modifiques archivos en `.claude/commands`, `.opencode/commands`, etc. Esos se generan o symlinkean desde `system/`.

## Flujo de sync

| Target | Mecanismo | Cuándo |
|---|---|---|
| Claude Code | Symlinks | Automático — ve cambios inmediato |
| OpenCode | `transform.py` | Git pre-commit hook auto-regenera |
| Codex | `transform.py` | Manual (UNTESTED adapter) |

## Instalar adapters (primera vez)

```bash
bash adapters/claude-code/install.sh
bash adapters/opencode/install.sh
# adapters/codex/install.sh  (cuando tengas OpenAI API key)
```

## Estructura

| Directorio | Contenido | Format canónico |
|---|---|---|
| `commands/` | 23 slash command prompts | Claude Code (`allowed-tools`, `$ARGUMENTS`) |
| `agents/` | 12 subagent definitions | Claude Code (`tools: A, B`) |
| `skills/` | 14 skill dirs | Compatible ambos CLIs (same `name`, `description`) |
| `mcp/servers.json` | MCP server configs | Neutral JSON (translated per CLI) |
| `hooks/` | Shared hooks (vacío por ahora) | Bash |

## Agregar command/agent/skill nuevo

1. Crea archivo en `system/<tipo>/nombre.md` con formato Claude Code
2. Commit — git pre-commit hook regenera `.opencode/` automáticamente
3. Claude Code lo ve inmediato (symlink)

## Troubleshooting

- `.claude/commands` no es symlink: re-run `bash adapters/claude-code/install.sh`
- `.opencode/commands` stale: commit tus cambios o corre `bash adapters/opencode/watch.sh`
- MCP no carga: verifica `system/mcp/servers.json` paths son absolutos
