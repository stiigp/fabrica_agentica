# Tasks: Resumo de tarefas no terminal

**Input**: `specs/002-resumo-tarefas-cli/` — spec.md, plan.md, research.md, data-model.md, contracts/cli-resumo.md e quickstart.md.
**Prerequisites**: especificação aprovada pelo humano conforme handoff e plano validado; branch `002-resumo-tarefas-cli`.
**Organization**: incrementos por história, preservando o código existente. Caminhos abaixo relativos à raiz.
**Tests**: obrigatórios pela constituição e pelo plano. Os unitários e de integração fazem parte das próprias tarefas do Desenvolvedor; escrever o teste e constatar a falha pertinente antes da implementação. Aceite independente pertence ao QA na E6, sem tarefas E4 reservadas ao QA.

## Format: `[ID] [P?] [Story] Description`

`[P]` indica arquivos distintos e ausência de dependência pendente na janela indicada. `[USn]` identifica a história. Todas as caixas começam abertas.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: infraestrutura já existente. Sem tarefas: Python 3.10+, biblioteca padrão e unittest disponíveis; nenhuma instalação ou configuração nova necessária.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: reutilizar modelo, persistência e parser atuais. Sem tarefas: não há migração, alteração de esquema ou pré-requisito compartilhado a implementar.

**Checkpoint**: iniciar US1 diretamente.

## Phase 3: User Story 1 — Consultar contagens (Priority: P1) — MVP

**Goal**: consultar contagens exatas sem mutação.
**Independent Test**: conjunto misto 2/1 produz exatamente `Total: 3`, `Pendentes: 2`, `Concluídas: 1`, nessa ordem, com quebra final, código 0 e stderr vazio; verificar também vazio e categoria única, com bytes e coleção preservados.

- [X] T001 [US1] Implementar `resumir(tarefas: list[Tarefa]) -> tuple[int, int, int]` em `tarefas/servico.py`, com unitários em `tests/unit/test_servico.py` para vazio, misto, categorias únicas, IDs não sequenciais e coleção inalterada; aplicar as definições canônicas de `Tarefa.id`, `Tarefa.descricao`, `Tarefa.status` e `Resumo` (posições total, pendentes, concluidas) em `specs/002-resumo-tarefas-cli/data-model.md`, sem revalidar ou alterar o modelo; função pura O(n), memória adicional O(1), sem ordenar (FR-002, FR-004, FR-005; SC-001, SC-003).
- [X] T002 [US1] Registrar o subcomando `resumo` sem argumentos adicionais em `tarefas/cli.py`, importar a função e, após `carregar`, imprimir o contrato de três linhas e retornar 0 antes dos ramos mutáveis e de `salvar`; ampliar `tests/unit/test_cli.py` com contagens, código/stderr, coleção preservada e spy proibindo `salvar`, e `tests/integration/test_cli.py` com subprocesso para misto, vazio e categoria única, repetição e bytes preservados; manter contratos anteriores e reutilizar validação integral existente conforme `specs/002-resumo-tarefas-cli/data-model.md`, definições canônicas `Tarefa.id`, `Tarefa.descricao`, `Tarefa.status`, JSON `schema_version`/`tarefas` e registros `id`/`descricao`/`status`, sem modificar `tarefas/modelo.py` ou `tarefas/armazenamento.py` (FR-001, FR-002, FR-004, FR-005; SC-001, SC-003). Depende de T001.

**Checkpoint**: US1 funcional, teste independente aprovado; MVP técnico de contagens disponível.

## Phase 4: User Story 2 — Consultar a origem correta com segurança (Priority: P1)

**Goal**: demonstrar seleção correta, ausência legítima e preservação dos erros sem escrita.
**Independent Test**: consultar arquivos distintos e padrão fictício; ausência retorna zeros sem criar pais; falhas retornam código 1, stdout vazio e `Erro: não foi possível ler os dados locais.` em stderr, sem modificar dados.

- [X] T003 [P] [US2] Ampliar `tests/unit/test_cli.py` para resumo com caminho explícito sem consultar home, resolução padrão com home fictício, `PermissionError` determinístico na leitura, `ErroLeitura` e guards de gravação; conferir erro exato, código 1, stdout vazio e nenhuma chamada a salvar em falha; verificar o fluxo reutilizado em `tarefas/cli.py` sem duplicar resolução ou validação (FR-003, FR-005, FR-006; SC-002, SC-003, SC-004). Depende de T002.
- [X] T004 [P] [US2] Ampliar `tests/integration/test_cli.py` para resumo com arquivos explícitos distintos, caminho relativo, padrão em home fictício, arquivo e pais ausentes, diretório como destino, ancestral arquivo, bytes vazios, JSON malformado, versão inválida, registros/status inválidos, chaves e IDs repetidos; conferir resultados/erro exatos, ausência de resumo parcial e bytes/árvore preservados em sucesso e falha; reutilizar `carregar` sem mudar produção (FR-003, FR-004, FR-005, FR-006; SC-001, SC-002, SC-003, SC-004). Depende de T002.

**Checkpoint**: US2 verificável isoladamente com fixtures próprias; seleção e erros herdados comprovados.

## Phase 5: User Story 3 — Descobrir o resumo (Priority: P2)

**Goal**: descobrir o comando e reproduzir um exemplo fictício.
**Independent Test**: ajuda geral lista e descreve resumo; ajuda específica descreve a consulta; ambas saem com 0 sem I/O/home. Exemplo README resulta em 3/2/1 sem alteração na consulta.

- [X] T005 [US3] Conferir e completar descrição da consulta de contagens no parser de `tarefas/cli.py`, ampliando `tests/unit/test_cli.py` e `tests/integration/test_cli.py` para `--help` e `resumo --help`, código 0, stderr vazio e guards proibindo leitura, escrita e consulta a home; preservar comportamento de ajuda dos demais comandos (FR-007; SC-005). Depende de T003 e T004 para evitar edição simultânea dos mesmos arquivos.
- [X] T006 [P] [US3] Acrescentar a `README.md` exemplo reproduzível em diretório temporário com tarefas fictícias, `--arquivo` antes de `resumo`, três contagens esperadas 3/2/1 e indicação de somente leitura; reutilizar os comandos existentes de adicionar/concluir e conferir a sequência contra `specs/002-resumo-tarefas-cli/quickstart.md` (FR-008; SC-005). Depende de T002; pode ocorrer junto de T003, T004 ou T005.

**Checkpoint**: orientação completa; reprodução automatizada independente do exemplo será conferida pelo QA na E6.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: verificar regressão e reprodução, sem trabalho adicional de infraestrutura.

- [X] T007 Validar `tarefas/`, `tests/` e `README.md` executando `python -m unittest discover -s tests -t . -v` e `python -m compileall -q tarefas tests`, exigindo código 0, testes descobertos e nenhum obrigatório ignorado; executar a sequência fictícia de `specs/002-resumo-tarefas-cli/quickstart.md`, conferindo zeros sem criação, 3/2/1, hashes, ajuda e falha controlada; registrar comandos e resultados no retorno E4 (FR-001–FR-008; SC-001–SC-005). Depende de T001–T006.

Lint e typecheck não aplicáveis conforme plan.md: não há ferramenta configurada; não instalar dependências. Saídas compileall somente nos `__pycache__` previstos. Em todos os testes, usar TemporaryDirectory, HOME/USERPROFILE fictícios e PYTHONUTF8=1 nos subprocessos, sem dados pessoais.

## Dependencies & Execution Order

Setup e Foundational não bloqueiam. Ordem principal: `T001 → T002 → (T003 || T004) → T005 → T007`; ramo de documentação: `T002 → T006 → T007`.

US1 entrega o núcleo sem depender de US2/US3. US2 depende do comando da US1, mas seus cenários usam dados independentes; sua implementação consiste em verificar o comportamento reutilizado. US3 depende do registro na US1; T005 segue US2 por compartilhar arquivos, não por dependência de negócio. Polish depende das três histórias.

### Parallel Examples

- US1: T001 e T002 são sequenciais pela função importada; nenhuma oportunidade interna segura.
- US2: após T002, executar T003 (`tests/unit/test_cli.py`) e T004 (`tests/integration/test_cli.py`) em paralelo.
- US3: após T003/T004, executar T005 (CLI/testes) e T006 (`README.md`) em paralelo; T006 também pode acompanhar US2 após T002.

Paralelismo é possibilidade técnica; a fábrica mantém um especialista ativo por vez.

## Coverage

| Requisito | Tarefas | Critério |
|---|---|---|
| FR-001 | T002, T007 | SC-001 |
| FR-002 | T001, T002, T007 | SC-001 |
| FR-003 | T003, T004, T007 | SC-002 |
| FR-004 | T001, T002, T004, T007 | SC-001 |
| FR-005 | T001, T002, T003, T004, T007 | SC-003 |
| FR-006 | T003, T004, T007 | SC-004 |
| FR-007 | T005, T007 | SC-005 |
| FR-008 | T006, T007 | SC-005 |

Todos FR-001–FR-008 e SC-001–SC-005 cobertos; nenhum requisito pendente. Contrato: `specs/002-resumo-tarefas-cli/contracts/cli-resumo.md`. QA criará seu aceite independente em `tests/acceptance/`, incluindo `__init__.py`, na E6, conforme plan.md; isso não constitui pendência destas tarefas E4.

## Implementation Strategy

1. MVP: concluir T001–T002 e validar US1. Não entregar a feature completa antes das demais histórias.
2. Incremento de segurança P1: concluir T003–T004 e conferir US2.
3. Incremento de orientação P2: concluir T005–T006 e conferir US3.
4. Concluir T007 e devolver ao orquestrador para revisão e QA; sem deploy ou operações Git pelo Desenvolvedor.

## Notes

Marcar uma tarefa somente após implementação e testes pertinentes aprovados. Não alterar requisitos, plano, modelo, persistência ou configuração da fábrica. Erros de requisito/plano retornam ao orquestrador; não ampliar o escopo para filtros, formatos ou abstrações adicionais.
