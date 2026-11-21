# Contrato CLI

**Feature**: 001-gerenciar-tarefas-terminal | **Fase**: 1 de `$speckit-plan` | **Data**: 2026-11-18

## Invocação

```text
python -m tarefas [--arquivo CAMINHO] adicionar [DESCRICAO]
python -m tarefas [--arquivo CAMINHO] listar
python -m tarefas [--arquivo CAMINHO] concluir [ID]
python -m tarefas --help
```

Executar da raiz do repositório. `--arquivo` é global, antes do subcomando, e aceita caminho absoluto ou relativo ao diretório corrente. Substitui o default `Path.home() / '.tarefas' / 'tarefas.json'` sem consultá-lo. Cada caminho seleciona um conjunto independente. Sem configuração sensível ou serviços externos.

Uma operação por processo, sem menu interativo. Subcomando obrigatório; `--help`/`-h` e ajuda de subcomando retornam 0 sem ler/criar dados. Ajuda descreve opções e operações em português. Comando desconhecido, argumento extra ou sintaxe inválida retorna 2 com mensagem reconhecível de entrada inválida em stderr, sem I/O de tarefas.

## Operações e saídas

Cada mensagem abaixo termina em nova linha. Resultados normais vão para stdout; erros para stderr, sem confirmação de sucesso em stdout.

| Operação | Regra | stdout / resultado | Código |
|---|---|---|---|
| adicionar descrição válida | um argumento string, pelo menos um caractere não whitespace; preservar string exata, aceitar repetição; ID = maior existente + 1 | `Tarefa 1 adicionada.` no caso ID 1, após salvar | 0 |
| adicionar sem descrição ou só whitespace | rejeitar antes de leitura/gravação | stderr `Erro: a descrição é obrigatória.` | 2 |
| listar vazio | arquivo ausente ou documento válido sem tarefas; não criar/salvar | `Nenhuma tarefa cadastrada.` | 0 |
| listar com tarefas | ID crescente; todas uma vez; campos abaixo | uma linha por tarefa | 0 |
| concluir pendente existente | mudar somente status, salvar antes de confirmar | `Tarefa 1 concluída.` no caso ID 1 | 0 |
| concluir já concluída | não salvar ou reserializar | `Tarefa 1 já está concluída.` | 0 |
| concluir ID inexistente | não criar/alterar documento | stderr `Erro: tarefa 999 não encontrada.` no caso ID 999 | 1 |
| concluir ID ausente ou inválido | validar antes de I/O | stderr `Erro: informe um identificador inteiro positivo.` | 2 |
| falha de leitura/validação do documento | não tratar como vazio, não escrever | stderr `Erro: não foi possível ler os dados locais.` | 1 |
| falha ao salvar, incluindo criar pais/temporário/fechar/substituir | preservar original, não confirmar sucesso | stderr `Erro: não foi possível salvar os dados locais.` | 1 |

Falha ao resolver o home padrão também é erro de acesso aos dados, código 1; não imprimir traceback para falhas esperadas. Mensagens de persistência podem trazer detalhe adicional na mesma linha após o texto obrigatório; testes conferem prefixo, código, ausência de sucesso e preservação dos dados.

ID de entrada: representação decimal ASCII positiva no padrão `[1-9][0-9]*`, sem sinal, fração ou espaços. Zero, negativos, texto, decimal e zeros iniciais são inválidos; não impor limite artificial. Formato é decisão técnica autorizada pela spec.

Formato estável de listagem:

```text
1 | pendente | "Preparar relatório"
2 | concluída | "  Rever seção 1  "
```

Campos na ordem ID, status legível e descrição como string JSON (`ensure_ascii=False`). Aspas, delimitadores e caracteres de controle no conteúdo recebem escape JSON, mantendo cada tarefa numa linha e permitindo recuperar exatamente a descrição. Status no arquivo é `concluida`; na apresentação, `concluída`. Sem cabeçalho adicional na listagem; nenhuma filtragem. Detalhes do documento em [data-model.md](../data-model.md).

## Fronteiras e garantias

Validar entrada antes de abrir dados; ler e validar todo documento; operar em nova coleção; salvar apenas alteração efetiva. Sucesso de adição/conclusão implica persistência em nova execução sequencial com mesmo caminho. Repetição, erro de ID e entrada inválida não escrevem. Só ausência real do arquivo inicializa vazio; arquivo vazio/malformado ou esquema desconhecido são erro. Falhas de gravação não truncam destino.

Testes de contrato: subprocessos com caminho temporário explícito, captura UTF-8, stdout/stderr e código de saída. Falhas de sistema são exercitadas adicionalmente em integração com mocks determinísticos. Exemplos executáveis e resultados em [quickstart.md](../quickstart.md); cobertura por FR/SC/US em [plan.md](../plan.md).
