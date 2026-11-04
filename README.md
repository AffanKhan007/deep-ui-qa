# Deep UI QA

**Black-box QA that thinks before it clicks.**

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-SKILL.md-1F3864)](https://agentskills.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![Works with](https://img.shields.io/badge/Works_with-Claude_Code_%7C_OpenCode_%7C_Codex_%7C_Cursor_%7C_Windsurf-548235)](#installation)

`deep-ui-qa` turns an AI agent into a disciplined black-box QA team for web apps you can only reach through the UI. It maps the product before testing it, models how modules and settings affect each other, designs tests with real oracles, executes them in a real browser, and produces an evidence-backed Excel report.

It is built for the messy reality of SaaS, ERP, HRMS, payroll, CRM, admin panels and staging sites: deeply nested tabs, settings that silently change other modules, calculations with no visible formula, roles that see different screens, and no source code.

---

## Why this exists

Most "AI QA" prompts produce a long list of shallow checks: open the page, click the button, confirm it exists. That is not testing. It misses the defects that matter — the loan deduction that ignores its cap, the approval that can still be edited after sign-off, the export that ignores the active filter, the setting that changes history retroactively.

Deep UI QA is built around a different order:

> **Understand the product first. Design tests from the model. Execute with evidence. Report honestly.**

The skill is deliberately not a brittle auto-crawler. A generic crawler can click every button and still understand nothing. The agent maps the app, reasons about what should happen, and then uses browser automation to prove it.

---

## What it does

- **Maps every screen** — modules, tabs, nested tabs, pills, accordions, wizards, drawers, modals, row actions and pseudo-tabs that do not change the URL.
- **Inventories every control** — every field, dropdown option, toggle, button, column, filter and computed output, with constraints, defaults, dependencies and save behaviour.
- **Models the product** — cross-module relationships, precedence rules, state machines, effective dates, roles and outputs.
- **Runs perturbation experiments** — change one setting, diff the watch set, restore it, and record the edge with evidence.
- **Designs deep tests** — validation boundaries, calculations, CRUD lifecycles, workflow locks, permissions, temporal edges, data volume, exports, concurrency, accessibility and localization.
- **Executes in a real browser** — via the host's browser tool, Playwright MCP, Chrome DevTools MCP, Playwright Python, or guided mode when no browser exists.
- **Verifies on multiple surfaces** — immediate view, after reload, sibling summaries, downstream reports, exports, audit logs and UI-generated network payloads.
- **Produces a validated Excel report** — Summary, Test Cases, Defects, Coverage, Field Atlas, Relationships, Test Data & Config, Open Questions.
- **Cleans up** — restores config changes, removes `QA_` fixtures, deletes auth state, and records anything that could not be undone.

---

## What makes it different

| Common approach | Deep UI QA |
|---|---|
| Crawl and click every element | Map the product, then design tests from a model |
| Expected result copied from the app | Oracle chosen before the actual result; independent calculation for numbers |
| "Page loads" cases | Cases with a reason, a boundary, a risk and a checkable oracle |
| One admin account | Role and permission matrix, data scope, server-side enforcement |
| Test the form | Test the lifecycle, the ripple effects and the outputs |
| Trust the first screen | Reload persistence, cross-surface consistency, exports and audit logs |
| Inflated pass counts | Honest statuses: Pass, Fail, Blocked, Needs Clarification, Observation, Not Run |
| Leave the environment dirty | Config ledger, `QA_` fixtures, restoration evidence |
| Hand-made spreadsheet | Schema validation, coverage calculations, styled workbook with charts |

---

## Workflow

| Phase | What happens | Artifact |
|---|---|---|
| **0 Intake** | Scope, staging confirmation, roles, rules, forbidden actions | `00-scope.md`, `meta.json` |
| **1 Recon** | Map every screen, tab, nested tab and overlay; prove completeness | `01-app-map.md`, `00-progress.md` |
| **2 Atlas** | Inventory every control and every option | `02-field-atlas.json` |
| **3 Model** | Relationships, rules, state machines, oracles, fixtures, scenarios | `03-relationships.json`, `03-rules.md`, `04-scenarios.md` |
| **4 Design** | Turn the model into layered test cases | `05-test-cases.json` |
| **5 Execute** | Run in risk order, capture evidence, reproduce failures | updated cases, `evidence/` |
| **6 Second look** | Hunt gaps, cluster defects, probe neighbours | more cases, `06-defects.json` |
| **7 Report** | Validate and build the Excel workbook | `QA_Report_*.xlsx` |
| **8 Cleanup** | Restore settings, remove fixtures, hand off | restored ledger |

Depth dial: **Quick**, **Standard**, **Deep** (default), **Exhaustive**. A module can be scoped with a ring model: Ring 0 is the module, Ring 1 is what feeds or consumes it, Ring 2 only where evidence demands it.

---

## Installation

### Requirements

- **Python 3.10+** with `openpyxl` for the report builder.
- A **browser automation tool** for execution: the host's native browser, Playwright MCP, Chrome DevTools MCP, or Playwright Python.
- No browser? The skill switches to **guided mode**: it produces an execution-ready plan and analyses the evidence you provide. It never pretends to have executed anything.

```bash
pip install -r requirements.txt
# Optional, only if you want Playwright Python instead of a host browser:
pip install playwright && playwright install chromium
```

### One-command install

```bash
git clone https://github.com/AffanKhan007/deep-ui-qa.git
cd deep-ui-qa

# User-level install (available in every project)
./install.sh --global

# Project-level install (committed with the repo)
./install.sh --project
```

Windows PowerShell:

```powershell
git clone https://github.com/AffanKhan007/deep-ui-qa.git
cd deep-ui-qa

.\install.ps1 -Scope Global
# or
.\install.ps1 -Scope Project
```

Install for a specific host:

```bash
./install.sh --global --host claude
./install.sh --global --host opencode
./install.sh --global --host codex
./install.sh --global --host cursor
./install.sh --global --host windsurf
./install.sh --global --host gemini
./install.sh --global --host copilot
```

The default is the portable `.agents/skills/` location. See [references/06-tool-compat.md](references/06-tool-compat.md) for host paths and setup details.

### Manual install

Copy `SKILL.md`, `references/` and `scripts/` into a folder named `deep-ui-qa` inside your host's skills directory. The folder name must match the `name` field in `SKILL.md`. Start a new session so the host discovers it.

```bash
mkdir -p ~/.config/opencode/skills/deep-ui-qa
cp -R SKILL.md references scripts ~/.config/opencode/skills/deep-ui-qa/
```

---

## Usage

### Full application audit

> Use `deep-ui-qa` to audit `https://staging.example.com`. It is staging. Login: `qa_admin@example.com` / the password I will send separately. Scope: whole app. Forbidden: finalise payroll, send email, invite users. Depth: Deep. Produce the Excel report.

### Targeted module with correlated modules

> Use `deep-ui-qa` on the **Payroll** module of `https://staging.example.com`. Also trace and test the upstream settings in **Employees**, **Leave**, **Loans** and **Attendance**, and the downstream **Reports** and **Payslips**. I have admin and payroll-admin logins; no manager login. Generate the report.

### With your own business rules

> Use `deep-ui-qa` on the **Subscription Billing** module. Verify these rules:
> 1. Mid-month upgrades prorate by exact calendar days in the active month.
> 2. A tax-exempt customer must show zero VAT on draft invoices, but paid invoices must not change.
> 3. A credit note cannot exceed the original invoice.
> Test the happy paths, retroactive changes and boundaries, then produce the report.

### No browser available

> Use `deep-ui-qa` in guided mode. I cannot give you a browser, but I can run steps and send screenshots. Build the recon plan, test cases and exact execution sheet first.

The skill asks only for what it does not already know. Credentials are used only to sign in and are never written to files, reports, logs or screenshots.

The QA workspace is created in your current project directory, not inside the installed skill folder. The agent runs the bundled scripts by absolute path from the skill folder, so it works the same whether the skill is installed globally or per project.

---

## What you get

A workspace with structured artifacts and an Excel workbook:

```
qa-acme-hr-20261104-1430/
├── 00-scope.md
├── 00-progress.md
├── meta.json
├── 01-app-map.md
├── 02-field-atlas.json
├── 03-relationships.json
├── 03-rules.md
├── 04-scenarios.md
├── 05-test-cases.json
├── 06-defects.json
├── 07-fixtures-and-config-ledger.json
├── 08-open-questions.json
├── evidence/
├── calc/
└── QA_Report_Acme_HR_20261104.xlsx
```

The workbook contains:

| Sheet | Purpose |
|---|---|
| **Summary** | Executive counts, pass rate, coverage, top defects, limitations, charts |
| **Test Cases** | Full execution record with oracle, expected vs actual, status, evidence |
| **Defects** | Triage view: severity, reproduction, impact, likely cause, suggestion, workaround |
| **Coverage** | Module, category, relationship and role coverage, with gaps visible |
| **Field Atlas** | Every control and option, with tested-by links or a stated reason not tested |
| **Relationships** | Source -> target correlation matrix with confidence and verification |
| **Test Data & Config** | Fixtures and every setting change, including restoration status |
| **Open Questions** | Questions, assumptions, limitations, conflicts and deliberately untested areas |

The report builder **validates before writing**. A `Fail` without evidence, a missing linked defect, an unrestored setting without explanation, or a possible credential blocks the final report. Use `--allow-incomplete` only for a clearly marked draft.

---

## Repository structure

```
deep-ui-qa/
├── SKILL.md                       # Entry point: rules, workflow, definition of done
├── references/
│   ├── 01-recon-playbook.md       # Mapping, nested tabs, state signatures, completeness
│   ├── 02-field-atlas-and-model.md # Atlas, perturbation experiments, rules, fixtures
│   ├── 03-test-design-catalog.md  # Layers, techniques, per-control checklists, deep lenses
│   ├── 04-execution-and-defects.md# Evidence, multi-surface checks, severity, cleanup
│   ├── 05-report-spec.md          # JSON schemas, Excel sheets, validation rules
│   ├── 06-tool-compat.md          # Hosts, browser setup, auth, guided mode
│   └── 07-domain-packs.md         # SaaS, HR/payroll, finance, e-commerce, CRM, support, scheduling
├── scripts/
│   ├── qa_common.py               # Shared constants, validation, coverage
│   ├── init_workspace.py          # Create a workspace with all artifacts
│   ├── validate_workspace.py      # Validate before reporting
│   └── build_report.py            # Build the styled Excel workbook
├── tests/
│   ├── check_skill.py             # Frontmatter and referenced-file checks
│   └── smoke_test.py              # End-to-end workspace -> validation -> workbook test
├── evals/
│   └── evals.json                 # Realistic prompts for manual/agent evaluation
├── install.sh
├── install.ps1
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── README.md
├── .gitattributes
└── .github/workflows/validate.yml
```

---

## Design principles

1. **Model before tests.** A test case that falls out of a product model is deep; a click-through checklist is not.
2. **Oracle before actual.** Expected results come from a spec, in-app text, domain rule, independent calculation or invariant — never from the app's own output.
3. **Evidence or it didn't happen.** Every Pass and Fail has an observation saved under `evidence/`.
4. **Perturb, don't guess.** When the UI will not explain a setting, change it, diff the watch set, and restore it.
5. **Verify on multiple surfaces.** Reload, sibling summaries, downstream reports, exports, audit logs and UI-generated payloads.
6. **Honest coverage.** Blocked, Needs Clarification, Observation and Not Run are first-class statuses.
7. **Cleanup is part of the test.** A run that leaves the environment dirtier than it found it is not finished.
8. **Structured artifacts, validated report.** The Excel is generated from JSON that has been checked, not hand-assembled.

---

## Limitations

- **Not a security audit.** It observes what the UI exposes; it does not scan, exploit, fuzz APIs or attempt privilege escalation.
- **Not a load test.** It can note slow screens, but it is not a performance testing tool.
- **Not a replacement for code review.** It infers behaviour from the outside.
- **Browser coverage varies.** Canvas, cross-origin iframes, shadow DOM and virtualised tables may be partially inaccessible; the skill records the limitation instead of guessing.
- **Statutory rules vary.** Tax, payroll and compliance rates must be confirmed for the country and year.
- **No magic crawler.** The agent maps the app deliberately; a generic crawler would create false confidence.
- **Report quality depends on evidence discipline.** The validator catches structural gaps, not bad judgment.

---

## Development

```bash
python -m py_compile scripts/*.py tests/*.py
python tests/check_skill.py
python tests/smoke_test.py
```

The smoke test creates a temporary workspace, writes a small valid dataset, validates it, builds the workbook and checks the expected sheets. CI runs it on Linux and Windows.

Contributions are welcome: add a domain pack, a test lens, a per-control checklist, or a host path. Keep `SKILL.md` short; detail belongs in `references/`.

---

## License

MIT. See [LICENSE](LICENSE).
