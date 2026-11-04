#!/usr/bin/env python3
"""Lightweight checks for the deep-ui-qa skill package (no PyYAML required)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    skill_path = ROOT / "SKILL.md"
    if not skill_path.exists():
        fail("SKILL.md is missing")

    text = skill_path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md must start with YAML frontmatter delimited by ---")

    frontmatter = match.group(1)
    name_match = re.search(r"^name:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    description_match = re.search(r"^description:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    if not name_match:
        fail("frontmatter is missing 'name'")
    if not description_match:
        fail("frontmatter is missing 'description'")

    name = name_match.group(1).strip()
    description = description_match.group(1).strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        fail(f"invalid skill name '{name}' (use lowercase kebab-case)")
    if name != ROOT.name:
        fail(f"skill name '{name}' does not match directory name '{ROOT.name}'")
    if not (1 <= len(description) <= 1024):
        fail(f"description length is {len(description)}; must be 1-1024 characters")

    lines = text.count("\n") + 1
    if lines > 500:
        print(f"WARN: SKILL.md is {lines} lines; keep it under 500 where possible.")
    else:
        print(f"SKILL.md: {lines} lines, description {len(description)} chars.")

    referenced = set(re.findall(r"references/[A-Za-z0-9_.-]+\.md", text))
    if not referenced:
        fail("SKILL.md does not reference any reference files")
    for relative in sorted(referenced):
        if not (ROOT / relative).exists():
            fail(f"referenced file does not exist: {relative}")
    for path in sorted((ROOT / "references").glob("*.md")):
        relative = f"references/{path.name}"
        if relative not in referenced:
            fail(f"reference file is not mentioned in SKILL.md: {relative}")

    for relative in sorted(set(re.findall(r"scripts/[A-Za-z0-9_.-]+\.py", text))):
        if not (ROOT / relative).exists():
            fail(f"referenced script does not exist: {relative}")

    for required in ["README.md", "LICENSE", "install.sh", "install.ps1"]:
        if not (ROOT / required).exists():
            fail(f"missing repository file: {required}")

    print(f"References: {len(referenced)} linked files.")
    print("Skill package checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
