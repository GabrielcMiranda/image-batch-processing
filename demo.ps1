<#
.SYNOPSIS
  Comandos da apresentacao, na ordem. Dono: Pessoa 3.
.EXAMPLE
  .\demo.ps1 -Etapa preparar
  .\demo.ps1 -Etapa seq
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("preparar", "seq", "corrida", "estavel", "par", "verificar", "site", "servir")]
    [string]$Etapa,
    [string]$Python = (Join-Path $PSScriptRoot ".venv\Scripts\python.exe")
)

# ===== AJUSTE AQUI depois da calibracao (Pessoa 1) e da bateria (Pessoa 4) =====
$N = 3334                       # --limite calibrado: a sequencial deve levar ~4 min
$P = 8                          # processos da demonstracao (o melhor resultado da bateria)
$Entrada = "dados\val2017"
# ===============================================================================

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Rodar([string[]]$Argumentos) {
    Write-Host ""
    Write-Host ("> python " + ($Argumentos -join " ")) -ForegroundColor Cyan
    & $Python @Argumentos
    if ($LASTEXITCODE -ne 0) {
        Write-Host "O comando terminou com erro (codigo $LASTEXITCODE)." -ForegroundColor Red
    }
}

switch ($Etapa) {
    "preparar" {
        Remove-Item -Recurse -Force saida_seq, saida_par, saida_estavel_1, saida_estavel_2 -ErrorAction SilentlyContinue
        Rodar @("aquecer_cache.py", $Entrada)
    }
    "seq" {
        Rodar @("seq.py", "--entrada", $Entrada, "--saida", "saida_seq", "--limite", "$N")
    }
    "corrida" {
        Rodar @("teste_corrida.py")
    }
    "estavel" {
        Rodar @("par.py", "--entrada", $Entrada, "--saida", "saida_estavel_1", "--limite", "300", "--progresso", "0")
        Rodar @("par.py", "--entrada", $Entrada, "--saida", "saida_estavel_2", "--limite", "300", "--progresso", "0")
        Rodar @("verificar.py", "saida_estavel_1", "saida_estavel_2")
    }
    "par" {
        Rodar @("par.py", "--entrada", $Entrada, "--saida", "saida_par", "--limite", "$N", "--workers", "$P")
    }
    "verificar" {
        Rodar @("verificar.py", "saida_seq", "saida_par")
    }
    "site" {
        Rodar @("gerar_site.py", "--execucao", "saida_par", "--entrada", $Entrada)
    }
    "servir" {
        Rodar @("-m", "http.server", "8000", "--directory", "site", "--bind", "0.0.0.0")
    }
}
