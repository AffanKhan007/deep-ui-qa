"""Shared constants, loading, validation and coverage helpers for deep-ui-qa.

This module is intentionally dependency-free (standard library only) so it can run
before the Excel dependencies are installed. build_report.py imports openpyxl
separately.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"

STATUSES = [
    "Pass",
    "Fail",
    "Blocked",
    "Needs Clarification",
    "Observation",
    "Not Run",
]

SEVERITIES = ["Critical", "High", "Medium", "Low", "Enhancement", "None"]

CATEGORIES = [
    "UI & Content",
    "Validation & Boundary",
    "CRUD & Lifecycle",
    "Business Rules & Calculation",
    "Cross-Module Ripple",
    "Workflow & State",
    "Roles & Permissions",
    "Data Volume & Search",
    "Time & Dates",
    "Outputs & Documents",
    "Resilience & Concurrency",
    "Accessibility & Locale",
    "Security & Privacy",
    "Other",
]

DEFECT_TYPES = [
    "Functional",
    "Calculation",
    "Validation",
    "Workflow/State",
    "Permission/Security",
    "Data Integrity",
    "Integration",
    "UI/UX",
    "Accessibility",
    "Performance",
    "Content/Localization",
    "Other",
]

DEFECT_STATUSES = [
    "Open",
    "In Progress",
    "Retest",
    "Fixed",
    "Won't Fix",
    "Duplicate",
    "Not a Bug",
]

REL_TYPES = [
    "enables",
    "hides",
    "filters",
    "populates",
    "computes",
    "validates",
    "permits",
    "schedules",
    "precedence",
    "locks",
    "notifies",
    "cascades",
    "duplicates",
]

CONFIDENCES = ["High", "Medium", "Low"]

QUESTION_TYPES = ["Question", "Assumption", "Limitation", "Not Tested", "Conflict"]

CONTROLS = [
    "text",
    "textarea",
    "number",
    "currency",
    "date",
    "datetime",
    "time",
    "select",
    "multiselect",
    "searchable-select",
    "radio",
    "checkbox",
    "toggle",
    "file",
    "button",
    "link",
    "table",
    "column",
    "filter",
    "tab",
    "menu",
    "chart",
    "badge",
    "computed",
    "other",
]

PRIORITIES = ["P0", "P1", "P2", "P3"]

ARTIFACTS = {
    "meta": ("meta.json", None),
    "atlas": ("02-field-atlas.json", "controls"),
    "relationships": ("03-relationships.json", "relationships"),
    "test_cases": ("05-test-cases.json", "test_cases"),
    "defects": ("06-defects.json", "defects"),
    "fixtures": ("07-fixtures-and-config-ledger.json", "fixtures"),
    "config_changes": ("07-fixtures-and-config-ledger.json", "config_changes"),
    "questions": ("08-open-questions.json", "items"),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str, fallback: str = "app") -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or fallback


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


def as_text(value: Any, sep: str = "; ") -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return sep.join(as_text(v) for v in value if as_text(v))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def steps_text(value: Any) -> str:
    items = as_list(value)
    if not items:
        return ""
    if len(items) == 1 and isinstance(items[0], str) and "\n" in items[0]:
        return items[0].strip()
    lines = []
    for index, item in enumerate(items, start=1):
        text = as_text(item)
        if not text:
            continue
        lines.append(f"{index}. {text}")
    return "\n".join(lines)


def evidence_text(value: Any) -> str:
    items = as_list(value)
    out = []
    for item in items:
        if isinstance(item, dict):
            path = as_text(item.get("path") or item.get("file") or "")
            note = as_text(item.get("note") or item.get("description") or "")
            if path and note:
                out.append(f"{path} ({note})")
            elif path:
                out.append(path)
            elif note:
                out.append(note)
        else:
            text = as_text(item)
            if text:
                out.append(text)
    return "\n".join(out)


def oracle_text(value: Any) -> str:
    if isinstance(value, dict):
        kind = as_text(value.get("type"))
        source = as_text(value.get("source"))
        confidence = as_text(value.get("confidence"))
        description = as_text(value.get("description"))
        parts = [p for p in [kind, source] if p]
        text = " — ".join(parts) if parts else ""
        if confidence:
            text = f"{text} ({confidence})" if text else f"({confidence})"
        if description:
            text = f"{text}: {description}" if text else description
        return text
    return as_text(value)


def read_json(path: Path) -> tuple[Any, str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except FileNotFoundError:
        return None, f"missing file: {path.name}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path.name}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
    except OSError as exc:
        return None, f"cannot read {path.name}: {exc}"


def _collection(data: Any, key: str) -> list:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        value = data.get(key)
        if isinstance(value, list):
            return value
        if value is None:
            return []
    return []


def load_workspace(workspace: str | Path) -> dict:
    """Load every artifact, tolerating missing files so validation can report them."""
    ws = Path(workspace).expanduser().resolve()
    loaded: dict[str, Any] = {"workspace": ws, "errors": []}

    meta, err = read_json(ws / "meta.json")
    if err:
        loaded["errors"].append(err)
    loaded["meta"] = meta if isinstance(meta, dict) else {}

    for key, (filename, collection_key) in ARTIFACTS.items():
        if key == "meta":
            continue
        data, err = read_json(ws / filename)
        if err:
            loaded["errors"].append(err)
        loaded[key] = _collection(data, collection_key) if collection_key else data

    return loaded


def _issue(level: str, code: str, message: str, ref: str = "") -> dict:
    return {"level": level, "code": code, "message": message, "ref": ref}


def _required(record: dict, fields: Iterable[str], kind: str, ref: str, issues: list) -> None:
    for field in fields:
        value = record.get(field)
        missing = value is None
        if isinstance(value, str):
            missing = not value.strip()
        elif isinstance(value, (list, tuple, dict, set)):
            missing = len(value) == 0
        if missing:
            issues.append(_issue("error", "missing_field", f"{kind} {ref} is missing required field '{field}'", ref))


def _enum(record: dict, field: str, allowed: list, kind: str, ref: str, issues: list, required: bool = False) -> None:
    value = record.get(field)
    if value in (None, ""):
        if required:
            issues.append(_issue("error", "missing_field", f"{kind} {ref} is missing required field '{field}'", ref))
        return
    if value not in allowed:
        issues.append(
            _issue(
                "error",
                "bad_enum",
                f"{kind} {ref} has invalid {field} '{value}'. Allowed: {', '.join(allowed)}",
                ref,
            )
        )


def _evidence_paths(value: Any) -> list[str]:
    paths = []
    for item in as_list(value):
        if isinstance(item, dict):
            path = as_text(item.get("path") or item.get("file") or "")
        else:
            path = as_text(item)
        if path:
            paths.append(path)
    return paths


def _missing_evidence(workspace: Path, value: Any) -> list[str]:
    missing = []
    for path_text in _evidence_paths(value):
        if path_text.startswith(("http://", "https://", "evidence:")):
            continue
        path = Path(path_text)
        candidate = path if path.is_absolute() else workspace / path
        if not candidate.exists():
            missing.append(path_text)
    return missing


def _unique_ids(records: list, kind: str, issues: list) -> set:
    seen = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(_issue("error", "bad_record", f"{kind}[{index}] is not an object", f"{kind}[{index}]"))
            continue
        rid = as_text(record.get("id"))
        if not rid:
            issues.append(_issue("error", "missing_id", f"{kind}[{index}] is missing 'id'", f"{kind}[{index}]"))
            continue
        if rid in seen:
            issues.append(_issue("error", "duplicate_id", f"Duplicate {kind} id '{rid}'", rid))
        seen.add(rid)
    return seen


SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "error"),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "error"),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"), "error"),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "error"),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]{20,}=*"), "warning"),
    (
        "url_credentials",
        re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
        "error",
    ),
    (
        "password_assignment",
        re.compile(r"(?i)\b(?:password|passwd|pwd)\b\s*[:=]\s*[\"']?([^\s\"'<>]{4,})"),
        "warning",
    ),
    (
        "secret_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|client[_-]?secret|access[_-]?token|refresh[_-]?token)\b"
            r"\s*[:=]\s*[\"']?([A-Za-z0-9_\-]{12,})"
        ),
        "warning",
    ),
]

SECRET_PLACEHOLDERS = (
    "<",
    "$",
    "{",
    "[",
    "***",
    "redacted",
    "your-",
    "your_",
    "example",
    "placeholder",
    "changeme",
    "change-me",
    "dummy",
    "fake",
    "sample",
    "xxx",
    "todo",
    "none",
    "null",
)


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    return any(lowered.startswith(token) or lowered == token for token in SECRET_PLACEHOLDERS)


def scan_secrets(workspace: str | Path) -> list:
    ws = Path(workspace)
    issues: list = []
    extensions = {".md", ".json", ".txt", ".py", ".log", ".csv", ".yaml", ".yml", ".ini", ".env"}
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    for path in ws.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for name, pattern, level in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                captured = ""
                if match.groups():
                    captured = match.group(1)
                if captured and _looks_like_placeholder(captured):
                    continue
                issues.append(
                    _issue(
                        level,
                        "possible_secret",
                        f"Possible {name} in {path.name}:{line_number}. Remove it or replace with a redacted placeholder.",
                        f"{path.name}:{line_number}",
                    )
                )
    return issues


def validate_workspace(loaded: dict, include_secret_scan: bool = True) -> list:
    """Validate a loaded workspace. Returns a list of issue dicts with level/code/message/ref."""
    issues: list = []
    ws = loaded["workspace"]

    for error in loaded.get("errors", []):
        issues.append(_issue("error", "load_error", error))

    meta = loaded.get("meta") or {}
    if not meta:
        issues.append(_issue("error", "missing_meta", "meta.json is missing or empty"))
    else:
        if meta.get("staging_confirmed") is not True:
            issues.append(
                _issue(
                    "warning",
                    "staging_unconfirmed",
                    "meta.json does not confirm staging. Do read-only recon only until confirmed.",
                )
            )
        if not as_text(meta.get("app")):
            issues.append(_issue("error", "missing_meta", "meta.json is missing 'app'"))
        if not as_text(meta.get("url")):
            issues.append(_issue("warning", "missing_meta", "meta.json is missing 'url'"))

    controls = loaded.get("atlas") or []
    relationships = loaded.get("relationships") or []
    cases = loaded.get("test_cases") or []
    defects = loaded.get("defects") or []
    fixtures = loaded.get("fixtures") or []
    config_changes = loaded.get("config_changes") or []
    questions = loaded.get("questions") or []

    control_ids = _unique_ids(controls, "control", issues)
    relationship_ids = _unique_ids(relationships, "relationship", issues)
    case_ids = _unique_ids(cases, "test case", issues)
    defect_ids = _unique_ids(defects, "defect", issues)
    _unique_ids(fixtures, "fixture", issues)
    _unique_ids(config_changes, "config change", issues)
    _unique_ids(questions, "question", issues)

    # Atlas
    for control in controls:
        if not isinstance(control, dict):
            continue
        ref = as_text(control.get("id")) or "control"
        _required(control, ["id", "module", "path", "label", "control"], "control", ref, issues)
        _enum(control, "control", CONTROLS, "control", ref, issues)
        tested_by = as_list(control.get("tested_by"))
        reason = as_text(control.get("not_tested_reason"))
        if not tested_by and not reason:
            issues.append(
                _issue(
                    "warning",
                    "uncovered_control",
                    f"Control {ref} has no tested_by case and no not_tested_reason.",
                    ref,
                )
            )
        for case_id in tested_by:
            if as_text(case_id) not in case_ids:
                issues.append(
                    _issue("error", "bad_ref", f"Control {ref} references missing test case '{case_id}'.", ref)
                )

    # Relationships
    for relationship in relationships:
        if not isinstance(relationship, dict):
            continue
        ref = as_text(relationship.get("id")) or "relationship"
        _required(relationship, ["id", "source", "target", "type", "description"], "relationship", ref, issues)
        _enum(relationship, "type", REL_TYPES, "relationship", ref, issues)
        _enum(relationship, "confidence", CONFIDENCES, "relationship", ref, issues)
        verified_by = as_list(relationship.get("verified_by"))
        reason = as_text(relationship.get("not_tested_reason"))
        if not verified_by and not reason:
            issues.append(
                _issue(
                    "warning",
                    "uncovered_relationship",
                    f"Relationship {ref} has no verified_by case and no not_tested_reason.",
                    ref,
                )
            )
        for case_id in verified_by:
            if as_text(case_id) not in case_ids:
                issues.append(
                    _issue("error", "bad_ref", f"Relationship {ref} references missing test case '{case_id}'.", ref)
                )

    # Test cases
    for case in cases:
        if not isinstance(case, dict):
            continue
        ref = as_text(case.get("id")) or "test case"
        _required(
            case,
            ["id", "module", "path", "title", "status", "expected", "actual"],
            "test case",
            ref,
            issues,
        )
        _enum(case, "status", STATUSES, "test case", ref, issues, required=True)
        _enum(case, "category", CATEGORIES, "test case", ref, issues)
        _enum(case, "priority", PRIORITIES, "test case", ref, issues)
        _enum(case, "severity", SEVERITIES, "test case", ref, issues)
        _enum(case, "defect_type", DEFECT_TYPES, "test case", ref, issues)
        for field in ("category", "technique", "priority", "reason"):
            if not as_text(case.get(field)):
                issues.append(
                    _issue(
                        "warning",
                        "missing_quality_field",
                        f"Test case {ref} is missing '{field}'. The quality rubric expects it.",
                        ref,
                    )
                )
        if not case.get("oracle"):
            issues.append(
                _issue(
                    "warning",
                    "missing_oracle",
                    f"Test case {ref} has no oracle. Expected results must be independently justified.",
                    ref,
                )
            )
        status = case.get("status")
        evidence = as_list(case.get("evidence"))
        notes = as_text(case.get("notes"))
        actual = as_text(case.get("actual"))
        expected = as_text(case.get("expected"))
        for missing_path in _missing_evidence(ws, evidence):
            issues.append(
                _issue(
                    "warning",
                    "evidence_path_missing",
                    f"Test case {ref} references evidence that does not exist: {missing_path}",
                    ref,
                )
            )
        if status == "Pass":
            if not actual:
                issues.append(_issue("error", "pass_without_actual", f"Test case {ref} is Pass but has no actual result.", ref))
            if not evidence:
                issues.append(_issue("warning", "pass_without_evidence", f"Test case {ref} is Pass but has no evidence path.", ref))
        if status == "Fail":
            if not evidence:
                issues.append(_issue("error", "fail_without_evidence", f"Test case {ref} is Fail but has no evidence.", ref))
            if case.get("severity") in (None, "", "None"):
                issues.append(_issue("error", "fail_without_severity", f"Test case {ref} is Fail but has no severity.", ref))
            if not case.get("defect_type"):
                issues.append(_issue("error", "fail_without_type", f"Test case {ref} is Fail but has no defect_type.", ref))
            if not expected or not actual:
                issues.append(_issue("error", "fail_without_result", f"Test case {ref} is Fail but expected/actual is empty.", ref))
            linked = [d for d in defects if ref in [as_text(x) for x in as_list(d.get("test_case_ids"))]]
            if not linked:
                issues.append(
                    _issue("error", "fail_without_defect", f"Test case {ref} is Fail but no defect links to it.", ref)
                )
            else:
                if not any(as_text(d.get("suggestion")) for d in linked):
                    issues.append(
                        _issue("error", "fail_without_suggestion", f"Test case {ref} has a defect but no suggestion.", ref)
                    )
        if status in ("Blocked", "Needs Clarification", "Observation", "Not Run"):
            if not notes and not actual:
                issues.append(
                    _issue(
                        "warning",
                        "status_without_explanation",
                        f"Test case {ref} is {status} but has no explanatory note.",
                        ref,
                    )
                )
        for atlas_id in as_list(case.get("atlas_ids")):
            if as_text(atlas_id) not in control_ids:
                issues.append(_issue("error", "bad_ref", f"Test case {ref} references missing control '{atlas_id}'.", ref))
        for relationship_id in as_list(case.get("relationship_ids")):
            if as_text(relationship_id) not in relationship_ids:
                issues.append(
                    _issue("error", "bad_ref", f"Test case {ref} references missing relationship '{relationship_id}'.", ref)
                )

    # Defects
    for defect in defects:
        if not isinstance(defect, dict):
            continue
        ref = as_text(defect.get("id")) or "defect"
        _required(
            defect,
            ["id", "title", "severity", "type", "expected", "actual", "evidence", "suggestion"],
            "defect",
            ref,
            issues,
        )
        _enum(defect, "severity", SEVERITIES, "defect", ref, issues, required=True)
        _enum(defect, "type", DEFECT_TYPES, "defect", ref, issues)
        _enum(defect, "status", DEFECT_STATUSES, "defect", ref, issues)
        for missing_path in _missing_evidence(ws, defect.get("evidence")):
            issues.append(
                _issue(
                    "warning",
                    "evidence_path_missing",
                    f"Defect {ref} references evidence that does not exist: {missing_path}",
                    ref,
                )
            )
        for case_id in as_list(defect.get("test_case_ids")):
            if as_text(case_id) not in case_ids:
                issues.append(
                    _issue("error", "bad_ref", f"Defect {ref} references missing test case '{case_id}'.", ref)
                )

    # Fixtures and config changes
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        ref = as_text(fixture.get("id")) or "fixture"
        _required(fixture, ["id", "name", "purpose"], "fixture", ref, issues)

    for change in config_changes:
        if not isinstance(change, dict):
            continue
        ref = as_text(change.get("id")) or "config change"
        _required(change, ["id", "path", "original", "changed_to", "restored"], "config change", ref, issues)
        restored = change.get("restored")
        if not isinstance(restored, bool):
            issues.append(
                _issue("error", "bad_restored", f"Config change {ref} field 'restored' must be true or false.", ref)
            )
        elif restored is False:
            if not as_text(change.get("notes")):
                issues.append(
                    _issue(
                        "error",
                        "unrestored_config",
                        f"Config change {ref} is not restored and has no explanatory notes.",
                        ref,
                    )
                )
            else:
                issues.append(
                    _issue(
                        "warning",
                        "unrestored_config",
                        f"Config change {ref} is not restored: {as_text(change.get('notes'))}",
                        ref,
                    )
                )

    # Questions
    for question in questions:
        if not isinstance(question, dict):
            continue
        ref = as_text(question.get("id")) or "question"
        _required(question, ["id", "type", "description"], "question", ref, issues)
        _enum(question, "type", QUESTION_TYPES, "question", ref, issues, required=True)

    # Coverage warnings
    modules_with_cases = {as_text(c.get("module")) for c in cases if as_text(c.get("module"))}
    modules_with_controls = {as_text(c.get("module")) for c in controls if as_text(c.get("module"))}
    for module in sorted(modules_with_controls - modules_with_cases):
        issues.append(
            _issue("warning", "module_without_cases", f"Module '{module}' has controls but no test cases.", module)
        )

    roles = {as_text(c.get("role")) for c in cases if as_text(c.get("role"))}
    if cases and not roles:
        issues.append(_issue("warning", "no_role_coverage", "No test case records a role. Permission coverage is unproven."))

    if not cases:
        issues.append(_issue("warning", "no_cases", "No test cases recorded yet."))
    if not controls:
        issues.append(_issue("warning", "no_controls", "No controls recorded yet."))

    if include_secret_scan:
        issues.extend(scan_secrets(ws))

    return issues


def counts_by(items: list, key: str, allowed: list | None = None) -> dict:
    result = {}
    if allowed:
        result = {value: 0 for value in allowed}
    for item in items:
        if not isinstance(item, dict):
            continue
        value = as_text(item.get(key)) or "(blank)"
        result[value] = result.get(value, 0) + 1
    return result


def coverage(loaded: dict) -> dict:
    controls = loaded.get("atlas") or []
    relationships = loaded.get("relationships") or []
    cases = loaded.get("test_cases") or []
    defects = loaded.get("defects") or []

    controls_tested = [c for c in controls if as_list(c.get("tested_by"))]
    relationships_verified = [r for r in relationships if as_list(r.get("verified_by"))]
    status_counts = counts_by(cases, "status", STATUSES)
    severity_counts = counts_by(defects, "severity", SEVERITIES)
    defect_status_counts = counts_by(defects, "status", DEFECT_STATUSES)

    pass_count = status_counts.get("Pass", 0)
    fail_count = status_counts.get("Fail", 0)
    executed = pass_count + fail_count
    pass_rate = (pass_count / executed * 100) if executed else 0.0

    module_rows = {}
    for control in controls:
        module = as_text(control.get("module")) or "(unknown)"
        row = module_rows.setdefault(
            module,
            {
                "module": module,
                "controls": 0,
                "controls_tested": 0,
                "cases": 0,
                "Pass": 0,
                "Fail": 0,
                "Blocked": 0,
                "Needs Clarification": 0,
                "Observation": 0,
                "Not Run": 0,
            },
        )
        row["controls"] += 1
        if as_list(control.get("tested_by")):
            row["controls_tested"] += 1
    for case in cases:
        module = as_text(case.get("module")) or "(unknown)"
        row = module_rows.setdefault(
            module,
            {
                "module": module,
                "controls": 0,
                "controls_tested": 0,
                "cases": 0,
                "Pass": 0,
                "Fail": 0,
                "Blocked": 0,
                "Needs Clarification": 0,
                "Observation": 0,
                "Not Run": 0,
            },
        )
        row["cases"] += 1
        status = as_text(case.get("status"))
        if status in row:
            row[status] += 1
    for row in module_rows.values():
        row["controls_not_tested"] = max(0, row["controls"] - row["controls_tested"])
        row["coverage_pct"] = (
            row["controls_tested"] / row["controls"] * 100 if row["controls"] else 0.0
        )

    category_rows = {}
    for case in cases:
        category = as_text(case.get("category")) or "(uncategorised)"
        row = category_rows.setdefault(
            category,
            {
                "category": category,
                "cases": 0,
                "Pass": 0,
                "Fail": 0,
                "Blocked": 0,
                "Needs Clarification": 0,
                "Observation": 0,
                "Not Run": 0,
            },
        )
        row["cases"] += 1
        status = as_text(case.get("status"))
        if status in row:
            row[status] += 1

    return {
        "controls_total": len(controls),
        "controls_tested": len(controls_tested),
        "controls_not_tested": len(controls) - len(controls_tested),
        "controls_coverage_pct": (len(controls_tested) / len(controls) * 100) if controls else 0.0,
        "relationships_total": len(relationships),
        "relationships_verified": len(relationships_verified),
        "relationships_not_tested": len(relationships) - len(relationships_verified),
        "relationships_coverage_pct": (
            len(relationships_verified) / len(relationships) * 100 if relationships else 0.0
        ),
        "cases_total": len(cases),
        "status_counts": status_counts,
        "severity_counts": severity_counts,
        "defect_status_counts": defect_status_counts,
        "pass_rate": pass_rate,
        "module_rows": sorted(module_rows.values(), key=lambda row: row["module"].lower()),
        "category_rows": sorted(category_rows.values(), key=lambda row: row["category"].lower()),
        "roles": sorted({as_text(c.get("role")) for c in cases if as_text(c.get("role"))}),
    }
