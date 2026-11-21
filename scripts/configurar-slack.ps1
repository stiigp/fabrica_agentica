#requires -Version 5.1
<#
.SYNOPSIS
Solicita o token sem exibi-lo e configura as variaveis locais da integracao.
.DESCRIPTION
Por padrao salva no ambiente do usuario Windows e no processo atual.
Com -SomenteSessao salva apenas no processo atual. Nao grava arquivos.
Execute em PowerShell interativo; nao passe o token na linha de comando.
#>
[CmdletBinding()]
param([switch]$SomenteSessao)

$ErrorActionPreference = 'Stop'
if (-not $SomenteSessao -and $env:OS -ne 'Windows_NT') {
    throw 'Fora do Windows, use -SomenteSessao ou configure as variaveis no seu ambiente.'
}

$tokenSeguro = $null
$token = $null
try {
    $tokenSeguro = Read-Host 'Cole o Bot User OAuth Token (xoxb-..., entrada oculta)' -AsSecureString
    $token = ([Net.NetworkCredential]::new('', $tokenSeguro)).Password.Trim()
    $canal = (Read-Host 'Cole o ID do canal Slack (ex.: C0123456789)').Trim()
    if ($token -notmatch '^xoxb-[A-Za-z0-9-]+$') {
        throw 'Token invalido. Use o Bot User OAuth Token iniciado por xoxb-.'
    }
    if ($canal -cnotmatch '^[CG][A-Z0-9]{8,}$') {
        throw 'Canal invalido. Informe o ID do canal, nao seu nome ou URL.'
    }
    if (-not $SomenteSessao) {
        [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', $token, 'User')
        [Environment]::SetEnvironmentVariable('SLACK_CHANNEL_ID', $canal, 'User')
    }
    [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', $token, 'Process')
    [Environment]::SetEnvironmentVariable('SLACK_CHANNEL_ID', $canal, 'Process')
    Write-Output 'CONFIGURACAO: OK'
    if ($SomenteSessao) {
        Write-Output 'Variaveis disponiveis somente neste processo PowerShell.'
    } else {
        Write-Output 'Variaveis salvas no ambiente do usuario Windows e neste processo, fora do Git.'
    }
    Write-Output 'Nenhuma mensagem foi enviada. Use scripts/notificar-slack.ps1 para testar.'
}
finally {
    $token = $null
    if ($null -ne $tokenSeguro) { $tokenSeguro.Dispose() }
}
