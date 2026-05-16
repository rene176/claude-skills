#!/bin/bash
set -euo pipefail

# Async so the session starts without waiting for skill installation
echo '{"async": true, "asyncTimeout": 60000}'

SKILLS_DIR="$(cd "$(dirname "$0")/../.." && pwd)/skills"
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
COMMANDS_DIR="$(cd "$(dirname "$0")/../.." && pwd)/commands"
CLAUDE_COMMANDS_DIR="${HOME}/.claude/commands"

mkdir -p "$CLAUDE_SKILLS_DIR"
mkdir -p "$CLAUDE_COMMANDS_DIR"

# Symlink each skill into ~/.claude/skills/
for skill_path in "$SKILLS_DIR"/*/; do
    skill_name="$(basename "$skill_path")"
    target="$CLAUDE_SKILLS_DIR/$skill_name"
    if [ ! -e "$target" ]; then
        ln -s "$skill_path" "$target"
    fi
done

# Symlink each command into ~/.claude/commands/
for cmd_path in "$COMMANDS_DIR"/*/; do
    cmd_name="$(basename "$cmd_path")"
    target="$CLAUDE_COMMANDS_DIR/$cmd_name"
    if [ ! -e "$target" ]; then
        ln -s "$cmd_path" "$target"
    fi
done
