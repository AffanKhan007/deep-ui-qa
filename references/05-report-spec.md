# 05 Report specification

Read at the start of Phase 7. The report is the deliverable: it must let a busy reader see what was tested, what broke, how bad it is, what was not covered, and how to reproduce each finding.

## Contents

1. Workspace artifacts
2. Shared vocabularies
3. `meta.json`
4. `02-field-atlas.json`
5. `03-relationships.json`
6. `05-test-cases.json`
7. `06-defects.json`
8. `07-fixtures-and-config-ledger.json`
9. `08-open-questions.json`
10. Excel workbook
11. Validation rules
12. Writing style
13. Chat handoff

---

## 1. Workspace artifacts

```
qa-<app>-<timestamp>/
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
│   ├── screenshots/
│   ├── snapshots/
│   ├── network/
│   ├── console/
│   └── outputs/
├── calc/
└── QA_Report_<app>_<timestamp>.xlsx
```

Markdown files are for the agent and the human; JSON files are the source of truth for the report. Do not duplicate data by hand between them: write the JSON, then run the builder.

## 2. Shared vocabularies

Use these exact strings; the builder validates them.

**Test status**

| Status | Meaning |
|---|---|
| `Pass` | Observed and matches the oracle. |
| `Fail` | Observed, reproduced, contradicts the oracle. |
| `Blocked` | Could not execute (access, environment, missing data, forbidden action). |
| `Needs Clarification` | Oracle unclear, requirements conflict, or behaviour is ambiguous. |
| `Observation` | Noteworthy, but not a defect. |
| `Not Run` | Planned but out of time/scope; explain why. |

**Severity**: `Critical`, `High`, `Medium`, `Low`, `Enhancement`, `None`.

**Test category**: `UI & Content`, `Validation & Boundary`, `CRUD & Lifecycle`, `Business Rules & Calculation`, `Cross-Module Ripple`, `Workflow & State`, `Roles & Permissions`, `Data Volume & Search`, `Time & Dates`, `Outputs & Documents`, `Resilience & Concurrency`, `Accessibility & Locale`, `Security & Privacy`, `Other`.

**Defect type**: `Functional`, `Calculation`, `Validation`, `Workflow/State`, `Permission/Security`, `Data Integrity`, `Integration`, `UI/UX`, `Accessibility`, `Performance`, `Content/Localization`, `Other`.

**Defect status**: `Open`, `In Progress`, `Retest`, `Fixed`, `Won't Fix`, `Duplicate`, `Not a Bug`.

**Relationship type**: `enables`, `hides`, `filters`, `populates`, `computes`, `validates`, `permits`, `schedules`, `precedence`, `locks`, `notifies`, `cascades`, `duplicates`.

**Confidence**: `High`, `Medium`, `Low`.

**Open-question type**: `Question`, `Assumption`, `Limitation`, `Not Tested`, `Conflict`.

## 3. `meta.json`

```json
{
  "schema_version": "1.0",
  "app": "Acme HR",
  "url": "https://staging.example.com",
  "environment": "staging",
  "staging_confirmed": true,
  "version": "2026.10.3",
  "scope": "Payroll + correlated modules",
  "depth": "Deep",
  "module": "Payroll",
  "roles": ["Admin", "Payroll Admin", "Manager"],
  "host": "OpenCode",
  "browser_tool": "Playwright MCP",
  "viewports": ["1440x900", "390x844"],
  "locale": "en-US",
  "timezone": "Asia/Karachi",
  "started_at": "2026-11-04T09:00:00Z",
  "finished_at": "",
  "forbidden_actions": ["finalise payroll", "send email"],
  "limitations": ["No access to the Manager role", "Console logs unavailable"],
  "workspace_version": "1.0"
}
```

`staging_confirmed` must be true before any mutation. If false, the builder warns and the report should say read-only.

## 4. `02-field-atlas.json`

```json
{
  "controls": [
    {
      "id": "A-0142",
      "state_id": "S-014",
      "module": "Payroll",
      "path": "Payroll > Run > Deductions > Loan deduction",
      "label": "Loan deduction",
      "control": "currency",
      "required": "conditional",
      "default": "0.00",
      "options": [],
      "options_count": 0,
      "constraints": "min 0, max 30% of net, 2 decimals",
      "helper_text": "Capped at 30% of net pay per Settings > Loans",
      "depends_on": "Employee has an active loan",
      "affects": "Net pay; loan balance; payslip",
      "saves_how": "On Calculate",
      "roles_visible": ["Payroll Admin"],
      "tested_by": ["TC-0031"],
      "not_tested_reason": "",
      "notes": "",
      "evidence": "evidence/snapshots/S-014.html"
    }
  ]
}
```

`required`: `yes`, `no`, or `conditional: <condition>`.
`control`: one of the values listed in `02-field-atlas-and-model.md`.

## 5. `03-relationships.json`

```json
{
  "relationships": [
    {
      "id": "R-007",
      "source": "Settings > Attendance > Grace period",
      "target": "Payroll > Run > Late deductions",
      "type": "computes",
      "description": "Grace minutes reduce the late-mark count",
      "evidence": "Perturbation E-012: grace 10 -> 0 changed late count 2 -> 5",
      "confidence": "High",
      "verified_by": ["TC-0031"],
      "not_tested_reason": ""
    }
  ]
}
```

## 6. `05-test-cases.json`

```json
{
  "test_cases": [
    {
      "id": "TC-0031",
      "module": "Payroll",
      "path": "Payroll > Run > Deductions",
      "title": "Loan deduction is capped at 30% of net pay",
      "category": "Business Rules & Calculation",
      "technique": "Boundary value analysis",
      "priority": "P0",
      "reason": "Over-deduction directly underpays an employee.",
      "role": "Payroll Admin",
      "preconditions": "QA_EMP_04 has net pay 10,000 and an active loan balance of 8,000; cap is 30%.",
      "test_data": "QA_EMP_04; loan QA_LOAN_01; August 2026 run",
      "steps": [
        "Open Payroll > Run > August 2026.",
        "Add QA_EMP_04 and calculate.",
        "Open the deduction breakdown."
      ],
      "oracle": {
        "type": "Calculation + in-app policy",
        "source": "Settings > Loans > Cap = 30%; independent calculation in calc/TC-0031.py",
        "confidence": "High",
        "description": "Loan deduction must be <= 30% of net pay; expected 3,000."
      },
      "expected": "Loan deduction = 3,000.00; net pay = 7,000.00.",
      "actual": "Loan deduction = 4,800.00; net pay = 5,200.00.",
      "status": "Fail",
      "severity": "High",
      "defect_type": "Calculation",
      "correlated_modules": ["Employees", "Loans", "Reports"],
      "relationship_ids": ["R-007"],
      "atlas_ids": ["A-0142"],
      "evidence": [
        "evidence/screenshots/TC-0031_breakdown.png",
        "evidence/network/TC-0031_response.json",
        "calc/TC-0031.py"
      ],
      "suggestion": "Apply the cap after tax and other deductions; add a boundary regression test.",
      "notes": "Reproduced twice; persists after reload.",
      "executed_at": "2026-11-04T12:40:00Z"
    }
  ]
}
```

For non-fail statuses, `severity` may be `None`. For `Blocked`, `Needs Clarification`, `Observation`, `Not Run`, put the reason in `notes` and/or `actual`.

## 7. `06-defects.json`

```json
{
  "defects": [
    {
      "id": "DEF-007",
      "title": "Loan deduction exceeds the 30% cap for QA_EMP_04",
      "severity": "High",
      "type": "Calculation",
      "module": "Payroll",
      "path": "Payroll > Run > Deductions",
      "test_case_ids": ["TC-0031"],
      "environment": "staging, build 2026.10.3, Payroll Admin, en-US, UTC+5",
      "preconditions": "QA_EMP_04 net pay 10,000; loan balance 8,000; cap 30%.",
      "steps": [
        "Open Payroll > Run > August 2026.",
        "Add QA_EMP_04 and calculate.",
        "Open the deduction breakdown."
      ],
      "expected": "Loan deduction <= 3,000.00.",
      "actual": "Loan deduction 4,800.00; net pay 5,200.00.",
      "evidence": [
        "evidence/screenshots/TC-0031_breakdown.png",
        "calc/TC-0031.py"
      ],
      "impact": "Employee is underpaid; payroll cannot be finalised.",
      "likely_cause": "Cap applied to gross pay instead of net (hypothesis).",
      "suggestion": "Apply the cap after tax and other deductions.",
      "workaround": "Manually reduce the deduction before finalising.",
      "status": "Open",
      "notes": "",
      "created_at": "2026-11-04T12:45:00Z"
    }
  ]
}
```

Every `Fail` test case must have at least one defect whose `test_case_ids` includes it.

## 8. `07-fixtures-and-config-ledger.json`

```json
{
  "fixtures": [
    {
      "id": "F-004",
      "name": "QA_EMP_04_midmonth_joiner",
      "purpose": "Proration boundary",
      "created_via": "Employees > Add",
      "status": "active",
      "cleanup": "delete after payroll run; archive if payslip exists",
      "notes": ""
    }
  ],
  "config_changes": [
    {
      "id": "C-003",
      "path": "Settings > Attendance > Grace period",
      "setting": "Grace period",
      "original": "10",
      "changed_to": "0",
      "changed_at": "2026-11-04T10:12:00Z",
      "role": "Admin",
      "reason": "Perturbation E-012",
      "restored": true,
      "restored_at": "2026-11-04T10:30:00Z",
      "restored_value": "10",
      "evidence": "evidence/snapshots/E-012_before.html",
      "notes": ""
    }
  ]
}
```

If `restored` is false, `notes` must explain why and what remains changed.

## 9. `08-open-questions.json`

```json
{
  "items": [
    {
      "id": "Q-001",
      "type": "Question",
      "description": "Should a mid-month joiner accrue leave from the join date or the next month?",
      "impact": "Affects proration cases and the leave balance report.",
      "owner": "Product owner",
      "status": "Open",
      "related": ["TC-0018", "R-004"]
    }
  ]
}
```

Use `Assumption` for a decision you made to keep moving, `Limitation` for something you could not access, `Not Tested` for coverage you deliberately skipped, and `Conflict` when two oracles disagree.

## 10. Excel workbook

`build_report.py` creates a fresh workbook with these sheets:

### 10.1 Summary

A key/value block:

- App, URL, environment, version, date, depth, scope, roles, host/browser tool.
- Counts: total cases, Pass, Fail, Blocked, Needs Clarification, Observation, Not Run.
- Pass rate: `Pass / (Pass + Fail)` — do not include Blocked/Not Run in the denominator; state the formula.
- Defects by severity and status.
- Coverage: controls inventoried/tested, relationships verified, modules covered, roles covered.
- Top 5 risks/defects (title + severity).
- Limitations and open questions count.
- A note on how to read the workbook.

Include two bar charts: status counts and defect severity counts.

### 10.2 Test Cases

Columns:

`ID`, `Module`, `Path / Breadcrumb`, `Title`, `Category`, `Technique`, `Priority`, `Reason`, `Role`, `Preconditions & Test Data`, `Steps`, `Oracle (type / source / confidence)`, `Expected`, `Actual`, `Status`, `Severity`, `Defect Type`, `Correlated Modules`, `Relationships`, `Atlas Refs`, `Evidence`, `Suggestion`, `Notes`, `Executed At`.

Freeze the header, enable autofilter, wrap text, colour status and severity, add data validation dropdowns for status/severity.

### 10.3 Defects

Columns:

`ID`, `Title`, `Severity`, `Type`, `Module`, `Path`, `Test Cases`, `Environment`, `Preconditions`, `Steps`, `Expected`, `Actual`, `Evidence`, `Impact`, `Likely Cause`, `Suggestion`, `Workaround`, `Status`, `Notes`.

Colour severity. Sort by severity (Critical -> Low), then ID. This sheet contains only defects, not Passes.

### 10.4 Coverage

Three tables:

- **By module**: Module, Controls, Controls Tested, Controls Not Tested, Cases, Pass, Fail, Blocked, Needs Clarification, Observation, Not Run, Coverage %.
- **By category**: Category, Cases, Pass, Fail, Blocked, Needs Clarification, Observation, Not Run.
- **Relationships**: Total, Verified, Not Tested, Coverage %.

Coverage % is `controls tested / controls inventoried`; state the denominator.

### 10.5 Field Atlas

Columns:

`ID`, `State`, `Module`, `Path`, `Label`, `Control`, `Required`, `Default`, `Options`, `Constraints`, `Helper Text`, `Depends On`, `Affects`, `Saves How`, `Roles Visible`, `Tested By`, `Not Tested Reason`, `Notes`.

### 10.6 Relationships

Columns:

`ID`, `Source`, `Target`, `Type`, `Description`, `Evidence`, `Confidence`, `Verified By`, `Not Tested Reason`.

### 10.7 Test Data & Config

Two tables:

- **Fixtures**: ID, Name, Purpose, Created Via, Status, Cleanup, Notes.
- **Config changes**: ID, Path, Setting, Original, Changed To, Changed At, Role, Reason, Restored, Restored At, Restored Value, Evidence, Notes.

Highlight unrestored config changes in red/amber.

### 10.8 Open Questions

Columns:

`ID`, `Type`, `Description`, `Impact`, `Owner`, `Status`, `Related`.

---

## 11. Validation rules

The builder refuses to produce a final report when an **error** exists; `--allow-incomplete` produces a draft with a visible banner.

**Errors**

- JSON is unreadable or missing required top-level keys.
- Duplicate IDs within an artifact.
- Unknown status, severity, category, defect type, relationship type, confidence, or question type.
- A test case is missing `id`, `title`, `status`, `expected`, or `actual`.
- A `Pass` has an empty `actual`.
- A `Fail` is missing `severity`, `defect_type`, `expected`, `actual`, or evidence.
- A `Fail` has no linked defect with a non-empty `suggestion`.
- A defect is missing `title`, `severity`, `type`, `expected`, `actual`, `evidence`, or `suggestion`.
- A referenced ID (atlas, relationship, test case) does not exist.
- A config change with `restored: false` has no explanatory `notes`.
- A likely credential or private key is found in a text artifact.

**Warnings**

- `staging_confirmed` is not true.
- A control has neither `tested_by` nor `not_tested_reason`.
- A relationship has neither `verified_by` nor `not_tested_reason`.
- A `Pass` has no evidence.
- A `Blocked`, `Needs Clarification`, `Observation`, or `Not Run` case has no explanatory note.
- A config change is not restored.
- A module has no cases.
- A role has no permission case.
- The scope says a module is in scope but the atlas has no controls for it.
- An `Assumption` or `Conflict` remains open.

Warnings do not block the report, but the Summary lists them and the handoff must mention them.

## 12. Writing style

- **Specific titles.** Entity + condition + wrong outcome.
- **Expected vs actual in parallel.** Same units, same precision, same field names.
- **Numbers with units and precision.** `3,000.00`, `30%`, `2026-08-31`, not "about 3k".
- **No vague words.** "Wrong", "broken", "issue" are placeholders; replace them with the observed behaviour.
- **No speculation as fact.** Label likely causes as hypotheses.
- **No credentials or personal data.** Redact evidence; use `QA_` data.
- **No screenshots pasted into the workbook.** Use paths; the workbook stays small.
- **No inflated counts.** Report what you ran, not what you planned.

## 13. Chat handoff

Keep the chat summary under ~20 lines:

```
Scope: Payroll + correlated Employees, Leave, Loans, Reports. Deep depth.
Coverage: 34 screens, 212 controls, 118 cases, 3 roles. 96 Pass, 14 Fail, 5 Blocked, 2 Needs Clarification, 1 Observation.
Top defects:
1. [Critical] Loan cap applied to gross, not net (DEF-007, TC-0031)
2. [High] Approved timesheet can still be edited by manager (DEF-009, TC-0044)
3. [Medium] Export ignores department filter (DEF-012, TC-0051)
Not covered: Manager role (no credentials), payroll finalisation (forbidden), mobile layout (out of scope).
Open questions: 3 (see Open Questions sheet).
Config restored: 12/12. Fixtures: 6 created, 5 deleted, 1 archived.
Report: qa-acme-hr-20261104/QA_Report_Acme_HR_20261104.xlsx
```

Point to the workbook; do not paste its contents. Mention the biggest risk even if it is not a defect (for example an untested payroll path).
