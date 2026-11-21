#requires -Version 5.1
<#
.SYNOPSIS
Verifica a integracao Slack com API e entrada simuladas, sem publicar mensagens.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$notificador = Join-Path $PSScriptRoot 'notificar-slack.ps1'
$configurador = Join-Path $PSScriptRoot 'configurar-slack.ps1'
$tokenAnterior = [Environment]::GetEnvironmentVariable('SLACK_BOT_TOKEN', 'Process')
$canalAnterior = [Environment]::GetEnvironmentVariable('SLACK_CHANNEL_ID', 'Process')
$testToken = 'xoxb-token-ficticio-para-testes'
$testChannel = 'C0123456789'
$requisicoes = [Collections.Generic.List[object]]::new()
$cenario = 'sucesso'
$erroApiSimulado = 'missing_scope'
$entradaTokenSimulada = $testToken
$entradaCanalSimulada = $testChannel
$total = 0

function Assert-Condition {
    param([bool]$Condicao, [string]$Mensagem)
    if (-not $Condicao) { throw "TESTE FALHOU: $Mensagem" }
}

function Invoke-RestMethod {
    param([string]$Uri, [string]$Method, [hashtable]$Headers,
        [string]$ContentType, [byte[]]$Body,
        [int]$MaximumRedirection, [int]$TimeoutSec)
    $requisicoes.Add(@{
        Uri = $Uri; Method = $Method; Headers = $Headers
        ContentType = $ContentType; Redirection = $MaximumRedirection
        Timeout = $TimeoutSec
        Payload = ([Text.Encoding]::UTF8.GetString($Body) | ConvertFrom-Json)
    })
    switch ($cenario) {
        'api' { return [pscustomobject]@{ ok = $false; error = $erroApiSimulado } }
        'rede' { throw [System.Net.WebException]::new("Nao exibir $testToken") }
        'sem-ts' { return [pscustomobject]@{ ok = $true; channel = $testChannel } }
        'canal-errado' { return [pscustomobject]@{ ok = $true; channel = 'C9999999999'; ts = '1700000000.123456' } }
        'ok-textual' { return [pscustomobject]@{ ok = 'true'; channel = $testChannel; ts = '1700000000.123456' } }
        default { return [pscustomobject]@{ ok = $true; channel = $testChannel; ts = '1700000000.123456' } }
    }
}

function Read-Host {
    param([string]$Prompt, [switch]$AsSecureString)
    if ($AsSecureString) {
        return ConvertTo-SecureString $entradaTokenSimulada -AsPlainText -Force
    }
    return $entradaCanalSimulada
}

function Assert-NotificationFails {
    param([hashtable]$Aviso, [string]$Esperado)
    $mensagem = $null
    try { $null = & $notificador @Aviso } catch { $mensagem = $_.Exception.Message }
    Assert-Condition ($null -ne $mensagem -and $mensagem -like "*$Esperado*") "erro esperado: $Esperado"
    Assert-Condition (-not $mensagem.Contains($testToken)) 'um erro revelou o token ficticio'
}

try {
    $env:SLACK_BOT_TOKEN = $testToken
    $env:SLACK_CHANNEL_ID = $testChannel
    $aviso = @{
        Agente = 'qa'; Feature = 'teste-local'; Etapa = 'E6'
        ExecucaoId = 'acionamento-de-teste'; Status = 'DONE'
        Resumo = 'Validacao UTF-8: a' + [char]0x00e7 + 'ao; parecer reprovado. <!channel> <@U123> & teste'
        Artefato = 'specs/teste-local/qa-report.md'
    }
    $saida = & $notificador @aviso
    Assert-Condition ($saida -contains 'NOTIFICACAO: ENVIADA') 'sucesso nao confirmado'
    Assert-Condition ($saida -contains 'MESSAGE_ID: C0123456789:1700000000.123456') 'canal:ts incorreto'
    Assert-Condition ($saida -contains 'SLACK_TS: 1700000000.123456') 'ts perdeu precisao'
    Assert-Condition ($saida -contains 'EXECUCAO_ID: acionamento-de-teste') 'correlacao incorreta'
    Assert-Condition (-not ($saida -join '').Contains($testToken)) 'saida revelou o token'
    $req = $requisicoes[0]
    Assert-Condition ($req.Uri -ceq 'https://slack.com/api/chat.postMessage') 'destino incorreto'
    Assert-Condition ($req.Method -eq 'Post' -and $req.Headers.Authorization -ceq "Bearer $testToken") 'autenticacao incorreta'
    Assert-Condition ($req.Redirection -eq 0 -and $req.Timeout -eq 20) 'limites HTTP incorretos'
    Assert-Condition ($req.Payload.channel -ceq $testChannel) 'payload aponta a outro canal'
    Assert-Condition ($req.Payload.text.Contains($aviso.Resumo.Split(';')[0])) 'UTF-8 nao preservado'
    Assert-Condition ($req.Payload.text.Contains('Status: DONE') -and $req.Payload.text.Contains('parecer reprovado')) 'status tecnico/parecer alterados'
    Assert-Condition ($req.Payload.text.Contains('&lt;!channel&gt;') -and -not $req.Payload.text.Contains('<@U123>')) 'marcadores de mencao nao escapados'
    Assert-Condition (-not $req.Payload.mrkdwn -and -not $req.Payload.link_names -and $req.Payload.parse -eq 'none') 'interpretacao de markup habilitada'
    Assert-Condition (-not $req.Payload.unfurl_links -and -not $req.Payload.unfurl_media) 'previews habilitados'
    $total++
    Write-Output 'OK: POST autenticado, UTF-8, mencoes, correlacao, status e confirmacao canal:ts.'

    $cenario = 'api'
    foreach ($codigo in @('missing_scope', 'not_in_channel', 'invalid_auth', 'channel_not_found', 'ratelimited')) {
        $erroApiSimulado = $codigo
        Assert-NotificationFails $aviso $codigo
        $total++
    }
    $erroApiSimulado = $testToken
    Assert-NotificationFails $aviso 'nao confirmou envio'
    $total++
    Write-Output 'OK: HTTP 200 com erro da API nao confirma envio; erro desconhecido e sanitizado.'

    foreach ($caso in @('sem-ts', 'canal-errado', 'ok-textual')) {
        $cenario = $caso
        Assert-NotificationFails $aviso 'NOTIFICACAO: FALHOU'
        $total++
    }
    Write-Output 'OK: respostas incompletas, canal divergente e ok textual recusados.'

    $cenario = 'rede'
    $antes = $requisicoes.Count
    Assert-NotificationFails $aviso 'rede ou timeout'
    Assert-Condition ($requisicoes.Count -eq $antes + 1) 'ocorreu repeticao automatica'
    $total++
    Write-Output 'OK: erro de rede sem vazamento e sem repeticao automatica.'

    $cenario = 'sucesso'
    $antes = $requisicoes.Count
    $longo = $aviso.Clone(); $longo.Resumo = 'x' * 4100
    Assert-NotificationFails $longo 'excede 4000'
    $vazamento = $aviso.Clone(); $vazamento.Resumo = $testToken
    Assert-NotificationFails $vazamento 'remova tokens'
    $env:SLACK_BOT_TOKEN = 'tipo-de-token-errado'
    Assert-NotificationFails $aviso 'Bot User OAuth Token'
    $env:SLACK_BOT_TOKEN = $testToken
    $env:SLACK_CHANNEL_ID = '#nome-do-canal'
    Assert-NotificationFails $aviso 'ID de canal'
    $env:SLACK_CHANNEL_ID = $testChannel
    Assert-Condition ($requisicoes.Count -eq $antes) 'entrada invalida chegou a rede'
    $total += 4
    Write-Output 'OK: texto longo, token no texto e configuracoes invalidas bloqueados antes da rede.'

    $saidaSetup = & $configurador -SomenteSessao
    Assert-Condition ($saidaSetup -contains 'CONFIGURACAO: OK') 'configurador nao confirmou'
    Assert-Condition ($env:SLACK_BOT_TOKEN -ceq $testToken -and $env:SLACK_CHANNEL_ID -ceq $testChannel) 'variaveis da sessao incorretas'
    Assert-Condition (-not ($saidaSetup -join '').Contains($testToken)) 'configurador revelou token'
    $total++
    $entradaCanalSimulada = '#invalido'
    $falhou = $false
    try { $null = & $configurador -SomenteSessao } catch { $falhou = $_.Exception.Message -like '*Canal invalido*' }
    Assert-Condition $falhou 'configurador aceitou canal invalido'
    Assert-Condition ($env:SLACK_CHANNEL_ID -ceq $testChannel) 'configuracao invalida alterou ambiente'
    $total++
    Write-Output 'OK: configurador simulado, sem eco do token nem alteracoes persistentes.'
}
finally {
    [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', $tokenAnterior, 'Process')
    [Environment]::SetEnvironmentVariable('SLACK_CHANNEL_ID', $canalAnterior, 'Process')
}

Write-Output "RESULTADO: $total casos aprovados; nenhuma chamada externa."
