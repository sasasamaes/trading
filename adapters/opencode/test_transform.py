"""Unit tests for transform.py — CC → OpenCode translator."""
import json
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
