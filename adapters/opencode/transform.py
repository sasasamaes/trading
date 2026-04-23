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


def translate_mcp(servers_json_path, config_json_path):
    """Merge system/mcp/servers.json into .opencode/config.json under `mcp` key.

    Preserves other keys in config.json if present.
    """
    with open(servers_json_path) as f:
        source = json.load(f)

    # Load existing config.json if present
    if Path(config_json_path).exists():
        with open(config_json_path) as f:
            config = json.load(f)
    else:
        config = {}

    # OpenCode MCP schema: config.mcp.servers = {name: {command, args, env}}
    config['mcp'] = {'servers': source.get('servers', {})}

    Path(config_json_path).parent.mkdir(parents=True, exist_ok=True)
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
        shutil.move(str(skills_link), str(opencode_dir / 'skills.backup'))
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
