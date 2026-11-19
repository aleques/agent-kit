"""install.sh links skills and the profile for Claude Code, Kiro and Copilot, turns on the git
hooks, and can run any number of times without damage. Each test runs a copy of the script inside
a throwaway kit and a throwaway HOME."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import KIT_ROOT, clean_env

SKILL_DIRS = [".claude/skills", ".kiro/skills", ".copilot/skills"]
PROFILE_LINKS = [".kiro/steering/AGENTS.md", ".copilot/copilot-instructions.md"]


class InstallTest(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp(prefix="install-"))
        self.kit = base / "kit"
        for name in ("alpha", "beta"):
            (self.kit / "skills" / name).mkdir(parents=True)
            (self.kit / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
        (self.kit / "profile").mkdir()
        (self.kit / "profile" / "AGENTS.md").write_text("profile\n")
        shutil.copy(KIT_ROOT / "install.sh", self.kit / "install.sh")
        subprocess.run(["git", "init", "-q", str(self.kit)], check=True)
        self.env = clean_env(None)
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(base / "gitconfig"))
        self.home = Path(self.env["HOME"])

    def add_deny_list(self):
        folder = self.home / ".config" / "agent-kit" / "deny"
        folder.mkdir(parents=True)
        (folder / "mine.txt").write_text("zorblax\n")

    def install(self):
        return subprocess.run(["bash", str(self.kit / "install.sh")], env=self.env,
                              capture_output=True, text=True, cwd=tempfile.gettempdir())

    def test_links_every_skill_and_the_profile(self):
        self.add_deny_list()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for folder in SKILL_DIRS:
            for name in ("alpha", "beta"):
                link = self.home / folder / name
                self.assertTrue(link.is_symlink(), link)
                self.assertEqual(link.resolve(), (self.kit / "skills" / name).resolve())
        for relative in PROFILE_LINKS:
            self.assertEqual((self.home / relative).resolve(),
                             (self.kit / "profile" / "AGENTS.md").resolve())

    def test_turns_on_the_git_hooks(self):
        self.add_deny_list()
        self.install()
        value = subprocess.run(["git", "-C", str(self.kit), "config", "core.hooksPath"],
                               env=self.env, capture_output=True, text=True).stdout.strip()
        self.assertEqual(value, "guard/hooks")

    def test_second_run_changes_nothing(self):
        self.add_deny_list()
        self.install()
        before = sorted(str(p) for p in self.home.rglob("*"))
        result = self.install()
        self.assertEqual(result.returncode, 0)
        self.assertIn("0 linked", result.stdout)
        self.assertEqual(sorted(str(p) for p in self.home.rglob("*")), before)

    def test_existing_file_is_kept_and_reported(self):
        self.add_deny_list()
        target = self.home / ".kiro" / "skills" / "alpha"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("someone else's skill\n")
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(target.is_symlink())
        self.assertEqual((target / "SKILL.md").read_text(), "someone else's skill\n")
        self.assertIn(".kiro/skills/alpha", result.stdout)

    def test_skills_folder_that_is_a_link_elsewhere_is_left_alone(self):
        self.add_deny_list()
        elsewhere = Path(tempfile.mkdtemp(prefix="managed-"))
        (self.home / ".claude").mkdir()
        os.symlink(elsewhere, self.home / ".claude" / "skills")
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(list(elsewhere.iterdir()), [])
        self.assertIn(".claude/skills", result.stdout)

    def test_skills_folder_linked_to_this_kit_counts_as_done(self):
        self.add_deny_list()
        (self.home / ".claude").mkdir()
        os.symlink(self.kit / "skills", self.home / ".claude" / "skills")
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_deny_list_is_reported(self):
        result = self.install()
        self.assertEqual(result.returncode, 1)
        self.assertIn(".config/agent-kit/deny", result.stdout)


if __name__ == "__main__":
    unittest.main()
