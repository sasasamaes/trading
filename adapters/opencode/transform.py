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
