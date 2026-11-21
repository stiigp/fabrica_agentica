#requires -Version 5.1
<#
.SYNOPSIS
Envia o mesmo resultado ao Slack e ao Discord, com confirmacoes independentes.
.DESCRIPTION
Tenta ambos mesmo se um falhar. Para retomar apenas um envio pendente, informe
-Transportes slack ou -Transportes discord com o mesmo ExecucaoId original.
Nao repete envios automaticamente e nao escreve state.json.
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
    [ValidateNotNullOrEmpty()][string]$ExecucaoId = ([guid]::NewGuid().ToString('N')),
    [ValidateNotNullOrEmpty()][ValidateSet('slack', 'discord')]
    [string[]]$Transportes = @('slack', 'discord')
)

$ErrorActionPreference = 'Stop'
if (@($Transportes | Select-Object -Unique).Count -ne $Transportes.Count) {
    throw 'NOTIFICACOES: FALHOU; nao repita transportes na mesma chamada.'
}
$aviso = @{
    Agente = $Agente; Feature = $Feature; Etapa = $Etapa
    ExecucaoId = $ExecucaoId; Status = $Status
    Resumo = $Resumo; Artefato = $Artefato
}
$pendentes = [Collections.Generic.List[string]]::new()
foreach ($transporte in $Transportes) {
    $nome = if ($transporte -eq 'slack') { 'slack_bot_api' } else { 'discord_webhook' }
    Write-Output "TRANSPORTE: $nome"
    Write-Output "EXECUCAO_ID: $ExecucaoId"
    try {
        $caminho = Join-Path $PSScriptRoot "notificar-$transporte.ps1"
        if (-not (Test-Path -LiteralPath $caminho -PathType Leaf)) {
            throw 'NOTIFICACAO: FALHOU; MOTIVO: script de transporte ausente.'
        }
        $evidencia = @(& $caminho @aviso)
        if ($evidencia -notcontains 'NOTIFICACAO: ENVIADA' -or
            $evidencia -notcontains "EXECUCAO_ID: $ExecucaoId") {
            throw 'NOTIFICACAO: FALHOU; MOTIVO: transporte nao retornou confirmacao esperada.'
        }
        $evidencia | Write-Output
    }
    catch {
        $pendentes.Add($transporte)
        Write-Output 'NOTIFICACAO: FALHOU'
        $mensagem = $_.Exception.Message
        if ($mensagem.StartsWith('NOTIFICACAO: FALHOU; MOTIVO:')) {
            Write-Output $mensagem
        } else {
            Write-Output 'MOTIVO: falha no transporte; confira a configuracao e o canal antes de reenviar.'
        }
    }
}

if ($pendentes.Count) {
    throw "NOTIFICACOES: PENDENTES ($($pendentes -join ', ')). Preserve os envios confirmados; nao reenvie aos dois automaticamente."
}
Write-Output 'NOTIFICACOES: CONCLUIDAS'
