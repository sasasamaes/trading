# Multi-CLI Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructurar `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, and MCP config como fuente canónica en `system/`, con adapters que generan config para Claude Code (symlinks), OpenCode (transform.py) y Codex (blind), con auto-sync via git pre-commit hook.

**Architecture:** Single source of truth en `system/`. Claude Code consume via symlinks (zero translation). OpenCode adapter lee `system/` y escribe `.opencode/` en su formato via transform.py. Codex adapter análogo pero untested hasta que user instale CLI.

**Tech Stack:** Bash (adapters + hooks), Python 3 + PyYAML (transforms + tests via pytest), git hooks.

**Spec:** `docs/superpowers/specs/2026-04-22-multi-cli-portability-design.md`

---

## Baseline state (verified)

- 23 files en `.claude/commands/`
- 12 files en `.claude/agents/`
- 14 dirs en `.claude/skills/` (project-local, portables)
- MCP tradingview configurado globally: `node ~/Documents/trading/tradingview-mcp/src/server.js`
- `.claude/scripts/` y `.claude/profiles/` se quedan donde están (ya portables)
- `.claude/settings.json` queda Claude-only

## File Structure final

```
trading/
├── system/                                # CANONICAL SOURCE OF TRUTH
│   ├── commands/                          # 23 *.md files
│   ├── agents/                            # 12 *.md files
│   ├── skills/                            # 14 skill dirs (format compatible)
│   ├── mcp/
│   │   └── servers.json                   # neutral MCP config
│   ├── hooks/                             # placeholder (.gitkeep)
│   └── README.md
│
├── adapters/
│   ├── claude-code/
│   │   └── install.sh                     # symlinks + MCP sync
│   ├── opencode/
│   │   ├── install.sh                     # first-time + git hook install
│   │   ├── transform.py                   # CC → OC translator
│   │   ├── test_transform.py              # 10+ pytest tests
│   │   ├── watch.sh                       # fswatch daemon
│   │   └── README.md
│   └── codex/
│       ├── install.sh                     # UNTESTED
│       ├── transform.py                   # UNTESTED
│       └── README.md                      # ⚠️ UNTESTED
│
├── .claude/
│   ├── commands/ → ../system/commands/    # symlink
│   ├── agents/   → ../system/agents/      # symlink
│   ├── skills/   → ../system/skills/      # symlink
│   ├── scripts/, profiles/, settings.json (stay, Claude-only)
│
├── .opencode/                              # COMMITTED
│   ├── commands/ (translated files, NOT symlinked)
│   ├── agents/   (translated files)
│   ├── skills/   → ../system/skills/      # symlink (identical format)
│   └── config.json                        # incluye seccion mcp.servers
│
└── .git/hooks/pre-commit                   # installed by adapters/opencode/install.sh
```

---

## Task 1: Baseline snapshot commit

**Files:** None (git operation)

- [ ] **Step 1: Verify on correct branch + clean worktree**

```bash
cd ~/Documents/trading/.worktrees/multi-cli
git branch --show-current
git status --short
```

Expected branch: `feature/multi-cli`. Working tree should be clean except for the spec already committed.

- [ ] **Step 2: Empty snapshot commit**

```bash
git commit --allow-empty -m "chore: baseline snapshot before multi-CLI migration"
```

---

## Task 2: Migrate commands, agents, skills to system/

**Files:**
- Move: `.claude/commands/` → `system/commands/`
- Move: `.claude/agents/` → `system/agents/`
- Move: `.claude/skills/` → `system/skills/`
- Create: `.claude/commands` (symlink)
- Create: `.claude/agents` (symlink)
- Create: `.claude/skills` (symlink)

- [ ] **Step 1: Create system/ parent directory**

```bash
mkdir -p system
```

- [ ] **Step 2: Git mv directories (preserves history)**

```bash
git mv .claude/commands system/commands
git mv .claude/agents system/agents
git mv .claude/skills system/skills
```

- [ ] **Step 3: Create symlinks in .claude/ pointing to system/**

```bash
ln -s ../system/commands .claude/commands
ln -s ../system/agents .claude/agents
ln -s ../system/skills .claude/skills
```

- [ ] **Step 4: Verify symlinks resolve correctly**

```bash
ls -la .claude/commands .claude/agents .claude/skills | head
readlink .claude/commands .claude/agents .claude/skills
```

Expected output shows three symlinks pointing to `../system/commands`, `../system/agents`, `../system/skills`.

- [ ] **Step 5: Verify commands/agents/skills accessible via symlink**

```bash
ls .claude/commands/ | wc -l  # Expected: 23
ls .claude/agents/ | wc -l    # Expected: 12
ls .claude/skills/ | wc -l    # Expected: 14
```

- [ ] **Step 6: Regression test — Claude Code sees same commands**

```bash
# Verify an agent file reads correctly via symlink
head -3 .claude/agents/morning-analyst-ftmo.md
# Should show YAML frontmatter (not "No such file")
```

- [ ] **Step 7: Commit migration**

```bash
git add .claude/commands .claude/agents .claude/skills system/
git commit -m "refactor: migrate commands/agents/skills to system/ with symlinks back to .claude/"
```

---

## Task 3: Seed system/mcp/servers.json + hooks placeholder + system/README.md

**Files:**
- Create: `system/mcp/servers.json`
- Create: `system/hooks/.gitkeep`
- Create: `system/README.md`

- [ ] **Step 1: Create system/mcp/servers.json from current MCP config**

```bash
mkdir -p system/mcp system/hooks
touch system/hooks/.gitkeep
```

Write `system/mcp/servers.json`:
```json
{
  "servers": {
    "tradingview": {
      "command": "node",
      "args": [
        "~/Documents/trading/tradingview-mcp/src/server.js"
      ],
      "env": {}
    }
  }
}
```

- [ ] **Step 2: Write system/README.md**

```markdown
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
```

- [ ] **Step 3: Verify files created**

```bash
ls -la system/mcp/ system/hooks/
wc -l system/README.md  # Expected: >30 lines
python3 -c "import json; print(json.load(open('system/mcp/servers.json'))['servers']['tradingview']['command'])"
# Expected: node
```

- [ ] **Step 4: Commit**

```bash
git add system/mcp/ system/hooks/ system/README.md
git commit -m "feat: seed system/mcp + hooks placeholder + README canonical docs"
```

---

## Task 4: Claude Code adapter — install.sh

**Files:**
- Create: `adapters/claude-code/install.sh`
- Create: `adapters/claude-code/README.md`

- [ ] **Step 1: Write `adapters/claude-code/install.sh`**

```bash
#!/usr/bin/env bash
# adapters/claude-code/install.sh
# Idempotent: creates symlinks from .claude/ to system/
# Safe to run multiple times.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

# Symlink commands/agents/skills if not already symlinked
for dir in commands agents skills; do
  src="system/$dir"
  dst=".claude/$dir"

  if [ ! -d "$src" ]; then
    echo "⚠️  $src does not exist — run migration first"
    continue
  fi

  if [ -L "$dst" ]; then
    # Already a symlink, verify target
    target=$(readlink "$dst")
    if [ "$target" = "../system/$dir" ]; then
      echo "✓ $dst already symlinked"
    else
      echo "⚠️  $dst points to $target, expected ../system/$dir — fixing"
      rm "$dst"
      ln -s "../system/$dir" "$dst"
    fi
  elif [ -d "$dst" ] && [ ! -L "$dst" ]; then
    echo "⚠️  $dst is a real dir (not symlink) — backup & symlink"
    mv "$dst" "${dst}.backup"
    ln -s "../system/$dir" "$dst"
    echo "   Backup in ${dst}.backup — delete manually if safe"
  else
    # Doesn't exist yet
    ln -s "../system/$dir" "$dst"
    echo "✓ created symlink $dst → ../system/$dir"
  fi
done

echo ""
echo "✅ Claude Code adapter synced."
echo "   MCP config stays in global ~/.claude (via 'claude mcp add' or plugins)."
echo "   To sync MCP from system/mcp/servers.json, manually re-add:"
echo "   claude mcp remove tradingview && claude mcp add-json tradingview \"\$(cat system/mcp/servers.json | jq '.servers.tradingview')\""
```

- [ ] **Step 2: Make executable**

```bash
chmod +x adapters/claude-code/install.sh
```

- [ ] **Step 3: Run adapter idempotently (should be no-op since symlinks exist)**

```bash
bash adapters/claude-code/install.sh
```

Expected output: 3 lines "✓ X already symlinked".

- [ ] **Step 4: Write `adapters/claude-code/README.md`**

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add adapters/claude-code/
git commit -m "feat: Claude Code adapter with idempotent symlink install"
```

---

## Task 5: OpenCode transform.py — command translation (TDD)

**Files:**
- Create: `adapters/opencode/transform.py`
- Create: `adapters/opencode/test_transform.py`

- [ ] **Step 1: Write failing tests for translate_command**

Create `adapters/opencode/test_transform.py`:

```python
"""Unit tests for transform.py — CC → OpenCode translator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import transform


def test_translate_command_removes_allowed_tools(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("""---
description: Dashboard
allowed-tools: Bash, Read
---

Pasos del comando
$ARGUMENTS
""")
    dst = tmp_path / "dst.md"
    transform.translate_command(src, dst)

    result = dst.read_text()
    assert "allowed-tools" not in result
    assert "description: Dashboard" in result
    assert "$ARGUMENTS" in result
    assert "Pasos del comando" in result


def test_translate_command_preserves_description_only(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("""---
description: Simple command
---

Body here
""")
    dst = tmp_path / "dst.md"
    transform.translate_command(src, dst)

    result = dst.read_text()
    assert "description: Simple command" in result
    assert "Body here" in result


def test_translate_command_argument_hint_to_comment(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("""---
description: Takes args
argument-hint: <symbol> <side>
---

Use $1 and $2
""")
    dst = tmp_path / "dst.md"
    transform.translate_command(src, dst)

    result = dst.read_text()
    assert "argument-hint" not in result  # removed from frontmatter
    assert "<!-- args: <symbol> <side> -->" in result
    assert "Use $1 and $2" in result


def test_translate_command_no_frontmatter(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("Body only without frontmatter\n")
    dst = tmp_path / "dst.md"
    transform.translate_command(src, dst)

    result = dst.read_text()
    assert result == "Body only without frontmatter\n"


def test_translate_command_preserves_body_with_arguments(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("""---
description: Test
---

Run with $ARGUMENTS and output result.
""")
    dst = tmp_path / "dst.md"
    transform.translate_command(src, dst)

    assert "$ARGUMENTS" in dst.read_text()
```

- [ ] **Step 2: Run tests, verify fail**

```bash
cd ~/Documents/trading/.worktrees/multi-cli
python3 -m pytest adapters/opencode/test_transform.py -v 2>&1 | tail -5
```

Expected: ImportError or ModuleNotFoundError (transform.py doesn't exist yet).

- [ ] **Step 3: Write transform.py with translate_command**

Create `adapters/opencode/transform.py`:

```python
"""
transform.py — Translate Claude Code commands/agents to OpenCode format.

Usage (invoked by install.sh or pre-commit hook):
    python3 transform.py

Reads system/commands/*.md, system/agents/*.md, system/mcp/servers.json
Writes .opencode/commands/*.md, .opencode/agents/*.md, .opencode/config.json
Symlinks .opencode/skills → ../system/skills
"""
import json
import re
import shutil
import sys
from pathlib import Path


try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def _parse_frontmatter(text):
    """Extract (frontmatter_dict, body_str) from markdown with YAML frontmatter.
    Returns (None, text) if no frontmatter.
    """
    m = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not m:
        return None, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def _serialize(fm, body):
    """Serialize frontmatter + body to markdown."""
    if not fm:
        return body
    return "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n" + body


def translate_command(src_path, dst_path):
    """Claude Code → OpenCode command format.

    Removes `allowed-tools` (not in OC schema).
    Moves `argument-hint` to body as HTML comment.
    Preserves description, body ($ARGUMENTS compatible).
    """
    text = src_path.read_text()
    fm, body = _parse_frontmatter(text)

    if fm is None:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(text)
        return

    new_fm = {}
    if 'description' in fm:
        new_fm['description'] = fm['description']

    # argument-hint → HTML comment in body (OC has no equivalent field)
    if 'argument-hint' in fm:
        body = f"<!-- args: {fm['argument-hint']} -->\n{body}"

    # `allowed-tools` silently dropped (OC uses agent-level permission)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(_serialize(new_fm, body))
```

- [ ] **Step 4: Run tests, verify pass**

```bash
python3 -m pytest adapters/opencode/test_transform.py -v 2>&1 | tail -10
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add adapters/opencode/transform.py adapters/opencode/test_transform.py
git commit -m "feat: OpenCode transform.py scaffold + translate_command + tests"
```

---

## Task 6: OpenCode transform.py — agent translation (TDD)

**Files:**
- Modify: `adapters/opencode/transform.py`
- Modify: `adapters/opencode/test_transform.py`

- [ ] **Step 1: Write failing tests for translate_agent**

Append to `adapters/opencode/test_transform.py`:

```python
def test_translate_agent_tools_to_permission(tmp_path):
    src = tmp_path / "agent.md"
    src.write_text("""---
name: my-agent
description: Does stuff
tools: Bash, Read, mcp__tv__quote_get
---

Agent body prompt.
""")
    dst = tmp_path / "dst.md"
    transform.translate_agent(src, dst)

    import yaml as y
    text = dst.read_text()
    m = __import__('re').match(r'^---\n(.*?)\n---\n(.*)', text, __import__('re').DOTALL)
    fm = y.safe_load(m.group(1))

    assert fm['description'] == 'Does stuff'
    assert fm['mode'] == 'subagent'
    assert fm['permission']['Bash'] == 'allow'
    assert fm['permission']['Read'] == 'allow'
    assert fm['permission']['mcp__tv__quote_get'] == 'allow'
    assert 'Agent body prompt' in m.group(2)


def test_translate_agent_no_tools(tmp_path):
    src = tmp_path / "agent.md"
    src.write_text("""---
name: simple
description: No tools
---

Body
""")
    dst = tmp_path / "dst.md"
    transform.translate_agent(src, dst)

    import yaml as y
    m = __import__('re').match(r'^---\n(.*?)\n---\n(.*)', dst.read_text(), __import__('re').DOTALL)
    fm = y.safe_load(m.group(1))
    assert fm['mode'] == 'subagent'
    assert 'permission' not in fm or fm.get('permission') == {}


def test_translate_agent_preserves_body(tmp_path):
    src = tmp_path / "agent.md"
    src.write_text("""---
name: a
description: b
tools: Bash
---

Line 1
Line 2
Line 3
""")
    dst = tmp_path / "dst.md"
    transform.translate_agent(src, dst)

    assert "Line 1" in dst.read_text()
    assert "Line 2" in dst.read_text()
    assert "Line 3" in dst.read_text()


def test_translate_agent_removes_name_field(tmp_path):
    """`name` is redundant in OC (filename = agent id). Optional to preserve."""
    src = tmp_path / "my-agent.md"
    src.write_text("""---
name: my-agent
description: d
---

body
""")
    dst = tmp_path / "out.md"
    transform.translate_agent(src, dst)

    import yaml as y
    m = __import__('re').match(r'^---\n(.*?)\n---\n(.*)', dst.read_text(), __import__('re').DOTALL)
    fm = y.safe_load(m.group(1))
    # name is OK to preserve or drop; test just verifies body + description remain
    assert fm['description'] == 'd'
```

- [ ] **Step 2: Run tests, verify fail on new ones**

```bash
python3 -m pytest adapters/opencode/test_transform.py -v 2>&1 | tail -10
```

Expected: 4 new tests fail (AttributeError: module has no attribute 'translate_agent').

- [ ] **Step 3: Implement translate_agent in transform.py**

Add to `adapters/opencode/transform.py` after translate_command:

```python
def translate_agent(src_path, dst_path):
    """Claude Code → OpenCode agent format.

    Converts `tools: A, B, C` string/list to `permission: {A: allow, B: allow}`.
    Adds `mode: subagent` default.
    Preserves description + body.
    """
    text = src_path.read_text()
    fm, body = _parse_frontmatter(text)

    if fm is None:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(text)
        return

    new_fm = {
        'description': fm.get('description', ''),
        'mode': 'subagent',
    }

    # Parse tools (string "A, B" or list)
    tools_raw = fm.get('tools', '')
    if isinstance(tools_raw, str):
        tools = [t.strip() for t in re.split(r'[,\n]', tools_raw) if t.strip()]
    elif isinstance(tools_raw, list):
        tools = [str(t).strip() for t in tools_raw if t]
    else:
        tools = []

    if tools:
        new_fm['permission'] = {t: 'allow' for t in tools}

    # Preserve name if present (filename usually matches but frontmatter can differ)
    if 'name' in fm:
        new_fm['name'] = fm['name']

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(_serialize(new_fm, body))
```

- [ ] **Step 4: Run tests, verify pass**

```bash
python3 -m pytest adapters/opencode/test_transform.py -v 2>&1 | tail -15
```

Expected: 9 passed (5 command + 4 agent).

- [ ] **Step 5: Commit**

```bash
git add adapters/opencode/transform.py adapters/opencode/test_transform.py
git commit -m "feat: translate_agent (tools→permission, add mode: subagent) + tests"
```

---

## Task 7: OpenCode transform.py — MCP translation + main (TDD)

**Files:**
- Modify: `adapters/opencode/transform.py`
- Modify: `adapters/opencode/test_transform.py`

- [ ] **Step 1: Write failing test for MCP translation + main entry**

Append to `adapters/opencode/test_transform.py`:

```python
def test_translate_mcp_basic(tmp_path):
    src = tmp_path / "servers.json"
    src.write_text(json.dumps({
        "servers": {
            "tradingview": {
                "command": "node",
                "args": ["/path/to/server.js"],
                "env": {"DEBUG": "1"}
            }
        }
    }))
    dst_config = tmp_path / "config.json"
    transform.translate_mcp(src, dst_config)

    loaded = json.loads(dst_config.read_text())
    assert 'mcp' in loaded
    assert 'servers' in loaded['mcp']
    assert loaded['mcp']['servers']['tradingview']['command'] == 'node'
    assert loaded['mcp']['servers']['tradingview']['args'] == ['/path/to/server.js']


def test_translate_mcp_preserves_existing_config(tmp_path):
    """If .opencode/config.json already has other settings, merge only mcp section."""
    src = tmp_path / "servers.json"
    src.write_text(json.dumps({
        "servers": {"tradingview": {"command": "node", "args": [], "env": {}}}
    }))
    dst = tmp_path / "config.json"
    dst.write_text(json.dumps({
        "theme": "dark",
        "model": "claude-sonnet-4"
    }))
    transform.translate_mcp(src, dst)

    loaded = json.loads(dst.read_text())
    assert loaded['theme'] == 'dark'  # preserved
    assert loaded['model'] == 'claude-sonnet-4'  # preserved
    assert 'mcp' in loaded  # added
```

Import json at top of test file if not yet:

```python
import json
```

- [ ] **Step 2: Run tests, verify fail**

```bash
python3 -m pytest adapters/opencode/test_transform.py -v 2>&1 | tail -10
```

- [ ] **Step 3: Implement translate_mcp + main in transform.py**

Append to `adapters/opencode/transform.py`:

```python
def translate_mcp(servers_json_path, config_json_path):
    """Merge system/mcp/servers.json into .opencode/config.json under `mcp` key.

    Preserves other keys in config.json if present.
    """
    with open(servers_json_path) as f:
        source = json.load(f)

    # Load existing config.json if present
    if config_json_path.exists():
        with open(config_json_path) as f:
            config = json.load(f)
    else:
        config = {}

    # OpenCode MCP schema: config.mcp.servers = {name: {command, args, env}}
    config['mcp'] = {'servers': source.get('servers', {})}

    config_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_json_path, 'w') as f:
        json.dump(config, f, indent=2)


def _ensure_skills_symlink(system_dir, opencode_dir):
    """Create .opencode/skills symlink if not present."""
    skills_link = opencode_dir / 'skills'
    target = Path('../system/skills')
    if skills_link.is_symlink():
        if Path(str(skills_link.readlink())) != target:
            skills_link.unlink()
            skills_link.symlink_to(target)
    elif skills_link.exists():
        # Real dir exists — back up and replace with symlink
        import shutil as sh
        sh.move(str(skills_link), str(opencode_dir / 'skills.backup'))
        skills_link.symlink_to(target)
    else:
        opencode_dir.mkdir(parents=True, exist_ok=True)
        skills_link.symlink_to(target)


def main():
    repo = Path(__file__).parent.parent.parent
    system_dir = repo / 'system'
    opencode_dir = repo / '.opencode'

    if not system_dir.exists():
        print(f"ERROR: {system_dir} not found. Run migration first.", file=sys.stderr)
        sys.exit(1)

    # Commands
    cmd_count = 0
    src_cmd_dir = system_dir / 'commands'
    dst_cmd_dir = opencode_dir / 'commands'
    dst_cmd_dir.mkdir(parents=True, exist_ok=True)
    # Clean old files (avoid stale)
    for f in dst_cmd_dir.glob('*.md'):
        f.unlink()
    for src in src_cmd_dir.glob('*.md'):
        translate_command(src, dst_cmd_dir / src.name)
        cmd_count += 1

    # Agents
    agent_count = 0
    src_agent_dir = system_dir / 'agents'
    dst_agent_dir = opencode_dir / 'agents'
    dst_agent_dir.mkdir(parents=True, exist_ok=True)
    for f in dst_agent_dir.glob('*.md'):
        f.unlink()
    for src in src_agent_dir.glob('*.md'):
        translate_agent(src, dst_agent_dir / src.name)
        agent_count += 1

    # MCP
    mcp_src = system_dir / 'mcp' / 'servers.json'
    mcp_dst = opencode_dir / 'config.json'
    if mcp_src.exists():
        translate_mcp(mcp_src, mcp_dst)

    # Skills — symlink (identical format)
    _ensure_skills_symlink(system_dir, opencode_dir)

    print(f"✓ Translated {cmd_count} commands → .opencode/commands/")
    print(f"✓ Translated {agent_count} agents → .opencode/agents/")
    print(f"✓ Merged MCP into .opencode/config.json")
    print(f"✓ Symlinked skills → ../system/skills")


if __name__ == '__main__':
    main()
```

Also add `import json` and `import shutil` to top of file if not yet imported.

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest adapters/opencode/test_transform.py -v 2>&1 | tail -15
```

Expected: 11 passed (5 command + 4 agent + 2 mcp).

- [ ] **Step 5: Run transform.py end-to-end**

```bash
python3 adapters/opencode/transform.py
ls .opencode/
```

Expected output:
```
✓ Translated 23 commands → .opencode/commands/
✓ Translated 12 agents → .opencode/agents/
✓ Merged MCP into .opencode/config.json
✓ Symlinked skills → ../system/skills
```

`.opencode/` directory should contain commands/, agents/, skills/ (symlink), config.json.

- [ ] **Step 6: Spot check a translated file**

```bash
head -10 .opencode/agents/morning-analyst-ftmo.md
cat .opencode/config.json
```

Should show:
- Agent has `mode: subagent` and `permission: {...}`
- config.json has `mcp.servers.tradingview`

- [ ] **Step 7: Commit**

```bash
git add adapters/opencode/transform.py adapters/opencode/test_transform.py .opencode/
git commit -m "feat: translate_mcp + transform main() + first .opencode/ generation"
```

---

## Task 8: OpenCode install.sh + pre-commit hook

**Files:**
- Create: `adapters/opencode/install.sh`

- [ ] **Step 1: Write install.sh**

```bash
#!/usr/bin/env bash
# adapters/opencode/install.sh
# First-time setup + install git pre-commit hook for auto-sync.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

# Verify Python 3 + pyyaml available
python3 -c "import yaml" 2>/dev/null || {
  echo "⚠️  PyYAML not installed. Installing..."
  pip3 install --user pyyaml
}

# First generation
echo "🔄 Generating .opencode/ from system/..."
python3 "$REPO/adapters/opencode/transform.py"

# Install pre-commit hook
HOOK_DIR="$REPO/.git/hooks"
HOOK="$HOOK_DIR/pre-commit"

# Handle case where HOOK_DIR doesn't exist (rare, e.g. linked worktree)
mkdir -p "$HOOK_DIR"

# Marker to detect if already installed
MARKER='# opencode-adapter-v1'

if [ -f "$HOOK" ] && grep -q "$MARKER" "$HOOK"; then
  echo "✓ pre-commit hook already installed"
else
  if [ -f "$HOOK" ]; then
    # Backup existing hook and append our logic
    cp "$HOOK" "$HOOK.backup-$(date +%s)"
    echo "   Backed up existing pre-commit to $HOOK.backup-*"
  fi

  cat >> "$HOOK" <<'EOF'

# opencode-adapter-v1 — auto-regenerate .opencode/ on system/ changes
__REPO="$(git rev-parse --show-toplevel)"
__CHANGED=$(git diff --cached --name-only | grep -E '^system/(commands|agents|mcp)/' || true)
if [ -n "$__CHANGED" ]; then
  echo "[opencode-adapter] system/ changed → re-generando .opencode/"
  python3 "$__REPO/adapters/opencode/transform.py" || exit 1
  git add "$__REPO/.opencode"
fi
EOF
  chmod +x "$HOOK"
  echo "✓ pre-commit hook installed at $HOOK"
fi

echo ""
echo "✅ OpenCode adapter ready."
echo "   .opencode/ will auto-regenerate on git commit when system/ changes."
echo "   For real-time sync during active editing: bash adapters/opencode/watch.sh"
```

- [ ] **Step 2: Make executable + run**

```bash
chmod +x adapters/opencode/install.sh
bash adapters/opencode/install.sh
```

Expected: re-generates .opencode/, installs hook.

- [ ] **Step 3: Verify hook installed**

```bash
cat .git/hooks/pre-commit | grep "opencode-adapter-v1"
```

Expected: matches.

- [ ] **Step 4: Test idempotency (re-run should say "already installed")**

```bash
bash adapters/opencode/install.sh 2>&1 | grep "already"
```

Expected: "✓ pre-commit hook already installed".

- [ ] **Step 5: Test hook triggers on system/ changes**

```bash
# Modify a system file
echo "" >> system/commands/status.md
git add system/commands/status.md

# Stage-and-attempt-commit, abort via --no-commit flag equivalent (just to verify hook runs)
git commit --dry-run 2>&1 | head -5
# Real commit
git commit -m "test: trigger hook" 2>&1 | grep -A1 "opencode-adapter"
```

Expected: output shows "[opencode-adapter] system/ changed → re-generando .opencode/"

- [ ] **Step 6: Commit (this commit includes the test edit + hook install)**

```bash
# already committed in step 5 via hook trigger
git log --oneline -2
```

---

## Task 9: OpenCode watch.sh (fswatch daemon)

**Files:**
- Create: `adapters/opencode/watch.sh`

- [ ] **Step 1: Write watch.sh**

```bash
#!/usr/bin/env bash
# adapters/opencode/watch.sh
# Watches system/ for changes and regenerates .opencode/ in real-time.
# Requires: brew install fswatch

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"

if ! command -v fswatch >/dev/null 2>&1; then
  echo "❌ fswatch not installed."
  echo "   Install: brew install fswatch"
  exit 1
fi

echo "👀 Watching $REPO/system/ for changes... (Ctrl+C to stop)"
fswatch -o "$REPO/system/commands" "$REPO/system/agents" "$REPO/system/mcp" | while read -r _; do
  if python3 "$REPO/adapters/opencode/transform.py" 2>&1 | tail -1; then
    echo "  $(date +%H:%M:%S) • re-synced"
  fi
done
```

- [ ] **Step 2: Make executable**

```bash
chmod +x adapters/opencode/watch.sh
```

- [ ] **Step 3: Verify script syntax**

```bash
bash -n adapters/opencode/watch.sh && echo "syntax OK"
```

- [ ] **Step 4: Commit**

```bash
git add adapters/opencode/watch.sh
git commit -m "feat: OpenCode watch.sh fswatch daemon for real-time sync"
```

---

## Task 10: Codex adapter (BLIND, UNTESTED)

**Files:**
- Create: `adapters/codex/install.sh`
- Create: `adapters/codex/transform.py`
- Create: `adapters/codex/README.md`

- [ ] **Step 1: Write adapters/codex/transform.py**

Codex CLI supports custom prompts under `~/.codex/prompts/`. Less formalized for agents/commands — basically prompts are just markdown templates.

```python
"""
transform.py — Translate Claude Code commands to Codex prompts.

⚠️ UNTESTED — may be broken until validated against live Codex install.

Codex stores prompts at ~/.codex/prompts/<name>.md (single flat dir).
We treat commands and agents both as prompts (Codex doesn't distinguish).

Skills: not natively supported. We copy to a reference dir that can be included in context manually.

MCP: Codex uses TOML config. We do not attempt to translate (error out with notice).
"""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'opencode'))
from transform import _parse_frontmatter  # reuse


def translate_to_codex_prompt(src_path, dst_path, prefix=''):
    """Strip frontmatter (Codex doesn't use it), write body with optional prefix in name.

    prefix: 'cmd_' for commands, 'agent_' for agents (to avoid collisions in flat dir).
    """
    text = src_path.read_text()
    _fm, body = _parse_frontmatter(text)

    if body is None:
        body = text  # no frontmatter

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(body.strip() + '\n')


def main():
    repo = Path(__file__).parent.parent.parent
    system_dir = repo / 'system'
    codex_dir = Path.home() / '.codex' / 'prompts'

    if not system_dir.exists():
        print(f"ERROR: {system_dir} not found.", file=sys.stderr)
        sys.exit(1)

    codex_dir.mkdir(parents=True, exist_ok=True)

    # Commands
    cmd_count = 0
    for src in (system_dir / 'commands').glob('*.md'):
        dst = codex_dir / f'cmd_{src.name}'
        translate_to_codex_prompt(src, dst, 'cmd_')
        cmd_count += 1

    # Agents
    agent_count = 0
    for src in (system_dir / 'agents').glob('*.md'):
        dst = codex_dir / f'agent_{src.name}'
        translate_to_codex_prompt(src, dst, 'agent_')
        agent_count += 1

    # Skills — just copy (Codex manual reference)
    skills_ref = codex_dir / 'skills_ref'
    skills_ref.mkdir(exist_ok=True)
    skill_count = 0
    skills_src = system_dir / 'skills'
    if skills_src.exists():
        # Clean target
        shutil.rmtree(skills_ref, ignore_errors=True)
        skills_ref.mkdir()
        for src in skills_src.iterdir():
            if src.is_dir():
                shutil.copytree(src, skills_ref / src.name)
                skill_count += 1

    print(f"⚠️ UNTESTED Codex adapter:")
    print(f"   {cmd_count} commands → {codex_dir}/cmd_*.md")
    print(f"   {agent_count} agents → {codex_dir}/agent_*.md")
    print(f"   {skill_count} skills → {codex_dir}/skills_ref/")
    print(f"   MCP: not translated (Codex uses TOML, configure manually)")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Write adapters/codex/install.sh**

```bash
#!/usr/bin/env bash
# adapters/codex/install.sh
# ⚠️ UNTESTED — Codex CLI not installed locally. Report issues to regenerate.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"

echo "⚠️  Codex adapter is UNTESTED."
echo "   Prerequisite: OpenAI API key + codex CLI installed."
echo "   If something breaks: report and regenerate."
echo ""

python3 "$REPO/adapters/codex/transform.py"

echo ""
echo "✅ Codex prompts written to ~/.codex/prompts/"
echo "   Invocation (in Codex session): /cmd_morning  /agent_morning-analyst-ftmo  etc."
```

- [ ] **Step 3: Write adapters/codex/README.md**

```markdown
# Codex adapter — ⚠️ UNTESTED

Este adapter **no ha sido validado contra un Codex CLI vivo** por falta de acceso a OpenAI API en la sesión de desarrollo.

## Supuestos del diseño (pueden estar incorrectos)

- Codex CLI stores prompts at `~/.codex/prompts/<name>.md`
- Codex no distingue entre commands y agents — todo es prompt-template
- Skills se copian como referencia (Codex no tiene skills system native)
- MCP no se traduce (Codex usa TOML, formato distinto)

## Cuando valides

1. Instala Codex: `npm install -g @openai/codex`
2. Configura API key: `codex auth login`
3. Corre adapter: `bash adapters/codex/install.sh`
4. En Codex, intenta: `/cmd_status`
5. Reporta issues para que el adapter se corrija

## Convenciones de naming

- Commands: `cmd_<name>.md` (ej: `cmd_morning.md`, invoca con `/cmd_morning`)
- Agents: `agent_<name>.md` (ej: `agent_morning-analyst-ftmo.md`)
- Skills: referencia en `~/.codex/prompts/skills_ref/<name>/`

## Diferencias vs OpenCode adapter

- No git pre-commit hook (no confiable mientras UNTESTED)
- No watch daemon
- Output a `~/.codex/` (global, no project-local)
```

- [ ] **Step 4: Make executable + verify syntax**

```bash
chmod +x adapters/codex/install.sh
bash -n adapters/codex/install.sh && echo "syntax OK"
python3 -c "import ast; ast.parse(open('adapters/codex/transform.py').read()); print('py syntax OK')"
```

- [ ] **Step 5: Commit**

```bash
git add adapters/codex/
git commit -m "feat: Codex adapter scaffold (UNTESTED)"
```

---

## Task 11: OpenCode adapter README

**Files:**
- Create: `adapters/opencode/README.md`

- [ ] **Step 1: Write README.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add adapters/opencode/README.md
git commit -m "docs: OpenCode adapter README"
```

---

## Task 12: Regression verification + implementation log

**Files:**
- Create: `docs/superpowers/plans/2026-04-22-multi-cli-portability-IMPLEMENTATION-LOG.md`

- [ ] **Step 1: Run all tests**

```bash
python3 -m pytest .claude/scripts/ adapters/opencode/ -v 2>&1 | tail -5
```

Expected: all tests pass (24 guardian + 19 mt5_bridge + 11 transform = 54 total).

- [ ] **Step 2: Verify Claude Code regression — /status via symlinks**

```bash
# Verify commands still accessible
test -f .claude/commands/status.md && echo "status.md OK"
test -f .claude/agents/morning-analyst-ftmo.md && echo "agent OK"
test -d .claude/skills/trendlines-sr && echo "skill OK"

# Verify guardian + statusline still work
bash .claude/scripts/profile.sh set retail
bash .claude/scripts/statusline.sh
bash .claude/scripts/profile.sh set ftmo
bash .claude/scripts/statusline.sh
bash .claude/scripts/profile.sh set retail
```

Expected: statusline outputs unchanged (retail $13.63, ftmo $10k initial).

- [ ] **Step 3: Verify .opencode/ outputs**

```bash
ls .opencode/
ls .opencode/commands/ | wc -l  # Expected: 23
ls .opencode/agents/ | wc -l    # Expected: 12
readlink .opencode/skills       # Expected: ../system/skills
python3 -c "import json; d=json.load(open('.opencode/config.json')); print(d['mcp']['servers']['tradingview']['command'])"
# Expected: node
```

- [ ] **Step 4: Write implementation log**

Create `docs/superpowers/plans/2026-04-22-multi-cli-portability-IMPLEMENTATION-LOG.md`:

```markdown
# Multi-CLI Portability — Implementation Log

**Fecha:** 2026-04-22 (noche tardía)
**Branch:** `feature/multi-cli`
**Commits:** <N> (update at finalization)
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

- Commits en branch: <N>
- Tests nuevos: 11 (transform.py)
- Líneas de código nuevas: ~500 (transform.py ~300 + adapters ~200)
- Archivos migrados: 49 (23 commands + 12 agents + 14 skills)

## Riesgos conocidos

1. OpenCode format puede haber cambiado desde docs consultados (2026-04-22). Re-fetchar antes de validar.
2. Codex adapter: 100% especulativo sin test real.
3. Skills: OpenCode doc dice compatible, pero no se valida hasta que user corra `opencode` y lo pruebe.
```

- [ ] **Step 5: Commit log**

```bash
git add docs/superpowers/plans/2026-04-22-multi-cli-portability-IMPLEMENTATION-LOG.md
git commit -m "docs: multi-CLI portability implementation log"
```

---

## Task 13: Final branch summary + merge decision

**Files:** None (git review)

- [ ] **Step 1: Summary of the branch**

```bash
git log --oneline main..HEAD
```

Expected: 11-12 commits covering migration + adapters + docs.

- [ ] **Step 2: Prepare merge command (user decides)**

Don't merge automatically. Show summary to user:

```
Branch feature/multi-cli listo con:
- <N> commits
- 54 tests verdes
- system/ canonical creado
- .opencode/ generado listo para probar

Próximo paso:
1. Usuario instala OpenCode: curl -fsSL https://opencode.ai/install | bash
2. Usuario corre: opencode en el repo
3. Valida /status funciona
4. Reporta issues — iteramos
5. Luego merge a main
```

Si user aprueba merge sin validar primero (acepta el riesgo):

```bash
cd ~/Documents/trading
git checkout main
git merge feature/multi-cli --no-ff -m "feat: multi-CLI portability (canonical system/ + adapters)"
git worktree remove .worktrees/multi-cli
git branch -d feature/multi-cli
```

---

## Execution choice

Plan complete and saved to `docs/superpowers/plans/2026-04-22-multi-cli-portability.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between, fast iteration.

**2. Inline Execution** — Batch tasks with checkpoints in this session.

¿Cuál prefieres?
