# 02 Field atlas and product model

Read at the start of Phase 2 (atlas) and Phase 3 (model). The atlas answers "what exists?". The model answers "how does it behave and how is it connected?". Test cases are generated from both.

## Contents

1. The atlas: what to record for every control
2. Capturing options and cascades
3. Discovering relationships
4. Perturbation experiments
5. Rules, states and outputs
6. Scenario synthesis
7. Fixtures: designing the cast of test entities
8. Risk ranking
9. Modeling anti-patterns

---

## 1. The atlas

`02-field-atlas.json` is a list of rows, one per control or output element. Aim for **no unvisited screen and no un-inventoried control**.

| Key | Meaning |
|---|---|
| `id` | Stable ID such as `A-0142` |
| `state_id` | The state where it was observed (`S-014`) |
| `module` | Top-level module |
| `path` | Full path: `Module > Tab > Subtab > Section` |
| `label` | The visible label, exactly as shown (typos included) |
| `control` | text, textarea, number, currency, date, datetime, time, select, multiselect, searchable-select, radio, checkbox, toggle, file, button, link, table, column, filter, tab, menu, chart, badge, computed, other |
| `required` | yes / no / conditional (and the condition) |
| `default` | Default value, or "empty" |
| `options` | Every option, in order, for any choice control |
| `options_count` | Number of options captured (helps prove completeness) |
| `constraints` | maxlength, min/max, pattern, format hint, step, allowed file types, decimals shown |
| `helper_text` | Tooltip, placeholder, help text, inline hints |
| `depends_on` | What enables, shows, hides, filters or populates this control |
| `affects` | What this control changes elsewhere (fill in during Phase 3) |
| `saves_how` | On blur, on Save button, on toggle, autosave, wizard final step |
| `roles_visible` | Which roles see or can edit it |
| `tested_by` | Test case IDs that cover it (fill in Phase 4) |
| `not_tested_reason` | Required if no case covers it |
| `notes` | Anything odd: truncated label, inconsistent wording, wrong tab order |
| `evidence` | Snapshot/screenshot path |

Buttons, links, table columns, filters, tabs and badges are atlas rows too. A button's `affects` column is where "what does it do?" lives.

Batch your writing: capture the page, add its rows, move on. Do not hold a module's controls in your head.

## 2. Capturing options and cascades

- **Every option, in order.** Scroll long lists. If options load lazily or by search, record how you retrieved them and the count.
- **Cascades.** If choosing A changes the options of B, record the mapping for each value of A (for large sets: every value for Deep, a representative set for Standard, and say which).
- **Options that vary by context.** The same dropdown on two screens, or for two roles, may list different values. Record both. A difference is either a rule or a bug; Phase 3 decides.
- **Defaults and their sources.** Is the default constant, remembered from last use, or inherited from a setting elsewhere? If inherited, that is a relationship edge.
- **Option labels vs behaviour.** Options with odd names ("Other", "N/A", "None", "Custom") often hide special logic. Flag them.
- **Disabled options.** Record them and why they are disabled if the UI says.
- **Multi-select semantics.** Is it additive? Is there a maximum? Does "Select all" include disabled items?
- **Searchable selects.** What fields does the search match? Does it search server-side? What happens with no results?

## 3. Discovering relationships

A relationship edge says: *changing or having X causes Y to behave or appear differently somewhere else.* Edges come from four sources.

**Static clues** (free, collect while building the atlas):

- A dropdown lists records managed on another screen (the edge: that screen feeds this field).
- Helper text names another setting or module.
- The same noun appears in several modules (employee, product, account, project, template).
- Computed or read-only fields (they depend on something; find what).
- Badges and counters that summarise another list.
- Import/export templates that expose fields not visible in the form.
- Permission labels that mention another module or action.

**Lifecycle tracing**: create one entity and follow it everywhere. Where does it appear? Where does it not appear when it should? What changes at each state? Entities include people, products, accounts, orders, tickets, projects, policies.

**Output tracing**: for every report, dashboard widget, export, document, notification, find the inputs it must depend on. Then check whether it does.

**Precedence discovery**: wherever the same setting can live at several levels (company, department, group, individual, record), the product has a precedence rule. Find the levels, set them to conflicting values on a fixture, and see which wins. Test the "inherit / override / reset to default" paths.

Record each edge in `03-relationships.json`:

```json
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
```

`type`: enables, hides, filters, populates, computes, validates, permits, schedules, precedence, locks, notifies, cascades, duplicates.

`confidence`: High (observed), Medium (strong clue), Low (hypothesis to probe).

## 4. Perturbation experiments

When the UI will not tell you what a setting does, **measure it.** This is the single most effective technique for UI-only testing of heavily interconnected software.

Protocol:

1. Pick a fixture entity and a quiet baseline. **Snapshot** every screen that might be affected (the "watch set"): lists, detail pages, summaries, reports, dashboards.
2. Change **one** setting. Log it in the config ledger with the original value.
3. Re-snapshot the watch set. **Diff.** Anything that changed is evidence of an edge.
4. Record the edge, then run the change in the other direction and at boundary values.
5. Restore the setting. Re-snapshot and confirm you are back at baseline. A failed restore is itself a defect.

Tips:

- One factor at a time first; combinations later (pairwise, see `03-test-design-catalog.md`).
- Choose the watch set from static clues; widen it when an experiment surprises you.
- Some effects appear only after an action (recalculate, run, publish, close period, next scheduled run). Note what you had to do to see it.
- Some effects apply to future records only, others retroactively. Test both and record which.
- No change observed is also a finding: a setting that appears to do nothing is either dormant, for a module you cannot see, or broken. Ask or note it.
- Use the smallest possible fixture so the diff is readable.
- Record timestamps and role: the same setting may behave differently for different roles.

### High-value perturbation experiments

- Turn a feature toggle off and on; watch navigation, fields, actions and reports.
- Change a global default that a record has already inherited; does the record change, stay frozen, or show a mixed state?
- Change a policy mid-period; are past and future records treated differently?
- Change a role permission; does the UI hide the action, disable it, or allow it and fail server-side?
- Change a currency, locale or timezone; what recalculates and what does not?
- Change a status to a locked state; which fields become read-only and which remain editable?
- Set conflicting values at two precedence levels; which wins, and is the conflict visible?

## 5. Rules, states and outputs

**Rules** go in `03-rules.md`, one line each, as IF/THEN with a source:

```
RULE-014  IF employee.type = "Contract" THEN annual leave accrual = 0   [source: helper text, Leave > Policy]
RULE-015  IF grace < late minutes THEN mark late                         [source: hypothesis, probe via E-012]
```

Sources, strongest first: in-app text, user-provided rule documents, repeated observation, domain convention, hypothesis. Hypotheses become probes, never assumed facts.

**State machines.** For every entity with a status, draw the states and the allowed transitions (who can trigger, what changes, what becomes locked). Include the "illegal" transitions you expect to be blocked. A compact notation works:

```
Draft -> Submitted (employee) -> Approved (manager) -> Paid (payroll admin) -> Locked
Draft -> Cancelled (owner)
Approved -> Rejected (manager) -> Draft (owner)   # expected, verify
Paid -> Edit                                   # expected to be blocked
```

**Outputs.** For each important output (a total, a document, a report line, a notification), write down how you will judge it correct. Candidates are listed in the oracle hierarchy in `03-test-design-catalog.md`. Decide now which outputs you can check by independent recomputation and prepare the calculation (a small Python or spreadsheet formula in `calc/`).

### Oracle hierarchy

Use the strongest available oracle, and record which one you used:

1. **User-provided specification or policy** — a claim to verify, not proof the app is right.
2. **In-app text** — helper text, validation copy, policy descriptions, release notes.
3. **Domain or statutory rule** — confirm country and year with the user; rules change.
4. **Mathematical or accounting invariant** — independently recompute; totals equal the sum of parts; gross minus deductions equals net.
5. **Consistency invariant** — the same value across screens, after reload, in the export and in the summary.
6. **Common UX convention** — weak; use for `Observation` or `Low` severity, not a confident `Fail`.
7. **Hypothesis** — probe it; never fail the app on it alone.

If two oracles conflict, say so in `Needs Clarification`. The conflict itself is a valuable finding.

## 6. Scenario synthesis

Scenarios are what turn a pile of field tests into depth. Build them by combining the model with the lenses in `03-test-design-catalog.md` and write them as cards in `04-scenarios.md`:

```
SC-021  "Mid-month joiner with an unpaid-leave week and a loan"
  Entities: QA_EMP_04 (joiner on the 12th), QA_LOAN_01, one unpaid leave week
  Config:   proration = calendar days, loan deduction cap = 30%
  Path:     create employee > assign salary > record leave > add loan > run payroll
  Oracle:   independent calculation in calc/SC-021.py
  Risk:     money, compliance
  Touches:  Employees, Leave, Loans, Payroll, Reports
  Expected: net pay = independently computed value; loan deduction <= 30% of net
```

Good scenarios cross at least two modules, put the product in an uncomfortable position (boundaries, conflicts, reversals, lateness, volume), and have a checkable oracle. Generate them systematically:

- For each relationship edge, ask "what is the most revealing situation that exercises this edge?"
- For each state machine, walk every transition and a few illegal ones.
- For each output, ask who consumes it and what would embarrass the business if wrong.
- For each role, ask what they should never see or do.

## 7. Fixtures: designing the cast of test entities

The product may need entities you do not have: new employees, customers, products, accounts, rate tables, rules, calendars. Create them, but design them like a test-data engineer, not at random.

1. List the **partitions** that matter (employment types, plan tiers, tax categories, currencies, locations, product types, roles, statuses).
2. Create the **smallest cast** that covers each partition at least once, plus boundary members (the joiner on the last day of the month, the order of exactly the free-shipping threshold, the salary exactly at a slab edge).
3. Name them `QA_<module>_<nn>_<what-they-represent>`, so purpose and ownership are obvious and cleanup is easy.
4. Record each in `07-fixtures-and-config-ledger.json` (id, name, purpose, where created, status, cleanup plan).
5. Create them in dependency order (reference data first, then the entities that use it). Creating them through the UI is itself a test: log any problems as results, not as setup noise.
6. Keep one pristine "control" entity that you never alter, as a baseline for comparison.
7. Plan teardown now: which can be deleted, which only archived, which cannot be removed (note those for the user).

If the app has roles, create or request one account per role so permission tests are real. If creating users would send real invitations, stop and ask.

### Fixture design patterns

- **Boundary twin**: two records either side of a threshold (99.99 and 100.00).
- **Control**: untouched baseline for diffing.
- **State ladder**: the same entity cloned into each lifecycle state.
- **Conflict pair**: two records whose settings disagree, to test precedence.
- **Retroactive subject**: a record created before a config change, to test history.
- **Volume set**: enough records to exercise pagination, search and export.
- **Role subject**: an entity owned by a different role or department.

## 8. Risk ranking

Rank modules and scenarios by `impact x likelihood of defect` and test in that order.

Raise **impact** for:

- money or calculations;
- legal or compliance meaning;
- data loss or irreversibility;
- security and permissions;
- many users or high frequency;
- downstream consumers (reports, exports, integrations).

Raise **likelihood** for:

- complex rules;
- many settings;
- recently changed areas (release notes);
- unusual UI controls;
- anywhere you already found a defect.

Record the rationale in the test case. "P0 because payroll net pay" is useful; "P0" alone is not.

## 9. Modeling anti-patterns

- **Testing fields instead of behaviour.** A field matrix is not a product model.
- **Assuming the happy path is the rule.** Read the helper text and probe the edges.
- **Treating a setting's label as its behaviour.** Labels lie; perturb and observe.
- **Ignoring "no change".** A setting that does nothing may be dormant or broken.
- **One giant fixture.** It hides which attribute caused the effect.
- **Changing several settings at once.** You lose the causal edge.
- **Forgetting to restore.** The next test inherits a contaminated baseline.
- **Confusing a UI hide with a server permission.** Verify with a role that should be blocked; observe the UI-generated response, do not craft requests.
