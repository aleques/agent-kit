#!/usr/bin/env python3
"""Keep sensitive and company data out of this repository.

Two kinds of checks run over every line:

- deny lists: terms nobody may write here (people, companies, products, domains). The lists live
  OUTSIDE the repository, in ~/.config/agent-kit/deny/*.txt (folder overridable with
  AGENT_KIT_DENY_DIR) and in the AGENT_KIT_DENY_TERMS variable (used by CI as a secret). One term
  per line; '#' starts a comment. With no term at all the scan fails closed (exit 2).
- generic detectors: e-mail, IP, URL host, machine path, phone, IBAN, credential, binary file.
  Exceptions live in guard/allow.txt (host:, ip:, email:).

The output names file, line and detector, never the matched text, so the scan itself cannot leak
what it found. Exit codes: 0 clean, 1 findings, 2 configuration error.

Modes:
  scan.py --paths FILE_OR_DIR...   files on disk (directories recursively, .git skipped)
  scan.py --staged                 the git index, i.e. what the next commit will contain
  scan.py --message FILE           a commit message (git comment lines skipped)
  scan.py --commits "REV..."       every commit `git rev-list REV...` returns (one argument, split
                                   on spaces): files, message, author and committer e-mail
  scan.py --stdin --name NAME      text from standard input, reported as NAME
  scan.py --identity               the git user.email that the next commit will use
"""
from __future__ import annotations

import argparse
import ipaddress
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ALLOW = HERE / "allow.txt"
DEFAULT_DENY_DIR = Path(".config") / "agent-kit" / "deny"
NOREPLY = re.compile(r"@users\.noreply\.github\.com$", re.I)
BUILTIN_HOSTS = {"example.com", "example.org", "example.net", "localhost"}
BUILTIN_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}
DOC_NETWORKS = [ipaddress.ip_network(n) for n in
                ("127.0.0.0/8", "0.0.0.0/32", "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]


class ConfigError(Exception):
    """The scan cannot run safely; nothing was checked."""


@dataclass(frozen=True)
class Term:
    source: str
    lineno: int
    pattern: re.Pattern


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    detector: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line} [{self.detector}]"


@dataclass
class Allow:
    hosts: set = field(default_factory=set)
    ips: set = field(default_factory=set)
    emails: set = field(default_factory=set)


# ---------------------------------------------------------------- deny lists

def fold(text: str) -> str:
    """Lower case without accents, so 'Ácme' and 'acme' compare equal."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def parse_terms(source: str, body: str) -> list[Term]:
    terms = []
    for lineno, raw in enumerate(body.splitlines(), 1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        words = [re.escape(w) for w in fold(text).split()]
        core = r"[\s_-]+".join(words)
        # A term is a whole word: not glued to letters or digits ('ana' must not hit 'banana').
        terms.append(Term(source, lineno, re.compile(r"(?<![^\W_])" + core + r"(?![^\W_])")))
    return terms


def deny_dir(environ) -> Path:
    if environ.get("AGENT_KIT_DENY_DIR"):
        return Path(environ["AGENT_KIT_DENY_DIR"])
    return Path(environ.get("HOME", str(Path.home()))) / DEFAULT_DENY_DIR


def load_deny_terms(environ=os.environ) -> list[Term]:
    folder = deny_dir(environ)
    terms: list[Term] = []
    if folder.is_dir():
        for path in sorted(folder.glob("*.txt")):
            terms += parse_terms(path.name, path.read_text(encoding="utf-8"))
    if environ.get("AGENT_KIT_DENY_TERMS"):
        terms += parse_terms("env", environ["AGENT_KIT_DENY_TERMS"])
    if not terms:
        raise ConfigError(
            f"no deny terms found. Create {folder}/<name>.txt with one term per line "
            "(people, companies, products, domains that must never appear here), or set "
            "AGENT_KIT_DENY_TERMS. The guard refuses to run without them.")
    return terms


# ---------------------------------------------------------------- allow list

def parse_allow(body: str) -> Allow:
    allow = Allow()
    for raw in body.splitlines():
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        kind, _, value = text.partition(":")
        value = value.strip().lower()
        if kind == "host" and value:
            allow.hosts.add(value)
        elif kind == "ip" and value:
            allow.ips.add(value)
        elif kind == "email" and value:
            allow.emails.add(value)
        else:
            raise ConfigError(f"allow list: unknown entry {kind!r} (use host:, ip: or email:)")
    return allow


def load_allow(path: Path = DEFAULT_ALLOW) -> Allow:
    return parse_allow(path.read_text(encoding="utf-8")) if path.is_file() else Allow()


# ---------------------------------------------------------------- generic detectors

URL = re.compile(r"https?://([^/\s)\]>'\"`]+)", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
IPV4 = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?!\.?\d)")
HOME_PATH = re.compile(r"(?:/home/|/Users/)(?!<)[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\(?!<)[^\\\s]+")
PHONE = re.compile(r"(?<![\w+])\+\d{1,3}(?:[\s.-]?\d){7,13}(?!\d)")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b")
SECRET = re.compile("|".join([
    r"gh[pousr]_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{22,}",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"AKIA[0-9A-Z]{16}",
    "-----BEGIN " + r"[A-Z ]*" + "PRIVATE KEY-----",
    r"xox[abprs]-[A-Za-z0-9-]{10,}",
    r"AIza[0-9A-Za-z_-]{35}",
    r"eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}",
    # name = value, where the value is a plain literal: code such as `x = call()`,
    # `x = form.value` or an unquoted constant name (`secret: SESSION_SECRET,`) does not count.
    r"(?i:\b(?:password|passwd|pwd|secret|token|api[_-]?key)\b\s*[:=]\s*['\"]?"
    r"(?![A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+['\"]?(?:\s|$|[,;]))"
    r"(?!(?-i:[A-Z][A-Z0-9]*_[A-Z0-9_]*)(?:\s|$|[,;]))"
    r"[^\s'\"<>{}$()\[\],;]{8,}['\"]?(?=\s|$|[,;]))",
]))


def host_allowed(host: str, allow: Allow) -> bool:
    host = host.lower().rstrip(".")
    return any(host == h or host.endswith("." + h) for h in BUILTIN_HOSTS | allow.hosts)


def email_allowed(email: str, allow: Allow) -> bool:
    email = email.lower()
    domain = email.rsplit("@", 1)[1]
    return bool(NOREPLY.search(email)) or domain in BUILTIN_EMAIL_DOMAINS or email in allow.emails


def ip_allowed(text: str, allow: Allow) -> bool:
    if text in allow.ips:
        return True
    address = ipaddress.ip_address(text)
    return any(address in net for net in DOC_NETWORKS)


def generic_findings(line: str, allow: Allow) -> list[str]:
    found: list[str] = []
    url_spans = []
    url_detectors = []
    for m in URL.finditer(line):
        url_spans.append(m.span())
        authority = m.group(1)
        userinfo, at, hostport = authority.rpartition("@")
        if at and ":" in userinfo:
            url_detectors.append("secret")
            continue
        host = hostport.split(":", 1)[0]
        if not host_allowed(host, allow):
            url_detectors.append("url")

    def inside_url(span) -> bool:
        return any(a <= span[0] and span[1] <= b for a, b in url_spans)

    for m in EMAIL.finditer(line):
        if not inside_url(m.span()) and not email_allowed(m.group(0), allow):
            found.append("email")
    for m in IPV4.finditer(line):
        text = m.group(1)
        if all(int(octet) <= 255 for octet in text.split(".")) and not ip_allowed(text, allow):
            found.append("ip")
    found += url_detectors
    found += ["home-path" for _ in HOME_PATH.finditer(line)]
    found += ["phone" for _ in PHONE.finditer(line)]
    found += ["iban" for _ in IBAN.finditer(line)]
    found += ["secret" for _ in SECRET.finditer(line)]
    return found


# ---------------------------------------------------------------- scanning

def scan_text(name: str, text: str, terms: list[Term], allow: Allow,
              skip_comments: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if skip_comments and line.startswith("#"):
            continue
        folded = fold(line)
        for term in terms:
            for _ in term.pattern.finditer(folded):
                findings.append(Finding(name, lineno, f"deny:{term.source}#{term.lineno}"))
        for detector in generic_findings(line, allow):
            findings.append(Finding(name, lineno, detector))
    return findings


def scan_bytes(name: str, data: bytes, terms: list[Term], allow: Allow) -> list[Finding]:
    if b"\x00" in data[:8192]:
        return [Finding(name, 1, "binary")]
    return scan_text(name, data.decode("utf-8", errors="replace"), terms, allow)


def git(*args: str, cwd=None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


def git_lines(*args: str) -> list[str]:
    return [p for p in git(*args).decode().split("\0") if p]


def identity_findings(name: str, email: str) -> list[Finding]:
    return [] if NOREPLY.search(email.strip()) else [Finding(name, 1, "author-email")]


def run(args, terms: list[Term], allow: Allow) -> tuple[int, list[Finding], str]:
    """Returns (items scanned, findings, extra summary)."""
    findings: list[Finding] = []
    if args.paths:
        files = []
        for raw in args.paths:
            path = Path(raw)
            if path.is_dir():
                files += sorted(p for p in path.rglob("*")
                                if p.is_file() and ".git" not in p.relative_to(path).parts)
            else:
                files.append(path)
        for path in files:
            findings += scan_bytes(str(path), path.read_bytes(), terms, allow)
        return len(files), findings, ""
    if args.stdin:
        data = sys.stdin.buffer.read()
        return 1, scan_bytes(args.name, data, terms, allow), ""
    if args.message:
        text = Path(args.message).read_text(encoding="utf-8", errors="replace")
        return 1, scan_text("commit-message", text, terms, allow, skip_comments=True), ""
    if args.identity:
        result = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True)
        return 1, identity_findings("git-config:user.email", result.stdout), ""
    if args.staged:
        paths = git_lines("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
        for path in paths:
            findings += scan_bytes(path, git("show", f":{path}"), terms, allow)
        return len(paths), findings, ""
    if args.commits:
        commits = git("rev-list", *args.commits.split()).decode().split()
        items = 0
        for commit in commits:
            short = commit[:8]
            for path in git_lines("diff-tree", "--root", "--no-commit-id", "-r", "-z",
                                  "--name-only", "--diff-filter=ACMR", commit):
                findings += scan_bytes(f"{short}:{path}", git("show", f"{commit}:{path}"),
                                       terms, allow)
                items += 1
            message = git("log", "-1", "--format=%B", commit).decode("utf-8", errors="replace")
            findings += scan_text(f"{short}:message", message, terms, allow)
            people = git("log", "-1", "--format=%ae%n%ce", commit).decode().split("\n")
            findings += identity_findings(f"{short}:author", people[0])
            findings += identity_findings(f"{short}:committer", people[1])
            items += 1
        return items, findings, f" in {len(commits)} commits"
    raise ConfigError("choose a mode: --paths, --staged, --message, --commits, --stdin or --identity")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--paths", nargs="+")
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--message")
    mode.add_argument("--commits")
    mode.add_argument("--stdin", action="store_true")
    mode.add_argument("--identity", action="store_true")
    parser.add_argument("--name", default="stdin")
    args = parser.parse_args(argv)
    try:
        terms = load_deny_terms() if not args.identity else []
        allow = load_allow()
        items, findings, extra = run(args, terms, allow)
    except ConfigError as error:
        print(f"agent-kit guard: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"agent-kit guard: git failed ({' '.join(error.cmd[:3])}...)", file=sys.stderr)
        return 2
    for finding in findings:
        print(finding)
    print(f"agent-kit guard: scanned {items} files, {len(findings)} findings{extra}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
