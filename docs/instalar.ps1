# Programa Depor: descarga el instalador a C:\apps y lo abre.
# Uso (en PowerShell):  irm https://grupo-depor-ti.github.io/programa-depor/instalar.ps1 | iex
#
# Lo que baja PowerShell no lleva la marca de "descargado de internet", así que
# Windows no muestra el aviso "Windows protegió su PC". El programa igual pide
# permisos de administrador al abrirse.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$carpeta = 'C:\apps'
$exe = Join-Path $carpeta 'ProgramasV3.exe'
$url = 'https://github.com/Grupo-Depor-TI/programa-depor/releases/latest/download/ProgramasV3.exe'

try {
    New-Item -ItemType Directory -Force -Path $carpeta | Out-Null
    Get-Process -Name 'ProgramasV3' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe } | Stop-Process -Force
    Write-Host 'Descargando Programa Depor en C:\apps ...' -ForegroundColor Cyan
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile "$exe.descarga"
    Move-Item -Force "$exe.descarga" $exe
    Unblock-File -Path $exe
    Write-Host 'Listo. Abriendo el programa (acepta el permiso de administrador)...' -ForegroundColor Green
    Start-Process -FilePath $exe
}
catch {
    Write-Host "No se pudo instalar: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Revisa la conexión a internet o descarga el programa desde la página.'
}
