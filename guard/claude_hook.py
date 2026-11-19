#!/usr/bin/env python3
"""Claude Code PreToolUse hook: deny Write, Edit, MultiEdit and NotebookEdit calls that would put
deny-list terms or sensitive data into a file of this kit.

Register it for the matcher "Write|Edit|MultiEdit|NotebookEdit" with
    python3 <kit>/guard/claude_hook.py --kit-root <kit>

Only the new text is scanned (the content of a Write, each new_string of an edit), so line numbers
in the reason refer to that text. Files outside the kit are not looked at. Without a deny list the
hook denies writes inside the kit, like the git hooks. Shell commands that write files escape this
hook; the git hooks catch them at commit time.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan  # noqa: E402

TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def deny(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "agent-kit guard: " + reason,
    }}))


def new_texts(tool: str, data: dict) -> list[str]:
    if tool == "Write":
        return [str(data.get("content") or "")]
    if tool == "Edit":
        return [str(data.get("new_string") or "")]
    if tool == "MultiEdit":
        return [str(e.get("new_string") or "") for e in data.get("edits") or []]
    return [str(data.get("new_source") or "")]


def target_inside_kit(raw: str, cwd: str, kit_root: Path) -> str | None:
    """The path relative to the kit, or None when the file is elsewhere."""
    path = Path(raw)
    if not path.is_absolute():
        path = Path(cwd or ".") / path
    try:
        relative = path.resolve().relative_to(kit_root.resolve())
    except ValueError:
        return None
    return None if relative.parts[:1] == (".git",) else relative.as_posix()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit-root", required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    tool = payload.get("tool_name")
    data = payload.get("tool_input") or {}
    if tool not in TOOLS:
        return 0
    raw = data.get("file_path") or data.get("notebook_path") or ""
    name = target_inside_kit(str(raw), str(payload.get("cwd") or ""), Path(args.kit_root))
    if not name:
        return 0
    try:
        terms = scan.load_deny_terms()
        allow = scan.load_allow()
    except scan.ConfigError as error:
        deny(str(error))
        return 0
    findings = []
    for text in new_texts(tool, data):
        findings += scan.scan_text(name, text, terms, allow)
    if findings:
        listed = "; ".join(str(f) for f in findings[:20])
        deny(f"{len(findings)} findings in the new text ({listed}). Rewrite without names of "
             "people, companies, products, domains, addresses or credentials; use a neutral "
             "example. Never add a company term to guard/allow.txt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
