<#
.SYNOPSIS
  Regras de firewall do projeto: o equivalente local do "grupo de seguranca". Dono: Pessoa 3.
  Rode num PowerShell ABERTO COMO ADMINISTRADOR, na pasta do projeto:
      .\infra\firewall_windows.ps1 -IpEquipe 192.168.0.23
  Para apagar as regras depois da apresentacao:
      .\infra\firewall_windows.ps1 -Remover
#>
#Requires -RunAsAdministrator
param(
    [string]$IpEquipe,
    [switch]$Remover
)
$ErrorActionPreference = "Stop"
$Grupo = "Lote Imagens"

# apaga as regras antigas do projeto (o script pode ser rodado de novo quando o IP mudar)
Get-NetFirewallRule -Group $Grupo -ErrorAction SilentlyContinue | Remove-NetFirewallRule
if ($Remover) {
    Write-Host "Regras do grupo '$Grupo' removidas."
    return
}
if (-not $IpEquipe) {
    throw "Informe o IP da maquina de quem administra. Exemplo: -IpEquipe 192.168.0.23"
}

# negar por padrao: toda conexao de entrada sem regra de permissao e bloqueada
Set-NetFirewallProfile -Profile Domain, Private, Public -Enabled True -DefaultInboundAction Block

# porta do servico: a pagina de resultados, aberta
New-NetFirewallRule -Group $Grupo -DisplayName "Lote - Servico: pagina de resultados (TCP 8000)" `
    -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any | Out-Null

# porta administrativa: SSH, so a partir do IP da equipe
New-NetFirewallRule -Group $Grupo -DisplayName "Lote - Administracao: SSH so da equipe (TCP 22)" `
    -Direction Inbound -Protocol TCP -LocalPort 22 -RemoteAddress $IpEquipe -Action Allow -Profile Any | Out-Null

# o OpenSSH Server do Windows cria a regra OpenSSH-Server-In-TCP sem restringir a origem: restringe
if (Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue) {
    Set-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -RemoteAddress $IpEquipe
    Write-Host "Regra OpenSSH-Server-In-TCP restrita a $IpEquipe."
}

# mostra o resultado: e isto que vai para o relatorio e para a apresentacao
Get-NetFirewallRule -Group $Grupo | ForEach-Object {
    [PSCustomObject]@{
        Regra  = $_.DisplayName
        Porta  = ($_ | Get-NetFirewallPortFilter).LocalPort
        Origem = ($_ | Get-NetFirewallAddressFilter).RemoteAddress
        Acao   = $_.Action
    }
} | Format-Table -AutoSize
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction | Format-Table -AutoSize
