"""The git hooks in guard/hooks block commits and pushes that carry deny-list terms."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import KIT_ROOT, clean_env, j, make_deny_dir

HOOKS = KIT_ROOT / "guard" / "hooks"
NOREPLY = j("1+bot", "@", "users.noreply.github.com")


class GitHooksTest(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp(prefix="hooks-"))
        self.env = clean_env(make_deny_dir())
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(base / "gitconfig"))
        self.remote = base / "remote.git"
        self.repo = base / "work"
        self.git("init", "-q", "--bare", "-b", "main", str(self.remote), cwd=base)
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=base)
        self.git("config", "user.name", "bot")
        self.git("config", "user.email", NOREPLY)
        self.git("config", "core.hooksPath", str(HOOKS))
        self.git("remote", "add", "origin", str(self.remote))

    def git(self, *args, cwd=None, check=True):
        result = subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env,
                                capture_output=True, text=True)
        if check and result.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {result.stderr}")
        return result

    def commit_file(self, name, text, message="add file", verify=True):
        (self.repo / name).write_text(text, encoding="utf-8")
        self.git("add", name)
        args = ["commit", "-q", "-m", message] + ([] if verify else ["--no-verify"])
        return self.git(*args, check=False)

    def test_clean_commit_passes(self):
        result = self.commit_file("a.md", "plain advice\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_commit_with_term_in_file_is_blocked(self):
        result = self.commit_file("a.md", "ask Jane Roe\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[deny:fake.txt#4]", result.stdout + result.stderr)
        self.assertNotIn("Jane", result.stdout + result.stderr)
        self.assertEqual(self.git("rev-list", "--all").stdout.strip(), "")

    def test_commit_with_term_in_message_is_blocked(self):
        result = self.commit_file("a.md", "plain\n", message="thanks to zorblax")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commit-message:1", result.stdout + result.stderr)

    def test_commit_with_personal_email_is_blocked(self):
        self.git("config", "user.email", j("me", "@", "mail.test"))
        result = self.commit_file("a.md", "plain\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[author-email]", result.stdout + result.stderr)

    def test_push_blocks_a_term_that_only_lives_in_a_middle_commit(self):
        self.commit_file("a.md", "plain\n")
        self.assertEqual(self.git("push", "-q", "origin", "main", check=False).returncode, 0)
        self.commit_file("b.md", "Acme Corp notes\n", verify=False)
        self.commit_file("b.md", "neutral notes\n", verify=False)
        result = self.git("push", "-q", "origin", "main", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(":b.md:1 [deny:fake.txt#3]", result.stdout + result.stderr)
        remote_log = self.git("log", "--format=%s", "main", cwd=self.remote).stdout.split()
        self.assertEqual(len(remote_log), 2)  # only the first commit: 'add' 'file'

    def test_clean_push_passes(self):
        self.commit_file("a.md", "plain\n")
        result = self.git("push", "-q", "origin", "main", check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_first_push_of_a_new_branch_is_scanned(self):
        self.commit_file("a.md", "plain\n")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", "topic")
        self.commit_file("c.md", "zorblax plan\n", verify=False)
        result = self.git("push", "-q", "origin", "topic", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(":c.md:1 [deny:fake.txt#6]", result.stdout + result.stderr)

    def test_push_by_author_with_personal_email_is_blocked(self):
        self.git("config", "user.email", j("me", "@", "mail.test"))
        self.commit_file("a.md", "plain\n", verify=False)
        result = self.git("push", "-q", "origin", "main", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[author-email]", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
