# 06 Tool compatibility and browser setup

Read at the start of a run, before promising execution. Hosts differ in browser tools, subagents, commands and skill paths. Detect what you have, record it in `meta.json`, and choose the strongest option on the ladder.

## Contents

1. Capability detection
2. The tool ladder
3. Browser setup recipes
4. Authentication and session state
5. Host skill paths
6. Optional slash commands and `AGENTS.md`
7. Browser technique notes
8. Guided mode (no browser)
9. Parallel subagents
10. Security boundaries

---

## 1. Capability detection

At the start of the run, answer these questions:

| Capability | Why it matters | If missing |
|---|---|---|
| Navigate and read the DOM/accessibility tree | Primary recon channel | Screenshots only; slower, less exact |
| Click, type, select, upload | Execute cases | Guided mode |
| Screenshot | Visual evidence | DOM/text evidence only |
| Console log | Detect JS errors | Note limitation |
| Network log | Observe enums, payloads, status codes | Note limitation; rely on UI |
| JavaScript evaluation | Read attributes, hidden fields, computed values | Use snapshots |
| Multiple tabs/contexts | Role and concurrency tests | Sequential re-login |
| Storage state / persistent profile | Reuse login across steps | Re-login manually |
| Download capture | Verify exports/documents | Ask user to download and provide |
| Iframe/shadow DOM piercing | Reach embedded content | Screenshot + note limitation |
| Subagents | Parallel module exploration | Sequential |

Record the chosen tool and limitations in `meta.json`:

```json
{
  "host": "Claude Code",
  "browser_tool": "Playwright MCP",
  "capabilities": {
    "dom_snapshot": true,
    "screenshot": true,
    "console": true,
    "network": true,
    "js_eval": true,
    "multiple_contexts": true,
    "downloads": true,
    "iframes": true
  }
}
```

## 2. The tool ladder

Choose the highest rung that works:

1. **Host-native browser tool.** Best integration: the agent can navigate, snapshot, click, screenshot and inspect without extra setup. Use it first.
2. **Playwright MCP or Chrome DevTools MCP.** Best when the host supports MCP but not a native browser. Rich DOM, console and network access.
3. **Playwright CLI or Python.** Best when the host has shell access but no browser tool. You write the automation; the agent still designs the tests.
4. **Computer-use / visual automation.** Use when there is no DOM access. Expect slower runs and weaker evidence; record the limitation.
5. **Guided mode.** No browser. Produce the plan, cases and exact steps; the user executes and returns evidence. Never claim execution.

Do not install a new browser stack mid-run unless the user approves. A missing tool is a limitation, not a reason to fake results.

## 3. Browser setup recipes

These are starting points; verify the current package names and flags for your host.

### Playwright MCP

```bash
npx @playwright/mcp@latest
```

Typical configuration: run headed for login, headless for execution. If the host config takes a command, add the MCP server to the host's MCP settings. Use a persistent profile or storage state for repeat runs.

### Chrome DevTools MCP

```bash
npx chrome-devtools-mcp@latest
```

Useful for console, network, performance and DOM inspection against a running Chrome instance. Check whether it can attach to the browser profile you need.

### Playwright Python

```bash
pip install playwright openpyxl
playwright install chromium
```

Minimal pattern:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.goto("https://staging.example.com")
    page.wait_for_load_state("networkidle")
    # login manually or via a storage state
    page.screenshot(path="evidence/screenshots/S-001.png", full_page=True)
    print(page.locator("body").inner_text()[:4000])
    context.storage_state(path="%TEMP%/qa_auth_state.json")  # never in the workspace
    browser.close()
```

On Windows, use an absolute temp path such as `C:\Users\<you>\AppData\Local\Temp\qa_auth_state.json`. Delete it at the end.

### Host-native browser

If the host provides browser tools (for example OpenCode's browser, Claude's browser, or a built-in agent), use them directly. Do not wrap them in a second automation stack; that doubles the failure modes.

## 4. Authentication and session state

- Prefer a **manual login** in a headed browser. It handles MFA, CAPTCHA and tenant selection without storing credentials.
- If the user provides credentials, use them only in the login form. Do not put them in a command line, a script, a URL, or a file.
- Storage state is a bearer token equivalent. Keep it outside the workspace, in the OS temp directory, with restricted permissions. Delete it at the end.
- Use a separate context/storage state per role. Do not mix roles in one context; stale cookies cause false permission results.
- If MFA/CAPTCHA appears, ask the user to complete it. Do not attempt to bypass it.
- If the session expires mid-run, detect the login page, re-authenticate, and resume from `00-progress.md`.
- Logout at the end and verify the back button does not restore a protected page.
- Never commit storage state, `.env` files, cookies or HAR files containing auth headers.

## 5. Host skill paths

The Agent Skills format uses a folder containing `SKILL.md`. Common locations:

| Host | Project level | User level |
|---|---|---|
| **Universal / Codex / Cursor / OpenCode compatible** | `.agents/skills/deep-ui-qa/` | `~/.agents/skills/deep-ui-qa/` |
| **Claude Code** | `.claude/skills/deep-ui-qa/` | `~/.claude/skills/deep-ui-qa/` |
| **OpenCode** | `.opencode/skills/deep-ui-qa/` | `~/.config/opencode/skills/deep-ui-qa/` |
| **Cursor** | `.cursor/skills/deep-ui-qa/` or `.agents/skills/...` | `~/.cursor/skills/deep-ui-qa/` or `~/.agents/skills/...` |
| **Codex CLI** | `.codex/skills/deep-ui-qa/` or `.agents/skills/...` | `~/.codex/skills/deep-ui-qa/` or `~/.agents/skills/...` |
| **Windsurf** | `.windsurf/skills/deep-ui-qa/` | `~/.codeium/windsurf/skills/deep-ui-qa/` |
| **Gemini CLI** | `.gemini/skills/deep-ui-qa/` | `~/.gemini/skills/deep-ui-qa/` |
| **GitHub Copilot** | `.github/skills/deep-ui-qa/` or `.claude/skills/...` | `~/.copilot/skills/deep-ui-qa/` |

Hosts add support over time. If a path does not exist, check the host's current documentation rather than guessing. The universal `.agents/skills/` path is the safest portable choice.

The folder name must match the `name` field in `SKILL.md` (`deep-ui-qa`). Start a new session after installing so the host discovers the skill.

## 6. Optional slash commands and `AGENTS.md`

A slash command is a convenience wrapper, not a requirement. If the host supports custom commands, create one that invokes the skill with the user's scope.

### Claude Code example

`.claude/commands/qa.md`:

```markdown
---
description: Run deep UI QA on a staging web app
---
Use the `deep-ui-qa` skill. Ask for the URL, staging confirmation, credentials per role, scope and forbidden actions if they are not already provided. Default to Deep depth. Create a workspace, run the workflow, and produce the Excel report.
```

### OpenCode example

`.opencode/command/qa.md` (check your host's current command path):

```markdown
---
description: Run deep UI QA on a staging web app
---
Load the `deep-ui-qa` skill and follow its workflow. Ask only for missing intake details. Default to Deep depth. Produce the Excel report and a short chat summary.
```

### `AGENTS.md` bootstrap

Add a short pointer so agents know the skill exists:

```markdown
## UI QA

For black-box UI testing, load `.agents/skills/deep-ui-qa/SKILL.md` (or the host's installed path).
Never test production. Never write credentials to files. Use `QA_` fixtures and restore config changes.
```

Keep the bootstrap short; the skill carries the detail.

## 7. Browser technique notes

### Waiting

- Wait for network idle and DOM stability, not a fixed sleep.
- For async screens, take two snapshots a moment apart and compare.
- After a save, wait for the success signal, then reload to verify persistence.

### Nested tabs and panels

- Scope locators to the active visible panel (`[role="tabpanel"]:visible` or the host's equivalent).
- Inactive panels may stay mounted with stale values; do not read them.
- After switching tabs, re-snapshot; do not assume the previous DOM is valid.

### Virtualised tables

- Only visible rows exist in the DOM. Scroll in steps, change page size, or export.
- Do not conclude a row is missing from a virtualised list until you have scrolled and searched.
- Record the retrieval method and the count.

### Iframes and shadow DOM

- Use a tool that pierces frames or shadow roots. If it cannot, take screenshots and note the limitation.
- Do not claim a control does not exist just because the snapshot missed it.

### Canvas and charts

- Read legends, tooltips, "view as table" and exports.
- Compare chart totals to the underlying list; a chart is not an oracle by itself.

### Downloads

- Configure the browser to accept downloads and save them under `evidence/outputs/`.
- Verify file type, name, content, encoding and totals.
- Do not open untrusted files with macros.

### Uploads

- Prepare small benign files in `evidence/` or a `fixtures/` folder: valid type, wrong type, empty, oversized, unicode name.
- Never upload real personal data, malware, or files from the user's home directory without permission.

### Console and network

- Capture after each significant action; save excerpts to files, not giant dumps into context.
- Filter known noise; note it rather than reporting every deprecation warning.
- Network inspection is read-only. Do not replay, fuzz, or hand-craft requests.
- Status codes and payloads are evidence of what the UI received, not permission to call the API directly.

### Screenshots

- Use full-page screenshots for evidence and viewport screenshots for layout/responsive checks.
- Capture before and after for state changes.
- Redact personal data and secrets.
- Name files by test case or state ID.

### Viewports and locales

- Default desktop: 1440x900. Mobile: 390x844. Tablet: 768x1024.
- Test at least one narrow width for navigation and table behaviour.
- Record the locale and timezone; do not assume the host's locale matches the app's.

## 8. Guided mode (no browser)

When no browser tool exists, do not pretend to execute. Switch to guided mode:

1. Say clearly: "I cannot drive a browser in this environment, so I will produce an execution-ready plan and analyze the evidence you provide."
2. Complete Phases 1–4 from what the user can show you: screenshots, screen recordings, exported HTML, or a narrated walkthrough. Mark unobserved areas as `Blocked` or `Not Tested`.
3. Produce a **guided execution sheet** with: case ID, role, preconditions, exact steps, expected result, what to capture, and where to save it.
4. Ask the user to run the steps and return screenshots/text. Analyze the evidence, fill `actual` and `status`, and mark `execution_mode: "guided"`.
5. Build the report with the same schema. The Summary must state that execution was guided and list what was not directly observed.
6. Never mark a case `Pass` or `Fail` without the user's evidence.

Guided mode is slower but honest. It is better than a fabricated browser run.

## 9. Parallel subagents

If the host supports subagents:

- Give each subagent a module, a browser context, a fixture prefix and its own output file.
- One agent owns each shared JSON file; others return structured results to the orchestrator.
- Do not let two agents change the same global setting or use the same record.
- The orchestrator merges, deduplicates IDs, resolves references, and runs validation.
- If the host cannot isolate browser contexts, run sequentially.

A practical split: one agent per module for recon/atlas, then one agent per risk area for execution, then a single report owner.

## 10. Security boundaries

- Test only environments the user authorizes.
- Do not scan, exploit, brute-force, or attempt privilege escalation.
- Do not access other tenants, users or records beyond what the UI exposes to the provided roles.
- Do not exfiltrate data; evidence stays in the workspace and is redacted.
- Do not install browser extensions or software without approval.
- Do not disable security controls, MFA, CSP, or certificate warnings.
- Stop if you encounter production data, real personal data, or an action with irreversible external effects.
- Delete auth state, cookies, HAR files and temporary credentials at the end.
