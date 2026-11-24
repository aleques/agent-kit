# agent-kit

A personal kit of working habits for coding agents: skills and an always-on profile that Claude
Code, Kiro and GitHub Copilot read in the same format, plus a guard that keeps sensitive and
company data out of this repository.

## What is inside

- [`profile/AGENTS.md`](profile/AGENTS.md): eight rules that go into every conversation, each one
  pointing to the skill with the detail.
- Skills written for this kit:
  [`senior-engineering-posture`](skills/senior-engineering-posture/SKILL.md) (how to plan, measure
  and act before and during a task), [`clear-communication`](skills/clear-communication/SKILL.md)
  (how to report and how to hand over a command), [`test-coverage`](skills/test-coverage/SKILL.md)
  (what to test, how to measure, how CI gates a deploy) and
  [`shared-repo-hygiene`](skills/shared-repo-hygiene/SKILL.md) (what never goes into a shared
  repository).
- Third-party skills, frozen copies: the fourteen Superpowers skills (planning, debugging, TDD,
  code review, writing skills), `writing-clearly-and-concisely`, and six specialists:
  [`angular-developer`](skills/angular-developer/SKILL.md),
  [`multi-tenancy`](skills/multi-tenancy/SKILL.md) (Spring Boot 4),
  [`docker-compose-patterns`](skills/docker-compose-patterns/SKILL.md),
  [`security-and-hardening`](skills/security-and-hardening/SKILL.md),
  [`frontend-design`](skills/frontend-design/SKILL.md) (new UI) and
  [`impeccable`](skills/impeccable/SKILL.md) (critique and polish of existing UI). Origin, licenses
  and changes in [`THIRD_PARTY.md`](THIRD_PARTY.md).

## Install on a machine

```bash
git clone <this repository> ~/agent-kit
~/agent-kit/install.sh
```

The script links each skill into `~/.claude/skills`, `~/.kiro/skills` and `~/.copilot/skills`,
links `profile/AGENTS.md` as Kiro global steering and Copilot personal instructions, and turns on
the git hooks of the guard. It never overwrites something that is not a link to this kit, can run
again at any time, and ends with `OK` or with `ATTENTION` and the list of what needs a look.

In VS Code, Copilot may need agent skills turned on in the settings before it lists them.

## The guard

Read [the hygiene skill](skills/shared-repo-hygiene/SKILL.md) before writing here. In short:

- Create a deny list before the first commit: `~/.config/agent-kit/deny/<origin>.txt`, one term per
  line (people, companies, products, domains). Keep one file per origin and never commit them.
  Without a list, every commit is refused.
- [`guard/scan.py`](guard/scan.py) checks the deny lists and generic detectors (e-mail, IP, URL
  host, machine path, phone, IBAN, credential, binary file). It prints file, line and detector,
  never the matched text.
- The git hooks in [`guard/hooks`](guard/hooks) run it on every commit (files, message, author
  e-mail, which must be a GitHub noreply address) and on every push (each commit, not only the
  final tree).
- [`guard/claude_hook.py`](guard/claude_hook.py) is a Claude Code `PreToolUse` hook that denies a
  write before it reaches the disk. Register it in `~/.claude/settings.json`:

  ```json
  {"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit|NotebookEdit", "hooks": [
    {"type": "command", "command": "python3 ~/agent-kit/guard/claude_hook.py --kit-root ~/agent-kit"}
  ]}]}}
  ```

- CI runs the suite and the guard over the whole history, with the terms in the repository secret
  `AGENT_KIT_DENY_TERMS`.
- Exceptions for the generic detectors go in [`guard/allow.txt`](guard/allow.txt): public
  documentation hosts only.

## Tests

```bash
python3 -m unittest discover -s tests
```

Run them before every commit. Test data is invented, and values that look like addresses or
credentials are assembled at run time, so the repository passes its own guard.

