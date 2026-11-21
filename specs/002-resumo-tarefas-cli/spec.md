# Feature Specification: Resumo de tarefas no terminal

**Feature Branch**: `002-resumo-tarefas-cli` (a criar pelo orquestrador; especificação inicial na branch `main`)

**Created**: 2026-11-21

**Status**: Draft — aguardando revisão humana

**Input**: User description: "Adicionar python -m tarefas --arquivo CAMINHO resumo com contagens Total, Pendentes e Concluídas; zeros sem tarefas; respeitar arquivo e padrão existentes; somente leitura; ausência não cria arquivo; preservar erros; incluir ajuda e exemplo README. Sem recursos extras."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar contagens de tarefas (Priority: P1)

Como pessoa que gerencia tarefas no terminal, quero consultar quantas tarefas tenho no total, pendentes e concluídas, para acompanhar meu progresso sem contar a listagem manualmente. Identificador de rastreabilidade: **US1**.

**Why this priority**: É o resultado central solicitado e entrega valor em uma única consulta.

**Independent Test**: Consultar um conjunto controlado com dois itens pendentes e um concluído e comparar as três contagens com os registros, verificando que o arquivo permaneceu com o mesmo conteúdo.

**Acceptance Scenarios**:

1. **Dado** um arquivo válido com duas tarefas pendentes e uma concluída, **Quando** executar `python -m tarefas --arquivo CAMINHO resumo`, **Então** obter em stdout, nessa ordem e em linhas separadas, `Total: 3`, `Pendentes: 2` e `Concluídas: 1`, com código 0, stderr vazio e conteúdo do arquivo inalterado (FR-001, FR-002, FR-005).
2. **Dado** um conjunto válido vazio, **Quando** consultar o resumo, **Então** obter `Total: 0`, `Pendentes: 0` e `Concluídas: 0`, com código 0 (FR-002, FR-004).
3. **Dado** um conjunto contendo apenas tarefas pendentes ou apenas concluídas, **Quando** consultar o resumo, **Então** a categoria ausente ser zero e o total ser igual à soma das duas categorias (FR-002).

---

### User Story 2 - Consultar a origem correta com segurança (Priority: P1)

Como pessoa que mantém conjuntos locais de tarefas, quero consultar o conjunto selecionado sem criar nem alterar dados e ser informada quando eles não puderem ser lidos. Identificador de rastreabilidade: **US2**.

**Why this priority**: Uma contagem de outra origem ou zeros ocultando uma falha prejudicam a confiança no resultado.

**Independent Test**: Usar origens distintas, um caminho ausente e entradas inválidas; conferir seleção, resultados, códigos, mensagens e preservação dos arquivos.

**Acceptance Scenarios**:

1. **Dado** dois arquivos com contagens diferentes e dados diferentes no caminho padrão, **Quando** consultar com `--arquivo CAMINHO`, **Então** contar somente as tarefas desse caminho (FR-003).
2. **Dado** dados no caminho padrão `.tarefas/tarefas.json` do diretório pessoal, **Quando** executar `python -m tarefas resumo` sem `--arquivo`, **Então** apresentar as contagens dessa origem, preservando a convenção existente (FR-003).
3. **Dado** um arquivo ausente, inclusive com diretórios pais ausentes, **Quando** consultar o resumo, **Então** retornar as três contagens zero, código 0 e não criar arquivo nem diretórios (FR-004, FR-005).
4. **Dado** falha de leitura, caminho que é diretório ou ancestral que é arquivo, **Quando** consultar o resumo, **Então** retornar código 1, mensagem `Erro: não foi possível ler os dados locais.` em stderr, stdout vazio e nenhum dado alterado (FR-005, FR-006).
5. **Dado** conteúdo malformado ou documento inválido segundo as regras existentes, **Quando** consultar o resumo, **Então** produzir o mesmo erro de leitura e código 1, sem apresentar contagens nem substituir o conteúdo por zeros (FR-006).

---

### User Story 3 - Descobrir como consultar o resumo (Priority: P2)

Como pessoa que usa a aplicação, quero descobrir o novo comando pela ajuda e consultar um exemplo no README. Identificador de rastreabilidade: **US3**.

**Why this priority**: Torna o comportamento acessível pelos meios de orientação já existentes.

**Independent Test**: Consultar a ajuda e conferir se o exemplo documentado permite reproduzir as três contagens com dados fictícios.

**Acceptance Scenarios**:

1. **Dado** o terminal da aplicação, **Quando** executar `python -m tarefas --help`, **Então** a ajuda incluir `resumo` e descrever a consulta de contagens, com código 0 (FR-007).
2. **Dado** o comando de resumo, **Quando** executar `python -m tarefas resumo --help`, **Então** exibir sua ajuda e sair com código 0 sem ler nem alterar tarefas (FR-007).
3. **Dado** o README do projeto, **Quando** seguir seu exemplo de resumo com arquivo explícito e tarefas fictícias, **Então** conseguir identificar a invocação, as contagens esperadas e o caráter somente leitura da consulta (FR-008).

---

### Edge Cases

- Nenhuma tarefa ou arquivo ausente: três zeros, sem criar arquivo ou diretórios.
- Somente uma categoria de status: a outra permanece zero; identificadores não sequenciais não influenciam a contagem.
- Documento vazio em bytes, texto malformado, versão desconhecida, registros inválidos, status desconhecido ou identificadores repetidos: falha de leitura conforme regras existentes, nunca resumo parcial.
- Caminho inacessível, diretório como destino ou ancestral que é arquivo: erro de leitura, não ausência legítima.
- Caminho explícito diferente do padrão: consultar somente a origem solicitada.
- Consulta repetida: mesmos dados produzem mesmas contagens, sem regravar, reordenar ou normalizar o arquivo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A aplicação DEVE disponibilizar `resumo` em `python -m tarefas`, aceitando a opção global existente `--arquivo CAMINHO` antes do comando e sem exigir argumentos adicionais (US1).
- **FR-002**: O resumo DEVE exibir em stdout exatamente três linhas, na ordem `Total: N`, `Pendentes: P`, `Concluídas: C`, com inteiros não negativos. Cada tarefa válida conta uma vez; N = P + C. Os status existentes `pendente` e `concluida` correspondem às duas categorias. Consultas bem-sucedidas DEVEM retornar código 0 e stderr vazio (US1).
- **FR-003**: O resumo DEVE respeitar a seleção de arquivo existente: usar o caminho explícito de `--arquivo` e, na sua ausência, `.tarefas/tarefas.json` no diretório pessoal, com as mesmas regras atuais de resolução de caminhos (US2).
- **FR-004**: Conjunto válido vazio ou arquivo legitimamente ausente DEVE resultar nas três contagens zero e código 0 (US1, US2).
- **FR-005**: O resumo DEVE ser somente leitura: não criar arquivo ou diretórios, nem modificar conteúdo, tarefas, identificadores, status ou formato dos dados existentes, em sucesso ou falha (US1, US2).
- **FR-006**: O resumo DEVE preservar a validação de dados e o tratamento de falhas de leitura existentes. Falhas de acesso ou dados inválidos DEVEM produzir `Erro: não foi possível ler os dados locais.` em stderr, código 1 e stdout vazio, sem contagens parciais nem zeros que ocultem a falha (US2).
- **FR-007**: A ajuda geral DEVE listar e descrever `resumo`; `resumo --help` DEVE apresentar a ajuda do comando e sair com código 0 sem acessar os dados (US3).
- **FR-008**: O README DEVE incluir exemplo reproduzível de `python -m tarefas --arquivo CAMINHO resumo` com dados fictícios, as três contagens esperadas e a indicação de que a consulta não altera os dados (US3).

### Key Entities *(include if feature involves data)*

- **Tarefa**: Registro existente com identificador, descrição e status pendente ou concluído; esta feature apenas o consulta.
- **Resumo**: Contagens total, pendentes e concluídas de um único conjunto selecionado, calculadas para exibição e sem persistência própria.
- **Origem de tarefas**: Arquivo escolhido explicitamente ou pelo caminho padrão existente; sua ausência legítima representa conjunto vazio.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos cenários válidos de US1, as três contagens correspondem ao conjunto consultado e o total equivale à soma das categorias (FR-001, FR-002, FR-004).
- **SC-002**: Em 100% dos cenários de seleção explícita e padrão de US2, os resultados representam exclusivamente a origem solicitada (FR-003).
- **SC-003**: Em todas as consultas de sucesso e falha previstas, nenhum arquivo de tarefas tem seu conteúdo alterado e nenhum arquivo ou diretório ausente é criado (FR-005).
- **SC-004**: Em 100% dos cenários de falha previstos em US2, a pessoa recebe o erro definido, sem resumo enganoso ou parcial (FR-006).
- **SC-005**: Os dois caminhos de ajuda de US3 permitem descobrir o comando sem acessar dados; o exemplo do README reproduz as três contagens documentadas (FR-007, FR-008).

## Assumptions

- Público e contexto permanecem os da aplicação local existente: pessoas gerenciando tarefas pelo terminal.
- A invocação em Python é a interface já existente solicitada, não uma nova decisão tecnológica nesta especificação.
- A apresentação em três linhas com rótulo, dois-pontos e número é o padrão simples adotado para tornar o resultado inequívoco; nenhuma nova opção de formatação é necessária.
- Dependências de comportamento: seleção de caminho, estados válidos, leitura e validação já existentes. Os demais comandos mantêm o comportamento aprovado.
- Escopo limitado às contagens, segurança de leitura, ajuda e exemplo no README. Filtros, percentuais, agrupamentos, exportação e alterações de tarefas não fazem parte desta feature.
- Notificações da fábrica são infraestrutura do processo e não integram o produto.
- A verificação futura dos requisitos deve usar dados fictícios e testes automatizados conforme a constituição; esta etapa valida somente a especificação.
