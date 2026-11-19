"""guard/claude_hook.py denies Claude Code edits that would write deny-list terms into the kit."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import KIT_ROOT, clean_env, make_deny_dir

HOOK = KIT_ROOT / "guard" / "claude_hook.py"


def run_hook(payload, env, kit_root=KIT_ROOT):
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOK), "--kit-root", str(kit_root)], input=data,
                          env=env, capture_output=True, text=True)


def decision(result):
    if not result.stdout.strip():
        return "allow"
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def reason(result):
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]


class ClaudeHookTest(unittest.TestCase):
    def setUp(self):
        self.env = clean_env(make_deny_dir())
        self.inside = str(KIT_ROOT / "skills" / "demo" / "SKILL.md")

    def test_write_with_term_inside_kit_is_denied_without_showing_the_term(self):
        result = run_hook({"tool_name": "Write", "tool_input": {
            "file_path": self.inside, "content": "intro\nJane Roe said so\n"}}, self.env)
        self.assertEqual(decision(result), "deny")
        self.assertIn("skills/demo/SKILL.md:2 [deny:fake.txt#4]", reason(result))
        self.assertNotIn("Jane", result.stdout)

    def test_clean_write_inside_kit_is_allowed(self):
        result = run_hook({"tool_name": "Write", "tool_input": {
            "file_path": self.inside, "content": "plain advice\n"}}, self.env)
        self.assertEqual(decision(result), "allow")

    def test_edit_scans_only_the_new_text(self):
        result = run_hook({"tool_name": "Edit", "tool_input": {
            "file_path": self.inside, "old_string": "Acme Corp", "new_string": "a vendor"}},
            self.env)
        self.assertEqual(decision(result), "allow")
        result = run_hook({"tool_name": "Edit", "tool_input": {
            "file_path": self.inside, "old_string": "a vendor", "new_string": "Acme Corp"}},
            self.env)
        self.assertEqual(decision(result), "deny")

    def test_multiedit_scans_every_new_text(self):
        result = run_hook({"tool_name": "MultiEdit", "tool_input": {"file_path": self.inside,
            "edits": [{"old_string": "a", "new_string": "b"},
                      {"old_string": "c", "new_string": "zorblax"}]}}, self.env)
        self.assertEqual(decision(result), "deny")

    def test_relative_path_is_resolved_against_cwd(self):
        result = run_hook({"tool_name": "Write", "cwd": str(KIT_ROOT), "tool_input": {
            "file_path": "skills/demo/SKILL.md", "content": "Acme Corp"}}, self.env)
        self.assertEqual(decision(result), "deny")

    def test_file_outside_kit_is_not_scanned(self):
        outside = str(Path(tempfile.mkdtemp()) / "notes.md")
        result = run_hook({"tool_name": "Write", "tool_input": {
            "file_path": outside, "content": "Jane Roe"}}, self.env)
        self.assertEqual(decision(result), "allow")

    def test_missing_deny_list_denies_writes_inside_kit(self):
        result = run_hook({"tool_name": "Write", "tool_input": {
            "file_path": self.inside, "content": "plain"}}, clean_env(None))
        self.assertEqual(decision(result), "deny")
        self.assertIn(".config/agent-kit/deny", reason(result))

    def test_invalid_json_is_allowed(self):
        result = run_hook("not json", self.env)
        self.assertEqual(decision(result), "allow")
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
