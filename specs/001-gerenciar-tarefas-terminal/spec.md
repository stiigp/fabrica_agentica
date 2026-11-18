# Feature Specification: Gerenciar tarefas pelo terminal

**Feature Branch**: `001-gerenciar-tarefas-terminal` (proposta; criação pelo orquestrador após E1; branch atual: `main`)

**Created**: 2026-11-18

**Status**: Draft — aguardando revisão humana

**Input**: User description: "Nova feature: criar uma aplicação de terminal para gerenciar tarefas. Requisitos: Adicionar tarefa com descrição obrigatória e identificador automático. Listar tarefas mostrando identificador, descrição e status. Marcar uma tarefa existente como concluída. Informar erro quando o identificador não existir. Persistir as tarefas localmente entre execuções. Incluir testes automatizados com dados isolados dos dados de uso. Documentar como executar a aplicação e os testes. Comece pela especificação e pare para minha aprovação."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - US1 Registrar e consultar tarefas entre execuções (Priority: P1)

Como pessoa que organiza suas atividades no terminal, quero adicionar tarefas e consultar a lista depois de encerrar e abrir a aplicação, para manter meu registro local de trabalho.

**Why this priority**: Registrar, recuperar e reconhecer as tarefas é o valor mínimo da aplicação e permite seu uso mesmo antes da funcionalidade de conclusão.

**Independent Test**: Em um conjunto local de dados controlados inicialmente vazio, adicionar tarefas, listar, encerrar a aplicação, iniciar novamente e conferir o mesmo conteúdo. Essa história entrega um registro consultável e persistente. Abrange FR-001 a FR-005 e FR-008 a FR-009.

**Acceptance Scenarios**:

1. **Dado** um conjunto sem tarefas, **Quando** a pessoa lista as tarefas, **Então** recebe indicação de que nenhuma tarefa está cadastrada.
2. **Dado** um conjunto sem tarefas, **Quando** a pessoa adiciona uma tarefa com descrição "Preparar relatório", **Então** a tarefa é registrada com identificador automático, descrição informada e status pendente, e seu identificador é informado no resultado.
3. **Dado** que uma tarefa já existe, **Quando** a pessoa adiciona outra tarefa com a mesma descrição, **Então** ambas permanecem cadastradas com identificadores distintos.
4. **Dado** tarefas cadastradas, **Quando** a pessoa solicita a listagem, **Então** vê cada tarefa uma vez, com identificador, descrição e status.
5. **Dado** tarefas cadastradas, **Quando** a pessoa tenta adicionar uma tarefa sem descrição ou com descrição composta somente por espaços em branco, **Então** recebe erro que informa a obrigatoriedade da descrição e nenhuma tarefa é criada ou alterada.
6. **Dado** tarefas adicionadas em uma execução encerrada normalmente, **Quando** a aplicação é iniciada novamente e a pessoa solicita a listagem, **Então** todas reaparecem com os mesmos identificadores, descrições e status; adicionar uma nova tarefa não repete o identificador de uma tarefa existente.
7. **Dado** que os dados locais não podem ser lidos ou uma alteração não pode ser salva, **Quando** a pessoa tenta a operação correspondente, **Então** recebe indicação da falha, sem confirmação de sucesso nem substituição dos dados anteriores por uma lista vazia.

---

### User Story 2 - US2 Concluir uma tarefa pelo identificador (Priority: P2)

Como pessoa que acompanha suas atividades, quero marcar uma tarefa como concluída usando seu identificador, para distinguir o trabalho finalizado do que ainda está pendente.

**Why this priority**: A conclusão complementa o registro e a consulta, permitindo acompanhar o andamento das atividades.

**Independent Test**: Preparar dados controlados com duas tarefas pendentes e uma concluída; concluir uma delas e conferir a listagem e a recuperação em outra execução. A preparação não depende de executar a história US1. Abrange FR-001, FR-005 a FR-009.

**Acceptance Scenarios**:

1. **Dado** duas tarefas pendentes, **Quando** a pessoa conclui uma delas pelo identificador existente, **Então** recebe confirmação e apenas a tarefa selecionada passa a concluída, preservando seu identificador e sua descrição.
2. **Dado** uma tarefa marcada como concluída em execução encerrada normalmente, **Quando** a pessoa inicia outra execução e lista as tarefas, **Então** essa tarefa continua concluída e as demais mantêm seus dados.
3. **Dado** um identificador que não pertence a nenhuma tarefa, **Quando** a pessoa tenta concluir uma tarefa com ele, **Então** recebe erro de tarefa inexistente e nenhuma tarefa é criada ou alterada.
4. **Dado** uma tarefa já concluída, **Quando** a pessoa solicita sua conclusão novamente, **Então** é informada de que ela já está concluída e os dados permanecem inalterados.
5. **Dado** tarefas cadastradas, **Quando** a pessoa tenta concluir sem fornecer um identificador válido, **Então** recebe erro que permite reconhecer a entrada inválida e nenhuma tarefa é alterada.

---

### User Story 3 - US3 Reproduzir o uso e verificar a aplicação com dados isolados (Priority: P3)

Como pessoa que vai executar ou verificar a aplicação, quero instruções de uso e testes automatizados reproduzíveis, para conferir os comportamentos sem afetar minhas tarefas reais.

**Why this priority**: Permite reproduzir a entrega e sustentar sua qualidade, conforme a constituição. A prioridade indica a ordem das jornadas; testes e documentação continuam obrigatórios para o aceite da feature.

**Independent Test**: Com um conjunto de tarefas de uso conhecido, seguir as instruções de execução em dados de demonstração, executar os testes duas vezes e comparar os dados de uso antes e depois. A verificação pode usar conjuntos preparados independentemente das demais histórias. Abrange FR-010 a FR-012.

**Acceptance Scenarios**:

1. **Dado** um ambiente que atende aos pré-requisitos documentados, **Quando** a pessoa segue as instruções, **Então** consegue iniciar a aplicação e reproduzir adição, listagem, conclusão e erro por identificador inexistente, com os resultados esperados descritos.
2. **Dado** tarefas locais de uso já existentes, **Quando** a suíte automatizada é executada pelo procedimento documentado, **Então** todos os testes obrigatórios executam sobre dados controlados separados, sem ler, alterar ou excluir as tarefas de uso.
3. **Dado** os mesmos dados iniciais controlados, **Quando** a suíte é executada duas vezes consecutivas, **Então** ambas as execuções verificam os mesmos resultados esperados, sem depender de resíduos da execução anterior.
4. **Dado** os requisitos desta especificação, **Quando** as verificações automatizadas são executadas, **Então** há cobertura observável dos caminhos principais, entradas inválidas, persistência, isolamento e exemplos de execução documentados, com identificação da relação entre requisitos e verificações.

---

### Edge Cases

- Lista inicialmente vazia: informar ausência de tarefas (US1.1; FR-005).
- Descrição ausente ou composta apenas por espaços em branco: rejeitar sem alteração dos dados (US1.5; FR-002).
- Descrições repetidas: permitir tarefas distintas com identificadores próprios (US1.3; FR-003).
- Descrição com acentos e espaços entre palavras: preservar seu conteúdo na listagem e após nova execução (US1.2, US1.6; FR-002, FR-008).
- Nova tarefa após reiniciar: manter a distinção entre os identificadores existentes e o novo (US1.6; FR-003, FR-008).
- Conclusão com identificador inexistente, ausente ou inválido: informar erro sem alterar o conjunto (US2.3, US2.5; FR-007).
- Conclusão repetida: manter o estado concluído sem duplicar tarefas (US2.4; FR-006).
- Falha de leitura ou gravação local: informar falha sem alegar sucesso e sem tratar uma falha de leitura como ausência de tarefas (US1.7; FR-009).
- Execução repetida dos testes com dados de uso presentes: manter isolamento e resultados reproduzíveis (US3.2, US3.3; FR-010, FR-011).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A aplicação DEVE permitir, pelo terminal, adicionar tarefas, listar tarefas e marcar uma tarefa como concluída pelo identificador.
- **FR-002**: A adição DEVE exigir descrição com pelo menos um caractere que não seja espaço em branco. Descrição ausente ou somente em branco DEVE resultar em erro explicativo e nenhuma alteração dos dados. O conteúdo aceito da descrição, incluindo acentos e espaços entre palavras, DEVE ser preservado.
- **FR-003**: Cada adição válida DEVE atribuir automaticamente um identificador distinto dos identificadores de todas as tarefas existentes, informá-lo à pessoa e mantê-lo estável entre operações e execuções. Descrições iguais DEVEM poder pertencer a tarefas distintas.
- **FR-004**: Toda tarefa recém-adicionada DEVE ter status pendente.
- **FR-005**: A listagem DEVE mostrar todas as tarefas cadastradas, pendentes e concluídas, cada uma uma única vez, com identificador, descrição e status reconhecíveis. Se não houver tarefas, DEVE informar essa condição.
- **FR-006**: A conclusão de uma tarefa existente e pendente DEVE mudar apenas seu status para concluída e informar o resultado, preservando seu identificador, descrição e as outras tarefas. Repetir a conclusão DEVE informar que a tarefa já está concluída e manter os dados inalterados.
- **FR-007**: A tentativa de conclusão com identificador inexistente DEVE informar erro de tarefa inexistente. Identificador ausente ou inválido DEVE produzir erro de entrada. Em todos esses casos, nenhuma tarefa DEVE ser criada ou alterada.
- **FR-008**: As adições e conclusões confirmadas como bem-sucedidas DEVEM ser persistidas localmente. Após encerrar normalmente e iniciar uma nova execução no mesmo contexto de dados, a aplicação DEVE recuperar os mesmos identificadores, descrições e status, permitindo novas operações sobre esse conjunto.
- **FR-009**: Falhas ao ler ou salvar os dados locais DEVEM ser informadas como erro, sem confirmar sucesso da operação. Uma falha de leitura NÃO DEVE substituir os dados existentes por um conjunto vazio.
- **FR-010**: A entrega DEVE incluir testes automatizados reproduzíveis dos comportamentos de FR-001 a FR-009, do isolamento de FR-011 e dos exemplos e comandos documentados de FR-012, com rastreabilidade. DEVE incluir testes unitários da lógica e testes de integração da persistência e das fronteiras aplicáveis, cobrindo caminhos principais, entradas inválidas e casos de borda desta especificação.
- **FR-011**: Os testes DEVEM usar dados controlados isolados dos dados de uso. Sua execução NÃO DEVE ler, alterar ou excluir tarefas de uso e DEVE permitir execuções consecutivas com resultados independentes de resíduos anteriores.
- **FR-012**: A documentação DEVE apresentar pré-requisitos, preparação, comandos exatos para iniciar a aplicação, adicionar, listar, concluir e executar os testes, com exemplos e resultados esperados, incluindo descrição inválida e identificador inexistente. DEVE explicar a persistência entre execuções e o procedimento que garante o isolamento dos dados de teste.

### Key Entities *(include if feature involves data)*

- **Tarefa**: Atividade registrada pela pessoa, composta por identificador automático e estável, descrição obrigatória e status pendente ou concluída. Uma tarefa pode passar de pendente a concluída; repetições da conclusão não mudam seus dados.
- **Conjunto local de tarefas**: Tarefas disponíveis em um mesmo contexto de uso e preservadas entre execuções. Os conjuntos controlados usados nos testes são separados dos dados de uso.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em um cenário com três adições válidas, incluindo duas descrições iguais e uma com acentos, 100% das tarefas recebem identificadores distintos e status pendente, e reaparecem com os mesmos dados após encerrar e iniciar outra execução (US1; FR-001 a FR-005, FR-008).
- **SC-002**: Ao concluir uma de três tarefas preparadas, a listagem exibe exatamente uma mudança de status, preserva todos os identificadores e descrições e mantém esse resultado após uma nova execução. Repetir a conclusão produz zero alterações adicionais (US2; FR-005, FR-006, FR-008).
- **SC-003**: Em 100% dos cenários especificados de descrição inválida, identificador inexistente ou inválido e falha de persistência, a aplicação informa o erro correspondente sem confirmação falsa de sucesso; os cenários de entrada inválida produzem zero alterações no conjunto de tarefas (US1, US2; FR-002, FR-007, FR-009).
- **SC-004**: 100% dos cenários de aceite e casos de borda desta especificação possuem verificação automatizada rastreável; duas execuções consecutivas da suíte terminam sem falhas ou testes obrigatórios ignorados e deixam os dados de uso idênticos ao estado anterior (US1 a US3; FR-010, FR-011).
- **SC-005**: Todos os exemplos e comandos publicados para aplicação e testes podem ser reproduzidos em um ambiente com os pré-requisitos declarados, alcançando 100% dos resultados esperados sem etapas de preparação omitidas (US3; FR-012).

## Assumptions

- O ator principal é uma pessoa que usa o terminal localmente. O escopo é adicionar, listar e concluir tarefas; edição, exclusão, reabertura, filtros, prazos, prioridades, contas e sincronização não integram esta feature.
- Uma tarefa nasce pendente e pode ser concluída. Como default, repetir sua conclusão é uma operação sem alteração, com indicação do estado atual.
- O identificador é usado para selecionar tarefas e não depende de a descrição ser única. Seu formato e a ordem da listagem não estão definidos como requisitos; a saída deve permitir reconhecer cada tarefa e seus campos.
- A descrição obrigatória exclui conteúdo apenas em branco. Não há limite de tamanho nem regra de unicidade estabelecidos nesta demanda.
- A persistência é local e considerada em execuções sequenciais no mesmo contexto de dados. Compartilhamento entre pessoas ou computadores, gravações concorrentes e recuperação de interrupção abrupta não integram os cenários de aceite desta feature.
- O ambiente precisa permitir a leitura e gravação dos dados locais para operações bem-sucedidas. Diante de falhas, aplica-se FR-009; não se exige reparação automática dos dados.
- A aplicação não depende de serviços externos para gerenciar as tarefas. Tecnologia, formato de armazenamento, comandos concretos e organização do código serão definidos no planejamento, após aprovação humana.
- Testes e demonstrações usam dados fictícios. As exigências de automação, integração aplicável e rastreabilidade decorrem também da constituição 1.0.0, ratificada em 2026-11-18.
