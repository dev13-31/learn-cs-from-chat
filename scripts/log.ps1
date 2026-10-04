param (
    [Parameter(Mandatory=$true)]
    [string]$dir,

    [Parameter(Mandatory=$false)]
    [string]$slug,

    [Parameter(Mandatory=$true)]
    [string]$did,

    [Parameter(Mandatory=$true)]
    [string]$why,

    [Parameter(Mandatory=$true)]
    [string]$happened,

    [Parameter(Mandatory=$true)]
    [string]$next
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$scriptDir/log_decision.py" --dir $dir --slug $slug --did $did --why $why --happened $happened --next $next
