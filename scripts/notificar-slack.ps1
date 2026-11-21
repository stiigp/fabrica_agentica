#requires -Version 5.1
<#
.SYNOPSIS
Publica o resultado de um acionamento da fabrica no canal Slack configurado.
.DESCRIPTION
Usa SLACK_BOT_TOKEN e SLACK_CHANNEL_ID do processo ou do usuario Windows.
Confirma o envio apenas quando chat.postMessage retorna ok=true, canal e ts.
Nao imprime credenciais e nao repete envios automaticamente.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('analista_requisitos', 'arquiteto', 'criador_tarefas',
        'desenvolvedor', 'revisor_codigo', 'qa', 'teste_manual')]
    [string]$Agente,
    [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string]$Feature,
    [Parameter(Mandatory)]
    [ValidateSet('DONE', 'BLOCKED', 'NEEDS_CLARIFICATION', 'HUMAN_REVIEW_REQUIRED', 'TESTE')]
    [string]$Status,
    [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string]$Resumo,
    [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string]$Artefato,
    [ValidateNotNullOrEmpty()][string]$Etapa = 'validacao-manual',
    [ValidateNotNullOrEmpty()][string]$ExecucaoId = ([guid]::NewGuid().ToString('N'))
)

$ErrorActionPreference = 'Stop'

function Get-ConfiguracaoSlack {
    param([string]$Nome)
    $valor = [Environment]::GetEnvironmentVariable($Nome, 'Process')
    if ([string]::IsNullOrWhiteSpace($valor) -and $env:OS -eq 'Windows_NT') {
        $valor = [Environment]::GetEnvironmentVariable($Nome, 'User')
    }
    if ([string]::IsNullOrWhiteSpace($valor)) {
        throw "NOTIFICACAO: FALHOU; MOTIVO: $Nome nao configurada. Execute scripts/configurar-slack.ps1."
    }
    return $valor.Trim()
}

$token = Get-ConfiguracaoSlack 'SLACK_BOT_TOKEN'
$canal = Get-ConfiguracaoSlack 'SLACK_CHANNEL_ID'
if ($token -notmatch '^xoxb-[A-Za-z0-9-]+$') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: use o Bot User OAuth Token iniciado por xoxb-.'
}
if ($canal -cnotmatch '^[CG][A-Z0-9]{8,}$') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: SLACK_CHANNEL_ID deve ser um ID de canal, nao seu nome ou URL.'
}

$data = [DateTimeOffset]::Now.ToString('o')
$conteudo = @"
Agente: $Agente
Feature: $Feature
Etapa: $Etapa
Execucao: $ExecucaoId
Status: $Status
Resumo: $Resumo
Artefato: $Artefato
Data: $data
"@

if ($conteudo.Contains($token) -or $conteudo -match '(?i)xox[a-z](?:-|\.)|hooks\.slack\.com/services/|/api(?:/v[0-9]+)?/webhooks/') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: remova tokens e URLs de webhook do conteudo.'
}
# Escapa marcadores de mencao/link do Slack e desliga interpretacao de markup.
$texto = $conteudo.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;')
if ($texto.Length -gt 4000) {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: mensagem excede 4000 caracteres. Reduza o resumo.'
}

$payload = @{
    channel = $canal
    text = $texto
    mrkdwn = $false
    parse = 'none'
    link_names = $false
    unfurl_links = $false
    unfurl_media = $false
} | ConvertTo-Json -Depth 3 -Compress

try {
    $resposta = Invoke-RestMethod -Uri 'https://slack.com/api/chat.postMessage' `
        -Method Post -Headers @{ Authorization = "Bearer $token" } `
        -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($payload)) `
        -MaximumRedirection 0 -TimeoutSec 20
}
catch {
    # Nunca propaga o corpo da resposta ou excecoes contendo o Authorization.
    $codigoHttp = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $codigoHttp = [int]$_.Exception.Response.StatusCode
    }
    $motivo = if ($codigoHttp) { "HTTP $codigoHttp" } else { 'rede ou timeout' }
    throw "NOTIFICACAO: FALHOU; MOTIVO: $motivo. Confira o canal pelo EXECUCAO_ID antes de reenviar; o envio pode ter ocorrido."
}

# HTTP 200 com ok=false e uma falha de API, nao uma confirmacao de envio.
if ($resposta.ok -isnot [bool] -or -not $resposta.ok) {
    $motivos = @{
        invalid_auth = 'token invalido; confira o Bot User OAuth Token.'
        not_authed = 'token nao aceito pelo Slack.'
        token_revoked = 'token revogado; configure um token valido.'
        token_expired = 'token expirado; configure um token valido.'
        account_inactive = 'app ou conta desativada.'
        missing_scope = 'adicione chat:write em Bot Token Scopes e reinstale o app.'
        not_in_channel = 'adicione o bot ao canal configurado.'
        channel_not_found = 'confira o ID do canal e o acesso do bot.'
        is_archived = 'o canal configurado esta arquivado.'
        restricted_action = 'a politica do workspace impede a publicacao.'
        ratelimited = 'limite de envio atingido; aguarde antes de uma nova tentativa.'
        msg_too_long = 'reduza o resumo da notificacao.'
    }
    $erroApi = [string]$resposta.error
    if ($motivos.ContainsKey($erroApi)) {
        throw "NOTIFICACAO: FALHOU; MOTIVO: $erroApi - $($motivos[$erroApi])"
    }
    throw 'NOTIFICACAO: FALHOU; MOTIVO: resposta Slack nao confirmou envio. Confira o canal antes de reenviar.'
}

if ($resposta.channel -cne $canal -or [string]$resposta.ts -notmatch '^[0-9]+\.[0-9]+$') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: resposta sem canal/ts esperados. Confira o canal antes de reenviar.'
}

# ts e um identificador textual: nunca converter para ponto flutuante.
Write-Output 'NOTIFICACAO: ENVIADA'
Write-Output "MESSAGE_ID: $($resposta.channel):$($resposta.ts)"
Write-Output "SLACK_CHANNEL_ID: $($resposta.channel)"
Write-Output "SLACK_TS: $($resposta.ts)"
Write-Output "EXECUCAO_ID: $ExecucaoId"
Write-Output "NOTIFICACAO_EM: $data"
