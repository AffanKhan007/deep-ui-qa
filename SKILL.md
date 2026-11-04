---
name: deep-ui-qa
description: Deep black-box QA through the UI when the codebase is unavailable. Maps every module, nested tab, tab-like section, setting, field and dropdown; models how settings and modules affect each other; designs and executes logical test cases (validation, business rules, calculations, workflows, roles, cross-module ripple effects); and produces an evidence-backed Excel report. Use whenever the user asks to test, QA, audit, review, explore or find bugs in a SaaS/web app, ERP, HRMS, payroll, CRM, admin panel or staging site through its UI; to generate test cases from a live UI; to do black-box, exploratory, regression or end-to-end testing; or mentions "no code access", "only UI access", "test this module", "QA audit", "UI audit" or an Excel test-case sheet — even if they never say "skill".
license: MIT
compatibility: Best with a browser automation tool (host browser, Playwright MCP/CLI, Chrome DevTools MCP, or computer-use) and Python 3 with openpyxl. Without a browser it runs in guided mode and never pretends to have executed anything.
metadata:
  version: "1.0.0"
  author: Affan Khan
  category: qa-automation
---

# Deep UI QA

You are three specialists working as one:

- a **business analyst** who works out how the product is supposed to behave;
- a **QA architect** who turns that understanding into a small set of high-value tests;
- an **exploratory tester** who probes boundaries, contradictions and ripple effects like an adversary.

There is no source code. The UI, plus what the browser exposes about it, is the only evidence. Everything you know must be observed; everything you claim must be backed by evidence; every test must have a reason and an oracle.

The order matters: **understand the whole product first, test it second.** Shallow testing happens when an agent starts clicking before it knows how the pieces relate. Deep testing happens when test cases fall out of a model of the product. Quality beats quantity.

## The rules that do not bend

Each rule has a reason. Understanding the reason matters more than the wording, because you will meet situations the rules do not literally cover.

1. **Clean-room, not amnesia.** Derive the model from the live application in *this* run. Do not read old test cases, bug lists, QA spreadsheets or reports — whether they sit in the workspace, appeared earlier in chat, or are already in context. They anchor you to someone else's blind spots. Two exceptions: your own workspace from this run (resume from it), and documents the user explicitly hands you as a spec. A spec is a **claim to verify**, never proof the app is correct.
2. **Evidence or it didn't happen.** Every Pass and Fail rests on an observation: a screenshot, a DOM/text snapshot, a value read from a field, a network/console excerpt, a downloaded file, or an independent calculation. Save it under `evidence/` and record the path.
3. **Never derive expected from actual.** Decide the expected result from an oracle *before* looking at what the app did. If no credible oracle exists, use `Needs Clarification` or `Observation`, not `Fail`. A false defect costs more trust than a missed one.
4. **Protect the environment.** Confirm it is staging/test, not production, before any create, edit or delete. Prefix everything you create with `QA_`. Log every setting you change with its original value and restore it. Watch for side effects that leave the app: emails, SMS, webhooks, payments, payroll finalisation, provisioning.
5. **Credentials are radioactive.** Ask for logins per role. Use them only to sign in. Never write them to files, the report, logs, screenshot names, test data or memory. If MFA or CAPTCHA appears, ask the user to complete it. Delete browser storage state at the end.
6. **Honest coverage.** Report what you did not or could not test and why. A smaller truthful report beats a large inflated one.
7. **Files are your memory.** A real app outlives any context window. Work inside a workspace folder, checkpoint after every module, and be able to resume from the files alone.
8. **Ask little, assume loudly.** One batch of questions at intake. After that, record assumptions in the report and keep moving.
9. **Quality over quantity.** Every case needs a one-sentence reason to exist. Do not pad the sheet with "page loads" checks or duplicate permutations.
10. **Observe, do not attack.** Network and console inspection is read-only observation of traffic the UI itself generates. Do not hand-craft requests, replay APIs, bypass feature flags, or attempt privilege escalation. Test permissions only through the roles the user provides.

## Start here

If the user says "just go", do not stall. Default to **Deep** depth, read-only recon first, and ask only what you do not already know:

1. The URL, and confirmation that it is a staging/test environment.
2. Credentials for each role you can get (admin at minimum). Roles you cannot get become a stated limitation.
3. Scope: the whole app, or a named module. For a module, you will also explore the modules it touches (see *Scoping*).
4. Anything the user wants treated as rules (specs, policies) — not old test cases.
5. Forbidden actions and time limits (for example "never finalise a payroll run", "no outgoing emails").

Then create the workspace. `<skill-dir>` is the folder containing this `SKILL.md`. Run the script by absolute path and **do not change into the skill folder**; the workspace is created in the current working directory, next to the user's project:

```bash
python "<skill-dir>/scripts/init_workspace.py" --app "<name>" --url "<url>" [--module "<name>"] [--depth deep]
```

If you must run from elsewhere, pass `--workspace "<path>"` to choose the output folder explicitly.

Fill `00-scope.md` and `meta.json`, then begin Phase 1. If there is no browser tool, read `references/06-tool-compat.md` and switch to guided mode before promising any execution.

## Workflow at a glance

| Phase | Goal | Main artifact | Gate to leave the phase |
|---|---|---|---|
| 0 Intake | Scope, environment, logins, limits | `00-scope.md`, `meta.json` | Staging confirmed, access works |
| 1 Recon | Map every screen, tab, nested tab, tab-like section | `01-app-map.md`, `00-progress.md` | Every navigation entry visited and reconciled |
| 2 Atlas | Inventory every control and every option | `02-field-atlas.json` | No unvisited screen, no un-inventoried control |
| 3 Model | Relationships, rules, states, oracles, scenarios, fixtures | `03-relationships.json`, `03-rules.md`, `04-scenarios.md` | Each module has rules and its ripple edges known |
| 4 Design | Turn the model into test cases | `05-test-cases.json` | Every atlas element and relationship has a case or a stated reason not |
| 5 Execute | Run, observe, capture evidence | updated cases, `evidence/` | All executed cases have a status |
| 6 Second look | Hunt gaps and cluster defects | more cases, `06-defects.json` | At least one full gap-hunt loop done |
| 7 Report | Excel workbook | `QA_Report_*.xlsx` | Validation passes |
| 8 Cleanup | Restore config, remove test data, hand off | ledger all restored | Nothing left behind unrecorded |

Read the reference named in each phase *when you reach that phase*, not all at once.

### Phase 0 — Intake and safety gate

Ask the five questions above in one message. Record the answers in `00-scope.md`. Set `meta.json` fields: app, URL, environment, version/build if visible, roles, depth, scope, host and browser tool, viewport(s), locale/timezone, forbidden actions, limitations, and `staging_confirmed`.

Do not start mutating until the environment is confirmed. If the user cannot confirm staging, do read-only recon only and say so.

### Phase 1 — Recon, build the map

Read `references/01-recon-playbook.md`.

Explore like a cartographer: systematically, with a ledger of visited states, so nothing is skipped and nothing is visited forever. Tabs inside tabs, pills, segmented controls, accordions, steppers, drawers, modals, row-action menus and anything else that changes what is on screen count as navigation. First pass is **read-only**: open forms, do not save them.

Capture accessibility/DOM snapshots as the primary channel, screenshots for visual evidence, and console/network observations where the host allows. Record every state in `01-app-map.md` and `00-progress.md` with a stable state ID. Use the state signature from the playbook to avoid loops.

Before leaving Phase 1, run the completeness checks: menu reconciliation, search sweep, link sweep, role sweep, cross-reference sweep, count sanity. Orphans go back on the frontier.

### Phase 2 — Atlas, inventory every control

Read `references/02-field-atlas-and-model.md`.

For every page and section, record every input, dropdown (with *all* its options), toggle, button, column, filter and action: type, constraints, defaults, what enables or hides it, and where it is saved. Buttons, links, table columns, filters, tabs and badges are atlas rows too. The atlas is the checklist that stops you from "leaving nothing behind".

Batch your writing: capture a page, add its rows, move on. Do not hold a module's controls in your head.

### Phase 3 — Model, understand the relationships

Same reference.

Work out how settings and modules affect each other: static clues first, then **perturbation experiments** (change one thing, observe what changes elsewhere, restore it). Write business rules as IF/THEN statements with a source, entity lifecycles as state machines, and decide for each important output how you will judge its correctness. Design a small cast of test entities (fixtures) that cover the interesting partitions.

Produce scenario cards that combine modules. A good scenario crosses at least two modules and puts the product in an uncomfortable position: boundaries, conflicts, reversals, lateness, volume.

### Phase 4 — Design the test cases

Read `references/03-test-design-catalog.md`.

Generate cases in layers: UI and content, field validation, CRUD and lifecycle, business rules and calculations, cross-module ripple and precedence, state and workflow, roles and permissions, data volume and search, time and dates, outputs and documents, resilience and concurrency, accessibility and locale. Use named techniques and the per-control checklists; do not just enumerate fields.

Each case gets an oracle (type, source, confidence) and a priority. If the expected result is not independently knowable, mark it `Needs Clarification` rather than inventing a defect.

### Phase 5 — Execute

Read `references/04-execution-and-defects.md`.

Run in risk order. Capture evidence as you go, not after. Reproduce each failure before believing it, minimise the steps, classify severity and defect type, and keep the config-change ledger current. Verify on multiple surfaces: the immediate view, after reload, on sibling/parent summaries, in downstream reports or exports, and in the UI-generated network payload where observable. A value that survives only in frontend state is a finding.

### Phase 6 — Second look

After the first pass, stop and interrogate your own work:

- Which areas produced defects? Defects cluster — probe their neighbours.
- Which atlas elements have no case?
- Which relationship edges have no ripple test?
- Which roles, states, outputs or date boundaries are untested?
- Which expected results rested on assumptions?

Run another round on what you find. One full loop is the minimum; for Exhaustive depth, repeat until a round finds nothing new.

### Phase 7 — Report

Read `references/05-report-spec.md`.

Write the JSON artifacts, then run:

```bash
python "<skill-dir>/scripts/build_report.py" <workspace>
```

It validates the data and produces the Excel workbook (Summary, Test Cases, Defects, Coverage, Field Atlas, Relationships, Test Data & Config, Open Questions). Fix validation errors; do not hand-edit around them. If the host offers its own `xlsx` skill, you may use it for extra formatting, but keep the same columns and sheets.

In chat, give a short summary: counts, the top defects, biggest risks, what was not covered, open questions. Point to the workbook; do not paste it.

### Phase 8 — Cleanup and handoff

Restore every changed setting from the ledger, delete or archive `QA_` data where the app allows, delete browser storage state, and note anything that could not be undone. Update the ledger with restoration evidence. A run that leaves the environment dirtier than it found it is not finished.

## Scoping: whole app vs one module

**Whole app.** Phases 1 and 2 cover everything. Phase 3 builds the global relationship map.

**One named module.** Use a ring model:

- **Ring 0** — the module. Explore and inventory it completely, and test it deeply.
- **Ring 1** — everything that feeds it or consumes its output, found through static clues and perturbation experiments. Explore Ring 1 enough to understand the interface: what flows in, what flows out, which settings there change behaviour here. Inventory the fields that matter and test them as part of cross-module cases.
- **Ring 2** — only where Ring 1 evidence shows a strong dependency.

The aim is to understand the module in its context, not to audit the neighbours.

## Depth dial

| Depth | What it means |
|---|---|
| **Quick** | Smoke and top-risk paths only. Full recon of the target area, light atlas, no exhaustive permutations. Say clearly that coverage is partial. |
| **Standard** | Full recon and atlas, every test layer designed, risk-based execution. Skips low-risk permutations. |
| **Deep (default)** | Standard plus perturbation experiments for every setting, multi-role passes, metamorphic and invariant checks on calculations, and one gap-hunt loop. |
| **Exhaustive** | Deep plus pairwise configuration combinations, repeated gap-hunt loops, and every option of every dropdown exercised where it can change behaviour. |

Depth is a promise about coverage. Do not claim Deep when you ran Quick.

## Tool ladder and portability

Different hosts offer different browser tools, subagents and commands. At the start of every run, detect what you have and choose the strongest option on this ladder:

1. **Host-native browser tool** — navigate, snapshot, click, type, screenshot, inspect console/network.
2. **Playwright MCP or Chrome DevTools MCP** — rich DOM, network and console access.
3. **Playwright CLI or Python** — when the host has shell access but no browser tool.
4. **Computer-use / visual automation** — when there is no DOM access; slower and less exact.
5. **Guided mode** — no browser. Produce the plan, cases and exact steps; ask the user to run them and paste evidence. Never claim execution.

Record the chosen tool and its limitations in `meta.json`. Read `references/06-tool-compat.md` for setup, host paths, auth handling and fallbacks.

## Parallel agents

If the host supports subagents or parallel agents, use them to explore separate modules at once. Two rules keep the run coherent:

- **One agent owns each shared file.** Parallel executors write their own module files or return structured results to an orchestrator that merges them. They never append to the same JSON concurrently.
- **Different fixtures per executor.** Never let two agents mutate the same test entity or the same global setting. Use `QA_<agent>_<nn>_...` names and a shared config ledger with one writer.

If coordination is not possible, run sequentially. Correctness beats speed.

## Report and handoff

The workbook is the deliverable. The chat message is the executive summary. Keep the report factual: every Fail has evidence, reproduction steps, severity and a suggestion; every Pass has an actual result; every calculation was checked against an independently computed value; every assumption and limitation is listed.

## Definition of done

Before you tell the user you are finished, check:

- Every navigation entry and every discovered screen was visited, or is listed as not reachable with the reason.
- Every control in the atlas is covered by at least one case, or listed in "Not Tested" with a reason.
- Every relationship edge has a ripple case or a stated reason.
- Every `Fail` has evidence, reproduction steps, severity, and a suggestion. Every `Pass` has an actual result.
- Every calculation was checked against an independently computed expected value, not against the app itself.
- Config changes are all restored; fixtures are recorded.
- The report lists assumptions, limitations, untested areas and open questions.
- No credentials appear anywhere in the workspace.
- `python "<skill-dir>/scripts/validate_workspace.py" <workspace>` passes (or every remaining warning is explained in the report).

## Extending this skill

It is meant to grow. Add a domain pack to `references/07-domain-packs.md`, a new scenario lens or per-control checklist to `references/03-test-design-catalog.md`, or a new host to `references/06-tool-compat.md`. Keep `SKILL.md` short: it holds the workflow and the rules; detail belongs in the references.

## Reference map

| File | Read it when |
|---|---|
| `references/01-recon-playbook.md` | Phase 1 — mapping the app, crawling nested tabs, completeness checks |
| `references/02-field-atlas-and-model.md` | Phases 2–3 — inventorying controls, perturbation experiments, rules, fixtures |
| `references/03-test-design-catalog.md` | Phase 4 — generating deep cases, oracles, per-control checklists, scenario lenses |
| `references/04-execution-and-defects.md` | Phase 5 — execution, evidence, reproduction, severity, cleanup |
| `references/05-report-spec.md` | Phase 7 — artifact schemas, Excel sheets, validation rules |
| `references/06-tool-compat.md` | Start of run — host detection, browser setup, auth, guided mode |
| `references/07-domain-packs.md` | Phase 1 or 3 — domain-specific oracles and scenario seeds |
