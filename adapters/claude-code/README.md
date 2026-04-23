# Claude Code adapter

Mantiene symlinks `.claude/{commands,agents,skills}/ → system/{commands,agents,skills}/`.

## Uso

```bash
bash adapters/claude-code/install.sh
```

Idempotente — safe correr múltiples veces.

## Qué hace

1. Verifica cada symlink (commands, agents, skills)
2. Si falta, lo crea apuntando a `../system/<dir>`
3. Si existe y apunta al lugar correcto, no-op
4. Si `.claude/<dir>` es un directorio real (no symlink), lo mueve a `.backup` y crea symlink

## MCP sync

Claude Code almacena MCP config globalmente (no en `.claude/` del proyecto). El adapter no toca MCP. Si quieres sincronizar `system/mcp/servers.json` → Claude Code MCP, corre manualmente:

```bash
claude mcp remove tradingview
claude mcp add-json tradingview "$(cat system/mcp/servers.json | jq '.servers.tradingview')"
```

## Troubleshooting

- "does not exist": correr migration (Task 2 del plan)
- Permission denied: `chmod +x adapters/claude-code/install.sh`
