#!/usr/bin/env python3
"""Smoke test for the deep-ui-qa scripts.

Creates a temporary workspace, writes a small valid dataset, validates it, builds
the workbook and checks the expected sheets. Run from the repository root:

    python tests/smoke_test.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def populate(workspace: Path) -> None:
    meta_path = workspace / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(
        {
            "staging_confirmed": True,
            "version": "2026.10.3",
            "roles": ["Admin", "Payroll Admin"],
            "host": "test",
            "browser_tool": "none",
            "locale": "en-US",
            "timezone": "Asia/Karachi",
            "limitations": ["Manager role not available"],
        }
    )
    write_json(meta_path, meta)

    controls = [
        {
            "id": "A-0001",
            "state_id": "S-001",
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
            "tested_by": ["TC-0002"],
            "not_tested_reason": "",
            "notes": "",
            "evidence": "evidence/snapshots/S-001.html",
        },
        {
            "id": "A-0002",
            "state_id": "S-001",
            "module": "Payroll",
            "path": "Payroll > Run > Summary > Net pay",
            "label": "Net pay",
            "control": "computed",
            "required": "no",
            "default": "empty",
            "options": [],
            "options_count": 0,
            "constraints": "2 decimals",
            "helper_text": "",
            "depends_on": "Gross pay, deductions, taxes",
            "affects": "Payslip; bank file",
            "saves_how": "On Calculate",
            "roles_visible": ["Payroll Admin"],
            "tested_by": ["TC-0001"],
            "not_tested_reason": "",
            "notes": "",
            "evidence": "",
        },
        {
            "id": "A-0003",
            "state_id": "S-002",
            "module": "Payroll",
            "path": "Payroll > Run > Settings > Rounding",
            "label": "Rounding",
            "control": "select",
            "required": "yes",
            "default": "Half-up",
            "options": ["Half-up", "Half-even"],
            "options_count": 2,
            "constraints": "",
            "helper_text": "",
            "depends_on": "",
            "affects": "All calculated amounts",
            "saves_how": "On Save",
            "roles_visible": ["Admin"],
            "tested_by": [],
            "not_tested_reason": "Rounding variants are out of scope for this run.",
            "notes": "",
            "evidence": "",
        },
    ]
    write_json(workspace / "02-field-atlas.json", {"controls": controls})

    relationships = [
        {
            "id": "R-0001",
            "source": "Settings > Loans > Cap",
            "target": "Payroll > Run > Deductions > Loan deduction",
            "type": "computes",
            "description": "The cap limits the loan deduction to a percentage of net pay.",
            "evidence": "Perturbation E-001: cap 30% -> 10% changed deduction 3,000 -> 1,000.",
            "confidence": "High",
            "verified_by": ["TC-0002"],
            "not_tested_reason": "",
        },
        {
            "id": "R-0002",
            "source": "Payroll > Run > Rounding",
            "target": "Payslip > Net pay",
            "type": "computes",
            "description": "Rounding mode changes the final net pay.",
            "evidence": "Static clue from helper text.",
            "confidence": "Medium",
            "verified_by": [],
            "not_tested_reason": "Out of scope in this run.",
        },
    ]
    write_json(workspace / "03-relationships.json", {"relationships": relationships})

    test_cases = [
        {
            "id": "TC-0001",
            "module": "Payroll",
            "path": "Payroll > Run > Summary",
            "title": "Net pay equals gross minus deductions and taxes",
            "category": "Business Rules & Calculation",
            "technique": "Invariant",
            "priority": "P0",
            "reason": "Net pay is the number employees are paid.",
            "role": "Payroll Admin",
            "preconditions": "QA_EMP_01 has gross 10,000, deductions 1,000 and tax 500.",
            "test_data": "QA_EMP_01; August 2026 run",
            "steps": ["Open Payroll > Run > August 2026.", "Calculate QA_EMP_01.", "Read net pay."],
            "oracle": {
                "type": "Calculation",
                "source": "calc/TC-0001.py",
                "confidence": "High",
                "description": "10,000 - 1,000 - 500 = 8,500.",
            },
            "expected": "8,500.00",
            "actual": "8,500.00",
            "status": "Pass",
            "severity": "None",
            "defect_type": "",
            "correlated_modules": ["Employees"],
            "relationship_ids": ["R-0001"],
            "atlas_ids": ["A-0002"],
            "evidence": ["evidence/screenshots/TC-0001.png", "calc/TC-0001.py"],
            "suggestion": "",
            "notes": "",
            "executed_at": "2026-11-04T12:00:00Z",
        },
        {
            "id": "TC-0002",
            "module": "Payroll",
            "path": "Payroll > Run > Deductions",
            "title": "Loan deduction is capped at 30% of net pay",
            "category": "Business Rules & Calculation",
            "technique": "Boundary value analysis",
            "priority": "P0",
            "reason": "Over-deduction directly underpays an employee.",
            "role": "Payroll Admin",
            "preconditions": "QA_EMP_02 has net pay 10,000 and an active loan balance of 8,000; cap is 30%.",
            "test_data": "QA_EMP_02; loan QA_LOAN_01; August 2026 run",
            "steps": [
                "Open Payroll > Run > August 2026.",
                "Add QA_EMP_02 and calculate.",
                "Open the deduction breakdown.",
            ],
            "oracle": {
                "type": "Calculation + in-app policy",
                "source": "Settings > Loans > Cap = 30%; calc/TC-0002.py",
                "confidence": "High",
                "description": "Loan deduction must be <= 30% of net pay; expected 3,000.",
            },
            "expected": "Loan deduction = 3,000.00; net pay = 7,000.00.",
            "actual": "Loan deduction = 4,800.00; net pay = 5,200.00.",
            "status": "Fail",
            "severity": "High",
            "defect_type": "Calculation",
            "correlated_modules": ["Employees", "Loans", "Reports"],
            "relationship_ids": ["R-0001"],
            "atlas_ids": ["A-0001"],
            "evidence": [
                "evidence/screenshots/TC-0002.png",
                "evidence/network/TC-0002.json",
                "calc/TC-0002.py",
            ],
            "suggestion": "Apply the cap after tax and other deductions; add a boundary regression test.",
            "notes": "Reproduced twice; persists after reload.",
            "executed_at": "2026-11-04T12:40:00Z",
        },
        {
            "id": "TC-0003",
            "module": "Payroll",
            "path": "Payroll > Run > Bank file",
            "title": "Bank file download for a finalised run",
            "category": "Outputs & Documents",
            "technique": "CRUD matrix",
            "priority": "P1",
            "reason": "The bank file is the payment instruction.",
            "role": "Payroll Admin",
            "preconditions": "A finalised run exists.",
            "test_data": "QA_RUN_01",
            "steps": ["Open the finalised run.", "Click Download bank file."],
            "oracle": {
                "type": "User spec",
                "source": "Scope: bank file must match the run total.",
                "confidence": "Medium",
                "description": "File total equals the run net total.",
            },
            "expected": "A CSV whose total equals the run net total.",
            "actual": "Download blocked: the test role lacks the export permission.",
            "status": "Blocked",
            "severity": "None",
            "defect_type": "",
            "correlated_modules": ["Reports"],
            "relationship_ids": [],
            "atlas_ids": [],
            "evidence": ["evidence/screenshots/TC-0003.png"],
            "suggestion": "",
            "notes": "Export permission is not available for the provided role.",
            "executed_at": "2026-11-04T13:00:00Z",
        },
        {
            "id": "TC-0004",
            "module": "Payroll",
            "path": "Payroll > Run > Summary",
            "title": "Rounding label is inconsistent with the settings page",
            "category": "UI & Content",
            "technique": "Differential",
            "priority": "P3",
            "reason": "Inconsistent terminology can cause misconfiguration.",
            "role": "Payroll Admin",
            "preconditions": "None.",
            "test_data": "",
            "steps": ["Open Payroll > Run > Summary.", "Compare the rounding label with Settings > Rounding."],
            "oracle": {
                "type": "Consistency invariant",
                "source": "Same setting should use the same label.",
                "confidence": "Medium",
                "description": "The label should match.",
            },
            "expected": "The same label on both screens.",
            "actual": "Summary says 'Rounding method'; settings says 'Rounding mode'.",
            "status": "Observation",
            "severity": "Low",
            "defect_type": "UI/UX",
            "correlated_modules": ["Settings"],
            "relationship_ids": [],
            "atlas_ids": [],
            "evidence": ["evidence/screenshots/TC-0004.png"],
            "suggestion": "Use one label.",
            "notes": "Cosmetic; recorded as an observation.",
            "executed_at": "2026-11-04T13:10:00Z",
        },
    ]
    write_json(workspace / "05-test-cases.json", {"test_cases": test_cases})

    defects = [
        {
            "id": "DEF-0001",
            "title": "Loan deduction exceeds the 30% cap for QA_EMP_02",
            "severity": "High",
            "type": "Calculation",
            "module": "Payroll",
            "path": "Payroll > Run > Deductions",
            "test_case_ids": ["TC-0002"],
            "environment": "staging, build 2026.10.3, Payroll Admin, en-US, UTC+5",
            "preconditions": "QA_EMP_02 net pay 10,000; loan balance 8,000; cap 30%.",
            "steps": [
                "Open Payroll > Run > August 2026.",
                "Add QA_EMP_02 and calculate.",
                "Open the deduction breakdown.",
            ],
            "expected": "Loan deduction <= 3,000.00.",
            "actual": "Loan deduction 4,800.00; net pay 5,200.00.",
            "evidence": ["evidence/screenshots/TC-0002.png", "calc/TC-0002.py"],
            "impact": "Employee is underpaid; payroll cannot be finalised.",
            "likely_cause": "Cap applied to gross pay instead of net (hypothesis).",
            "suggestion": "Apply the cap after tax and other deductions.",
            "workaround": "Manually reduce the deduction before finalising.",
            "status": "Open",
            "notes": "",
            "created_at": "2026-11-04T12:45:00Z",
        }
    ]
    write_json(workspace / "06-defects.json", {"defects": defects})

    write_json(
        workspace / "07-fixtures-and-config-ledger.json",
        {
            "fixtures": [
                {
                    "id": "F-0001",
                    "name": "QA_EMP_02_loan_cap",
                    "purpose": "Loan cap boundary",
                    "created_via": "Employees > Add",
                    "status": "active",
                    "cleanup": "delete after the payroll run",
                    "notes": "",
                }
            ],
            "config_changes": [
                {
                    "id": "C-0001",
                    "path": "Settings > Loans > Cap",
                    "setting": "Cap",
                    "original": "30",
                    "changed_to": "10",
                    "changed_at": "2026-11-04T10:00:00Z",
                    "role": "Admin",
                    "reason": "Perturbation E-001",
                    "restored": True,
                    "restored_at": "2026-11-04T10:10:00Z",
                    "restored_value": "30",
                    "evidence": "evidence/snapshots/E-001.html",
                    "notes": "",
                }
            ],
        },
    )

    write_json(
        workspace / "08-open-questions.json",
        {
            "items": [
                {
                    "id": "Q-0001",
                    "type": "Question",
                    "description": "Should the loan cap apply before or after tax?",
                    "impact": "Affects the expected net pay for TC-0002.",
                    "owner": "Product owner",
                    "status": "Open",
                    "related": ["TC-0002", "R-0001"],
                },
                {
                    "id": "Q-0002",
                    "type": "Limitation",
                    "description": "Manager role was not available, so manager-only approval paths were not tested.",
                    "impact": "Permission coverage is partial.",
                    "owner": "QA",
                    "status": "Open",
                    "related": [],
                },
            ]
        },
    )

    for relative in [
        "evidence/screenshots/TC-0001.png",
        "evidence/screenshots/TC-0002.png",
        "evidence/screenshots/TC-0003.png",
        "evidence/screenshots/TC-0004.png",
        "evidence/network/TC-0002.json",
        "evidence/snapshots/E-001.html",
        "evidence/snapshots/S-001.html",
        "calc/TC-0001.py",
        "calc/TC-0002.py",
    ]:
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("sample evidence\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="deep-ui-qa-smoke-") as temp:
        workspace = Path(temp) / "workspace"
        result = run(
            str(SCRIPTS / "init_workspace.py"),
            "--app",
            "Acme HR",
            "--url",
            "https://staging.example.com",
            "--module",
            "Payroll",
            "--workspace",
            str(workspace),
        )
        assert result.returncode == 0, result.stderr
        assert (workspace / "SKILL.md").exists() is False  # workspace is not the skill

        populate(workspace)

        result = run(str(SCRIPTS / "validate_workspace.py"), str(workspace))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Errors: 0" in result.stdout, result.stdout

        output = workspace / "report.xlsx"
        result = run(str(SCRIPTS / "build_report.py"), str(workspace), "--output", str(output))
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.exists(), result.stdout

        wb = load_workbook(output)
        expected_sheets = [
            "Summary",
            "Test Cases",
            "Defects",
            "Coverage",
            "Field Atlas",
            "Relationships",
            "Test Data & Config",
            "Open Questions",
        ]
        assert wb.sheetnames == expected_sheets, wb.sheetnames
        assert wb["Summary"]["A1"].value == "Deep UI QA Report"
        assert len(wb["Summary"]._charts) == 2, len(wb["Summary"]._charts)
        assert wb["Test Cases"].max_row == 5, wb["Test Cases"].max_row
        assert wb["Test Cases"]["O2"].value == "Pass", wb["Test Cases"]["O2"].value
        assert wb["Test Cases"]["O3"].value == "Fail", wb["Test Cases"]["O3"].value
        assert wb["Defects"].max_row == 2, wb["Defects"].max_row
        assert wb["Field Atlas"].max_row == 4, wb["Field Atlas"].max_row
        assert wb["Relationships"].max_row == 3, wb["Relationships"].max_row
        assert wb["Coverage"]["A3"].value == "Payroll", wb["Coverage"]["A3"].value

        # Negative path: a Fail without evidence or a linked defect must block a final report.
        cases_path = workspace / "05-test-cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        first = cases["test_cases"][0]
        first["status"] = "Fail"
        first["evidence"] = []
        first["severity"] = "High"
        first["defect_type"] = "Functional"
        write_json(cases_path, cases)

        result = run(str(SCRIPTS / "validate_workspace.py"), str(workspace))
        assert result.returncode != 0, "validation should fail for a Fail without evidence/defect"
        assert "fail_without_evidence" in result.stdout, result.stdout
        assert "fail_without_defect" in result.stdout, result.stdout

        result = run(str(SCRIPTS / "build_report.py"), str(workspace), "--output", str(workspace / "blocked.xlsx"))
        assert result.returncode != 0, "build_report should refuse a final report with errors"

        draft = workspace / "draft.xlsx"
        result = run(
            str(SCRIPTS / "build_report.py"),
            str(workspace),
            "--allow-incomplete",
            "--output",
            str(draft),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        draft_wb = load_workbook(draft)
        assert "DRAFT" in str(draft_wb["Summary"]["A3"].value), draft_wb["Summary"]["A3"].value

        print("Smoke test passed.")
        print(f"Workbook: {output}")
        print(f"Sheets: {', '.join(wb.sheetnames)}")
        print("Negative validation and draft path passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
