#requires -Version 5.1
<#
.SYNOPSIS
Testa o envio conjunto usando os adaptadores reais com HTTP simulado.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$notificador = Join-Path $PSScriptRoot 'notificar-fabrica.ps1'
$anteriores = @{}
foreach ($nome in @('SLACK_BOT_TOKEN', 'SLACK_CHANNEL_ID', 'DISCORD_WEBHOOK_URL')) {
    $anteriores[$nome] = [Environment]::GetEnvironmentVariable($nome, 'Process')
}
$chamadas = [Collections.Generic.List[object]]::new()
$cenario = 'sucesso'
$total = 0

function Invoke-RestMethod {
    param([uri]$Uri, [string]$Method, [hashtable]$Headers,
        [string]$ContentType, [byte[]]$Body, [int]$MaximumRedirection, [int]$TimeoutSec)
    $transporte = if ($Uri.Host -eq 'slack.com') { 'slack' } else { 'discord' }
    $chamadas.Add(@{ Transporte = $transporte; Payload = ([Text.Encoding]::UTF8.GetString($Body) | ConvertFrom-Json) })
    if ($transporte -eq 'slack') {
        if ($cenario -in @('falha-slack', 'falha-ambos')) {
            return [pscustomobject]@{ ok = $false; error = 'missing_scope' }
        }
        return [pscustomobject]@{ ok = $true; channel = 'C0123456789'; ts = '1700000000.123456' }
    }
    if ($Uri.Host -ne 'discord.com' -or $Uri.Query -ne '?wait=true') {
        throw 'Destino Discord inesperado.'
    }
    if ($cenario -in @('falha-discord', 'falha-ambos')) {
        throw [System.Net.WebException]::new('Falha ficticia de rede')
    }
    return [pscustomobject]@{ id = '123456789012345678' }
}

function Assert-Condition {
    param([bool]$Condicao, [string]$Motivo)
    if (-not $Condicao) { throw "TESTE FALHOU: $Motivo" }
}

function Executar-Caso {
    param([hashtable]$Argumentos)
    $saida = [Collections.Generic.List[string]]::new()
    $erro = $null
    try { & $notificador @Argumentos | ForEach-Object { $saida.Add([string]$_) } }
    catch { $erro = $_.Exception.Message }
    return @{ Saida = @($saida.ToArray()); Erro = $erro }
}

try {
    $env:SLACK_BOT_TOKEN = 'xoxb-token-ficticio-para-testes'
    $env:SLACK_CHANNEL_ID = 'C0123456789'
    $env:DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/123/token-ficticio'
    $aviso = @{
        Agente = 'qa'; Feature = 'teste-local'; Etapa = 'E6'
        Status = 'DONE'; Resumo = 'Teste conjunto; parecer reprovado.'
        Artefato = 'specs/teste-local/qa-report.md'; ExecucaoId = 'mesmo-id-nos-dois'
    }
    $resultado = Executar-Caso $aviso
    Assert-Condition (-not $resultado.Erro) 'envio conjunto falhou'
    Assert-Condition ($chamadas.Count -eq 2) 'nao enviou uma vez a cada servico'
    Assert-Condition ($resultado.Saida -contains 'MESSAGE_ID: C0123456789:1700000000.123456') 'sem confirmacao Slack'
    Assert-Condition ($resultado.Saida -contains 'MESSAGE_ID: 123456789012345678') 'sem confirmacao Discord'
    Assert-Condition ($resultado.Saida -contains 'TRANSPORTE: slack_bot_api' -and $resultado.Saida -contains 'TRANSPORTE: discord_webhook') 'evidencias sem transporte'
    foreach ($chamada in $chamadas) {
        $conteudo = if ($chamada.Transporte -eq 'slack') { $chamada.Payload.text } else { $chamada.Payload.content }
        Assert-Condition ($conteudo.Contains('Agente: qa') -and $conteudo.Contains('Execucao: mesmo-id-nos-dois')) 'identidade ou correlacao divergente'
        Assert-Condition ($conteudo.Contains('Status: DONE') -and $conteudo.Contains('parecer reprovado')) 'resultado tecnico alterado'
    }
    $total++
    Write-Output 'OK: Slack e Discord recebem o mesmo agente, resultado e ExecucaoId.'

    foreach ($caso in @('falha-slack', 'falha-discord', 'falha-ambos')) {
        $cenario = $caso
        $chamadas.Clear()
        $resultado = Executar-Caso $aviso
        Assert-Condition ([bool]$resultado.Erro) 'falha parcial nao sinalizada'
        Assert-Condition ($chamadas.Count -eq 2) 'falha de um impediu tentar o outro'
        if ($caso -eq 'falha-slack') {
            Assert-Condition ($resultado.Saida -contains 'MESSAGE_ID: 123456789012345678') 'sucesso Discord perdido'
        } elseif ($caso -eq 'falha-discord') {
            Assert-Condition ($resultado.Saida -contains 'MESSAGE_ID: C0123456789:1700000000.123456') 'sucesso Slack perdido'
        }
        Assert-Condition (-not ($resultado.Saida -join '').Contains('token-ficticio')) 'segredo ficticio vazou'
        $total++
    }
    Write-Output 'OK: falhas independentes preservam sucessos e tentam ambos.'

    $cenario = 'sucesso'
    foreach ($transporte in @('slack', 'discord')) {
        $chamadas.Clear()
        $retomada = $aviso.Clone(); $retomada.Transportes = @($transporte)
        $resultado = Executar-Caso $retomada
        Assert-Condition (-not $resultado.Erro -and $chamadas.Count -eq 1) 'retomada reenviou aos dois'
        Assert-Condition ($chamadas[0].Transporte -eq $transporte) 'retomada escolheu outro transporte'
        $total++
    }
    Write-Output 'OK: retomada seletiva nao repete o envio ja confirmado.'

    $chamadas.Clear()
    $duplicado = $aviso.Clone(); $duplicado.Transportes = @('slack', 'slack')
    $resultado = Executar-Caso $duplicado
    Assert-Condition ([bool]$resultado.Erro -and $chamadas.Count -eq 0) 'aceitou transporte duplicado'
    $total++
    Write-Output "RESULTADO: $total casos conjuntos aprovados; nenhuma chamada externa."
}
finally {
    foreach ($nome in $anteriores.Keys) {
        [Environment]::SetEnvironmentVariable($nome, $anteriores[$nome], 'Process')
    }
}
