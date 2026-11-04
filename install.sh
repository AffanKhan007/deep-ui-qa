#!/usr/bin/env bash
# Install the deep-ui-qa Agent Skill for a supported host.
set -euo pipefail

SKILL_NAME="deep-ui-qa"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOPE="global"
HOST="universal"

usage() {
  cat <<'EOF'
Install deep-ui-qa.

Usage:
  ./install.sh [--global | --project] [--host <host>]

Hosts:
  universal  .agents/skills (portable default)
  claude     .claude/skills
  opencode   .opencode/skills or ~/.config/opencode/skills
  codex      .codex/skills
  cursor     .cursor/skills
  windsurf   .windsurf/skills or ~/.codeium/windsurf/skills
  gemini     .gemini/skills
  copilot    .github/skills or ~/.copilot/skills
  all        install to universal, claude, opencode, codex and cursor

Examples:
  ./install.sh --global
  ./install.sh --project --host opencode
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global)
      SCOPE="global"
      shift
      ;;
    --project)
      SCOPE="project"
      shift
      ;;
    --host)
      HOST="${2:-}"
      if [[ -z "$HOST" ]]; then
        echo "Missing value for --host" >&2
        usage
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

destination() {
  local host="$1"
  local project_root="."
  if [[ "$SCOPE" == "global" ]]; then
    case "$host" in
      universal) echo "${HOME}/.agents/skills/${SKILL_NAME}" ;;
      claude) echo "${HOME}/.claude/skills/${SKILL_NAME}" ;;
      opencode) echo "${HOME}/.config/opencode/skills/${SKILL_NAME}" ;;
      codex) echo "${HOME}/.codex/skills/${SKILL_NAME}" ;;
      cursor) echo "${HOME}/.cursor/skills/${SKILL_NAME}" ;;
      windsurf) echo "${HOME}/.codeium/windsurf/skills/${SKILL_NAME}" ;;
      gemini) echo "${HOME}/.gemini/skills/${SKILL_NAME}" ;;
      copilot) echo "${HOME}/.copilot/skills/${SKILL_NAME}" ;;
      *) return 1 ;;
    esac
  else
    case "$host" in
      universal) echo "${project_root}/.agents/skills/${SKILL_NAME}" ;;
      claude) echo "${project_root}/.claude/skills/${SKILL_NAME}" ;;
      opencode) echo "${project_root}/.opencode/skills/${SKILL_NAME}" ;;
      codex) echo "${project_root}/.codex/skills/${SKILL_NAME}" ;;
      cursor) echo "${project_root}/.cursor/skills/${SKILL_NAME}" ;;
      windsurf) echo "${project_root}/.windsurf/skills/${SKILL_NAME}" ;;
      gemini) echo "${project_root}/.gemini/skills/${SKILL_NAME}" ;;
      copilot) echo "${project_root}/.github/skills/${SKILL_NAME}" ;;
      *) return 1 ;;
    esac
  fi
}

install_one() {
  local host="$1"
  local dest
  dest="$(destination "$host")" || {
    echo "Unknown host: $host" >&2
    return 1
  }
  mkdir -p "$dest/references" "$dest/scripts"
  cp "$SRC_DIR/SKILL.md" "$dest/SKILL.md"
  cp -R "$SRC_DIR/references/." "$dest/references/"
  cp -R "$SRC_DIR/scripts/." "$dest/scripts/"
  if [[ -d "$SRC_DIR/assets" ]]; then
    mkdir -p "$dest/assets"
    cp -R "$SRC_DIR/assets/." "$dest/assets/"
  fi
  chmod +x "$dest/scripts/"*.py 2>/dev/null || true
  echo "[+] Installed ${SKILL_NAME} -> ${dest}"
}

if [[ "$HOST" == "all" ]]; then
  for h in universal claude opencode codex cursor; do
    install_one "$h"
  done
else
  install_one "$HOST"
fi

cat <<'EOF'

[OK] Installed. Start a new agent session so the skill is discovered.
    Then ask: "Use deep-ui-qa to audit https://staging.example.com ..."

Requirements:
    Python 3.10+ and openpyxl:   pip install openpyxl
    Optional Playwright:         pip install playwright && playwright install chromium
EOF
