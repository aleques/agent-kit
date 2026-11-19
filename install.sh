#!/usr/bin/env bash
# Install this kit on this machine for Claude Code, Kiro and GitHub Copilot:
#   - turns on the git hooks of the guard (core.hooksPath=guard/hooks);
#   - links each skill into ~/.claude/skills, ~/.kiro/skills and ~/.copilot/skills;
#   - links profile/AGENTS.md as Kiro global steering and as Copilot personal instructions;
#   - checks that a deny list exists (~/.config/agent-kit/deny/*.txt).
# Run it from anywhere, as often as you like: what is already in place stays, and nothing that
# is not a link to this kit is touched. It ends with OK, or with ATTENTION and exit 1.
set -eu

KIT=$(cd "$(dirname "$0")" && pwd -P)
linked=0
ok=0
attention=0

note() { echo "  $1"; }
warn() { echo "  ATTENTION: $1"; attention=$((attention + 1)); }

link() {
  local src=$1 dst=$2
  if [ -L "$dst" ]; then
    if [ "$(readlink -f "$dst")" = "$(readlink -f "$src")" ]; then ok=$((ok + 1)); return; fi
    warn "$dst links to somewhere else; left as it is"
    return
  fi
  if [ -e "$dst" ]; then
    warn "$dst already exists and is not a link to this kit; left as it is"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  ln -s "$src" "$dst"
  linked=$((linked + 1))
  note "linked $dst"
}

echo "agent-kit: installing from $KIT"

# 1. Git hooks of the guard.
if git -C "$KIT" rev-parse --git-dir >/dev/null 2>&1; then
  if [ "$(git -C "$KIT" config core.hooksPath || true)" = "guard/hooks" ]; then
    ok=$((ok + 1))
  else
    git -C "$KIT" config core.hooksPath guard/hooks
    linked=$((linked + 1))
    note "git hooks turned on (core.hooksPath=guard/hooks)"
  fi
else
  warn "$KIT is not a git clone; git hooks not turned on"
fi

# 2. Skills, one link per skill, so skills that are already there stay.
for folder in .claude/skills .kiro/skills .copilot/skills; do
  base="$HOME/$folder"
  if [ -L "$base" ]; then
    if [ "$(readlink -f "$base")" = "$KIT/skills" ]; then ok=$((ok + 1)); continue; fi
    warn "$base is a link managed elsewhere; no skill linked there"
    continue
  fi
  for skill in "$KIT"/skills/*/; do
    [ -f "${skill}SKILL.md" ] || continue
    name=$(basename "$skill")
    link "$KIT/skills/$name" "$base/$name"
  done
done

# 3. The profile that goes into every conversation.
profile="$KIT/profile/AGENTS.md"
if [ -f "$profile" ]; then
  link "$profile" "$HOME/.kiro/steering/AGENTS.md"
  link "$profile" "$HOME/.copilot/copilot-instructions.md"
else
  note "no profile/AGENTS.md yet; profile not linked"
fi

# 4. Deny list: without it the git hooks refuse every commit.
deny="${AGENT_KIT_DENY_DIR:-$HOME/.config/agent-kit/deny}"
if ls "$deny"/*.txt >/dev/null 2>&1 && command grep -qv -E '^[[:space:]]*(#|$)' "$deny"/*.txt; then
  ok=$((ok + 1))
else
  warn "no deny list in $deny: create $deny/<name>.txt with one term per line (people, companies, products, domains); until then every commit is refused"
fi

note "Claude Code: register guard/claude_hook.py as a PreToolUse hook (see README)"
echo "agent-kit: $linked linked, $ok already in place, $attention need attention"
if [ "$attention" -eq 0 ]; then
  echo "agent-kit: OK"
else
  echo "agent-kit: ATTENTION, see the lines above"
  exit 1
fi
