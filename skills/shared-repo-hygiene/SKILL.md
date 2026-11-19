---
name: shared-repo-hygiene
description: Use when editing, committing or pushing to a repository that other people or machines can read, such as this kit, or when asked to turn a lesson into a rule here. Keeps names, company data and credentials out.
---

# Shared repository hygiene

This repository travels: to other machines, to other employers, to whoever gets read access.
Anything written here must make sense, and be safe, with no context about where it came from.

## What never goes in

- Names of people, companies, customers, products, internal projects or teams.
- Domains, URLs of internal systems, e-mail addresses, phone numbers, IP addresses, host names.
- Machine paths with a user name in them (write `/home/<user>/` or `~/` instead).
- Amounts, order or invoice numbers, account numbers, document identifiers.
- Credentials of any kind, real or "just for testing".
- Screenshots, exports and any other binary file.
- An incident told with details that let a reader recognise it.

## How to bring a lesson in

1. Write the rule, not the case. "A verification must print how many items it compared" carries
   the lesson; the story of the night it failed does not belong here.
2. When an example helps, invent a neutral one: "an order import", "a billing service", "a vendor".
3. Round or invent numbers. Keep the shape of the problem, never its real values.
4. Read the result as a stranger would: if it hints at who you work for, rewrite it.

## The guard

- `guard/scan.py` checks deny lists and generic detectors (e-mail, IP, URL host, machine path,
  phone, IBAN, credential, binary). The git hooks run it on every commit and push, and the Claude
  Code hook runs it before a file is written. CI runs it again on every push.
- The deny lists live outside the repository, in `~/.config/agent-kit/deny/*.txt`, one per origin.
  Never commit them, never copy their terms into a file here.
- The scanner prints file, line and detector, never the matched text. Do not try to recover it;
  open the file at that line.
- Never bypass the hooks (`--no-verify`, `core.hooksPath` changes, editing on the web). The CI
  check would still catch it, but after the push.

## When the guard finds something

- Rewrite the text. Do not add a company term, a person or an internal host to `guard/allow.txt`;
  that file is for public documentation hosts and documentation addresses only.
- If the finding is in a commit that has not been pushed yet, fix that commit (amend or rebase)
  so the term leaves history before the push.
- If it already reached the remote, stop and tell the owner: rewriting shared history is their call.

## Before every push

Show the owner what will leave (commits and a short diff summary) and wait for an explicit yes in
this session. A yes given earlier, for other changes, does not cover this push.
