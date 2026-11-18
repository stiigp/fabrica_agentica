---
description: "Tarefas de implementação da CLI local de tarefas"
---

# Tasks: Gerenciar tarefas pelo terminal

**Input**: documentos de `specs/001-gerenciar-tarefas-terminal/`.
**Prerequisites**: `spec.md` aprovada; `plan.md`, `research.md`, `data-model.md`, `contracts/cli.md` e `quickstart.md` validados em E2; constituição 1.0.0.
**Branch**: `001-gerenciar-tarefas-terminal`.
**Tests**: obrigatórios por FR-010/FR-011 e constituição II. Unitários e integração acompanham cada entrega do Desenvolvedor; não são tarefas separadas por função. O contrato transversal de isolamento tem tarefa explícita em US3. Aceite é criado pelo QA em E6, conforme o plano.
**Organization**: Setup, Foundational, US1 (P1), US2 (P2), US3 (P3) e Polish; todos os caminhos abaixo são relativos à raiz do repositório.

## Format: `[ID] [P?] [Story] Description`

- `[P]`: tarefas com arquivos diferentes, executáveis em paralelo após suas dependências.
- `[USn]`: história da spec; obrigatório nas fases de história.
- IDs sequenciais; marcar conclusão apenas com arquivos e verificações aprovados.

## Path Conventions

Pacote `tarefas/` na raiz, sem instalação ou dependências externas; execução `python -m tarefas`. Desenvolvedor mantém `tests/unit/` e `tests/integration/`; QA mantém `tests/acceptance/`. README existente da fábrica deve ser preservado.

**Definição de pronto de cada tarefa**: implementar somente o comportamento delegado, acrescentar os testes unitários/integração pertinentes com IDs FR/SC/US nos nomes ou docstrings e dados fictícios isolados; verificar resultados, códigos, stdout/stderr e ausência de efeitos indevidos. Usar `TemporaryDirectory` independente por caso; subprocessos com UTF-8 explícito, `--arquivo` e home fictício passado no ambiente; testes do default com home fictício. Nenhum teste acessa tarefas reais. Não usar skip/expectedFailure para requisitos obrigatórios.

**Gate de toda fase**: executar da raiz `python -m unittest discover -s tests -t . -v` duas vezes (quantidade positiva, código 0, zero falhas/erros/skips obrigatórios) e `python -m compileall -q tarefas tests` (código 0). Registrar evidências no retorno ao orquestrador. Lint/typecheck não aplicáveis conforme justificativa de `plan.md`. Antes de E6, descoberta cobre os testes do Desenvolvedor existentes; depois inclui aceite do QA. Zero testes nunca aprova Setup.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: inicializar o pacote e entregar uma primeira fronteira CLI verificável, sem acesso a dados.

- [X] T001 Criar `tarefas/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` e `.gitignore` de produto para os caches/ambientes previstos em `plan.md`, sem dependências ou mudanças na fábrica (necessidade técnica: Project Structure e descoberta Python 3.10 do plano).
- [X] T002 Implementar entrada `tarefas/__main__.py` e `main(argv=None)` inicial em `tarefas/cli.py` com ajuda em português, código de saída propagado e importação/ajuda sem I/O de tarefas; incluir verificações significativas in-process e subprocesso em `tests/unit/test_cli.py` e `tests/integration/test_cli.py`, com guards que falhem se importação ou ajuda abrir/criar dados ou consultar home (FR-001, FR-010, FR-011, FR-012; `contracts/cli.md`). Depende de T001; não usar testes vazios de importação.

**Checkpoint**: ajuda executável e suíte positiva comprovam contrato inicial e ausência de I/O; comandos de negócio serão entregues nas fases seguintes.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: estabelecer modelo, validação de entrada e persistência compartilhados. Bloqueia todas as histórias.

- [ ] T003 [P] Implementar dataclass `Tarefa`, validação e erros simples de domínio em `tarefas/modelo.py`, com `tests/unit/test_modelo.py`; aplicar as definições canônicas de [data-model.md — Tarefa](data-model.md#tarefa) para **Tarefa.id**, **Tarefa.descricao** e **Tarefa.status**, incluindo validação de registros carregados, sem duplicar ou estreitar as restrições (FR-002, FR-003, FR-004, FR-006, FR-009; responsabilidade modelo no plano).
- [ ] T004 [P] Completar parser dos três subcomandos e opção global, rejeição sintática/descrição/ID antes de I/O, resolução lazy de caminho explícito/default e tradução de erros esperados em `tarefas/cli.py`, ampliando `tests/unit/test_cli.py` conforme todas as mensagens/códigos de `contracts/cli.md`; testar ajuda de subcomando, argumento extra/desconhecido, formas inválidas de ID, ausência de descrição e falha de home fictício, sem simular sucesso dos comandos ainda não implementados (FR-001, FR-002, FR-007, FR-009, FR-011).
- [ ] T005 Implementar `carregar(caminho)` e `salvar(caminho, tarefas)` em `tarefas/armazenamento.py`, com `tests/integration/test_armazenamento.py`, obedecendo [data-model.md — Conjunto local](data-model.md#conjunto-local), definições canônicas **Conjunto local.schema_version** e **Conjunto local.tarefas**, e [data-model.md — Tarefa](data-model.md#tarefa), **Tarefa.id**, **Tarefa.descricao**, **Tarefa.status**, inclusive estrutura exata e chaves repetidas; cumprir transições/persistência do mesmo documento e fluxo de falhas de `plan.md` (FR-008, FR-009, FR-010, FR-011). Distinguir ausência de erros; validar documento inteiro; salvar por temporário próprio fechado no mesmo diretório e substituição, preservando original/erro principal. Cobrir dados válidos/inválidos, Unicode, versão/tipos/chaves/IDs inválidos e falhas determinísticas de leitura, mkdir, escrita, fechamento, replace e limpeza. Depende de T003.

**Checkpoint**: modelo e armazenamento completos; casos inválidos/falhas nunca se tornam coleção vazia; parser e ajuda não acessam dados indevidamente. Gate da fase aprovado antes de US1.

## Phase 3: User Story 1 — Registrar e consultar tarefas entre execuções (Priority: P1) — MVP

**Goal**: adicionar e listar tarefas com persistência, identificação estável e erros seguros.
**Independent Test**: com arquivo temporário inicialmente ausente, listar sem criar arquivo, adicionar três tarefas (duas descrições iguais e uma acentuada), listar em novos processos e adicionar novamente sem reutilizar ID. Rejeitar descrições inválidas e exercitar falhas de persistência sem confirmação falsa. Cobre US1.1–US1.7, SC-001 e parte de SC-003.

### Implementation for User Story 1

- [ ] T006 [P] [US1] Implementar adição pura sobre nova coleção em `tarefas/servico.py` com `tests/unit/test_servico.py`, seguindo a transição Adicionar e as definições canônicas **Tarefa.id**, **Tarefa.descricao** e **Tarefa.status** em [data-model.md — Tarefa](data-model.md#tarefa); verificar descrição exata, duplicatas, coleção original intacta e geração de ID em fixture fora de ordem (FR-002, FR-003, FR-004; SC-001).
- [ ] T007 [P] [US1] Implementar `listar` em `tarefas/cli.py`, ampliando `tests/unit/test_cli.py`: compor carregamento, apresentar vazio ou cada registro uma vez na ordem/formato de `contracts/cli.md`, com escape reversível de descrição e ambos os status, sem escrita nem criação de arquivo ausente; traduzir falhas de leitura sem sucesso em stdout (FR-001, FR-005, FR-009; SC-001, SC-003). Usa T005; independe de T006.
- [ ] T008 [US1] Integrar `adicionar` e confirmação somente após persistência em `tarefas/cli.py`, ampliando `tests/unit/test_cli.py` e `tests/integration/test_cli.py`; automatizar o teste independente de US1, preservação de acentos/espaços/controles, rejeição sem I/O, novos processos/arquivos independentes, caminhos relativos e falhas de leitura/gravação sem sobrescrever original ou alegar sucesso (FR-001 a FR-005, FR-008, FR-009, FR-010, FR-011; SC-001, SC-003). Depende de T006 e T007.

**Checkpoint**: MVP de registro/consulta persistente demonstrável após gate. US1 não exige conclusão nem documentação final de US3 para ser testada; entrega final continua exigindo todas as fases e QA.

## Phase 4: User Story 2 — Concluir uma tarefa pelo identificador (Priority: P2)

**Goal**: concluir apenas a tarefa selecionada, preservar os demais dados e tratar repetição/ID inexistente.
**Independent Test**: preparar diretamente fixture temporária com duas pendentes e uma concluída, sem usar adição da US1; concluir uma pendente, recarregar em novo processo, repetir conclusão e testar IDs ausentes/inválidos/inexistentes. Comparar coleção e bytes nos casos sem alteração. Cobre US2.1–US2.5, SC-002 e parte de SC-003.

### Implementation for User Story 2

- [ ] T009 [US2] Implementar conclusão pura e indicação de mudança/estado já concluído em `tarefas/servico.py`, ampliando `tests/unit/test_servico.py` segundo transições e definições canônicas **Tarefa.id**, **Tarefa.descricao** e **Tarefa.status** em [data-model.md — Tarefa](data-model.md#tarefa); preservar original, identidade e demais tarefas, com erro de inexistência sem mutação (FR-006, FR-007; SC-002, SC-003).
- [ ] T010 [US2] Integrar `concluir` em `tarefas/cli.py`, ampliando `tests/unit/test_cli.py` e `tests/integration/test_cli.py`, conforme `contracts/cli.md`: salvar só mudança efetiva, confirmar após salvar, informar repetição sem reserializar, tratar ID inexistente/entrada inválida e falhas sem sucesso falso; verificar fixture independente, nova execução, stdout/stderr/códigos e bytes intactos nas operações sem alteração (FR-001, FR-005 a FR-011; SC-002, SC-003). Depende de T009.

**Checkpoint**: US2 verificável com fixture própria; US1 permanece aprovada. Gate da fase obrigatório.

## Phase 5: User Story 3 — Reproduzir o uso e verificar a aplicação com dados isolados (Priority: P3)

**Goal**: consolidar instruções reproduzíveis e comprovar isolamento/repetibilidade da suíte do Desenvolvedor; preparar a entrega para o aceite do QA.
**Independent Test**: seguir os exemplos em contexto fictício, executar a suíte duas vezes com sentinela fictícia de uso intacta e conferir rastreabilidade FR/SC/US. QA automatizará também os exemplos publicados em E6. Cobre US3.1–US3.4, SC-004 e SC-005.

### Tests and Implementation for User Story 3

- [ ] T011 [P] [US3] Consolidar os testes explicitamente exigidos do contrato de isolamento em `tests/unit/test_isolamento.py` e `tests/integration/test_isolamento.py`: guards de acesso ao default com caminho explícito, home fictício no teste do default, sentinela fictícia byte a byte intacta e casos consecutivos com temporários independentes, seguindo `plan.md` e sem ler/hash de dados reais; complementar lacunas observáveis da suíte existente com referências FR/SC/US, sem chamar a própria suíte recursivamente (FR-010, FR-011; SC-004). Estes testes verificam o código já entregue, sem depender de T012.
- [ ] T012 [P] [US3] Acrescentar seção de produto em `README.md`, preservando a documentação da fábrica e reproduzindo pré-requisitos, preparação, comandos, resultados/códigos, erros, persistência, isolamento e verificações de `specs/001-gerenciar-tarefas-terminal/quickstart.md`; manter exemplos de produto em blocos PowerShell reconhecíveis pelo QA, com `$arquivo` como única substituição de caminho, e validar diretamente os exemplos em dados fictícios (FR-012; SC-005). Não alterar quickstart/plano nem criar testes de aceite do QA.

**Checkpoint**: documentação pronta e isolamento observado em duas execuções. Em E6 o QA criará `tests/acceptance/__init__.py`, seus `test_*.py` e fixtures, automatizará os exemplos de quickstart/README como argv e relacionará todos os 16 cenários/casos de borda ao relatório. Essa obrigação do QA não é uma tarefa pendente do Desenvolvedor em E4.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: conferir integração final, comandos publicados e cobertura da entrega antes de revisão/QA.

- [ ] T013 Conferir coerência final de `README.md`, `tarefas/__main__.py`, `tarefas/cli.py`, `tarefas/modelo.py`, `tarefas/servico.py`, `tarefas/armazenamento.py`, `tests/unit/test_cli.py`, `tests/unit/test_modelo.py`, `tests/unit/test_servico.py`, `tests/unit/test_isolamento.py`, `tests/integration/test_armazenamento.py`, `tests/integration/test_cli.py` e `tests/integration/test_isolamento.py` com contrato e matriz de `plan.md`; corrigir somente lacunas da implementação/testes do Desenvolvedor, verificar IDs FR/SC/US e descoberta recursiva, executar versão/preparação, exemplos do quickstart em temporário e gate completo, e devolver evidências ao orquestrador (FR-001 a FR-012; SC-001 a SC-005). Não modificar artefatos de design; inconsistências voltam ao responsável.

**Checkpoint**: todas as tarefas E4 concluídas com evidência. Revisão E5 e aceite E6 continuam obrigatórios; não declarar aceite antecipado.

## Dependencies & Execution Order

### Phase Dependencies

`Setup (T001 → T002) → Foundational (T003 + T004; T003 → T005) → US1 (T006 + T007 → T008) → US2 (T009 → T010) → US3 (T011 + T012) → Polish (T013)`.

- Todos os itens de uma fase anterior devem estar concluídos e seu gate aprovado antes da próxima fase.
- T003 e T004 podem ocorrer em paralelo após Setup. T005 depende de T003 e pode coexistir com T004 se houver execução paralela dentro da fase.
- Após Foundational, T006 e T007 são independentes; T008 usa ambos.
- US2 é testável com fixture independente de US1, mas a execução planejada é sequencial por prioridade e compartilha `servico.py`, `cli.py` e testes com US1.
- US3 usa a aplicação completa para consolidar testes e instruções. T011 e T012 são independentes entre si após US2.
- Polish depende de todas as histórias. Revisão e QA são etapas posteriores do orquestrador.

### Within Each User Story

Regras puras precedem composição CLI; persistência precede confirmação. Testes unitários/integração acompanham a implementação e demonstram falha observável ao reproduzir um comportamento ainda ausente. Não é exigido TDD. A tarefa explícita T011 testa uma fronteira já implementada. Nunca substituir assertions de negócio por testes vazios.

### Parallel Opportunities and Examples per Story

| Contexto | Exemplo executável | Limite |
|---|---|---|
| Foundational | T003: `tarefas/modelo.py` + `tests/unit/test_modelo.py`; T004: `tarefas/cli.py` + `tests/unit/test_cli.py` | Ambos após T002; T005 espera T003 |
| US1 | T006: `tarefas/servico.py` + `tests/unit/test_servico.py`; T007: `tarefas/cli.py` + `tests/unit/test_cli.py` | Ambos após gate Foundational; integrar em T008 |
| US2 | Executar T009 e depois T010 | Sem paralelismo seguro: CLI depende da conclusão pura; não marcar `[P]` |
| US3 | T011: arquivos `test_isolamento.py` de unit/integration; T012: `README.md` | Ambos após gate US2; sem arquivos compartilhados |

Estas são oportunidades de arquivos, sem autorização para novos subagentes: a fábrica delega um especialista por vez.

## Implementation Strategy

### MVP First (User Story 1 Only)

Concluir Setup, Foundational e US1 (T001–T008); validar adição/listagem persistentes e falhas com gate e teste independente. Demonstrar localmente em dados fictícios. MVP sugerido: registro e consulta com IDs estáveis; não implica aceite final da feature.

### Incremental Delivery

1. Setup entrega contrato inicial real e testes descobertos.
2. Foundational entrega invariantes, parser e armazenamento seguro.
3. US1 entrega registro/consulta persistente.
4. US2 entrega conclusão, repetição e erros sem regressão.
5. US3 entrega instruções e verificação transversal de isolamento.
6. Polish fecha E4; orquestrador aciona revisão, QA e revisão dos testes do QA conforme o fluxo.

## Coverage & Notes

| Requisito | Tarefas implementadoras / verificação do Desenvolvedor |
|---|---|
| FR-001 | T002, T004, T007, T008, T010 |
| FR-002 | T003, T004, T006, T008 |
| FR-003 | T003, T006, T008 |
| FR-004 | T003, T006, T008 |
| FR-005 | T007, T008, T010 |
| FR-006 | T009, T010 |
| FR-007 | T004, T009, T010 |
| FR-008 | T005, T008, T010 |
| FR-009 | T004, T005, T007, T008, T010 |
| FR-010 | Definição de pronto + T002, T005, T008, T010, T011, T013; exemplos documentados automatizados pelo QA em E6 |
| FR-011 | Definição de pronto + T002, T004, T005, T008, T010, T011 |
| FR-012 | T012, T013; automação dos exemplos pelo QA em E6 |

SC-001: T006–T008; SC-002: T009–T010; SC-003: T004–T005, T007–T010; SC-004: testes de cada entrega, T011/T013 e aceite QA; SC-005: T012/T013 e aceite QA. A comprovação integral de SC-004/SC-005 depende de E6, como definido no plano.

Todos os 12 FR possuem cobertura planejada; nenhum requisito sem tarefa ou conflito conhecido. Total: **13 tarefas** — Setup 2, Foundational 3, US1 3, US2 2, US3 2, Polish 1. Sem implementação de concorrência, migração antecipada, instalação de pacotes ou alteração da configuração da fábrica. Estado, operações Git de escrita, delegações e PR pertencem ao orquestrador.
