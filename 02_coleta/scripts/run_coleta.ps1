# Runs (or resumes) the multi-feature collection outside VS Code.
# Usage: right click > "Run with PowerShell", or in a PowerShell window:
#   & "C:\Users\Kevin Strey\Desktop\TCC-LPS-Prediction\5-Coleta_features\scripts\run_coleta.ps1"
# Resumable: everything already done is skipped. Progress: 5-Coleta_features\logs\run_all_<date>.log
# Each finished feature writes 5-Coleta_features\<feature>\AUDITORIA.md.
$ErrorActionPreference = 'Stop'
$scripts = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scripts
$py = Join-Path $scripts '..\.venv\Scripts\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$mem = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
Write-Host ("RAM livre agora: {0:N1} GB (o orcamento da coleta e calculado a partir dela)" -f $mem)
& $py run_all.py 2>&1 | Tee-Object -FilePath (Join-Path $scripts '..\logs\run_all_console.txt')
Write-Host 'Coleta encerrada. Veja 5-Coleta_features\logs e os AUDITORIA.md de cada feature.'
Read-Host 'Pressione Enter para fechar'
