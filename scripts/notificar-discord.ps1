#requires -Version 5.1
<#
.SYNOPSIS
Envia o resultado de um acionamento da fabrica ao canal Discord configurado.
.DESCRIPTION
Le DISCORD_WEBHOOK_URL do processo ou, no Windows, do ambiente do usuario.
Confirma a mensagem com wait=true. Nao grava nem imprime o segredo e nao
repete envios automaticamente: um timeout pode ocorrer apos a publicacao.
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

$webhookUrl = [Environment]::GetEnvironmentVariable('DISCORD_WEBHOOK_URL', 'Process')
if ([string]::IsNullOrWhiteSpace($webhookUrl) -and $env:OS -eq 'Windows_NT') {
    $webhookUrl = [Environment]::GetEnvironmentVariable('DISCORD_WEBHOOK_URL', 'User')
}
if ([string]::IsNullOrWhiteSpace($webhookUrl)) {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: DISCORD_WEBHOOK_URL nao configurada.'
}

# Restringe o segredo e o destino ao endpoint oficial de webhooks do Discord.
$uriWebhook = $null
if (-not [Uri]::TryCreate($webhookUrl.Trim(), [UriKind]::Absolute, [ref]$uriWebhook) -or
    $uriWebhook.Scheme -ne 'https' -or $uriWebhook.Host -ne 'discord.com' -or
    -not $uriWebhook.IsDefaultPort -or $uriWebhook.UserInfo -or $uriWebhook.Fragment -or
    $uriWebhook.AbsolutePath -notmatch '^/api(?:/v[0-9]+)?/webhooks/[0-9]+/[A-Za-z0-9._-]+/?$') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: URL de webhook Discord invalida.'
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

if ($conteudo.Length -gt 2000) {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: mensagem excede 2000 caracteres. Reduza o resumo.'
}
# Impede que o valor do segredo seja incluido acidentalmente no texto enviado.
if ($conteudo.Contains($webhookUrl.Trim()) -or $conteudo -match '(?i)/api(?:/v[0-9]+)?/webhooks/') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: remova URLs de webhook do conteudo.'
}

$payload = @{
    username = "Fabrica - $Agente"
    content = $conteudo
    allowed_mentions = @{ parse = @() }
} | ConvertTo-Json -Depth 4 -Compress

$destino = [UriBuilder]::new($uriWebhook)
$destino.Query = 'wait=true'

try {
    $resposta = Invoke-RestMethod -Uri $destino.Uri -Method Post `
        -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($payload)) `
        -MaximumRedirection 0 -TimeoutSec 20
}
catch {
    # Nao propaga excecoes HTTP que possam conter a URL/token do webhook.
    $codigoHttp = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $codigoHttp = [int]$_.Exception.Response.StatusCode
    }
    $motivo = if ($codigoHttp) { "HTTP $codigoHttp" } else { 'rede ou timeout' }
    throw "NOTIFICACAO: FALHOU; MOTIVO: $motivo. Confira o canal antes de reenviar; o envio pode ter ocorrido."
}

if (-not $resposta.id -or [string]$resposta.id -notmatch '^[0-9]+$') {
    throw 'NOTIFICACAO: FALHOU; MOTIVO: Discord nao retornou MESSAGE_ID. Confira o canal antes de reenviar.'
}

Write-Output 'NOTIFICACAO: ENVIADA'
Write-Output "MESSAGE_ID: $($resposta.id)"
Write-Output "EXECUCAO_ID: $ExecucaoId"
Write-Output "NOTIFICACAO_EM: $data"
