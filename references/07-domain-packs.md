# 07 Domain packs

Read the pack that matches what you see in Phase 1, and several if the product spans domains. Treat regulatory and statutory details as **hypotheses to confirm with the user**, because rules vary by country and year. A domain pack gives you oracles and scenario seeds; it does not replace the live product's own rules.

## Contents

1. Generic SaaS / admin platform
2. HR, attendance and payroll
3. Finance, billing and accounting
4. E-commerce and orders
5. CRM
6. Ticketing and support
7. Scheduling and booking
8. Cross-domain invariants

---

## 1. Generic SaaS / admin platform

### What to model

- Tenant/workspace, users, roles, invitations, SSO, MFA.
- Plans, seats, limits, trials, upgrades/downgrades, proration, invoices, dunning.
- Settings hierarchy: organization, workspace, team, user, record.
- Notifications, email templates, webhooks, integrations, API keys.
- Audit log, data export, deletion/retention.
- Onboarding, empty states, sample data.

### High-risk oracles

- Seat count and plan limits: can the tenant exceed the limit? What happens at the boundary?
- Upgrade/downgrade proration: independent calculation; credit for unused time; tax.
- Role matrix: owner/admin/member/viewer; invitation vs activation; removal mid-session.
- Tenant isolation: a user in tenant A must not see tenant B's data, even by URL.
- Deletion: what is soft-deleted, what is retained, what is exported, what is irreversible.
- Audit log: who, what, when, old/new value; immutable?
- Notification preferences: respected per channel and per event.
- API keys: visible once, revocable, scoped, never logged.

### Scenario seeds

- Invite a user, change their role, remove them, and check access at each step.
- Upgrade mid-cycle with a discount and tax; compare invoice to an independent calculation.
- Hit the seat limit exactly, then one over; observe the error and the upgrade path.
- Delete a workspace/project and check dependent records, exports and audit.
- Change the organization default timezone; check dates, reports and scheduled jobs.
- Create a viewer, try every edit action, and verify server-side enforcement through normal UI actions.

### Watch-outs

- "Admin" may mean tenant admin or platform admin; do not assume.
- Plan names and limits may be feature-flagged; record the exact plan.
- Trial expiry may be time-based; use a fixture with a near-expiry date if allowed.

---

## 2. HR, attendance and payroll

### What to model

- Employee lifecycle: hire, probation, transfer, promotion, termination, rehire.
- Org structure: company, branch, department, grade, designation, cost center.
- Salary structure: earnings, deductions, employer contributions, benefits.
- Attendance: shifts, rosters, holidays, leave, overtime, late/early, regularization.
- Leave: types, accrual, carry-forward, encashment, negative balance, approval.
- Payroll: inputs, proration, overtime, loans/advances, reimbursements, taxes, run, review, finalise, payslip, bank file.
- Compliance: statutory deductions, filings, year-end, audit.
- Self-service: profile, leave requests, payslips, tax declarations.

### High-risk oracles

- `gross = sum(earnings)`; `net = gross - employee deductions - taxes`; `employer cost = gross + employer contributions`.
- Proration: calendar days vs working days vs 30-day month; join/leave mid-period; unpaid leave.
- Overtime: rate multiplier, holiday/weekend rules, cap, approval.
- Leave accrual: monthly vs annual, probation, contract type, carry-forward cap, encashment.
- Loan/advance: cap (often % of net), recovery order, final settlement, outstanding balance.
- Tax: slabs, exemptions, rebates, surcharge, cess; confirm country/year. Never assume.
- Payroll run: locked period, retroactive changes, arrears, negative net, rounding.
- Final settlement: leave encashment, gratuity, notice pay, loan recovery, asset recovery.
- YTD: sums across runs, reversals, corrections.

### Scenario seeds

- Mid-month joiner with unpaid leave and a loan; independent net pay calculation.
- Employee transferred between departments mid-period; cost center allocation.
- Leave request crossing a month/year boundary; accrual and balance.
- Overtime on a public holiday with a cap and an approval.
- Salary revision effective mid-period; arrears and future proration.
- Termination with leave encashment, loan balance and final settlement.
- Payroll run with a retroactive attendance correction after a previous run.
- Two payroll admins run the same period concurrently; duplicate prevention.

### Watch-outs

- Statutory rates change by country, year and sometimes month. Ask for the exact rule set.
- "Gross" and "net" may include employer contributions in one screen and not another.
- Rounding may happen per line, per component or at total; check all three.
- Attendance imports and biometric integrations can create duplicate or missing days.
- A payroll run may be irreversible; never finalise without explicit permission.

---

## 3. Finance, billing and accounting

### What to model

- Chart of accounts, journals, ledgers, cost centers, dimensions.
- Customers, suppliers, invoices, bills, credit notes, payments, allocations.
- Products/services, price lists, discounts, taxes, currencies.
- Recurring billing, subscriptions, proration, usage, dunning.
- Bank reconciliation, payment gateways, refunds, chargebacks.
- Reports: trial balance, P&L, balance sheet, aging, cash flow, tax.
- Period close, locks, audit trail, approvals.

### High-risk oracles

- Invoice: `total = sum(qty x price) - discount + tax + shipping`; tax inclusive vs exclusive.
- Credit note <= original invoice; refund <= paid; allocation sums to payment.
- `debit = credit` in every journal; trial balance balances.
- AR aging buckets sum to outstanding; aging date basis is consistent.
- Multi-currency: rate date, source, rounding, gain/loss.
- Recurring billing: proration, mid-cycle changes, cancellation, tax.
- Period close: no postings before the lock date; reversals create new entries.
- Discount stacking: order, eligibility, cap, combinability.
- Rounding: line vs total; currency decimals; display vs stored.

### Scenario seeds

- Invoice with a percentage discount, tax, shipping and a partial payment; independent totals.
- Mid-cycle upgrade with proration, tax and a credit note.
- Refund a discounted invoice partially; allocation and balance.
- Multi-currency invoice paid after a rate change; gain/loss.
- Journal with debits and credits across cost centers; trial balance.
- Close the period, then attempt a backdated entry; observe the block.
- Recurring invoice with a skipped cycle and a cancellation.
- Duplicate payment submission; idempotency.

### Watch-outs

- Tax rules are jurisdictional and change; confirm.
- "Paid" may mean payment initiated, captured, settled or reconciled; model the states.
- Rounding differences of one cent are real defects in finance; do not dismiss them.
- Negative invoices/credit notes may have different workflows.
- Currency symbols can hide the underlying currency; check the code.

---

## 4. E-commerce and orders

### What to model

- Catalog: products, variants, SKUs, attributes, media, categories, collections.
- Pricing: list price, sale price, tiered pricing, customer groups, currencies.
- Promotions: coupons, automatic discounts, bundles, buy-one-get-one, free shipping.
- Cart and checkout: guest vs account, address, shipping, tax, payment, order review.
- Inventory: stock, reservation, backorder, multi-location, release.
- Orders: statuses, payment, fulfillment, shipment, delivery, cancellation, return, refund.
- Notifications: order confirmation, shipment, refund, abandoned cart.
- Admin: orders, customers, products, discounts, reports, exports.

### High-risk oracles

- Cart: `subtotal = sum(line qty x unit price)`; discount order; tax; shipping; grand total.
- Discount eligibility: minimum spend, product/category scope, customer group, usage limit, stacking.
- Free-shipping threshold: before vs after discount; exactly at threshold.
- Inventory: reservation on order, release on cancel/refund, no oversell.
- Tax: shipping taxable? discount reduces tax? jurisdiction.
- Payment states: authorized, captured, partially refunded, refunded, failed, chargeback.
- Returns: return <= purchased; refund <= paid; restock vs write-off.
- Fulfillment: partial shipment, split orders, tracking, delivery confirmation.
- Coupon reuse and race conditions.

### Scenario seeds

- Cart exactly at the free-shipping threshold, then one cent below.
- Stack a percentage coupon, a fixed coupon and a category sale; check eligibility and order.
- Buy a variant with low stock, cancel, and verify reservation release.
- Partial return with a discount and tax; refund calculation.
- Guest checkout vs account checkout; address and email validation.
- Payment failure then retry; duplicate order prevention.
- Multi-currency product with a rounded price; tax and total.
- Admin edits an order after payment; what recalculates and what is locked.

### Watch-outs

- Prices may be tax-inclusive in one market and exclusive in another.
- "Discount" may apply before or after tax; the order matters.
- Inventory may be eventual-consistency; do not call a one-second lag a bug without reproduction.
- Shipping rates may be external; note the integration.

---

## 5. CRM

### What to model

- Leads, accounts, contacts, deals/opportunities, activities, notes, attachments.
- Pipelines, stages, probabilities, forecasting, quotas, territories.
- Ownership, teams, sharing rules, role hierarchy.
- Conversion: lead -> account/contact/deal; merge duplicates.
- Email, calls, meetings, tasks, reminders, integrations.
- Reports, dashboards, exports, imports.

### High-risk oracles

- Pipeline value = sum(deal amount) by stage; weighted forecast = amount x probability.
- Stage transitions: allowed paths, required fields, probability defaults, close dates.
- Lead conversion: no duplicate account/contact; source and owner preserved.
- Duplicate detection and merge: which record survives, what is merged, what is lost.
- Ownership change: activities, deals, permissions and reports follow.
- Sharing rules: role hierarchy vs territory vs manual share; precedence.
- Activity reminders: timezone, recurrence, completion.
- Import: dedupe, owner assignment, field mapping, partial failure.
- Forecast: commit vs best case vs pipeline; period boundaries.

### Scenario seeds

- Convert a lead with an existing account; merge behaviour and data loss.
- Move a deal backward in the pipeline; probability and forecast.
- Change account owner; check deals, activities, reports and permissions.
- Duplicate contacts with different casing and phone formats; merge.
- Import leads with missing owner and invalid stage; partial failure.
- Close a deal on the last day of the quarter; forecast period.
- Restricted user shares a record; check visibility and edit rights.

### Watch-outs

- "Pipeline" may include closed-lost deals in some reports; check the filter.
- Probability may be manual or stage-driven; do not assume.
- Duplicate rules may be fuzzy; test case, whitespace and phone formats.
- Email integration may send real email; use a safe test address and ask first.

---

## 6. Ticketing and support

### What to model

- Tickets, requests, incidents, problems, changes (ITSM variants).
- Queues, teams, agents, groups, skills, assignment rules.
- Priorities, impact, urgency, SLA policies, business calendars.
- Statuses, transitions, resolutions, reopen, merge, link, parent/child.
- Channels: email, portal, chat, phone, API.
- Canned responses, macros, knowledge base, attachments.
- CSAT, time tracking, escalations, reports.

### High-risk oracles

- SLA due = created/start time + policy duration, adjusted for business hours, holidays and timezone.
- First response and resolution clocks; pause on customer wait; resume correctly.
- Priority/impact/urgency matrix; SLA selection.
- Status transitions: open -> pending -> resolved -> closed -> reopened; who can do what.
- Assignment: round-robin, load-based, skills; reassignment and ownership.
- Merge: which ticket survives, what happens to SLA, attachments, requester.
- Reopen: count, SLA reset or continue, notification.
- CSAT: one response per ticket, anonymous vs identified.
- Reports: counts by status, queue, agent, SLA breach.

### Scenario seeds

- Ticket created Friday 17:00 with a business-hours SLA; due time across the weekend.
- Customer reply reopens a resolved ticket; SLA behaviour.
- Merge two tickets with different priorities and requesters.
- Reassign a ticket mid-SLA; ownership and clocks.
- Bulk close tickets with required resolution; partial failure.
- Agent without permission tries to change priority; server enforcement.
- Timezone change for the tenant; existing SLA clocks.
- Attachment with a long/unicode filename; download and permissions.

### Watch-outs

- Business calendars and holidays are a common source of SLA defects.
- "Resolved" may stop the clock while "closed" is separate; model both.
- Email replies may create duplicates; check threading.
- Merged tickets can hide data; verify attachments and audit.

---

## 7. Scheduling and booking

### What to model

- Resources: people, rooms, equipment, vehicles.
- Services, durations, buffers, preparation/cleanup time.
- Availability: working hours, exceptions, holidays, time off, shifts.
- Bookings: one-off, recurring, group, waitlist, cancellation, no-show.
- Time zones, daylight saving, customer vs resource timezone.
- Capacity, overbooking rules, deposits, payments.
- Reminders, confirmations, calendar sync.

### High-risk oracles

- Availability = working hours - exceptions - existing bookings - buffers.
- No double booking of the same resource; capacity limits for group bookings.
- Duration + buffer; back-to-back bookings.
- Recurrence: weekly/monthly, last day of month, skipped occurrences, end date.
- Timezone: booking at 09:00 customer time maps to the resource's timezone; DST.
- Cancellation policy: cutoff, fee, refund, waitlist promotion.
- No-show: status, fee, resource release.
- Calendar sync: duplicates, updates, cancellations.

### Scenario seeds

- Book a slot exactly at the end of a buffer; then one minute earlier.
- Customer in a different timezone books across a DST change.
- Recurring monthly booking on the 31st; months with 30 days and February.
- Cancel within and outside the cutoff; fee and refund.
- Two customers book the last slot concurrently; overbooking.
- Resource time off added after bookings exist; conflict handling.
- Group booking at capacity, then one over.
- Reschedule a booking; old slot released, new slot reserved.

### Watch-outs

- Time zones are the most common source of scheduling defects; record both zones.
- DST gaps (spring forward) and overlaps (fall back) need explicit tests.
- "Available" may ignore buffers or preparation time.
- Calendar sync can be eventually consistent; reproduce before calling a bug.

---

## 8. Cross-domain invariants

These hold in almost every business product and are cheap, high-value oracles:

- **Conservation**: totals equal the sum of their parts; nothing appears or disappears.
- **Non-negativity**: stock, balances, quantities and refunds do not go below allowed bounds.
- **Monotonicity**: adding a positive line increases the total; removing it decreases it.
- **Idempotency**: repeating the same action does not double the effect.
- **Persistence**: a saved value survives reload and appears in downstream views.
- **Consistency**: the same fact has the same value and formatting across screens.
- **Authorization**: a role that cannot see an action cannot execute it by URL or API path.
- **Auditability**: a change that matters leaves a trace with actor, time and old/new value.
- **Reversibility**: a reversible action can be undone without corrupting history.
- **Temporal coherence**: effective dates, time zones and period locks agree across modules.
- **Referential integrity**: deleting or archiving a referenced entity does not orphan records silently.
- **Locale coherence**: numbers, dates and currency are formatted and interpreted consistently.

When you find a violation, check whether it is a display issue, a calculation issue, a persistence issue, or a permission issue. The fix and severity differ.
