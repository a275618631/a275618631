param(
  [ValidateSet('local','public')][string]$Mode = 'local',
  [ValidateRange(0,65535)][int]$Port = 8765,
  [switch]$NoOpen
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $command = @($python.Source, '.\portfolio\hub.py', 'serve', '--mode', $Mode, '--port', "$Port")
  } else {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $launcher) { throw 'Python 3.12+ is required. Install Python, then run this script again.' }
    $command = @($launcher.Source, '-3', '.\portfolio\hub.py', 'serve', '--mode', $Mode, '--port', "$Port")
  }
  if (-not $NoOpen) { $command += '--open' } else { $command += '--no-open' }
  $exe = $command[0]
  $arguments = $command[1..($command.Length - 1)]
  & $exe @arguments
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
