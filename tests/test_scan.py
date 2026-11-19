"""Behaviour of guard/scan.py: deny lists, generic detectors and what the output may show."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import (ALLOWED_HOST, ALLOWED_URLS, EMAIL, FAKE_TERMS, IBAN, MACHINE_PATHS,
                     OTHER_EMAIL, PHONE, PUBLIC_IP, UNKNOWN_URL, clean_env, fake_anthropic_key,
                     fake_aws_key, fake_github_token, fake_openai_key, fake_password_assignment,
                     fake_private_key_header, j, load_scan_module, make_deny_dir, run_scan)

scan = load_scan_module()


def detectors(text, allow=None, terms=None):
    terms = terms if terms is not None else scan.parse_terms("fake.txt", "\n".join(FAKE_TERMS))
    allow = allow if allow is not None else scan.Allow()
    return [f.detector for f in scan.scan_text("doc.md", text, terms, allow)]


class DenyListTest(unittest.TestCase):
    def test_term_matches_ignoring_case_and_accents(self):
        self.assertEqual(detectors("we met acme corp today"), ["deny:fake.txt#1"])
        self.assertEqual(detectors("Ácme Corp shipped"), ["deny:fake.txt#1"])

    def test_multiword_term_matches_across_hyphen(self):
        self.assertEqual(detectors("the Acme-Corp team"), ["deny:fake.txt#1"])

    def test_term_inside_a_longer_word_does_not_match(self):
        self.assertEqual(detectors("a banana and a canal"), [])

    def test_term_next_to_hyphen_or_underscore_matches(self):
        self.assertEqual(detectors("see zorblax-vault and zorblax_notes"),
                         ["deny:fake.txt#4", "deny:fake.txt#4"])

    def test_comments_and_blank_lines_are_not_terms(self):
        terms = scan.parse_terms("x.txt", "# comment\n\n  \nJane Roe\n")
        self.assertEqual([t.lineno for t in terms], [4])

    def test_missing_lists_fail_closed_with_a_hint(self):
        result = run_scan(["--stdin", "--name", "a.md"], clean_env(None), stdin="hello")
        self.assertEqual(result.returncode, 2)
        self.assertIn(".config/agent-kit/deny", result.stderr)

    def test_list_with_only_comments_fails_closed(self):
        result = run_scan(["--stdin", "--name", "a.md"],
                          clean_env(make_deny_dir(terms=["# nothing yet"])), stdin="hello")
        self.assertEqual(result.returncode, 2)

    def test_terms_from_environment_variable_work_without_folder(self):
        env = clean_env(None)
        env["AGENT_KIT_DENY_TERMS"] = "Jane Roe\nzorblax"
        result = run_scan(["--stdin", "--name", "a.md"], env, stdin="ask Jane Roe")
        self.assertEqual(result.returncode, 1)
        self.assertIn("deny:env#1", result.stdout)

    def test_default_folder_in_home_is_read(self):
        env = clean_env(None)
        folder = Path(env["HOME"]) / ".config" / "agent-kit" / "deny"
        folder.mkdir(parents=True)
        (folder / "work.txt").write_text("zorblax\n", encoding="utf-8")
        result = run_scan(["--stdin", "--name", "a.md"], env, stdin="the zorblax team")
        self.assertEqual(result.returncode, 1)
        self.assertIn("deny:work.txt#1", result.stdout)


class GenericDetectorTest(unittest.TestCase):
    def test_email_is_found(self):
        self.assertEqual(detectors("write to " + EMAIL), ["email"])

    def test_noreply_and_example_emails_pass(self):
        text = j("1+bot", "@", "users.noreply.github.com or dev", "@", "example.com")
        self.assertEqual(detectors(text), [])

    def test_ip_is_found(self):
        self.assertEqual(detectors("server at " + PUBLIC_IP), ["ip"])

    def test_version_numbers_are_not_ips(self):
        self.assertEqual(detectors("release 1.2.3.4.5 and 300.1.1.1"), [])

    def test_loopback_and_documentation_ips_pass(self):
        text = "127.0.0.1 192.0.2.10 198.51.100.7 203.0.113.99 0.0.0.0"
        self.assertEqual(detectors(text), [])

    def test_url_with_unknown_host_is_found(self):
        self.assertEqual(detectors("see " + UNKNOWN_URL), ["url"])

    def test_url_with_allowed_host_or_subdomain_passes(self):
        self.assertEqual(detectors(ALLOWED_URLS), ["url", "url"])
        allow = scan.parse_allow(f"host:{ALLOWED_HOST}\n")
        self.assertEqual(detectors(ALLOWED_URLS, allow=allow), [])

    def test_url_with_user_and_password_is_a_secret(self):
        text = j("https", "://", "bob:", "s3cr3tvalue", "@", ALLOWED_HOST, "/x")
        allow = scan.parse_allow(f"host:{ALLOWED_HOST}\n")
        self.assertEqual(detectors(text, allow=allow), ["secret"])

    def test_machine_paths_are_found(self):
        self.assertEqual(detectors(MACHINE_PATHS), ["home-path", "home-path", "home-path"])

    def test_placeholder_paths_pass(self):
        self.assertEqual(detectors(j("/ho", "me/<user>/x and ~/projects")), [])

    def test_international_phone_is_found(self):
        self.assertEqual(detectors("call " + PHONE), ["phone"])

    def test_iban_is_found(self):
        self.assertEqual(detectors("pay " + IBAN), ["iban"])

    def test_secrets_are_found(self):
        for value in (fake_github_token(), fake_anthropic_key(), fake_openai_key(),
                      fake_aws_key(), fake_private_key_header(), fake_password_assignment()):
            with self.subTest(kind=value[:6]):
                self.assertEqual(detectors(f"x {value} y"), ["secret"])

    def test_code_that_calls_a_function_is_not_a_secret(self):
        self.assertEqual(detectors(j("SEC", "RET = re.compile(")), [])
        self.assertEqual(detectors(j("tok", "en = get_token()")), [])

    def test_quoted_secret_value_is_found(self):
        self.assertEqual(detectors(j("api_", "key: ", '"', "Zx81Qw7Lp0aa", '"')), ["secret"])

    def test_password_placeholder_is_not_a_secret(self):
        self.assertEqual(detectors(j("pass", "word = <your-value>")), [])

    def test_allowed_ip_and_email_entries_pass(self):
        ip, email = j("10.1", ".2.3"), j("team", "@", "corp.test")
        allow = scan.parse_allow(f"ip:{ip}\nemail:{email}\n")
        self.assertEqual(detectors(f"{ip} {email}"), ["email", "ip"])
        self.assertEqual(detectors(f"{ip} {email}", allow=allow), [])

    def test_unknown_allow_entry_is_a_config_error(self):
        with self.assertRaises(scan.ConfigError):
            scan.parse_allow("everything:*\n")


class OutputTest(unittest.TestCase):
    """make_deny_dir writes a comment and a blank line first, so its terms sit on lines 3 to 6."""

    def setUp(self):
        self.env = clean_env(make_deny_dir())

    def test_output_never_shows_the_term_or_the_value(self):
        text = f"Jane Roe wrote to {OTHER_EMAIL} from {PUBLIC_IP}"
        result = run_scan(["--stdin", "--name", "notes.md"], self.env, stdin=text)
        self.assertEqual(result.returncode, 1)
        for leaked in ("Jane", "Roe", OTHER_EMAIL, PUBLIC_IP):
            self.assertNotIn(leaked, result.stdout + result.stderr)
        self.assertIn("notes.md:1 [deny:fake.txt#4]", result.stdout)

    def test_summary_counts_files_and_findings(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "a.md").write_text("clean text\n", encoding="utf-8")
        (folder / "b.md").write_text("zorblax\nalso zorblax\n", encoding="utf-8")
        result = run_scan(["--paths", str(folder / "a.md"), str(folder / "b.md")], self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("scanned 2 files, 2 findings", result.stdout)

    def test_directory_is_scanned_recursively_without_git_folder(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "sub").mkdir()
        (folder / ".git").mkdir()
        (folder / "sub" / "a.md").write_text("zorblax\n", encoding="utf-8")
        (folder / ".git" / "config").write_text("zorblax\n", encoding="utf-8")
        result = run_scan(["--paths", str(folder)], self.env)
        self.assertIn("scanned 1 files, 1 findings", result.stdout)

    def test_clean_input_exits_zero_with_summary(self):
        result = run_scan(["--stdin", "--name", "a.md"], self.env, stdin="plain advice\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("scanned 1 files, 0 findings", result.stdout)

    def test_binary_file_is_found(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
        result = run_scan(["--paths", str(folder / "shot.png")], self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("[binary]", result.stdout)

    def test_stdin_reports_the_given_name(self):
        result = run_scan(["--stdin", "--name", "skills/x/SKILL.md"], self.env, stdin="Acme Corp")
        self.assertIn("skills/x/SKILL.md:1 [deny:fake.txt#3]", result.stdout)

    def test_message_mode_skips_git_comment_lines(self):
        msg = Path(tempfile.mkdtemp()) / "COMMIT_EDITMSG"
        msg.write_text("fix: thanks Jane Roe\n\n# comment line is ignored zorblax\n",
                       encoding="utf-8")
        result = run_scan(["--message", str(msg)], self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("commit-message:1 [deny:fake.txt#4]", result.stdout)
        self.assertNotIn("commit-message:3", result.stdout)


if __name__ == "__main__":
    unittest.main()
