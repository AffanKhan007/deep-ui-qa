#!/usr/bin/env python3
"""Build a styled Excel QA report from a deep-ui-qa workspace.

Usage:
    python scripts/build_report.py <workspace> [--output report.xlsx] [--allow-incomplete]

The script validates the JSON artifacts first. With validation errors it refuses
to build a final report unless --allow-incomplete is passed, in which case the
workbook is clearly marked as a draft.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError as exc:  # pragma: no cover - dependency guidance
    print("openpyxl is required. Install it with: pip install openpyxl", file=sys.stderr)
    print(f"Import error: {exc}", file=sys.stderr)
    raise SystemExit(1)

from qa_common import (
    CATEGORIES,
    CONFIDENCES,
    CONTROLS,
    DEFECT_STATUSES,
    DEFECT_TYPES,
    PRIORITIES,
    QUESTION_TYPES,
    REL_TYPES,
    SEVERITIES,
    STATUSES,
    as_list,
    as_text,
    coverage,
    evidence_text,
    load_workspace,
    oracle_text,
    slugify,
    steps_text,
    validate_workspace,
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

NAVY = "1F3864"
BLUE = "2F5597"
LIGHT_BLUE = "D9E2F3"
PALE_BLUE = "DDEBF7"
ZEBRA = "F2F2F2"
WHITE = "FFFFFF"
GREY = "808080"
BORDER_COLOR = "BFBFBF"

TITLE_FONT = Font(name="Calibri", size=18, bold=True, color=WHITE)
SUBTITLE_FONT = Font(name="Calibri", size=10, color="D9E2F3")
SECTION_FONT = Font(name="Calibri", size=11, bold=True, color=NAVY)
HEADER_FONT = Font(name="Calibri", size=10, bold=True, color=WHITE)
BODY_FONT = Font(name="Calibri", size=10, color="000000")
SMALL_FONT = Font(name="Calibri", size=9, color="404040")
LINK_FONT = Font(name="Calibri", size=10, color="0563C1", underline="single")

THIN = Side(style="thin", color=BORDER_COLOR)
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

STATUS_FILLS = {
    "Pass": PatternFill("solid", fgColor="C6EFCE"),
    "Fail": PatternFill("solid", fgColor="FFC7CE"),
    "Blocked": PatternFill("solid", fgColor="D9D9D9"),
    "Needs Clarification": PatternFill("solid", fgColor="FFEB9C"),
    "Observation": PatternFill("solid", fgColor="DDEBF7"),
    "Not Run": PatternFill("solid", fgColor="EDEDED"),
}

STATUS_FONTS = {
    "Pass": Font(name="Calibri", size=10, bold=True, color="006100"),
    "Fail": Font(name="Calibri", size=10, bold=True, color="9C0006"),
    "Blocked": Font(name="Calibri", size=10, bold=True, color="404040"),
    "Needs Clarification": Font(name="Calibri", size=10, bold=True, color="9C6500"),
    "Observation": Font(name="Calibri", size=10, bold=True, color="1F4E79"),
    "Not Run": Font(name="Calibri", size=10, color="595959"),
}

SEVERITY_FILLS = {
    "Critical": PatternFill("solid", fgColor="C00000"),
    "High": PatternFill("solid", fgColor="FFC7CE"),
    "Medium": PatternFill("solid", fgColor="FFEB9C"),
    "Low": PatternFill("solid", fgColor="DDEBF7"),
    "Enhancement": PatternFill("solid", fgColor="E2EFDA"),
}

SEVERITY_FONTS = {
    "Critical": Font(name="Calibri", size=10, bold=True, color=WHITE),
    "High": Font(name="Calibri", size=10, bold=True, color="9C0006"),
    "Medium": Font(name="Calibri", size=10, bold=True, color="9C6500"),
    "Low": Font(name="Calibri", size=10, bold=True, color="1F4E79"),
    "Enhancement": Font(name="Calibri", size=10, bold=True, color="375623"),
}

SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Enhancement": 4, "None": 5}

ILLEGAL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean(value, limit: int = 32000) -> str:
    text = as_text(value)
    text = ILLEGAL_CHARS.sub("", text)
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def write_cell(ws, row: int, column: int, value, *, font=None, fill=None, alignment=None, border=True):
    cell = ws.cell(row=row, column=column)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        cell.value = value
    else:
        text = clean(value)
        cell.value = text
        if isinstance(text, str) and text.startswith("="):
            cell.data_type = "s"
    cell.font = font or BODY_FONT
    if fill:
        cell.fill = fill
    cell.alignment = alignment or Alignment(vertical="top", wrap_text=True)
    if border:
        cell.border = BORDER
    return cell


def merge_write(ws, row: int, start_col: int, end_col: int, value, *, font=None, fill=None, alignment=None):
    ws.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)
    return write_cell(ws, row, start_col, value, font=font, fill=fill, alignment=alignment)


def section(ws, row: int, title: str, last_col: int = 6) -> int:
    merge_write(
        ws,
        row,
        start_col=1,
        end_col=last_col,
        value=title,
        font=SECTION_FONT,
        fill=PatternFill("solid", fgColor=LIGHT_BLUE),
        alignment=Alignment(vertical="center"),
    )
    ws.row_dimensions[row].height = 20
    return row + 1


def set_widths(ws, widths: list[int]) -> None:
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width


def estimate_height(values: list[str], widths: list[int], cap: int = 120) -> float:
    lines = 1
    for index, value in enumerate(values):
        width = widths[index] if index < len(widths) else 20
        text = clean(value)
        if not text:
            continue
        count = 0
        for part in text.split("\n"):
            count += max(1, math.ceil(len(part) / max(width - 2, 8)))
        lines = max(lines, count)
    return min(cap, max(18, lines * 13.5))


def write_table(
    ws,
    start_row: int,
    headers: list[str],
    rows: list[list],
    widths: list[int],
    *,
    fill_map: dict[int, dict] | None = None,
    font_map: dict[int, dict] | None = None,
    header_height: int = 34,
) -> int:
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=start_row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[start_row].height = header_height

    for row_offset, values in enumerate(rows, start=1):
        row = start_row + row_offset
        for col, value in enumerate(values, start=1):
            fill = None
            font = None
            if fill_map and col in fill_map:
                fill = fill_map[col].get(clean(value))
            if font_map and col in font_map:
                font = font_map[col].get(clean(value))
            if fill is None and row_offset % 2 == 0:
                fill = PatternFill("solid", fgColor=ZEBRA)
            write_cell(ws, row, col, value, fill=fill, font=font)
        ws.row_dimensions[row].height = estimate_height([clean(v) for v in values], widths)

    return start_row + len(rows)


def finish_sheet(ws, last_row: int, last_col: int, freeze: str = "A2") -> None:
    ws.freeze_panes = freeze
    ws.auto_filter.ref = f"A1:{get_column_letter(last_col)}{max(1, last_row)}"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"


def add_list_validation(ws, column_letter: str, values: list[str], last_row: int) -> None:
    validation = DataValidation(
        type="list",
        formula1='"' + ",".join(values) + '"',
        allow_blank=True,
        showDropDown=False,
    )
    validation.error = "Choose a value from the list."
    validation.errorTitle = "Invalid value"
    ws.add_data_validation(validation)
    validation.add(f"{column_letter}2:{column_letter}{max(2, last_row + 200)}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def build_summary(wb: Workbook, loaded: dict, stats: dict, issues: list, *, incomplete: bool) -> None:
    ws = wb.active
    ws.title = "Summary"
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = NAVY
    set_widths(ws, [30, 18, 18, 20, 18, 18])

    merge_write(ws, 1, 1, 6, "Deep UI QA Report", font=TITLE_FONT, fill=PatternFill("solid", fgColor=NAVY))
    ws.row_dimensions[1].height = 30
    meta = loaded.get("meta") or {}
    subtitle = f"{as_text(meta.get('app')) or 'Application'}  |  {as_text(meta.get('environment')) or 'environment unknown'}  |  generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    merge_write(ws, 2, 1, 6, subtitle, font=SUBTITLE_FONT, fill=PatternFill("solid", fgColor=NAVY))

    row = 3
    if incomplete:
        merge_write(
            ws,
            row,
            1,
            6,
            "DRAFT — validation errors remain. Do not deliver until they are fixed.",
            font=Font(name="Calibri", size=11, bold=True, color=WHITE),
            fill=PatternFill("solid", fgColor="C00000"),
            alignment=Alignment(vertical="center"),
        )
        ws.row_dimensions[row].height = 22
        row += 2

    row = section(ws, row, "Engagement", 6)
    pairs = [
        ("App", meta.get("app")),
        ("URL", meta.get("url")),
        ("Environment", meta.get("environment")),
        ("Staging confirmed", "Yes" if meta.get("staging_confirmed") is True else "No / unconfirmed"),
        ("Version / build", meta.get("version")),
        ("Scope", meta.get("scope")),
        ("Depth", meta.get("depth")),
        ("Module", meta.get("module")),
        ("Roles", meta.get("roles")),
        ("Host / browser", f"{as_text(meta.get('host'))} / {as_text(meta.get('browser_tool'))}"),
        ("Viewports", meta.get("viewports")),
        ("Locale / timezone", f"{as_text(meta.get('locale'))} / {as_text(meta.get('timezone'))}"),
        ("Started", meta.get("started_at")),
        ("Finished", meta.get("finished_at")),
    ]
    for index in range(0, len(pairs), 2):
        pair = pairs[index]
        label_col = 1
        value_col = 2
        ws.cell(row=row, column=label_col, value=pair[0]).font = Font(name="Calibri", size=10, bold=True, color=NAVY)
        ws.cell(row=row, column=label_col).fill = PatternFill("solid", fgColor=LIGHT_BLUE)
        ws.cell(row=row, column=label_col).border = BORDER
        ws.cell(row=row, column=label_col).alignment = Alignment(vertical="top")
        merge_write(ws, row, value_col, value_col + 1, pair[1])
        if index + 1 < len(pairs):
            second = pairs[index + 1]
            ws.cell(row=row, column=4, value=second[0]).font = Font(name="Calibri", size=10, bold=True, color=NAVY)
            ws.cell(row=row, column=4).fill = PatternFill("solid", fgColor=LIGHT_BLUE)
            ws.cell(row=row, column=4).border = BORDER
            ws.cell(row=row, column=4).alignment = Alignment(vertical="top")
            merge_write(ws, row, 5, 6, second[1])
        row += 1

    row += 1
    row = section(ws, row, "Results", 6)
    status_header_row = row
    ws.cell(row=row, column=1, value="Status").font = HEADER_FONT
    ws.cell(row=row, column=1).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(row=row, column=1).border = BORDER
    ws.cell(row=row, column=2, value="Count").font = HEADER_FONT
    ws.cell(row=row, column=2).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(row=row, column=2).border = BORDER
    ws.cell(row=row, column=4, value="Severity").font = HEADER_FONT
    ws.cell(row=row, column=4).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(row=row, column=4).border = BORDER
    ws.cell(row=row, column=5, value="Defects").font = HEADER_FONT
    ws.cell(row=row, column=5).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(row=row, column=5).border = BORDER

    status_counts = stats["status_counts"]
    for offset, status in enumerate(STATUSES, start=1):
        r = status_header_row + offset
        ws.cell(row=r, column=1, value=status).fill = STATUS_FILLS.get(status, PatternFill())
        ws.cell(row=r, column=1).font = STATUS_FONTS.get(status, BODY_FONT)
        ws.cell(row=r, column=1).border = BORDER
        ws.cell(row=r, column=2, value=status_counts.get(status, 0)).border = BORDER
        ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")
    total_row = status_header_row + len(STATUSES) + 1
    ws.cell(row=total_row, column=1, value="Total cases").font = Font(name="Calibri", size=10, bold=True)
    ws.cell(row=total_row, column=1).border = BORDER
    ws.cell(row=total_row, column=2, value=stats["cases_total"]).font = Font(name="Calibri", size=10, bold=True)
    ws.cell(row=total_row, column=2).border = BORDER
    ws.cell(row=total_row, column=2).alignment = Alignment(horizontal="center")

    severity_counts = stats["severity_counts"]
    for offset, severity in enumerate(["Critical", "High", "Medium", "Low", "Enhancement"], start=1):
        r = status_header_row + offset
        ws.cell(row=r, column=4, value=severity).fill = SEVERITY_FILLS.get(severity, PatternFill())
        ws.cell(row=r, column=4).font = SEVERITY_FONTS.get(severity, BODY_FONT)
        ws.cell(row=r, column=4).border = BORDER
        ws.cell(row=r, column=5, value=severity_counts.get(severity, 0)).border = BORDER
        ws.cell(row=r, column=5).alignment = Alignment(horizontal="center")
    ws.cell(row=status_header_row + 6, column=4, value="Pass rate").font = Font(name="Calibri", size=10, bold=True)
    ws.cell(row=status_header_row + 6, column=4).border = BORDER
    ws.cell(row=status_header_row + 6, column=5, value=f"{stats['pass_rate']:.1f}%").font = Font(
        name="Calibri", size=10, bold=True
    )
    ws.cell(row=status_header_row + 6, column=5).border = BORDER
    ws.cell(row=status_header_row + 6, column=5).alignment = Alignment(horizontal="center")

    # Charts on the right.
    status_chart = BarChart()
    status_chart.type = "col"
    status_chart.style = 10
    status_chart.title = "Test status"
    status_chart.y_axis.title = "Cases"
    status_chart.height = 7
    status_chart.width = 13
    data = Reference(ws, min_col=2, min_row=status_header_row, max_row=status_header_row + len(STATUSES))
    cats = Reference(ws, min_col=1, min_row=status_header_row + 1, max_row=status_header_row + len(STATUSES))
    status_chart.add_data(data, titles_from_data=True)
    status_chart.set_categories(cats)
    status_chart.legend = None
    ws.add_chart(status_chart, "H4")

    severity_chart = BarChart()
    severity_chart.type = "col"
    severity_chart.style = 10
    severity_chart.title = "Defects by severity"
    severity_chart.y_axis.title = "Defects"
    severity_chart.height = 7
    severity_chart.width = 13
    data = Reference(ws, min_col=5, min_row=status_header_row, max_row=status_header_row + 5)
    cats = Reference(ws, min_col=4, min_row=status_header_row + 1, max_row=status_header_row + 5)
    severity_chart.add_data(data, titles_from_data=True)
    severity_chart.set_categories(cats)
    severity_chart.legend = None
    ws.add_chart(severity_chart, "H22")

    row = total_row + 2
    row = section(ws, row, "Coverage", 6)
    coverage_rows = [
        ("Controls inventoried", stats["controls_total"]),
        ("Controls tested", stats["controls_tested"]),
        ("Controls not tested", stats["controls_not_tested"]),
        ("Control coverage", f"{stats['controls_coverage_pct']:.1f}%"),
        ("Relationships mapped", stats["relationships_total"]),
        ("Relationships verified", stats["relationships_verified"]),
        ("Relationship coverage", f"{stats['relationships_coverage_pct']:.1f}%"),
        ("Test cases", stats["cases_total"]),
        ("Defects", len(loaded.get("defects") or [])),
    ]
    for label, value in coverage_rows:
        ws.cell(row=row, column=1, value=label).font = Font(name="Calibri", size=10, bold=True, color=NAVY)
        ws.cell(row=row, column=1).fill = PatternFill("solid", fgColor=LIGHT_BLUE)
        ws.cell(row=row, column=1).border = BORDER
        merge_write(ws, row, 2, 3, value)
        row += 1

    row += 1
    row = section(ws, row, "Top risks / defects", 6)
    defects = sorted(
        loaded.get("defects") or [],
        key=lambda d: (SEVERITY_RANK.get(as_text(d.get("severity")), 9), as_text(d.get("id"))),
    )
    if defects:
        for defect in defects[:5]:
            ws.cell(row=row, column=1, value=as_text(defect.get("id"))).font = BODY_FONT
            ws.cell(row=row, column=1).border = BORDER
            severity = as_text(defect.get("severity"))
            ws.cell(row=row, column=2, value=severity).fill = SEVERITY_FILLS.get(severity, PatternFill())
            ws.cell(row=row, column=2).font = SEVERITY_FONTS.get(severity, BODY_FONT)
            ws.cell(row=row, column=2).border = BORDER
            merge_write(ws, row, 3, 6, defect.get("title"))
            row += 1
    else:
        merge_write(ws, row, 1, 6, "No defects recorded.")
        row += 1

    row += 1
    row = section(ws, row, "Limitations, assumptions and warnings", 6)
    notes = []
    for limitation in as_list(meta.get("limitations")):
        notes.append(f"Limitation: {as_text(limitation)}")
    for question in loaded.get("questions") or []:
        qtype = as_text(question.get("type"))
        if qtype in ("Limitation", "Assumption", "Conflict", "Not Tested"):
            notes.append(f"{qtype}: {as_text(question.get('description'))}")
    warnings = [issue for issue in issues if issue["level"] == "warning"]
    for warning in warnings[:10]:
        notes.append(f"Warning: {warning['message']}")
    if len(warnings) > 10:
        notes.append(f"... and {len(warnings) - 10} more warnings. See the validation output.")
    if not notes:
        notes.append("None recorded.")
    for note in notes:
        merge_write(ws, row, 1, 6, note, font=SMALL_FONT)
        row += 1

    row += 1
    row = section(ws, row, "How to read this workbook", 6)
    how_to = [
        "Test Cases is the full execution record; Defects is the triage view of failures only.",
        "Status vocabulary: Pass, Fail, Blocked, Needs Clarification, Observation, Not Run.",
        "Pass rate = Pass / (Pass + Fail); Blocked and Not Run are excluded and listed separately.",
        "Coverage is controls tested / controls inventoried. A control is tested when tested_by is set.",
        "Evidence paths are relative to the workspace; open the files next to this workbook.",
        "Every Fail must have evidence, reproduction steps, severity and a suggestion. Drafts may not.",
    ]
    for line in how_to:
        merge_write(ws, row, 1, 6, f"- {line}", font=SMALL_FONT)
        row += 1

    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:F{row}"


# ---------------------------------------------------------------------------
# Detail sheets
# ---------------------------------------------------------------------------


def build_test_cases(wb: Workbook, loaded: dict) -> None:
    ws = wb.create_sheet("Test Cases")
    ws.sheet_properties.tabColor = BLUE
    headers = [
        "ID",
        "Module",
        "Path / Breadcrumb",
        "Title",
        "Category",
        "Technique",
        "Priority",
        "Reason",
        "Role",
        "Preconditions & Test Data",
        "Steps",
        "Oracle (type / source / confidence)",
        "Expected",
        "Actual",
        "Status",
        "Severity",
        "Defect Type",
        "Correlated Modules",
        "Relationships",
        "Atlas Refs",
        "Evidence",
        "Suggestion",
        "Notes",
        "Executed At",
    ]
    widths = [10, 16, 28, 38, 20, 18, 8, 28, 14, 38, 48, 38, 38, 38, 16, 12, 18, 20, 16, 16, 34, 34, 30, 18]
    set_widths(ws, widths)
    rows = []
    for case in loaded.get("test_cases") or []:
        preconditions = as_text(case.get("preconditions"))
        test_data = as_text(case.get("test_data"))
        combined = "\n".join(part for part in [preconditions, test_data] if part)
        rows.append(
            [
                case.get("id"),
                case.get("module"),
                case.get("path"),
                case.get("title"),
                case.get("category"),
                case.get("technique"),
                case.get("priority"),
                case.get("reason"),
                case.get("role"),
                combined,
                steps_text(case.get("steps")),
                oracle_text(case.get("oracle")),
                case.get("expected"),
                case.get("actual"),
                case.get("status"),
                case.get("severity"),
                case.get("defect_type"),
                as_text(case.get("correlated_modules")),
                as_text(case.get("relationship_ids")),
                as_text(case.get("atlas_ids")),
                evidence_text(case.get("evidence")),
                case.get("suggestion"),
                case.get("notes"),
                case.get("executed_at"),
            ]
        )
    last_row = write_table(
        ws,
        1,
        headers,
        rows,
        widths,
        fill_map={15: STATUS_FILLS, 16: SEVERITY_FILLS},
        font_map={15: STATUS_FONTS, 16: SEVERITY_FONTS},
    )
    finish_sheet(ws, last_row, len(headers), freeze="C2")
    add_list_validation(ws, "O", STATUSES, last_row)
    add_list_validation(ws, "P", SEVERITIES, last_row)
    ws.print_title_rows = "1:1"


def build_defects(wb: Workbook, loaded: dict) -> None:
    ws = wb.create_sheet("Defects")
    ws.sheet_properties.tabColor = "C00000"
    headers = [
        "ID",
        "Title",
        "Severity",
        "Type",
        "Module",
        "Path",
        "Test Cases",
        "Environment",
        "Preconditions",
        "Steps",
        "Expected",
        "Actual",
        "Evidence",
        "Impact",
        "Likely Cause",
        "Suggestion",
        "Workaround",
        "Status",
        "Notes",
    ]
    widths = [10, 40, 12, 18, 16, 26, 14, 30, 34, 44, 36, 36, 34, 34, 30, 34, 30, 14, 30]
    set_widths(ws, widths)
    defects = sorted(
        loaded.get("defects") or [],
        key=lambda d: (SEVERITY_RANK.get(as_text(d.get("severity")), 9), as_text(d.get("id"))),
    )
    rows = []
    for defect in defects:
        rows.append(
            [
                defect.get("id"),
                defect.get("title"),
                defect.get("severity"),
                defect.get("type"),
                defect.get("module"),
                defect.get("path"),
                as_text(defect.get("test_case_ids")),
                defect.get("environment"),
                defect.get("preconditions"),
                steps_text(defect.get("steps")),
                defect.get("expected"),
                defect.get("actual"),
                evidence_text(defect.get("evidence")),
                defect.get("impact"),
                defect.get("likely_cause"),
                defect.get("suggestion"),
                defect.get("workaround"),
                defect.get("status"),
                defect.get("notes"),
            ]
        )
    last_row = write_table(
        ws,
        1,
        headers,
        rows,
        widths,
        fill_map={3: SEVERITY_FILLS},
        font_map={3: SEVERITY_FONTS},
    )
    finish_sheet(ws, last_row, len(headers), freeze="B2")
    add_list_validation(ws, "C", SEVERITIES, last_row)
    add_list_validation(ws, "R", DEFECT_STATUSES, last_row)


def build_coverage(wb: Workbook, loaded: dict, stats: dict) -> None:
    ws = wb.create_sheet("Coverage")
    ws.sheet_properties.tabColor = "548235"
    ws.sheet_view.showGridLines = False
    set_widths(ws, [24, 12, 14, 16, 10, 10, 10, 12, 20, 12, 10, 12])

    row = section(ws, 1, "Coverage by module", 12)
    headers = [
        "Module",
        "Controls",
        "Controls Tested",
        "Controls Not Tested",
        "Cases",
        "Pass",
        "Fail",
        "Blocked",
        "Needs Clarification",
        "Observation",
        "Not Run",
        "Coverage %",
    ]
    rows = [
        [
            r["module"],
            r["controls"],
            r["controls_tested"],
            r["controls_not_tested"],
            r["cases"],
            r["Pass"],
            r["Fail"],
            r["Blocked"],
            r["Needs Clarification"],
            r["Observation"],
            r["Not Run"],
            f"{r['coverage_pct']:.1f}%",
        ]
        for r in stats["module_rows"]
    ]
    row = write_table(ws, row, headers, rows, [24, 12, 14, 16, 10, 10, 10, 12, 20, 12, 10, 12])
    merge_write(
        ws,
        row + 1,
        1,
        12,
        "Coverage % = controls tested / controls inventoried. A control is tested when its tested_by field is non-empty.",
        font=SMALL_FONT,
    )
    row += 3

    row = section(ws, row, "Coverage by test category", 12)
    headers = ["Category", "Cases", "Pass", "Fail", "Blocked", "Needs Clarification", "Observation", "Not Run"]
    category_map = {r["category"]: r for r in stats["category_rows"]}
    category_rows = []
    for category in CATEGORIES:
        found = category_map.get(category)
        if found:
            category_rows.append(found)
        else:
            category_rows.append(
                {
                    "category": category,
                    "cases": 0,
                    "Pass": 0,
                    "Fail": 0,
                    "Blocked": 0,
                    "Needs Clarification": 0,
                    "Observation": 0,
                    "Not Run": 0,
                }
            )
    rows = [
        [
            r["category"],
            r["cases"],
            r["Pass"],
            r["Fail"],
            r["Blocked"],
            r["Needs Clarification"],
            r["Observation"],
            r["Not Run"],
        ]
        for r in category_rows
    ]
    row = write_table(ws, row, headers, rows, [30, 10, 10, 10, 12, 20, 12, 10])
    row += 2

    row = section(ws, row, "Relationship coverage", 12)
    headers = ["Metric", "Value", "Notes"]
    rows = [
        ["Relationships mapped", stats["relationships_total"], "Edges in 03-relationships.json"],
        ["Relationships verified", stats["relationships_verified"], "Have at least one verified_by case"],
        ["Relationships not tested", stats["relationships_not_tested"], "Need a ripple case or a stated reason"],
        ["Relationship coverage", f"{stats['relationships_coverage_pct']:.1f}%", "Verified / mapped"],
    ]
    row = write_table(ws, row, headers, rows, [30, 14, 50])
    row += 2

    row = section(ws, row, "Role coverage", 12)
    headers = ["Role", "Cases", "Notes"]
    roles = stats["roles"]
    rows = [[role, sum(1 for c in loaded.get("test_cases") or [] if as_text(c.get("role")) == role), ""] for role in roles]
    if not rows:
        rows = [["(no roles recorded)", 0, "Add role to test cases to prove permission coverage."]]
    row = write_table(ws, row, headers, rows, [30, 10, 50])
    ws.freeze_panes = "A2"


def build_atlas(wb: Workbook, loaded: dict) -> None:
    ws = wb.create_sheet("Field Atlas")
    ws.sheet_properties.tabColor = "7030A0"
    headers = [
        "ID",
        "State",
        "Module",
        "Path",
        "Label",
        "Control",
        "Required",
        "Default",
        "Options",
        "Constraints",
        "Helper Text",
        "Depends On",
        "Affects",
        "Saves How",
        "Roles Visible",
        "Tested By",
        "Not Tested Reason",
        "Notes",
    ]
    widths = [10, 10, 16, 34, 26, 18, 14, 14, 40, 30, 34, 28, 28, 18, 18, 14, 30, 26]
    set_widths(ws, widths)
    rows = []
    for control in loaded.get("atlas") or []:
        rows.append(
            [
                control.get("id"),
                control.get("state_id"),
                control.get("module"),
                control.get("path"),
                control.get("label"),
                control.get("control"),
                control.get("required"),
                control.get("default"),
                as_text(control.get("options"), "; "),
                control.get("constraints"),
                control.get("helper_text"),
                control.get("depends_on"),
                control.get("affects"),
                control.get("saves_how"),
                as_text(control.get("roles_visible")),
                as_text(control.get("tested_by")),
                control.get("not_tested_reason"),
                control.get("notes"),
            ]
        )
    last_row = write_table(ws, 1, headers, rows, widths)
    finish_sheet(ws, last_row, len(headers), freeze="C2")
    # Highlight uncovered controls.
    for row_index in range(2, last_row + 1):
        tested = ws.cell(row=row_index, column=16).value
        reason = ws.cell(row=row_index, column=17).value
        if not tested and not reason:
            ws.cell(row=row_index, column=16).fill = PatternFill("solid", fgColor="FFEB9C")
            ws.cell(row=row_index, column=17).fill = PatternFill("solid", fgColor="FFEB9C")


def build_relationships(wb: Workbook, loaded: dict) -> None:
    ws = wb.create_sheet("Relationships")
    ws.sheet_properties.tabColor = "BF8F00"
    headers = [
        "ID",
        "Source",
        "Target",
        "Type",
        "Description",
        "Evidence",
        "Confidence",
        "Verified By",
        "Not Tested Reason",
    ]
    widths = [10, 36, 36, 16, 44, 40, 12, 16, 30]
    set_widths(ws, widths)
    rows = []
    for relationship in loaded.get("relationships") or []:
        rows.append(
            [
                relationship.get("id"),
                relationship.get("source"),
                relationship.get("target"),
                relationship.get("type"),
                relationship.get("description"),
                relationship.get("evidence"),
                relationship.get("confidence"),
                as_text(relationship.get("verified_by")),
                relationship.get("not_tested_reason"),
            ]
        )
    last_row = write_table(ws, 1, headers, rows, widths)
    finish_sheet(ws, last_row, len(headers), freeze="C2")
    for row_index in range(2, last_row + 1):
        verified = ws.cell(row=row_index, column=8).value
        reason = ws.cell(row=row_index, column=9).value
        if not verified and not reason:
            ws.cell(row=row_index, column=8).fill = PatternFill("solid", fgColor="FFEB9C")
            ws.cell(row=row_index, column=9).fill = PatternFill("solid", fgColor="FFEB9C")


def build_data_config(wb: Workbook, loaded: dict) -> None:
    ws = wb.create_sheet("Test Data & Config")
    ws.sheet_properties.tabColor = "ED7D31"
    ws.sheet_view.showGridLines = False
    set_widths(ws, [10, 34, 34, 26, 14, 40, 34])

    row = section(ws, 1, "Test fixtures", 7)
    headers = ["ID", "Name", "Purpose", "Created Via", "Status", "Cleanup", "Notes"]
    rows = [
        [
            fixture.get("id"),
            fixture.get("name"),
            fixture.get("purpose"),
            fixture.get("created_via"),
            fixture.get("status"),
            fixture.get("cleanup"),
            fixture.get("notes"),
        ]
        for fixture in loaded.get("fixtures") or []
    ]
    row = write_table(ws, row, headers, rows, [10, 34, 34, 26, 14, 40, 34])
    row += 2

    row = section(ws, row, "Configuration changes", 7)
    headers = [
        "ID",
        "Path",
        "Setting",
        "Original",
        "Changed To",
        "Changed At",
        "Role",
        "Reason",
        "Restored",
        "Restored At",
        "Restored Value",
        "Evidence",
        "Notes",
    ]
    set_widths(ws, [10, 36, 24, 14, 14, 20, 12, 28, 10, 20, 14, 32, 34])
    rows = []
    for change in loaded.get("config_changes") or []:
        rows.append(
            [
                change.get("id"),
                change.get("path"),
                change.get("setting"),
                change.get("original"),
                change.get("changed_to"),
                change.get("changed_at"),
                change.get("role"),
                change.get("reason"),
                "Yes" if change.get("restored") is True else "No",
                change.get("restored_at"),
                change.get("restored_value"),
                change.get("evidence"),
                change.get("notes"),
            ]
        )
    last_row = write_table(ws, row, headers, rows, [10, 36, 24, 14, 14, 20, 12, 28, 10, 20, 14, 32, 34])
    for row_index in range(row + 1, last_row + 1):
        if ws.cell(row=row_index, column=9).value == "No":
            for col in range(1, 14):
                ws.cell(row=row_index, column=col).fill = PatternFill("solid", fgColor="FFC7CE")
    ws.freeze_panes = "A2"


def build_questions(wb: Workbook, loaded: dict) -> None:
    ws = wb.create_sheet("Open Questions")
    ws.sheet_properties.tabColor = "808080"
    headers = ["ID", "Type", "Description", "Impact", "Owner", "Status", "Related"]
    widths = [10, 16, 60, 44, 18, 14, 24]
    set_widths(ws, widths)
    rows = []
    for question in loaded.get("questions") or []:
        rows.append(
            [
                question.get("id"),
                question.get("type"),
                question.get("description"),
                question.get("impact"),
                question.get("owner"),
                question.get("status"),
                as_text(question.get("related")),
            ]
        )
    last_row = write_table(ws, 1, headers, rows, widths)
    finish_sheet(ws, last_row, len(headers), freeze="A2")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deep-ui-qa Excel report.")
    parser.add_argument("workspace", help="Workspace directory")
    parser.add_argument("--output", default="", help="Output .xlsx path")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Build a clearly marked draft even when validation errors remain",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    parser.add_argument("--validate-only", action="store_true", help="Validate and print counts, do not build")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        print(f"Workspace not found: {workspace}", file=sys.stderr)
        return 1

    loaded = load_workspace(workspace)
    issues = validate_workspace(loaded)
    errors = [issue for issue in issues if issue["level"] == "error"]
    warnings = [issue for issue in issues if issue["level"] == "warning"]
    stats = coverage(loaded)

    if args.validate_only:
        print(f"Workspace: {workspace}")
        print(
            f"Controls: {stats['controls_total']} ({stats['controls_tested']} tested) | "
            f"Relationships: {stats['relationships_total']} ({stats['relationships_verified']} verified) | "
            f"Cases: {stats['cases_total']} | Defects: {len(loaded.get('defects') or [])}"
        )
        print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
        for issue in errors + warnings:
            print(f"- {issue['level'].upper()} {issue['code']}: {issue['message']}")
        return 1 if errors else 0

    if not loaded.get("test_cases") and not args.allow_incomplete:
        errors.append(
            {
                "level": "error",
                "code": "no_cases",
                "message": "No test cases recorded. Use --allow-incomplete for a draft, or execute Phase 5 first.",
                "ref": "",
            }
        )

    if errors and not args.allow_incomplete:
        print("Validation failed. Fix these errors or use --allow-incomplete for a draft:", file=sys.stderr)
        for issue in errors:
            print(f"- {issue['code']}: {issue['message']}", file=sys.stderr)
        return 1

    app_slug = slugify(as_text((loaded.get("meta") or {}).get("app")) or "app")
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    if args.output:
        output = Path(args.output).expanduser().resolve()
    else:
        output = workspace / f"QA_Report_{app_slug}_{stamp}.xlsx"

    if output.exists() and not args.force:
        print(f"Output already exists: {output}", file=sys.stderr)
        print("Use --force or a different --output.", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.properties.title = f"Deep UI QA Report — {as_text((loaded.get('meta') or {}).get('app'))}"
    wb.properties.creator = "deep-ui-qa"
    wb.properties.description = "Black-box UI QA report generated by deep-ui-qa."

    build_summary(wb, loaded, stats, issues, incomplete=bool(errors))
    build_test_cases(wb, loaded)
    build_defects(wb, loaded)
    build_coverage(wb, loaded, stats)
    build_atlas(wb, loaded)
    build_relationships(wb, loaded)
    build_data_config(wb, loaded)
    build_questions(wb, loaded)

    try:
        wb.save(output)
    except PermissionError:
        print(f"Cannot write {output}. Close the file if it is open in Excel.", file=sys.stderr)
        return 1

    print(f"Report written: {output}")
    print(
        f"Cases: {stats['cases_total']} | "
        f"Pass: {stats['status_counts'].get('Pass', 0)} | "
        f"Fail: {stats['status_counts'].get('Fail', 0)} | "
        f"Defects: {len(loaded.get('defects') or [])} | "
        f"Errors: {len(errors)} | Warnings: {len(warnings)}"
    )
    if errors:
        print("DRAFT: validation errors remain. The Summary sheet is marked accordingly.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
