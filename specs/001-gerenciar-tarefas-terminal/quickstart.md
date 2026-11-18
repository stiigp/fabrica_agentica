# Executar e validar a aplicação

**Feature**: 001-gerenciar-tarefas-terminal | **Fase**: 1 de `$speckit-plan` | **Data**: 2026-11-18

O [contrato CLI](contracts/cli.md) define mensagens/códigos e o [modelo](data-model.md) define o arquivo. Este guia apresenta a preparação, os comandos e os resultados esperados para validar a aplicação.

## Pré-requisitos e preparação

Windows com PowerShell, terminal UTF-8 e Python 3.10 ou superior disponível como `python`. Preferir versão mantida em novos ambientes. Abrir o terminal na raiz do checkout, onde existirão `tarefas/` e `tests/`. Sem instalação de pacotes, serviços, credenciais ou ambiente virtual obrigatório. O launcher `py` não é necessário.

```powershell
python --version
$diretorioDemo = Join-Path ([System.IO.Path]::GetTempPath()) ("tarefas-demo-" + [guid]::NewGuid().ToString("N"))
$arquivo = Join-Path $diretorioDemo "tarefas.json"
```

Versão deve ser >=3.10 e código de saída 0. As duas atribuições escolhem um caminho novo e isolado, sem remover dados. Não criar JSON vazio manualmente. A aplicação cria os pais na primeira adição válida; listar antes disso não cria arquivo. Usar a mesma sessão PowerShell para preservar `$arquivo`; cada comando Python abaixo já é uma nova execução da aplicação.

## Registrar, recuperar e concluir (SC-001, SC-002)

Executar na ordem:

```powershell
python -m tarefas --arquivo "$arquivo" listar
python -m tarefas --arquivo "$arquivo" adicionar "Preparar relatório"
python -m tarefas --arquivo "$arquivo" adicionar "Preparar relatório"
python -m tarefas --arquivo "$arquivo" adicionar "Revisar seção técnica"
python -m tarefas --arquivo "$arquivo" listar
python -m tarefas --arquivo "$arquivo" concluir 2
python -m tarefas --arquivo "$arquivo" listar
python -m tarefas --arquivo "$arquivo" concluir 2
```

Todos retornam 0. Primeira saída: `Nenhuma tarefa cadastrada.` As adições informam `Tarefa 1 adicionada.`, `Tarefa 2 adicionada.` e `Tarefa 3 adicionada.`. A primeira listagem preenchida é:

```text
1 | pendente | "Preparar relatório"
2 | pendente | "Preparar relatório"
3 | pendente | "Revisar seção técnica"
```

Concluir retorna `Tarefa 2 concluída.`. A listagem seguinte mantém as mesmas três tarefas, IDs e descrições; somente a linha 2 tem status `concluída`. Repetir retorna `Tarefa 2 já está concluída.` sem alterar o arquivo. Os processos distintos demonstram persistência; ao reabrir o terminal, selecionar exatamente o mesmo caminho para recuperar o conjunto. Novo caminho representa outro conjunto.

## Entradas rejeitadas e ausência de alterações (SC-003)

```powershell
python -m tarefas --arquivo "$arquivo" adicionar "   "
python -m tarefas --arquivo "$arquivo" adicionar
python -m tarefas --arquivo "$arquivo" concluir 999
python -m tarefas --arquivo "$arquivo" concluir abc
python -m tarefas --arquivo "$arquivo" concluir
python -m tarefas --arquivo "$arquivo" listar
python -m tarefas --help
```

Resultados na ordem: descrição obrigatória em stderr, código 2 (duas vezes); `Erro: tarefa 999 não encontrada.`, código 1; identificador inteiro positivo obrigatório, código 2 (duas vezes); listagem igual à anterior, código 0; ajuda em português com operações/opção de caminho, código 0. Erros não imprimem sucesso em stdout. Em PowerShell, `$LASTEXITCODE` imediatamente após cada comando fornece o código correspondente. Falhas de persistência são exercitadas por testes controlados, sem alterar permissões ou corromper tarefas pessoais.

## Suíte, repetibilidade e sintaxe (SC-004, SC-005)

Da mesma raiz, executar cada linha e conferir seu resultado:

```powershell
python -m unittest discover -s tests -t . -v
python -m unittest discover -s tests -t . -v
python -m compileall -q tarefas tests
```

Ambas as execuções de teste devem ter quantidade positiva, cobrir unitários/integração/aceite e terminar `OK`, código 0, sem falhas, erros ou testes obrigatórios ignorados. Compileall deve retornar 0; silêncio é normal. Lint e typecheck não se aplicam: sem ferramenta configurada e sem dependência adicional para essa CLI mínima; sintaxe é verificada por compileall e estilo por revisão. Não há percentual de cobertura de linhas imposto; a matriz em plan.md e o relatório QA devem comprovar todos os requisitos e 16 cenários.

Os testes criam TemporaryDirectory por caso e apontam explicitamente para seus arquivos; subprocessos recebem home fictício e `--arquivo`. Testes do caminho padrão substituem home pelo fictício. Sentinelas de tarefas de uso são fictícias e devem permanecer intactas; guards impedem acesso acidental ao default. Nenhum teste lê/altera/exclui tarefas reais, nem usa `$arquivo` da demonstração. Novos temporários tornam as duas execuções independentes. Sem dados compartilhados ou segredos. Caches `__pycache__/` em produto/testes são locais e ignorados pelo Git.

QA automatiza os exemplos CLI lendo estas linhas dos blocos PowerShell e a seção de produto do README, substituindo apenas `$arquivo` por um temporário e executando argv sem shell. Verifica saídas/códigos acima. Preparação, versão e comandos completos de teste/build são executados diretamente nos gates e registrados no relatório, evitando suíte recursiva. README deve preservar a documentação da fábrica e publicar os mesmos comandos/expectativas.

## Uso local e armazenamento

Sem `--arquivo`, o conjunto fica em `.tarefas/tarefas.json` dentro do diretório pessoal retornado por Path.home; não depende da raiz do checkout. Para demonstrações e testes, sempre usar o caminho explícito preparado acima. Arquivo ausente é início vazio; vazio/corrompido, esquema desconhecido ou acesso negado geram erro, sem apagar nem recriar dados. Alterações confirmadas já foram salvas. Concorrência e recuperação de interrupção abrupta não fazem parte do aceite. Nenhuma limpeza manual é necessária para repetir testes; não publicar dados locais no repositório.
