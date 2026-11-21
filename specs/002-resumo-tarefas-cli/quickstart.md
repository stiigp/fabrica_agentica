# Quickstart — resumo

Pré-requisitos: Python 3.10+ no PATH, PowerShell UTF-8, executar na raiz; nenhuma instalação. Executar após implementação, somente dados fictícios.

~~~powershell
$env:PYTHONUTF8 = '1'
$diretorioResumo = Join-Path ([IO.Path]::GetTempPath()) ('resumo-demo-' + [guid]::NewGuid().ToString('N'))
$arquivoResumo = Join-Path $diretorioResumo 'tarefas.json'
python -m tarefas --arquivo "$arquivoResumo" resumo
Test-Path -LiteralPath $diretorioResumo
python -m tarefas --arquivo "$arquivoResumo" adicionar "Preparar relatório"
python -m tarefas --arquivo "$arquivoResumo" adicionar "Revisar relatório"
python -m tarefas --arquivo "$arquivoResumo" adicionar "Enviar relatório"
python -m tarefas --arquivo "$arquivoResumo" concluir 3
$hashResumo = (Get-FileHash -LiteralPath $arquivoResumo).Hash
python -m tarefas --arquivo "$arquivoResumo" resumo
$hashResumo -eq (Get-FileHash -LiteralPath $arquivoResumo).Hash
python -m tarefas --help
python -m tarefas resumo --help
~~~

Conferir $LASTEXITCODE imediatamente após cada python: esperado 0. Primeiro resumo apresenta três zeros e Test-Path retorna False. Segundo: Total: 3, Pendentes: 2, Concluídas: 1 em três linhas; hash igual True. Apenas adicionar cria dados. Ajuda geral lista resumo; específica descreve consulta.

Falha controlada:
~~~powershell
$arquivoInvalido = Join-Path $diretorioResumo 'invalido.json'
Set-Content -LiteralPath $arquivoInvalido -Value '{invalido' -Encoding utf8
$hashInvalido = (Get-FileHash -LiteralPath $arquivoInvalido).Hash
python -m tarefas --arquivo "$arquivoInvalido" resumo
$codigoFalha = $LASTEXITCODE
$codigoFalha
$hashInvalido -eq (Get-FileHash -LiteralPath $arquivoInvalido).Hash
~~~

Esperado código 1, stdout vazio, erro definido em contracts/cli-resumo.md e hash igual. Caminho padrão deve ser testado somente com home fictício na suíte.

~~~powershell
python -m unittest discover -s tests -t . -v
python -m compileall -q tarefas tests
~~~

Exigir código 0, testes descobertos sem ignorados. QA executa também python -m unittest discover -s tests/acceptance -t . -v após criar o diretório. Comandos segmentados e justificativas lint/typecheck/cobertura em plan.md. Aceite automatizado reproduz README, origens, categorias, somente leitura, falhas e ajuda sem I/O. Modelo em data-model.md; contrato completo em contracts/cli-resumo.md.
