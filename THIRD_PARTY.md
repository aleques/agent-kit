# Third-party content

Everything under `skills/` that is not listed here was written for this kit and follows its
README. The skills below come from other projects, are kept as frozen copies (upstream fixes do
not arrive by themselves), and keep their licenses.

## Superpowers

Source: https://github.com/obra/superpowers, MIT license (text below).

Skills: brainstorming, dispatching-parallel-agents, executing-plans,
finishing-a-development-branch, receiving-code-review, requesting-code-review,
subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees,
using-superpowers, verification-before-completion, writing-plans, writing-skills.

Changes made here:

- `finishing-a-development-branch`, `subagent-driven-development` and `using-git-worktrees`: the
  `description` ends with a note that the project's own git rules take precedence, and the first
  two carry the same note at the top of the body.
- `using-git-worktrees` was taken from upstream later than the others, because the copy this kit
  started from had been replaced by a redirect.

```
MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Specialist skills

Six skills, one per role, picked by measurement (stars, installs, last commit, license) and by
reading each `SKILL.md` in full. Text only: no script, hook, agent or MCP server of the original
plugins came along. Each folder keeps the original license file (`LICENSE.txt`, and `NOTICE.md`
where the original has one).

| skill | source, path and commit | license |
|---|---|---|
| `angular-developer` | https://github.com/angular/skills, `angular-developer/`, `97c663a02b376a19eccc60f75909f20f15a2c9c1` | MIT, declared in the skill header (the repository has no license file; text below) |
| `multi-tenancy` | https://github.com/rrezartprebreza/spring-boot-skills, `skills/spring-boot-4/multi-tenancy/`, `b90c3dbd9699c0d0bfb81660c857ef58262168e6` | MIT |
| `docker-compose-patterns` | https://github.com/docker/skills, `skills/docker-compose-patterns/`, `caeee2024f7527d890a29dd1732b62a112f56d0e` | Apache-2.0 |
| `security-and-hardening` | https://github.com/addyosmani/agent-skills, `skills/security-and-hardening/`, `8c99fa36d90068c82d547f7c12a9d67a3e95f4ee` | MIT |
| `frontend-design` | https://github.com/anthropics/claude-plugins-official, `plugins/frontend-design/skills/frontend-design/`, `73c8cf3ea7e296057b467990f2f5d61b4c922260` | Apache-2.0 |
| `impeccable` | https://github.com/pbakaus/impeccable, `plugin/skills/impeccable/`, `b49177d32788f2dc585c42831d845dacf1ebed2c` | Apache-2.0, with its `NOTICE.md` |

Changes made here, in every one of the six: the `description` was rewritten as a trigger of up to
250 characters, and a "Kit note" block after the header says what does not apply and where the
project's own rules come first. Everything else is identical to the original, except:

- `multi-tenancy`: `agents/openai.yaml` (metadata for another tool) left out.
- `docker-compose-patterns`: `scripts/verify-compose.sh` (the note gives the command it runs),
  `evals/` (the authors' tests), `agents/openai.yaml` and `skill.yaml` left out.
- `security-and-hardening`: `references/security-checklist.md` came from the root of the original
  repository into this folder, and the five links to it in `SKILL.md` and
  `references/hardening-patterns.md` were adjusted.
- `impeccable`: the `scripts/` folder (the launcher, which downloads and runs a program, the browser
  scripts and the font index) and 25 of the 50 references left out: the ones that only work with the
  launcher (`live`, `live-setup`, `generate`, `hooks`, `doctor`, `component-review`, `region-map`,
  `new-work`, `new-work-comp`, `new-work-world`, `visualize`, `routing`, `foundations` and four in
  `degraded/`), the native-app ones (`ios`, `android`, `audit.native`, `adapt.native`), the three
  `mode-*` used only by `new-work`, and `craft`, a retired alias. The plugin's agents and hooks are
  not here either. In `reference/critique.md` and `reference/critique-rubric.md` the "power user"
  persona is called Morgan instead of its original name, which this kit's guard reserves. The
  fifteen left-out references that the remaining text links to have a
  one-paragraph placeholder in their place, written for this kit, so an agent that follows the link
  learns the file is missing on purpose.

MIT license of `angular-developer`, as declared in its header:

```
MIT License

Copyright 2026 Google LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## writing-clearly-and-concisely

Source: https://github.com/softaworks/agent-toolkit, originally from
https://github.com/joshuadavidthomas/agent-skills, adapted from Strunk's *The Elements of Style*
(1918), which is in the public domain. Both repositories are MIT licensed (texts below).

Change made here: the copy of the Wikipedia guide "Signs of AI writing" (CC BY-SA 4.0) was
removed; the skill links to the guide online instead.

```
MIT License

Copyright (c) 2026 Leonardo Flores

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```
MIT License

Copyright (c) 2025 Josh Thomas

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
