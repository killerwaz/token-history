<#
Install (or remove) the Windows Task Scheduler job that runs the collector.
Mirror of scripts/install-launchd.sh: 00:30, 12:00, 21:00 and at every logon.
The collector is idempotent and backfills gaps, so extra runs are harmless.

  powershell -ExecutionPolicy Bypass -File scripts\install-task-windows.ps1
  powershell -ExecutionPolicy Bypass -File scripts\install-task-windows.ps1 -Uninstall

UNTESTED: written against the documented ScheduledTasks cmdlets and not run on
a Windows machine by its author. Check it with the commands in the README.
#>
param([switch]$Uninstall, [string]$TaskName = "token-history-collect")
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "removed $TaskName"
    return
}

if (-not (Test-Path (Join-Path $repo "config.json"))) {
    throw "config.json not found. Copy config.example.json to config.json and set your host alias."
}

$uv = (Get-Command uv -ErrorAction Stop).Source
$log = Join-Path $repo "collect.log"
# One PowerShell command so output lands in a log file and a failure is diagnosable.
$cmd = "& '$uv' run --quiet --project '$repo' scripts\collect.py *>> '$log'"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`"" `
    -WorkingDirectory $repo

$me = "$env:USERDOMAIN\$env:USERNAME"
$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At "00:30"),
    (New-ScheduledTaskTrigger -Daily -At "12:00"),
    (New-ScheduledTaskTrigger -Daily -At "21:00"),
    (New-ScheduledTaskTrigger -AtLogOn -User $me)
)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
# Interactive logon: runs only while you are signed in. That is what lets Git
# Credential Manager supply your GitHub credentials for the push.
$principal = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers `
    -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "installed $TaskName. Log: $log"
