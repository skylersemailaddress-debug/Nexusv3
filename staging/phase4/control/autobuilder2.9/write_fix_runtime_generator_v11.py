from pathlib import Path

repo = Path(r"C:\ODPv3")
path = repo / "tools" / "ai_patch_build" / "FIX_RUNTIME_GENERATOR_V11.ps1"
path.parent.mkdir(parents=True, exist_ok=True)

content = r'''param([Parameter(Mandatory=$true)][string]$RepoRoot)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"

function Fail([string]$m){ throw $m }

$targets = Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Include *.ps1 |
  Where-Object {
    $_.FullName -notmatch '\\out\\' -and
    $_.FullName -notmatch '\\.git\\' -and
    (Get-Content -LiteralPath $_.FullName -Raw) -match 'WROTE_RUN_APP=.*RUN_APP\.ps1|WROTE_SMOKE=.*SMOKE\.ps1|WROTE_STOP_APP=.*STOP_APP\.ps1'
  }

if (-not $targets) { Fail "RUNTIME_GENERATOR_NOT_FOUND" }

$patched = @()

foreach($t in $targets){
  $raw  = Get-Content -LiteralPath $t.FullName -Raw
  $orig = $raw

  $replacementRunApp = @"
$deadline = (Get-Date).AddSeconds(15)
$ready = $false
while ((Get-Date) -lt $deadline) {
  try {
    $tcp = [System.Net.Sockets.TcpClient]::new()
    $iar = $tcp.BeginConnect($BindHost,$Port,$null,$null)
    if ($iar.AsyncWaitHandle.WaitOne(300)) {
      $tcp.EndConnect($iar)
      $tcp.Close()
      $ready = $true
      break
    }
    $tcp.Close()
  } catch { }
  if ($null -ne $p -and $p.HasExited) { Fail "RUN_APP_EXITED_EARLY" }
  Start-Sleep -Milliseconds 300
}

if (-not $ready) {
  try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch { }
  Fail "PORT_NOT_READY"
}
"@

  $raw = $raw.Replace('Start-Sleep -Milliseconds 250', $replacementRunApp)
  $raw = [regex]::Replace($raw, '\[int\]\$TimeoutSec = 30', '[int]$TimeoutSec = 60')

  $replacementStop = @"
try { Stop-Process -Id $AppPid -Force -ErrorAction SilentlyContinue } catch { }

$deadline = (Get-Date).AddSeconds(10)
while ((Get-Date) -lt $deadline) {
  $p2 = Get-Process -Id $AppPid -ErrorAction SilentlyContinue
  if ($null -eq $p2) { break }
  Start-Sleep -Milliseconds 250
}
# WAITED_FOR_EXIT
"@

  if ($raw -match 'Stop-Process -Id \$AppPid -Force -ErrorAction SilentlyContinue' -and $raw -notmatch 'WAITED_FOR_EXIT') {
    $raw = $raw.Replace('try { Stop-Process -Id $AppPid -Force -ErrorAction SilentlyContinue } catch { }', $replacementStop)
  }

  if ($raw -ne $orig) {
    Copy-Item -LiteralPath $t.FullName -Destination ($t.FullName + ".bak_v11") -Force
    Set-Content -LiteralPath $t.FullName -Value $raw -Encoding UTF8
    $patched += $t.FullName
  }
}

"PATCH_OK=1"
"PATCHED_COUNT=$($patched.Count)"
$patched | ForEach-Object { "PATCHED=$_"}
'''
path.write_text(content, encoding="utf-8")
print(f"FIX_SCRIPT_READY={path}")
