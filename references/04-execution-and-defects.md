# 04 Execution and defects

Read at the start of Phase 5. Recon and design are worthless if execution is sloppy: evidence gets lost, failures are not reproduced, and the environment is left dirty.

## Contents

1. Pre-flight checklist
2. Execution order
3. Evidence capture protocol
4. Multi-surface verification
5. Reproducing a failure
6. Severity and defect type
7. Writing a defect
8. False positives and honest statuses
9. The config-change ledger
10. Cleanup
11. Parallel execution
12. Stop conditions

---

## 1. Pre-flight checklist

Before the first mutating action:

- [ ] `meta.json` says staging/test and `staging_confirmed` is true.
- [ ] The URL, role, tenant/workspace and build/version are recorded.
- [ ] The browser tool works; snapshot, screenshot, console and network channels are known.
- [ ] Forbidden actions from `00-scope.md` are understood.
- [ ] Test fixtures are named `QA_...` and recorded in the ledger.
- [ ] A baseline snapshot of the watch set is saved (lists, summaries, dashboards, reports).
- [ ] The config ledger is ready; every setting you may change is listed.
- [ ] Outgoing side effects are identified: email, SMS, webhooks, payments, invitations, provisioning.
- [ ] You know how to restore or delete everything you are about to create.
- [ ] Credentials are in memory only, not in a file or shell history.

If any of the first four is missing, stop and fix it before mutating.

## 2. Execution order

Run in risk order, not in menu order:

1. **Smoke** the target scope: login, main navigation, one create/read/update path, one report. This proves the environment is usable.
2. **P0 cases**: money, security, data loss, compliance, complete blockers.
3. **P1 cases**: core workflows, high-frequency paths, important calculations, roles.
4. **P2 cases**: secondary flows, validation edges, cross-module ripple, outputs.
5. **P3 cases**: cosmetic, rare configuration, low-impact content.

Within a module, group cases by fixture and state so you do not recreate the same data repeatedly. But do not let grouping hide a cross-module case: run it while the relevant state exists.

After each module, update `00-progress.md` and the config ledger. Do not batch updates to the end.

## 3. Evidence capture protocol

For every executed case, capture enough that a stranger can verify the result without rerunning it.

| Evidence | When | Naming |
|---|---|---|
| Screenshot | Every Fail; key Passes; visual checks | `evidence/screenshots/TC-0031_before.png` |
| DOM/text snapshot | Every Fail; forms and lists | `evidence/snapshots/TC-0031.html` or `.txt` |
| Network excerpt | When the UI reveals a relevant payload/status | `evidence/network/TC-0031.json` |
| Console excerpt | When there is an error or warning | `evidence/console/TC-0031.log` |
| Downloaded output | Exports, PDFs, CSVs, documents | `evidence/outputs/TC-0031.xlsx` |
| Independent calculation | Any calculation case | `calc/TC-0031.py` plus its output |
| Config change | Any setting changed | Ledger row with original and restored values |

Rules:

- Capture **before and after** for state changes when the before state matters.
- Include the role, viewport, locale and timestamp in the case or filename metadata.
- Redact personal data and secrets; never put a password in a screenshot or log.
- Store images on disk; do not paste large images into chat or the report.
- For a Fail, capture the exact error text, the value shown, and the step that produced it.
- For a Pass, capture the actual result, not just a green checkmark.
- If evidence cannot be captured, say so and downgrade confidence.

## 4. Multi-surface verification

A value can be right on one screen and wrong everywhere else. For important results, verify these surfaces where they exist:

1. **Immediate view** — the form, toast, or detail page right after the action.
2. **After reload** — `page.reload()` or re-open the record. Confirms backend persistence, not frontend state.
3. **Sibling/parent summary** — list row, summary card, dashboard widget, counter.
4. **Downstream module** — the report, payroll run, invoice, analytics view that consumes the value.
5. **Export/document** — PDF, Excel, CSV, email preview, print view.
6. **Audit log** — who changed what, old and new value.
7. **UI-generated network payload** — read-only observation of the response the UI itself received. Do not craft requests.

Record which surfaces you checked. If a surface does not exist, say so. If it exists but you could not access it, mark the case `Blocked` or note the limitation.

### Reload persistence

The most common silent defect in SPAs is a value that looks saved but only lives in frontend state. Always reload after a save that matters, and compare. If the value disappears, that is a Fail with high severity, not a UI glitch.

### Cross-surface consistency

For one important number, compare detail, list, summary, report, export and notification. Differences in value, rounding, formatting, effective date or filtering are findings. Record all surfaces in the case.

## 5. Reproducing a failure

Before writing a defect:

1. Reproduce it once more from a clean state (reload, re-login if needed).
2. Minimise the steps; remove anything that is not necessary.
3. Check whether it depends on the fixture, role, browser, viewport, locale, time or config.
4. Try a second record or a second role to see whether it is general or data-specific.
5. Check whether a stale cache, an earlier failed step, or a test-data mistake explains it.
6. If it is intermittent, record the frequency and conditions; do not call it confirmed.

If it does not reproduce, the status is `Observation` or `Needs Clarification` with the evidence, not `Fail`. Flakiness itself can be a finding; describe it honestly.

## 6. Severity and defect type

Severity is about impact, not how annoying the bug is to the tester.

| Severity | Meaning | Examples |
|---|---|---|
| **Critical** | Blocks the business or risks money, security, legal or data loss; no workaround | Payroll net pay wrong; unauthorized data access; irreversible data loss; cannot complete checkout |
| **High** | Major workflow or calculation broken; workaround is painful | Approval stuck; invoice total wrong in a common case; role can edit what it should not |
| **Medium** | Real functional defect with a reasonable workaround, or a significant edge case | Filter count wrong; export missing a column; validation allows a bad value |
| **Low** | Minor functional or usability issue | Truncated label; confusing message; inconsistent formatting |
| **Enhancement** | Not a defect; a suggestion | Better empty state; clearer wording |

Consider **impact** (money, legal, data, users, downstream) and **frequency** (every time, common path, edge, rare config). A rare crash in payroll can be Critical; a common cosmetic issue is still Low.

Defect types:

- Functional
- Calculation
- Validation
- Workflow/State
- Permission/Security
- Data Integrity
- Integration
- UI/UX
- Accessibility
- Performance
- Content/Localization
- Other

Do not inflate severity to get attention. Do not downgrade a real defect because it is inconvenient to fix.

## 7. Writing a defect

A defect must be actionable without a meeting.

```
ID:          DEF-007
Title:       Loan deduction exceeds the 30% cap for QA_EMP_04
Severity:    High
Type:        Calculation
Module:      Payroll > Run > Deductions
Test case:   TC-0031
Environment: staging, build 2026.10.3, role Payroll Admin, en-US, UTC+5
Preconditions: QA_EMP_04 net pay 10,000; loan balance 8,000; cap 30%
Steps:
  1. Open Payroll > Run > August 2026.
  2. Add QA_EMP_04 and calculate.
  3. Open the deduction breakdown.
Expected:   Loan deduction <= 3,000 (30% of net), per Settings > Loans > Cap.
Actual:     Loan deduction 4,800; net pay 5,200.
Evidence:   evidence/screenshots/TC-0031_breakdown.png;
            evidence/network/TC-0031_response.json;
            calc/TC-0031.py
Impact:     Over-deduction; employee underpaid; payroll cannot be finalised.
Likely cause: Cap applied to gross pay instead of net (hypothesis; not confirmed).
Suggestion: Apply the cap after tax and other deductions; add a regression test at the boundary.
Workaround: Manually reduce the loan deduction before finalising.
```

Title rules: specific entity + condition + wrong outcome. "Loan cap not applied" is better than "Loan bug"; "Loan deduction exceeds 30% cap for QA_EMP_04" is best.

Likely cause is a hypothesis, labelled as such. Do not present speculation as fact.

Suggestion is a direction, not a full implementation. It should be safe and within the product's rules.

## 8. False positives and honest statuses

Use the status vocabulary consistently:

- `Pass` — observed and matches the oracle.
- `Fail` — observed, reproduced, contradicts the oracle.
- `Blocked` — could not execute (access, environment, missing data, forbidden action).
- `Needs Clarification` — oracle unclear, requirements conflict, or behaviour is ambiguous.
- `Observation` — noteworthy, but not a defect (UX, inconsistency, question, risk).
- `Not Run` — planned but out of time/scope; explain why.

Common false positives:

- Expected result came from the app itself.
- The test data was invalid or stale.
- The role or tenant was wrong.
- A previous step failed silently and contaminated the state.
- A cache or eventual-consistency delay was mistaken for a bug.
- The requirement is different by country, plan, or contract.
- The UI hides an action but the server would allow it — that is a permission finding, but verify the intended behaviour before calling it a defect.
- A cosmetic difference is real but Low, not High.

When in doubt, `Needs Clarification` with a precise question beats a confident wrong Fail.

## 9. The config-change ledger

Every setting you change goes in `07-fixtures-and-config-ledger.json` **before** you change it:

```json
{
  "id": "C-003",
  "path": "Settings > Attendance > Grace period",
  "original": "10",
  "changed_to": "0",
  "changed_at": "2026-11-04T10:12:00Z",
  "role": "Admin",
  "reason": "Perturbation E-012",
  "restored": false,
  "restored_at": "",
  "restored_value": "",
  "evidence": "evidence/snapshots/E-012_before.html",
  "notes": "Affects late marks; restore before payroll tests."
}
```

Rules:

- Log before changing, not after.
- One row per setting; do not bundle.
- Restore as soon as the experiment is done, unless the scenario needs the value.
- Verify the restore by re-reading the setting and re-snapshotting the watch set.
- A failed restore is a defect (and a blocker for later tests).
- If a setting cannot be restored (e.g. it triggers an irreversible process), stop and ask before changing it.

Fixtures go in the same file:

```json
{
  "fixtures": [
    {
      "id": "F-004",
      "name": "QA_EMP_04_midmonth_joiner",
      "purpose": "Proration boundary",
      "created_via": "Employees > Add",
      "status": "active",
      "cleanup": "delete after payroll run; cannot delete if payslip exists; archive instead",
      "notes": ""
    }
  ]
}
```

## 10. Cleanup

Cleanup is part of the test, not an afterthought.

1. Restore every config change; verify the value and the watch set.
2. Delete `QA_` records in reverse dependency order.
3. If deletion is blocked (referenced by a payslip, invoice, audit record), archive/deactivate and note it.
4. Remove uploaded files and generated documents where the app allows.
5. Delete browser storage state, downloaded credentials, and any temporary auth files.
6. Re-snapshot the baseline and compare; note any residue.
7. Update the ledger with cleanup status and evidence.
8. Tell the user what could not be removed and why.

If you cannot clean up, say so prominently. A report that hides residue is worse than a report that admits it.

## 11. Parallel execution

If using subagents:

- Give each executor its own module, fixtures and workspace files.
- One agent owns each shared JSON file; others return structured results to the orchestrator.
- Never run two config-changing experiments against the same global setting at once.
- Use distinct fixture prefixes: `QA_<agent>_<nn>_...`.
- Have the orchestrator merge, deduplicate, and re-validate before the report.
- If a shared dependency must change, serialize it and log it once.

If coordination is unreliable, run sequentially. A slow correct run beats a fast corrupt one.

## 12. Stop conditions

Stop and ask the user when:

- The environment is production or cannot be confirmed as staging.
- A required action would send real email/SMS, charge money, finalise payroll, provision access, or delete shared data.
- A setting cannot be restored.
- You need to bypass MFA, CAPTCHA, a feature flag, or a permission boundary.
- A test would require real personal data.
- The app is down, or a blocker prevents meaningful coverage.
- The user's time limit is reached; deliver what is done, with honest coverage.

Do not stop for a minor ambiguity; record the assumption and continue.
