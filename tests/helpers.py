"""Shared helpers for the guard tests.

Every term used here is invented. Values that look like an e-mail, IP, URL, phone, IBAN, machine
path or credential are assembled with j() at run time, so no file in this repository contains such a
literal and the repository scans clean with its own guard.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
SCAN_PY = KIT_ROOT / "guard" / "scan.py"

FAKE_TERMS = ["Acme Corp", "Jane Roe", "Ana", "zorblax"]


def j(*parts: str) -> str:
    return "".join(parts)


def load_scan_module():
    spec = importlib.util.spec_from_file_location("agent_kit_scan", SCAN_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_kit_scan"] = module
    spec.loader.exec_module(module)
    return module


def make_deny_dir(terms=FAKE_TERMS, name="fake.txt") -> Path:
    folder = Path(tempfile.mkdtemp(prefix="deny-"))
    body = "# invented terms for tests\n\n" + "\n".join(terms) + "\n"
    (folder / name).write_text(body, encoding="utf-8")
    return folder


def clean_env(deny_dir: Path | None) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_KIT_")}
    env["HOME"] = tempfile.mkdtemp(prefix="home-")
    if deny_dir is not None:
        env["AGENT_KIT_DENY_DIR"] = str(deny_dir)
    return env


def run_scan(args, env, stdin=None, cwd=None):
    return subprocess.run([sys.executable, str(SCAN_PY), *args], env=env, input=stdin,
                          capture_output=True, text=True, cwd=cwd)


EMAIL = j("someone", "@", "company.io")
OTHER_EMAIL = j("jane", "@", "corp.io")
PUBLIC_IP = j("88.12", ".4.200")
UNKNOWN_URL = j("https", "://", "intranet.company.io/page")
ALLOWED_HOST = "allowed.test"
ALLOWED_URLS = j("https", "://", ALLOWED_HOST, "/a and ", "https", "://docs.", ALLOWED_HOST, "/b")
MACHINE_PATHS = j("/ho", "me/fulano/x\n", "/Us", "ers/fulano/y\n", "C:", "\\Users\\fulano\\z")
PHONE = j("+32 470", " 12 34 56")
IBAN = j("BE71 0961", " 2345 6769")


def fake_github_token() -> str:
    return j("gh", "p_", "A1b2C3d4" * 4, "Zz9Y")


def fake_anthropic_key() -> str:
    return j("sk-", "ant-", "api03-", "x" * 40)


def fake_openai_key() -> str:
    return j("sk-", "proj-", "Q" * 40)


def fake_aws_key() -> str:
    return j("AK", "IA", "ABCDEFGHIJKLMNOP")


def fake_private_key_header() -> str:
    return j("-----BEGIN ", "RSA PRIVATE", " KEY-----")


def fake_password_assignment() -> str:
    return j("pass", "word = ", "hunter2hunter2")
