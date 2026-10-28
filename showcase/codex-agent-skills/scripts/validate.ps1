$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$skillsRoot = Join-Path $root 'skills'
$expected = @(
    'preventive-repair',
    'portable-tool-delivery',
    'workflow-automation-agent',
    'pr-review-agent',
    'output-contract'
)

if (-not (Test-Path -LiteralPath $skillsRoot)) {
    throw 'skills directory is missing.'
}

$actual = @(Get-ChildItem -LiteralPath $skillsRoot -Directory | Select-Object -ExpandProperty Name)
if (@(Compare-Object -ReferenceObject $expected -DifferenceObject $actual).Count -gt 0) {
    throw "Unexpected skill directory set. Expected: $($expected -join ', '); actual: $($actual -join ', ')"
}

$blocked = @(
    'C:\\Users\\', '/Users/', 'auth.json', 'history.jsonl', '.env', 'token=', 'password=',
    'BEGIN PRIVATE KEY', 'ghp_', 'github_pat_', 'xoxb-', 'AIza'
)

foreach ($name in $expected) {
    if ($name -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
        throw "Invalid skill directory name: $name"
    }

    $file = Join-Path $skillsRoot (Join-Path $name 'SKILL.md')
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Missing SKILL.md: $name"
    }

    $text = Get-Content -LiteralPath $file -Raw
    if ($text -notmatch '(?s)^---\s*\r?\nname:\s*[a-z0-9]+(?:-[a-z0-9]+)*\s*\r?\ndescription:\s*.+?\r?\n---') {
        throw "Invalid front matter: $file"
    }
    foreach ($term in $blocked) {
        if ($text -match [regex]::Escape($term)) {
            throw "Blocked sensitive pattern '$term' found in $file"
        }
    }
}

foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.md' | Where-Object { $_.FullName -notmatch '\\.git\\' }) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    foreach ($term in $blocked) {
        if ($content -match [regex]::Escape($term)) {
            throw "Blocked sensitive pattern '$term' found in repository content"
        }
    }
}

Write-Output "Validation passed: $($expected.Count) skills, front matter, required files, and blocked-pattern scan."
