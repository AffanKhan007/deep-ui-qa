<#
.SYNOPSIS
Install the deep-ui-qa Agent Skill for a supported host.

.EXAMPLE
.\install.ps1 -Scope Global

.EXAMPLE
.\install.ps1 -Scope Project -HostName opencode
#>
[CmdletBinding()]
param(
    [ValidateSet("Global", "Project")]
    [string]$Scope = "Global",

    [ValidateSet("universal", "claude", "opencode", "codex", "cursor", "windsurf", "gemini", "copilot", "all")]
    [string]$HostName = "universal"
)

$ErrorActionPreference = "Stop"
$SkillName = "deep-ui-qa"
$SrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-Destination {
    param([string]$AgentHost)

    $base = if ($Scope -eq "Global") { $HOME } else { (Get-Location).Path }

    switch ($AgentHost) {
        "universal" { return Join-Path $base ".agents\skills\$SkillName" }
        "claude"    { return Join-Path $base ".claude\skills\$SkillName" }
        "opencode"  {
            if ($Scope -eq "Global") { return Join-Path $base ".config\opencode\skills\$SkillName" }
            return Join-Path $base ".opencode\skills\$SkillName"
        }
        "codex"     { return Join-Path $base ".codex\skills\$SkillName" }
        "cursor"    { return Join-Path $base ".cursor\skills\$SkillName" }
        "windsurf"  {
            if ($Scope -eq "Global") { return Join-Path $base ".codeium\windsurf\skills\$SkillName" }
            return Join-Path $base ".windsurf\skills\$SkillName"
        }
        "gemini"    { return Join-Path $base ".gemini\skills\$SkillName" }
        "copilot"   {
            if ($Scope -eq "Global") { return Join-Path $base ".copilot\skills\$SkillName" }
            return Join-Path $base ".github\skills\$SkillName"
        }
        default     { throw "Unknown host: $AgentHost" }
    }
}

function Install-One {
    param([string]$AgentHost)

    $dest = Get-Destination -AgentHost $AgentHost
    New-Item -ItemType Directory -Force -Path (Join-Path $dest "references") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $dest "scripts") | Out-Null

    Copy-Item -Path (Join-Path $SrcDir "SKILL.md") -Destination (Join-Path $dest "SKILL.md") -Force
    Copy-Item -Path (Join-Path $SrcDir "references\*") -Destination (Join-Path $dest "references") -Recurse -Force
    Copy-Item -Path (Join-Path $SrcDir "scripts\*") -Destination (Join-Path $dest "scripts") -Recurse -Force

    if (Test-Path (Join-Path $SrcDir "assets")) {
        New-Item -ItemType Directory -Force -Path (Join-Path $dest "assets") | Out-Null
        Copy-Item -Path (Join-Path $SrcDir "assets\*") -Destination (Join-Path $dest "assets") -Recurse -Force
    }

    Write-Host "[+] Installed $SkillName -> $dest"
}

if ($HostName -eq "all") {
    foreach ($h in @("universal", "claude", "opencode", "codex", "cursor")) {
        Install-One -AgentHost $h
    }
} else {
    Install-One -AgentHost $HostName
}

Write-Host ""
Write-Host "[OK] Installed. Start a new agent session so the skill is discovered."
Write-Host '     Then ask: "Use deep-ui-qa to audit https://staging.example.com ..."'
Write-Host ""
Write-Host "Requirements:"
Write-Host "  Python 3.10+ and openpyxl:   pip install openpyxl"
Write-Host "  Optional Playwright:         pip install playwright; playwright install chromium"
