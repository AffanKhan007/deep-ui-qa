#!/usr/bin/env python3
"""Create a deep-ui-qa workspace with the required artifacts and folders."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from qa_common import SCHEMA_VERSION, now_iso, slugify


SCOPE_TEMPLATE = """# QA scope

## Engagement

- **App:** {app}
- **URL:** {url}
- **Environment:** {environment}
- **Module / scope:** {scope}
- **Depth:** {depth}
- **Started:** {started}

## Objective

<!-- One or two sentences: what decision will this QA run support? -->

## In scope

<!-- Modules, roles, workflows, outputs. -->

## Out of scope

<!-- Explicit exclusions, with the reason. -->

## Roles and access

| Role | Access confirmed | Notes |
|---|---|---|
|  |  |  |

## Rules and specifications provided by the user

<!-- Paste only rules/specs the user explicitly handed you. These are claims to verify, not proof the app is right. -->

## Forbidden actions

<!-- e.g. never finalise payroll, never send email, never delete shared records. -->

## Side effects to watch

<!-- Email, SMS, webhooks, payments, invitations, provisioning. -->

## Time limit and constraints

<!-- Deadline, maintenance window, data restrictions. -->

## Assumptions

<!-- Decisions made to keep moving; each will appear in the report. -->

## Open questions

<!-- Questions for the user; also add them to 08-open-questions.json. -->
"""

PROGRESS_TEMPLATE = """# Progress ledger

Phase: 0 — Intake
Modules complete: none
Modules in progress: none
Open blockers: none
Last updated: {started}

## Phase checkpoints

| Phase | Status | Notes |
|---|---|---|
| 0 Intake | in progress |  |
| 1 Recon | todo |  |
| 2 Atlas | todo |  |
| 3 Model | todo |  |
| 4 Design | todo |  |
| 5 Execute | todo |  |
| 6 Second look | todo |  |
| 7 Report | todo |  |
| 8 Cleanup | todo |  |

## State ledger

| State ID | Path | Role | Signature | Status (todo/visited/unreached) | Atlas rows added | Notes |
|---|---|---|---|---|---|---|
"""

APP_MAP_TEMPLATE = """# App map

A state is anything that changes what the user sees, including tabs, nested tabs, pills, accordions, modals, drawers, wizards and row actions.

Signature format: `URL | active tab path | open overlay | role | hash of visible control labels`.

## Navigation tree

<!-- Indent by depth. Use the same path format as the atlas and test cases. -->

```
App
├── Module
│   ├── Tab
│   │   └── Sub-tab
│   └── ...
└── ...
```

## States

| State ID | Path | Role | Signature | Status | Atlas rows | Notes |
|---|---|---|---|---|---|---|
| S-001 |  |  |  | todo |  |  |

## Unreached

| Path | Reason | What would be needed |
|---|---|---|
|  |  |  |

## Completeness checks

- [ ] Menu reconciliation
- [ ] Search sweep
- [ ] Link sweep
- [ ] Role sweep
- [ ] Cross-reference sweep
- [ ] Count sanity
"""

RULES_TEMPLATE = """# Business rules

One rule per line. Use IF/THEN. Record the source and confidence.

```
RULE-001  IF <condition> THEN <expected behaviour>   [source: <in-app text / user spec / observation / domain convention / hypothesis>]
```

## Rules

| ID | Rule | Source | Confidence | Probed by | Notes |
|---|---|---|---|---|---|
| RULE-001 |  |  |  |  |  |

## Conflicts between oracles

| Rule(s) | Conflict | Question for the user |
|---|---|---|
|  |  |  |
"""

SCENARIOS_TEMPLATE = """# Scenario cards

Scenarios combine modules and put the product in an uncomfortable position. Each needs an independent oracle.

```
SC-001  "<short name>"
  Entities:
  Config:
  Path:
  Oracle:
  Risk:
  Touches:
  Expected:
```

## Scenarios

| ID | Name | Modules touched | Oracle | Risk | Status |
|---|---|---|---|---|---|
| SC-001 |  |  |  |  |  |
"""

CALC_README = """# Independent calculations

Every calculation test needs an expected value computed outside the app.

- One script per scenario or test case: `TC-0031.py`, `SC-021.py`.
- Print the inputs, the formula, and the result with the same precision the UI uses.
- Save the output next to the script (`.txt` or `.json`) and reference it in the test case evidence.
- Do not import the app's code or call its API to compute the expected value.
"""


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deep-ui-qa workspace.")
    parser.add_argument("--app", required=True, help="Application name")
    parser.add_argument("--url", default="", help="Application URL")
    parser.add_argument("--module", default="", help="Module or scope (optional)")
    parser.add_argument(
        "--depth",
        default="deep",
        choices=["quick", "standard", "deep", "exhaustive"],
        help="QA depth (default: deep)",
    )
    parser.add_argument("--workspace", default="", help="Workspace path (default: qa-<app>-<timestamp>)")
    parser.add_argument("--force", action="store_true", help="Write into an existing non-empty workspace")
    args = parser.parse_args()

    started = now_iso()
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    if args.workspace:
        workspace = Path(args.workspace).expanduser().resolve()
    else:
        workspace = (Path.cwd() / f"qa-{slugify(args.app)}-{stamp}").resolve()

    if workspace.exists() and any(workspace.iterdir()) and not args.force:
        print(f"Refusing to overwrite non-empty workspace: {workspace}", file=sys.stderr)
        print("Use --force or choose another --workspace.", file=sys.stderr)
        return 1

    workspace.mkdir(parents=True, exist_ok=True)
    for folder in ["evidence/screenshots", "evidence/snapshots", "evidence/network", "evidence/console", "evidence/outputs", "calc"]:
        (workspace / folder).mkdir(parents=True, exist_ok=True)

    scope = args.module or "Whole application"
    meta = {
        "schema_version": SCHEMA_VERSION,
        "app": args.app,
        "url": args.url,
        "environment": "staging",
        "staging_confirmed": False,
        "version": "",
        "scope": scope,
        "depth": args.depth.capitalize(),
        "module": args.module,
        "roles": [],
        "host": "",
        "browser_tool": "",
        "capabilities": {},
        "viewports": ["1440x900", "390x844"],
        "locale": "",
        "timezone": "",
        "started_at": started,
        "finished_at": "",
        "forbidden_actions": [],
        "limitations": [],
        "workspace_version": SCHEMA_VERSION,
    }
    write_json(workspace / "meta.json", meta)
    write_text(
        workspace / "00-scope.md",
        SCOPE_TEMPLATE.format(
            app=args.app,
            url=args.url or "(not provided)",
            environment="staging (to be confirmed)",
            scope=scope,
            depth=args.depth.capitalize(),
            started=started,
        ),
    )
    write_text(workspace / "00-progress.md", PROGRESS_TEMPLATE.format(started=started))
    write_text(workspace / "01-app-map.md", APP_MAP_TEMPLATE)
    write_json(workspace / "02-field-atlas.json", {"controls": []})
    write_json(workspace / "03-relationships.json", {"relationships": []})
    write_text(workspace / "03-rules.md", RULES_TEMPLATE)
    write_text(workspace / "04-scenarios.md", SCENARIOS_TEMPLATE)
    write_json(workspace / "05-test-cases.json", {"test_cases": []})
    write_json(workspace / "06-defects.json", {"defects": []})
    write_json(
        workspace / "07-fixtures-and-config-ledger.json",
        {"fixtures": [], "config_changes": []},
    )
    write_json(workspace / "08-open-questions.json", {"items": []})
    write_text(workspace / "calc" / "README.md", CALC_README)

    print(f"Workspace created: {workspace}")
    print("Next: fill 00-scope.md and meta.json, then start Phase 1 recon.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
