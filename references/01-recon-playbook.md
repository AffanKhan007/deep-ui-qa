# 01 Recon playbook: mapping an app you can only see

Goal: a complete, verified map of every place the user can go and everything they can see or do there, built without source code. Read this at the start of Phase 1.

## Contents

1. Information channels
2. What counts as navigation
3. The crawl algorithm and state signature
4. Expand-everything checklist
5. Hard-to-reach content
6. Read-only first, mutate later
7. The progress ledger
8. Completeness checks
9. Signals of hidden logic
10. Recon anti-patterns

---

## 1. Information channels

No single channel shows everything. Combine them. Prefer text-based channels (cheap, exact) over screenshots (expensive, ambiguous), and keep images on disk rather than in your context.

| Channel | What it reveals | Notes |
|---|---|---|
| **Accessibility tree / DOM snapshot** | Every control with role, name, value, state (disabled, required, checked, expanded), and options of native selects | Primary channel. Take one on every state you visit. |
| **Screenshot** | Layout, overlap, truncation, colour, icons, charts, anything visual | Use for visual checks and for evidence. Name files by state ID. |
| **Network observation** (browser devtools or the tool's network log) | Option lists, enum values, validation messages, hidden fields, record counts, IDs, error payloads | **Read-only observation of traffic the UI itself generates.** Do not hand-craft or replay requests, and do not call APIs outside the UI unless the user authorises it. |
| **Console log** | JavaScript errors, failed requests, deprecation noise that points at broken features | Capture after each significant action. |
| **Hidden and attribute-level detail** | `disabled`, `readonly`, `maxlength`, `min`, `max`, `pattern`, `placeholder`, `aria-describedby`, hidden inputs, `data-*` | Via snapshot or DOM evaluation. |
| **Navigation sources** | Sidebar, top bar, breadcrumbs, user menu, settings gear, "More" menus, command palette, global search, footer links, quick-create buttons | Compare them: an entry present in one but not another is a finding or a hidden screen. |
| **In-app help** | Tooltips, helper text, empty-state copy, onboarding wizards, release notes, help links | These state rules in the product's own words: gold for oracles. |
| **Behavioural probing** | Hover reveals, focus order, keyboard shortcuts, right-click menus, responsive layout at several widths | |
| **Role switching** | Different menus, fields and actions per role | Repeat recon per role at least at the navigation level. |
| **Outputs** | Exports, downloads, printouts, PDFs, email previews, notifications | Where internal data becomes a deliverable. |

If your host cannot read the network or console, say so in `meta.json` limitations and lean harder on the other channels.

## 2. What counts as navigation

Anything that changes what the user is looking at, whether or not the URL changes. Treat all of these as nodes in the map:

- Sidebar and top-bar menu items, including collapsed groups and "More".
- **Tabs, nested tabs, tabs inside tabs.**
- **Tab-like sections**: pills, segmented controls, vertical side-menus inside a page, accordions, collapsible cards, steppers and wizards, stacked "step 1/2/3" forms.
- Modals, drawers, side panels, popovers, inline expanders.
- Detail pages reached from list rows, and the sub-tabs inside those.
- Row-action menus (kebab, "...", right-click).
- Wizards with conditional steps (record which answers lead to which steps).
- Pagination, page-size selectors, "load more", infinite scroll.
- User menu, profile, preferences, notifications, search results pages, error and 404 pages.

Name every node by its **path**: `Module > Tab > Subtab > Section > Control`. The same path format is used in the atlas, the test cases and the report, so keep it consistent.

## 3. The crawl algorithm and state signature

A **state** is what the user sees at a moment. Define its signature as:

`URL (path + meaningful query/hash) | active tab path | open overlay (modal/drawer name, if any) | selected role | short hash of the visible control labels`

Two visits with the same signature are the same state; do not process it twice. This is what stops loops and what proves you are finished.

```
frontier  = [landing state after login]
visited   = {}

while frontier not empty:
    state = pick next   # depth-first inside a module so nested tabs finish before moving on;
                        # breadth-first across modules
    if signature(state) in visited: continue
    capture snapshot (+ screenshot when visual detail matters)
    record node in 01-app-map.md and a row in 00-progress.md
    list every interactive element that could lead to a NEW state:
        tabs, pills, menu items, links, buttons that open overlays, row actions, expanders
    for each such element:
        activate it (read-only: never press Save/Submit/Delete here)
        if it produced a new signature -> add to frontier
        return to the previous state (close overlay, or navigate back)
    mark visited
```

Depth-first within a module matters because nested tabs are only reachable by descending. After each descent, **come back and take the next sibling** so no sibling is skipped.

If the app keeps state when you switch tabs (a filter stays applied, a value stays typed), note it: it is both a navigation fact and a future test.

### Pseudo-tabs and SPA state switches

Many enterprise apps switch views without changing the URL. Detect them by:

- ARIA `role="tab"`, `role="tablist"`, `aria-selected`, `aria-controls`.
- Repeated sibling elements with active/inactive classes that change a visible panel.
- Buttons whose labels match section names and whose click causes a DOM mutation but no navigation.
- A visible panel selector (`[role="tabpanel"]:visible`) changing while the URL stays constant.

Always scope locators and snapshots to the **active visible panel**. Inactive panels are often still mounted in the DOM; reading them produces false observations and stale values.

## 4. Expand-everything checklist

On every page, work through this list. Anything not applicable is a one-second check.

- [ ] All tabs, then all tabs inside each tab, to the deepest level.
- [ ] All pills, segmented controls, side-menus, accordions, collapsible cards.
- [ ] All "Add / New / Create" forms: open each and inventory it **without saving**.
- [ ] Row actions on a sample of rows: rows with different statuses, ages, owners. Different rows expose different actions.
- [ ] Open the first item of every list, then one item of each distinct status or type.
- [ ] Every dropdown: open it and capture **every option**; scroll long lists; note whether it is searchable, multi-select, or loads options lazily.
- [ ] Every toggle and checkbox that may reveal or hide other fields: flip it (read-only: do not save) and record what appears.
- [ ] Table features: column chooser, sort on each column, each filter and its options, saved views, page size, bulk-select, inline edit, row expansion, totals row.
- [ ] Toolbar and overflow menus: import, export, print, templates, bulk actions, settings cog.
- [ ] Empty states (a fresh screen with no data), loading states, error states you can trigger harmlessly.
- [ ] Help icons, info tooltips, "?" links, banners, badges and counters (what do they count?).
- [ ] The profile or account area, notification settings, preferences, API-key or integration pages (look only; do not generate keys).
- [ ] Footer, version number, "About", release notes: record the visible build/version in `meta.json`.
- [ ] Resize to a narrow and a tablet width; menus often rearrange and reveal different items.

## 5. Hard-to-reach content

| Situation | What to do |
|---|---|
| Virtualised tables or infinite scroll (only visible rows exist in the DOM) | Scroll in steps and collect; or use page-size controls; or rely on export for the full set. Note what you could not see. |
| Content in iframes or shadow DOM | Use a tool that pierces frames, or take screenshots and read visually; note the limitation. |
| Canvas charts | Read the legend, hover tooltips, any "view as table" or export; compare to the underlying list screens. |
| Date pickers, rich-text editors, drag-and-drop, sliders, colour pickers | Drive them through keyboard where possible; otherwise record how you operated them. |
| File uploads | Prepare small benign files of the accepted types (and a few wrong ones) in the workspace; never upload real personal data. |
| Auto-logout or session expiry mid-crawl | Detect the login page, sign in again, resume from the ledger. |
| CAPTCHA, MFA, email-link verification | Ask the user to complete it, then continue. |
| Features behind feature flags or licences | Note "visible but disabled/locked" and the exact message; do not try to bypass. |
| Slow or async screens | Wait for a stable snapshot (two identical snapshots a moment apart) before recording. |
| Anything you cannot operate | Record it as **unreached** with the reason. Unreached is honest; skipped silently is not. |

## 6. Read-only first, mutate later

Pass 1 (recon and atlas) changes nothing: it opens and closes, it does not save. This keeps the environment clean and lets you build the model before you touch the data. Pass 2 (perturbation experiments and test execution) mutates, using `QA_` fixtures and the config-change ledger described in `04-execution-and-defects.md`.

Exception: some screens only reveal their fields after a record exists (for example a detail page with no creation form). Create the minimum `QA_` record needed, log it as a fixture, and continue.

## 7. The progress ledger

Keep `01-app-map.md` as the map and `00-progress.md` as the ledger. Update the ledger after every module, not at the end. A ledger row:

```
| State ID | Path | Role | Signature | Status (todo/visited/unreached) | Atlas rows added | Notes |
```

State IDs are short and stable (`S-014`). Screenshots use the same ID (`evidence/screenshots/S-014.png`). If your context resets, a fresh agent must be able to read these two files, see which states are done, and continue.

Also keep a phase checkpoint at the top of `00-progress.md`:

```
Phase: 2 — Atlas
Modules complete: Employees, Leave
Modules in progress: Payroll (tabs 1-3 of 7)
Open blockers: none
Last updated: 2026-11-04T14:20:00Z
```

## 8. Completeness checks

Do this before leaving Phase 1. Reconcile from several angles and expect each to find something the previous missed:

1. **Menu reconciliation.** Count navigation entries per source (sidebar, top bar, user menu, command palette). Every entry has a ledger row.
2. **Search sweep.** Use the global search or command palette with common words (setting, report, list, new, add, config, policy, rule, template, import) and see what screens come up. Compare with the ledger.
3. **Link sweep.** Every link or button seen in snapshots that leads somewhere has a destination in the ledger.
4. **Role sweep.** Repeat the navigation-level crawl for each role and diff the menus.
5. **Cross-reference sweep.** Every dropdown that lists records (departments, grades, tax profiles, templates) points to a place where those records are managed. Is that place in the ledger?
6. **Count sanity.** Badges and counters ("Pending: 12") should match the list they point to: both a completeness check and a first test.

Orphans found this way go back on the frontier.

## 9. Signals of hidden logic

Flag these in the map; each is a pointer to a rule you must understand in Phase 3.

- Fields that are disabled, greyed, or absent until something else is set.
- Labels like "(required if...)", "based on", "as per policy", "default from", "overrides".
- Confirmation dialogs, warnings, banners, "this will affect N records".
- Counters and badges, status chips with many values, colour-coded rows.
- Effective-date fields, "from/to" ranges, period selectors, "locked" or "closed" states.
- Multiple places to set what looks like the same thing (company default, department level, individual override): a precedence rule is hiding there.
- Values that are displayed but cannot be edited (computed fields): what are they computed from?
- Dropdown options that differ between two screens or two roles.
- Tabs that disappear or become read-only after a record reaches a status.
- "Save", "Save & close", "Save & add another", "Submit", "Approve" on the same form: different lifecycle paths.
- Import/export screens: they define a data contract you can test round-trip.

## 10. Recon anti-patterns

- **Clicking Save during recon.** It mutates the environment before you have a model or a cleanup plan.
- **Trusting the URL alone.** SPAs change panels without changing the URL.
- **Reading inactive tab panels.** They may contain stale or hidden values.
- **Treating a screenshot as the whole truth.** It misses disabled state, options, tooltips and hidden fields.
- **Stopping at the first level of tabs.** Enterprise depth is usually two or three levels down.
- **Ignoring empty states.** They often contain the "create your first..." path and reveal required setup order.
- **Calling a menu item "missing" without checking roles and feature flags.** Note what you observed and from which role.
- **Declaring recon complete without the six completeness checks.** They exist because each finds different orphans.
