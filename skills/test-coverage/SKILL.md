---
name: test-coverage
description: Use when writing or planning tests, configuring coverage or CI test gates, deciding what to test or exclude from coverage, and before committing to a repository that has a test suite.
---

# Tests and coverage

## A check that compares nothing looks like a check that passed

A reconciliation of a few thousand imported orders compared each order's total with the source
file. It read a field that did not exist in the source, and it skipped any order whose expected
value was missing. It printed:

> `orders with a difference: 0 of 3000`

Zero differences, because zero comparisons. That output is identical to the output of a check that
really passed, and it hid a real error in hundreds of orders. A grand total, printed by the same
script, caught it because it did not match the source. Had the script printed only "3000 created,
OK", the error would have reached production.

**The rule:** every verification counts and prints how many items it compared, and the reader
checks that number against the expected universe.

```python
print(f"COMPARED: {compared} of {len(source)} expected")
assert compared == len(source), "the check skipped records; its result is void"
```

"0 differences" without "N compared" next to it is not a result. It is silence that looks like
success.

The same trap hides in test suites. Look for:

- an `assert` inside an `if` that is never true;
- a parametrized test with an empty list of cases (green, zero runs);
- a loop over an empty collection with the `assert` inside;
- a parametrized data source that failed silently and returned nothing;
- a filter that selects nothing (a `-k` expression that matches no test). Pipelines ban it for a
  second reason, below.

## The principle

Coverage finds untested code. It does not grade the quality of the tests (Fowler,
[TestCoverage](https://martinfowler.com/bliki/TestCoverage.html)). The goal is to validate the
application against real use cases, not to meet a metric.

Aim for about 90% of the whole repository, line and branch. The number is a guard-rail against
"I have tested enough", a judgement that people and models alike make too early. It is not a
fetish:

- It need not be exactly 90%. At 85% with real tests and the rest justified (code without logic,
  trivial glue), write down why the rest stays out, and stop.
- Never close the gap with junk tests. An inflated 90% made of tests without asserts is worse than
  an honest 80%: it gives false confidence and costs maintenance. Above about 90% the gain is
  logarithmic; what the tests check matters more
  ([Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)).
- The real measure of "tested enough": bugs rarely reach production, and the team changes code
  without fear.

## Rules

1. **Run the suite before every commit in a repository that has one. Red does not commit.** No
   exception for "a tiny fix": a broken main blocks everyone, so catch it locally. Green is not
   enough either. Every change gets its own test (unit, and integration where the stack has it) in
   the same commit. A slice of work is done when its new test is green and its docs are current,
   and only then does the next slice start.

2. **Measure coverage; never estimate it.** Turn on the stack's tool: JaCoCo on the JVM, the
   coverage report of Jest, Karma or Vitest for JavaScript and TypeScript, coverage.py for Python.
   In a repository that does not measure yet, the first step is to turn measurement on and record
   the baseline. Never state a percentage without a report.

3. **A valid test:**
   - Its name describes the behaviour under test, not the method.
   - It follows given-when-then: state X and input Y produce an observable result Z (a return
     value, persisted state, an HTTP response with a body, a visible effect).
   - It tests the public API or contract, not internals, so it breaks only when a requirement
     changes, not on every refactor.
   - Code with a branch (a condition, a validation, an error) gets at least one error or edge case,
     not only the happy path.
   - An API test asserts status, body and effect, not only `200`.

4. **Forbidden tests.** Reject them in review; where they exist, rewrite them instead of adding
   more.
   - No assert: the test only runs the code
     ([AssertionFreeTesting](https://martinfowler.com/bliki/AssertionFreeTesting.html)).
   - "Not null" or "true is true" as the only check.
   - Getters, setters, `equals` or `toString` of a data object. Exclude the data object from
     coverage instead.
   - Booting the whole application context again and again only to count lines.
   - Change-detector tests: mock everything, then verify every internal call. They mirror the
     implementation, break on every refactor and catch no bugs
     ([Change-Detector Tests](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html)).
   - A huge snapshot approved without reading it.
   - An assert on the value the mock itself returned. It tests the mock, not the code.

5. **Exclusions are legitimate and governed.** Excluding what should not be tested keeps the goal
   honest.
   - Candidates: data objects and records without logic, trivial framework configuration,
     generated code (mappers, API clients, anything marked as generated), the entry-point class,
     database migrations, front-end module and environment files.
   - Each exclusion enters through a commit that says why, never "to pass the gate". An excluded
     file that gains logic leaves the exclusion.

6. **Prioritise by risk** when time is short: business rules, then API contracts (status, body,
   errors), then integrations, then edge cases from real data, then UI, then glue. The core
   algorithm whose bug costs the most gets its tests before or with its implementation. The UI
   test on a phone-sized screen moves up this order: rule 12.

7. **Mutation testing on critical modules** catches sophisticated junk tests. Use
   [PIT](https://pitest.org) in incremental mode (`withHistory`, `scmMutationCoverage`) on the JVM
   and [Stryker](https://stryker-mutator.io) with `--incremental` for JavaScript and TypeScript.
   Start it as information only. High line coverage with a low mutation score means façade tests:
   rewrite them. Make it blocking once the score is stable.

8. **Where there is no line coverage** (low-code workflows, SQL, infrastructure), the equivalent
   is a contract or scenario gate: fixtures in, asserts on the output. Every critical workflow has
   one.

9. **Coverage never grades a person or a session.** Once it becomes a personal target, Goodhart's
   law turns it into junk tests. It diagnoses the repository, nothing else.

10. **The full suite gates the deploy.** Where nobody reviews code, the CI suite is the only brake
    between a commit and production. Every repository with a deploy pipeline runs its suite before
    shipping, and a red test does not deploy.
    - Where end-to-end tests exist, the deploy job depends on them too:
      `deploy: needs: [test, e2e]`. The gates run in parallel and the deploy ships only when all
      are green. Without end-to-end tests, the deploy depends at least on the unit and
      integration suite; when end-to-end tests arrive, add them to `needs`.
    - A flaky end-to-end test may block a hotfix. Accept that, and soften it with retries in the
      runner and fast jobs: it beats a broken deploy.
    - The gate must be a job in the **same** workflow as the deploy. In GitHub Actions, `needs:`
      links only jobs of the same file. A separate "signal only" workflow puts a red mark on the
      commit and blocks nothing.

11. **Parsers of human-written text** (order notes, operator remarks, hand-filled spreadsheets)
    need fixtures from the real production corpus. Fixtures the developer invents validate the
    implementation against itself: the tests pass, and production breaks on the first real input.
    Pull real samples before writing the parser, and turn each real format into a literal test
    case. A format with no real example becomes a question to the owner, not code. The parser
    rejects loudly (a line for someone to review) instead of extracting a wrong value in silence.
    Line coverage, even above 90%, does not cover the input space.

12. **Test on a phone-sized screen first** when most users arrive on a phone. A change with UI gets
    a test at phone size, and it comes before the desktop one: in end-to-end tests, in the browser
    check and in the manual test steps. In the order of rule 6, the main flow of the screen on a
    phone joins the first group, next to the business rules. UI tested only on desktop is a
    partial delivery: say so before delivering, with what is missing.

## Never skip the suite in a pipeline

Where the suite is the only brake, no job may pass without it having run. That bans
`-DskipTests`, `-Dmaven.test.skip`, `--passWithNoTests` hiding an empty suite, `|| true` after the
test command, a selector that selects nothing (`--co`, a `-k` that matches no test), and any other
trick with the same effect. Three exceptions exist, each with all its conditions:

1. **Skipping the test run at build time.** Allowed only when an earlier `test` job in the same
   workflow ran the suite and the deploy job has `needs: [test]`. The skip avoids running
   everything twice, and a comment in the YAML says so. Without that earlier job, it is forbidden.
2. **A push that changes only documentation.** The workflow does not run when every file in the
   push is Markdown: `paths-ignore: ['**.md']` on the trigger. Any other file in the same push runs
   everything. Use it only where Markdown does not go into the artifact (check the build file or
   `Dockerfile`), with a comment in the YAML.
3. **The merge delivers what the pull request already tested.** The workflow on the main branch may
   skip building and testing only when all three hold:
   - the suite ran in the pull request, as a check the main branch's protection requires green;
   - the protection requires the branch to be up to date with main before the merge, so what was
     tested is exactly what enters;
   - the deploy ships the artifact built and tested in that pull request, verified by checksum.

   If one is missing, run everything.

## The push trigger

The default trigger for a push is `paths-ignore: ['**.md']`, with a comment pointing to this rule.
Never use a `paths:` allow-list of what goes into the artifact. A change to a file outside the list
does not run the pipeline, so a new code folder that nobody added to the list stops deploying,
and nothing warns you.

In a pull-request workflow whose suite is a required check, a path filter on the trigger blocks
the merge: the check stays pending forever. There, move the filter into a condition on the job.
A skipped job counts as green.

## Read the denominator before the percentage

High coverage in a module of entities and repositories measures little. Repository interfaces
have no body, and the coverage tool skips generated accessors, so such a module can show 100% of a
handful of lines. That number says no hand-written logic is left untested. It does not say the
entities are tested; behaviour tests cover that. Before you trust a percentage, look at how many
lines it counts.

## Sources

- Fowler: [TestCoverage](https://martinfowler.com/bliki/TestCoverage.html),
  [AssertionFreeTesting](https://martinfowler.com/bliki/AssertionFreeTesting.html)
- Google Testing Blog:
  [Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html),
  [Change-Detector Tests](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html)
- Mutation testing: [PIT](https://pitest.org), [Stryker](https://stryker-mutator.io)
