# 03 Test design catalog

Read at the start of Phase 4. This file turns the atlas and the product model into test cases that are deep, reproducible and worth running.

## Contents

1. Generate cases from behaviour, not from fields
2. The oracle hierarchy
3. Test layers and case seeds
4. Named techniques
5. Per-control checklists
6. Deep scenario lenses
7. Coverage mapping
8. Test case quality rubric
9. Prioritization
10. Design anti-patterns

---

## 1. Generate cases from behaviour, not from fields

A field inventory is not a test plan. For each atlas element, ask:

- What rule is this control enforcing or expressing?
- What happens at its boundaries and in combination with its neighbours?
- What does it change elsewhere when it is set, cleared, or changed later?
- Who is allowed to see or change it?
- What output or decision depends on it?
- What would embarrass the business if it were wrong?

A good case has **one reason to exist**, stated in one sentence. If you cannot state the reason, do not write the case.

Prefer a small number of cases that each exercise several related behaviours over a large number of near-duplicates. Deep coverage comes from scenarios that cross modules, not from running the same validation on every text box.

## 2. The oracle hierarchy

Every expected result needs an oracle. Use the strongest available and record it in the case:

1. **User-provided specification or policy** — a claim to verify, not proof the app is right.
2. **In-app text** — helper text, validation copy, policy descriptions, release notes.
3. **Domain or statutory rule** — confirm country and year with the user.
4. **Mathematical or accounting invariant** — independently recompute.
5. **Consistency invariant** — same value across screens, after reload, in exports and summaries.
6. **Common UX convention** — weak; use `Observation` or `Low`, not a confident `Fail`.
7. **Hypothesis** — probe it; never fail the app on it alone.

If no credible oracle exists, the status is `Needs Clarification`, not `Fail`. If two oracles conflict, record the conflict — it is a finding about the requirement, not just the app.

## 3. Test layers and case seeds

Use the layers as a checklist for coverage, not as a rigid sequence. Every layer does not apply to every module; say why when it does not.

### L1 — UI and content integrity

Ask: Is the screen understandable, consistent and complete in every state?

- Labels match the domain and each other; no typos, truncation or placeholder text.
- Same concept named the same way across modules.
- Empty, loading, error, partial and no-permission states exist and are useful.
- Default tab, default filter, default sort and default date range are sensible.
- Dates, numbers, currency, percentages and names are formatted per locale.
- Icons, colours, badges and counters mean what they appear to mean.
- Links and buttons go where they say; no dead ends.
- Layout holds at desktop, tablet and narrow widths; no overlap or horizontal scroll.
- Keyboard focus is visible and in a sensible order.
- Copy is actionable: an error says what is wrong and how to fix it.
- Unsaved-changes warning appears when leaving a dirty form.
- Destructive actions are distinguishable and confirmed.

### L2 — Field validation and boundaries

Ask: What does the field accept, reject, normalise and preserve?

- Required vs optional vs conditional-required; whitespace-only input.
- Minimum, maximum, zero, negative, one below/above, exactly at boundary.
- Decimal precision, rounding, currency symbols, thousands separators, scientific notation.
- Leading zeros, plus/minus signs, pasted values, autofill.
- Maximum length, exactly at limit, one over; long unbroken strings.
- Unicode, emoji, RTL text, combining characters, HTML-like input (observe escaping, do not inject).
- Invalid dates (31 Feb, leap day), date ranges, start after end, equal dates.
- Time formats, time zones, DST gaps and overlaps.
- Cross-field rules: one field enables/requires/contradicts another.
- Server-side validation: bypass the client only through normal UI paths; observe the response.
- Error message placement, persistence after correction, and whether the invalid value is retained.
- Duplicate detection and uniqueness, including case and whitespace variants.

### L3 — CRUD and lifecycle

Ask: Can the entity be created, found, changed, copied, archived and removed without losing integrity?

- Create with minimum, typical and maximum data.
- Read: list, detail, search, filter, sort, export.
- Update one field, many fields, and clear a field.
- Cancel an edit; confirm nothing persisted.
- Duplicate; observe what is copied and what is reset.
- Delete: confirmation, soft vs hard delete, restore, dependent records.
- Archive/deactivate and its effect on lists, dropdowns, reports and logins.
- Bulk actions on mixed selections and across pages.
- Import: valid, invalid, partial, duplicate, large file, wrong template.
- Export: all vs filtered, column set, encoding, formulas, dates.
- Attachments: add, replace, remove, download, permissions.
- Audit trail: who changed what, when, old and new value.
- Concurrent edit: two sessions, stale form, optimistic locking.

### L4 — Business rules and calculations

Ask: Is the output independently correct, and does it stay correct through changes?

- Recompute every important number outside the app (Python or spreadsheet in `calc/`).
- Order of operations: discount before tax vs after; proration before caps.
- Rounding at line level vs total level; half-up vs half-even; currency decimals.
- Percentages, tiers, slabs, thresholds, caps, floors, minimums.
- Aggregations: sum of lines equals total; subtotal plus tax minus discount equals grand total.
- Proration: calendar days vs working days vs 30-day month; join/leave mid-period.
- Effective dates: which rate applies on which date; retroactive vs future changes.
- Negative adjustments, reversals, refunds, credit notes, write-offs.
- Year-to-date, period-to-date and carry-forward values.
- Idempotency: running the same calculation twice does not double-count.
- Invariants: gross - deductions = net; debit = credit; paid <= invoiced; stock >= 0; refund <= paid.

### L5 — Cross-module ripple and precedence

Ask: If I change X here, what must change there — and does it?

- Master setting changed after child records exist: future-only, retroactive, or frozen?
- Same setting at company, department, group and record level: which wins?
- Override and "reset to default": does the override disappear cleanly?
- Rename/delete a referenced entity: do dependent records update, block, or orphan?
- Status change in one module: does it lock, hide, notify or recalculate elsewhere?
- Reports, dashboards, exports and notifications reflect the change.
- Counters and badges match the lists they point to.
- Permissions in one module affect actions in another.
- Integration/webhook payload reflects the change (observe only).
- Changing a template affects existing documents vs new ones.

### L6 — State, workflow and approvals

Ask: Can the entity move through every legal transition, and is every illegal one blocked?

- Draw the state machine; test every transition and a sample of illegal ones.
- Who can trigger each transition; what happens when the wrong role tries.
- Required fields and attachments at each step.
- Approve, reject, return for changes, cancel, reopen, archive.
- Post-approval edits: blocked, allowed with audit, or silently allowed (a defect).
- Parallel approvals, delegation, escalation, expiry and reminders.
- Re-submission after rejection: does it preserve history and reset the right fields?
- Withdrawal mid-approval; approver no longer available.
- Status-dependent field visibility and editability.
- Notifications at each transition: right recipient, right content, no duplicates.
- Audit trail of every transition.

### L7 — Roles, permissions and tenancy

Ask: Can each role see and do exactly what it should — no more, no less?

- Menu and navigation visibility per role.
- Field-level visibility and editability.
- Action-level permissions: create, edit, delete, approve, export, invite.
- Data scope: own, team, department, branch, all; cross-tenant isolation.
- Read-only role sees no edit controls and cannot reach edit screens by URL.
- Role change mid-session: does the UI update, or stay stale until reload?
- Delegated or temporary access expires.
- Export and print permissions, including bulk export.
- Sensitive fields masked in lists, detail, exports and logs.
- Direct URL access to another record: blocked or exposed? Observe the UI-generated response.
- Permission checks are server-side, not just CSS hiding. Verify by observing the response to a normal UI action, never by crafting a request.

### L8 — Data volume, search, filter, sort and pagination

Ask: Does the list behave correctly when there is a lot of data and when there is none?

- Pagination: first, last, middle, page-size change, out-of-range page.
- Sort each column, multi-sort, stable order for equal values.
- Filter alone, combined, cleared, saved as a view, applied across pages.
- Search: partial, case, whitespace, unicode, special characters, no results, many results.
- Counts and totals match the filtered set, not the whole set.
- Bulk select: current page vs all pages vs filtered set.
- Export respects filters and sort.
- Virtual scroll and "load more" do not duplicate or skip rows.
- Large datasets: performance, timeouts, partial rendering.
- Empty state after filtering vs truly empty.

### L9 — Time, dates, time zones and periods

Ask: Does the product behave correctly at the edges of time?

- Effective-from/to dates; overlapping and adjacent ranges.
- Month-end, quarter-end, year-end, leap year, 30-day vs 31-day months.
- DST spring-forward and fall-back; timezone of the user vs the tenant.
- Cutoff times: an action at 23:59 vs 00:01.
- Backdating and future dating; permissions for each.
- Period close/lock: can anything change after close?
- Recurring events: weekly, monthly, last day of month, skipped occurrences.
- Expiry, aging, SLA clocks, reminders, scheduled jobs.
- "Today" boundary: what the user sees at midnight in their timezone.
- Duration calculations across DST and across month boundaries.

### L10 — Outputs, documents, exports and notifications

Ask: Does the output faithfully represent the data and the rules?

- PDF/Excel/CSV: values, totals, filters, column order, headers, footers, page breaks.
- Formulas vs hard-coded values; dates and numbers as data types.
- Encoding, special characters, long text, images, logos.
- Export of a filtered set vs all records; export permissions.
- Print layout and branding.
- Email/SMS: recipient, subject, body, variables, links, attachments, unsubscribe.
- Notification deduplication and retry; no notification on failed action.
- Document numbering, sequence gaps, duplicates.
- Signatures, approvals, audit stamps.
- Import/export round-trip: export, edit, re-import, compare.

### L11 — Resilience, concurrency and session

Ask: What happens when the user, the network or another session interferes?

- Reload after save: does the value persist? (A frontend-only value is a defect.)
- Double-click submit; rapid repeated actions; idempotency.
- Back/forward after save; stale form state.
- Two tabs editing the same record; last-write-wins vs conflict message.
- Session expiry mid-form; unsaved data; re-login behaviour.
- Network failure during save; partial save; retry.
- Slow response: loading state, disabled button, no duplicate submission.
- File upload interruption and resume.
- Browser zoom, small viewport, long text.
- Cache: stale data after a change in another module.
- Logout: does it clear sensitive state and prevent back-button access?

### L12 — Accessibility, responsive and localization

Ask: Can a diverse set of users operate the product?

- Keyboard-only: reach every control, activate, escape modals, no traps.
- Focus order and visible focus; skip links.
- Labels and error associations for screen readers; ARIA roles.
- Contrast and colour-only meaning.
- Zoom 200% and 400%; no loss of function.
- Mobile/tablet layouts: navigation, tables, modals, date pickers.
- RTL layout and mirrored icons.
- Long translations: truncation, overflow, button sizing.
- Locale number/date/currency formats; pluralization.
- Language switch persists and does not lose form state.
- Time zone displayed or explained where it matters.

### L13 — Security and privacy (UI-observable only)

Ask: Does the UI leak or allow what it should not?

- Sensitive data masked by default; reveal requires permission and is audited.
- No secrets, tokens or personal data in URLs, page source, console logs or exports.
- Logout and session timeout clear access; back button does not restore.
- Role-based data scope holds in lists, detail, search, export and print.
- Direct URL access to another tenant/record is blocked.
- Error messages do not reveal stack traces, SQL, internal IDs or other users' data.
- File downloads respect permissions and are not guessable.
- Password fields are masked; autocomplete behaviour is sensible.
- Audit log records access to sensitive data where the product claims it does.

Do not perform destructive security testing, scanning, injection, or privilege escalation. Record what the UI exposes and mark deeper security testing as out of scope.

## 4. Named techniques

Use the name in the case's `technique` field so coverage is auditable.

| Technique | Use it for |
|---|---|
| **Equivalence partitioning** | Group inputs that should behave the same; test one from each class. |
| **Boundary value analysis** | Test min-1, min, min+1, max-1, max, max+1, zero, empty. |
| **Decision table** | Combinations of conditions with different outcomes (role x status x amount). |
| **State transition** | Every legal transition plus illegal ones. |
| **Pairwise** | Configuration combinations; covers interactions without the full Cartesian product. |
| **Metamorphic** | Change an input in a way that must change the output predictably (double quantity -> double line total). |
| **Invariant** | Properties that must always hold (totals, balances, no negative stock). |
| **Differential** | Compare two views of the same truth (list vs export, summary vs detail). |
| **Negative testing** | Invalid, missing, conflicting, unauthorized input. |
| **Error guessing** | Use experience to probe likely weak spots. |
| **CRUD matrix** | Every entity x create/read/update/delete/archive. |
| **Permission matrix** | Every role x every sensitive action/data scope. |
| **Scenario testing** | Multi-module end-to-end journey with a business meaning. |
| **Round-trip** | Export -> edit -> import -> compare. |
| **Data volume** | Many records, long lists, large files, slow responses. |
| **Time travel** | Past/future dates, period boundaries, DST, leap year. |
| **Interrupted workflow** | Leave mid-wizard, expire session, fail network, resume. |
| **Dirty state** | Edit without saving, switch tab/module, navigate away, return. |
| **Duplicate submit** | Double-click, refresh, retry, back-and-resubmit. |
| **Reload persistence** | Save, reload, verify backend state. |
| **Cross-surface consistency** | Detail vs list vs summary vs report vs export vs notification. |
| **Precedence conflict** | Same setting at multiple levels with conflicting values. |
| **Retroactive mutation** | Change a master rule after records exist. |
| **Safe fuzzing** | Long strings, unicode, emoji, special characters in normal inputs. |

## 5. Per-control checklists

### Text input

Required/optional; whitespace; min/max length; unicode/emoji/RTL; leading/trailing spaces; paste; autofill; clear; special characters; duplicate; case sensitivity; error message; value retained after error; save and reload.

### Textarea / rich text

Line breaks; max length; formatting preserved; paste from Word/Google Docs; HTML/script-like input escaped; mentions/links; character counter; resize; save and reload.

### Number / currency / percentage

Min/max/zero/negative; decimals; rounding; currency symbol; thousands separator; paste; step; precision; calculation downstream; display vs stored value; locale format.

### Date / datetime / time

Invalid dates; leap day; min/max; start/end order; equal dates; timezone; DST; date picker vs typed; clear; default; "today"; display format; calculation downstream.

### Select / searchable select

All options; default; disabled options; search matching; no results; lazy load; long list; cascade; clear; keyboard; option that changes other fields; role-dependent options.

### Multi-select

Add/remove; select all; max; duplicates; search; ordering; clear; persistence; effect on downstream calculations.

### Radio / checkbox / toggle

Default; mutual exclusivity; dependent fields appear/disappear; save behaviour; keyboard; label click; disabled; tri-state if applicable; persistence after reload.

### File upload

Accepted types; wrong type; size limit; zero-byte; large file; multiple files; replace/remove; progress; cancel; interrupted; virus-scan message; download; permissions; filename with unicode/spaces.

### Table / list

Columns; sort; filter; search; pagination; page size; row actions; bulk actions; inline edit; expand; totals; empty/loading/error; column chooser; saved views; export; responsive.

### Filters and search

Each filter alone; combinations; clear all; saved view; URL persistence; back button; counts; no results; special characters; case; partial match; filter + sort + pagination interaction.

### Pagination

First/last/middle; page size; out-of-range; total count; selection across pages; filter reset; sort stability; deep link to page; export all.

### Bulk actions

None selected; one; many; mixed statuses; across pages; filtered set; confirmation; partial failure; result message; audit trail; undo if offered.

### Wizard / stepper

Each step; validation per step; back/forward; skip; save draft; resume; conditional steps; cancel; browser back; session expiry; final summary; edit from summary.

### Modal / drawer

Open/close; escape; click outside; focus trap; scroll; nested modal; unsaved changes; submit; error; responsive; deep link.

### Tabs / pseudo-tabs

Every tab and nested tab; default; state preservation; dirty state; URL; reload; role visibility; lazy load; badge counts; disabled tabs.

### Notifications / toasts

Success/error/warning; correct message; auto-dismiss; action link; duplicate; persistence; accessibility announcement; no false success on failure.

### Charts / dashboards

Legend; tooltip; filters; date range; totals match list; empty state; loading; export; responsive; colour-only meaning; rounding.

### Computed / read-only fields

What it is computed from; updates when inputs change; precision; formatting; cannot be edited; value after reload; value in export; stale after config change.

### Buttons / actions

Enabled/disabled conditions; permission; confirmation; result; duplicate click; keyboard; loading state; error handling; audit.

## 6. Deep scenario lenses

These are the highest-yield patterns for interconnected SaaS. Use them to generate scenarios, not just cases.

### Lens 1 — Master propagation and retroactive mutation

Change a master setting (tax rate, leave policy, approval threshold, price list) after child records exist. Check:

- Do existing records change, stay frozen, or enter a mixed state?
- Is the change future-dated, effective-dated, or immediate?
- Is there an audit trail? Is the old value recoverable?
- Do reports and exports reflect the same choice as the detail screen?
- Does a reversal or recalculation produce a different answer than the original run?

### Lens 2 — Nested tab dirty-state leakage

Edit fields in Sub-tab 1 without saving, switch to Sub-tab 2, edit, then save or navigate away. Check:

- Are unsaved changes preserved, lost, or leaked into the wrong record?
- Does switching tabs trigger validation or autosave?
- Does the Save button save all tabs or only the active one?
- Does the browser back button restore the dirty state?
- Does a modal opened from a dirty tab discard changes?

### Lens 3 — Calculation chains and rounding

Build a chain: quantity -> discount -> tax -> shipping -> total -> payment -> refund. Recompute independently at each step. Check:

- Rounding at line vs total; half-up vs half-even.
- Percentage on discounted vs original amount.
- Tax inclusive vs exclusive.
- Caps and floors applied before or after tax.
- Currency conversion at which rate and date.
- Refund of a discounted order; partial refund allocation.
- Invariant: components sum to total; refund <= paid; balance >= 0.

### Lens 4 — State machine and post-approval locks

Walk every transition, including illegal ones. Check:

- Can an approved record be edited? By whom? Is it audited?
- Can a paid/finalised record be reversed? Does the reversal create a new record or mutate history?
- Can a rejected record be resubmitted without changes?
- Do parallel approvals double-approve or deadlock?
- Does a status change cascade to child records, notifications and reports?
- Is the audit trail complete and immutable?

### Lens 5 — Temporal overlaps and effective dating

Create overlapping date ranges, adjacent ranges, open-ended ranges, and ranges that cross month/year boundaries. Check:

- Which rule applies on the boundary date?
- Is the end date inclusive or exclusive?
- Leap year and DST.
- Backdated change: does it recalculate history?
- Future-dated change: does it apply early?
- Period close: can anything change after close?
- Timezone of the actor vs the tenant.

### Lens 6 — Role and permission cascades

Use a permission matrix. Check:

- Menu, field, action and data-scope permissions.
- Role change mid-session.
- Delegation and expiry.
- Direct URL access.
- Export/print permissions.
- Sensitive data masking.
- Cross-tenant isolation.
- Server-side enforcement: observe the response to a normal UI action; do not craft requests.

### Lens 7 — Pagination, filter and sort bleed

Apply a filter, sort, go to page 3, change page size, select rows, export, clear the filter. Check:

- Does the selection survive a filter change? Should it?
- Does "select all" mean page or filtered set?
- Does export respect the current filter and sort?
- Does the total count match the filtered set?
- Does the sort order stay stable for equal values?
- Does a saved view restore filters, sort and page size?

### Lens 8 — Cross-surface inconsistency

For one value, compare: detail page, list row, summary card, dashboard, report, export, notification, audit log, and the UI-generated network payload. Check:

- Same value everywhere?
- Same rounding and formatting?
- Same effective date?
- Same permission filtering?
- Stale after a change in another tab/module?
- Survives reload?

### Lens 9 — Duplicate submission and idempotency

Double-click Save; press Enter twice; refresh during submit; retry after a timeout; use back and resubmit. Check:

- One record or two?
- One payment or two?
- One notification or two?
- Is the second attempt blocked, deduplicated, or silently accepted?
- Is there a recovery path after a partial failure?

### Lens 10 — Precedence conflicts

Set the same setting at company, department, group and individual level to different values. Check:

- Which wins? Is the winner visible?
- Is "inherit" distinguishable from "explicitly set to the same value"?
- Does resetting an override restore the inherited value?
- Does a change at a higher level affect records with overrides?
- Is the conflict explained in the UI?

### Lens 11 — Import/export round-trip

Export a representative set, edit a few fields, re-import. Check:

- Column order, headers, required fields, date/number formats.
- Encoding and special characters.
- Validation errors per row; partial import; rollback.
- Duplicate handling.
- Relationships by name vs ID.
- Round-trip fidelity: export -> import -> export produces the same data.

### Lens 12 — Localization and timezone

Switch language, locale and timezone. Check:

- Dates, numbers, currency, percentages.
- RTL layout and mirrored icons.
- Long translations and truncation.
- Pluralization.
- Timezone displayed vs stored; "today" boundary.
- Language switch preserves form state.
- Exports use the user's locale or the tenant's? Is it stated?

### Lens 13 — Concurrency and stale data

Two sessions edit the same record; one saves, the other saves later. Check:

- Last-write-wins, conflict message, or silent loss?
- Does the second form show stale values?
- Does a list refresh after a change in another tab?
- Does a dashboard cache expire?
- Does a bulk action conflict with a single edit?

### Lens 14 — Soft delete, restore and referential integrity

Delete or archive an entity referenced elsewhere. Check:

- Is it hidden from dropdowns, lists and search?
- Do existing records keep the reference and display it?
- Can it be restored? Does it return with relationships intact?
- Can a new record reference a deleted entity through an old link?
- Do reports and exports include or exclude deleted records consistently?
- Is deletion audited?

### Lens 15 — Notification side effects

Trigger an action that should notify. Check:

- Right recipient, right channel, right content, right timing.
- No notification on failure or cancellation.
- No duplicate on retry.
- Links work and land on the right record.
- Unsubscribe/preferences respected.
- Sensitive data not included.
- Notification is recorded in the audit trail where claimed.

### Lens 16 — Session and auth transitions

Expire the session mid-form; log out and back in; switch roles; use the back button. Check:

- Unsaved data preserved or lost with a warning?
- Sensitive state cleared?
- Back button does not restore a protected page?
- Role change takes effect immediately or after reload?
- MFA/CAPTCHA handled without losing the workflow.
- Storage state cleaned up at the end of the run.

## 7. Coverage mapping

Coverage is a claim you must be able to prove. Maintain these mappings:

| Coverage target | Proof |
|---|---|
| Every atlas control | `tested_by` contains at least one case, or `not_tested_reason` is set |
| Every relationship edge | A ripple case references the relationship ID, or `not_tested_reason` is set |
| Every state transition | A case per legal transition; illegal transitions sampled |
| Every role | A permission case per sensitive action/data scope |
| Every important output | A verification case with an independent oracle |
| Every calculation | An independent calculation in `calc/` |
| Every import/export | A round-trip case |
| Every date boundary | A time case |
| Every empty/loading/error state | A UI case |
| Every module | At least a smoke case |

The report's Coverage sheet is computed from the JSON. If a control has no case, the report should say so, not hide it.

## 8. Test case quality rubric

A case is ready when:

- **Reason**: one sentence explains why it exists.
- **Oracle**: type, source and confidence are recorded.
- **Independent expected**: the expected result was derived before observing the actual.
- **Reproducible**: preconditions, data, role and steps are enough for another tester.
- **Minimal**: no unnecessary steps; the failing step is obvious.
- **Evidence**: at least one artifact path for a Pass or Fail.
- **Specific title**: "Loan deduction exceeds 30% cap for QA_EMP_04" not "Loan issue".
- **Honest status**: `Pass`, `Fail`, `Blocked`, `Needs Clarification`, `Observation`, or `Not Run`.
- **No duplicate**: it is not a permutation of an existing case without a new reason.
- **Priority rationale**: P0–P3 with an impact x likelihood note.

Bad case: "Test employee form" — no oracle, no boundary, no expected result.

Good case: "Contract employee with zero leave accrual cannot request annual leave" — oracle from policy helper text, boundary partition, expected error, one reason.

## 9. Prioritization

Use P0–P3:

- **P0** — money, security, data loss, legal/compliance, complete blocker. Run first.
- **P1** — core workflow, high-frequency path, important calculation, role access.
- **P2** — secondary workflow, validation edge, cross-module ripple, output fidelity.
- **P3** — cosmetic, rare configuration, low-impact content.

Record the impact and likelihood that produced the priority. When time is short, cut P3 first and say so.

## 10. Design anti-patterns

- **Expected copied from actual.** This is the cardinal sin; it turns QA into a screenshot.
- **"Verify the page loads."** Not a test unless loading is the risk.
- **Every dropdown option as a separate case.** Test behaviour-changing options; group the rest.
- **Duplicate permutations.** They inflate counts and hide gaps.
- **Testing implementation, not behaviour.** The user cares what the product does.
- **Only happy paths.** The defects live at the edges.
- **Only one role.** Permission bugs are invisible from an admin account.
- **No independent calculation.** Comparing the app to itself proves nothing.
- **Unreproduced failures.** A flaky fail is a finding about reliability, not a confirmed defect.
- **Cosmetic-only report.** Balance usability findings with functional risk.
- **Old cases as a safety net.** They anchor you to someone else's blind spots.
- **Overclaiming coverage.** A smaller truthful report is more valuable.
