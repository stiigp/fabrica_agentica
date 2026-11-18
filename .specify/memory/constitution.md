<!--
Sync Impact Report (temporário; remover antes de commitar a constituição)
- Versão: modelo sem versão adotada → 1.0.0 (adoção inicial).
- Princípios definidos em substituição aos campos do modelo:
  - PRINCIPLE_1_NAME → I. Código simples e escopo mínimo.
  - PRINCIPLE_2_NAME → II. Testes automatizados obrigatórios.
  - PRINCIPLE_3_NAME → III. Critérios de aceite verificáveis.
  - PRINCIPLE_4_NAME → IV. Rastreabilidade e evidências de execução.
  - PRINCIPLE_5_NAME → V. Papéis delimitados e controle humano.
- Seções concretizadas: Restrições da demonstração; Fluxo e critérios de conclusão;
  Governance.
- Seções removidas: nenhuma.
- Pendências e placeholders adiados: nenhum.
- Escopo: somente .specify/memory/constitution.md; AGENTS.md preservado.
-->

# Fábrica de Software Agêntica para Codex Constitution

## Core Principles

### I. Código simples e escopo mínimo

O código DEVE implementar apenas o comportamento exigido pela especificação aprovada.
Funções e módulos DEVEM ter responsabilidade clara e nomes que expressem sua finalidade.
Abstrações, dependências e serviços adicionais DEVEM ter uma necessidade atual documentada
no plano ou nas notas da implementação e validada na revisão. Funcionalidades especulativas
e refatorações sem relação com a entrega NÃO DEVEM integrar a feature. Essa regra mantém
a demonstração compreensível e reduz o trabalho necessário para verificar o resultado.

### II. Testes automatizados obrigatórios

Cada requisito funcional DEVE ser coberto por teste automatizado que confira resultados
observáveis. A lógica DEVE ter testes unitários; fronteiras alteradas entre componentes,
persistência ou serviços DEVEM ter testes de integração quando existirem. Os testes DEVEM
cobrir o caminho principal, entradas inválidas e casos de borda aplicáveis à especificação.
Correções de defeitos DEVEM incluir teste de regressão que reproduza o defeito corrigido.

A suíte DEVE executar com dados de teste controlados e comandos reproduzíveis. Testes
obrigatórios com falha, ignorados ou não executados impedem o aceite. Demonstrações manuais
podem complementar as evidências, mas NÃO substituem os testes automatizados exigidos.

### III. Critérios de aceite verificáveis

A especificação DEVE definir cenários com precondições, ação e resultado esperado,
permitindo decidir objetivamente se cada requisito foi atendido. Termos como "funciona",
"rápido" ou "intuitivo" NÃO constituem critérios sem condições e medidas observáveis.
O QA DEVE relacionar cada critério aos testes e resultados correspondentes; qualquer
critério sem evidência impede o aceite. Alterações de requisitos DEVEM voltar ao Analista
via Spec Kit e receber nova aprovação humana antes da continuidade técnica.

### IV. Rastreabilidade e evidências de execução

Toda tarefa de implementação DEVE apontar o requisito ou a necessidade técnica do plano
que a justifica. Sua conclusão DEVE corresponder a arquivos verificáveis e aos resultados
dos comandos aplicáveis. Relatórios e notas DEVEM registrar o comando, o contexto de
execução, o resultado e as falhas ou limitações encontradas. Resultados não executados
NÃO DEVEM ser descritos como aprovados. Durante o fluxo da fábrica, o orquestrador DEVE
conferir os artefatos e manter `specs/<feature>/state.json` coerente com essas evidências.

### V. Papéis delimitados e controle humano

O fluxo da fábrica DEVE seguir `AGENTS.md`, `.codex/agents/orquestrador.md`, os seis
agentes registrados em `.codex/agents/*.toml` e `.codex/permissoes.yaml`. Somente o
orquestrador DEVE delegar, acionando um especialista por vez e aguardando sua conclusão.
Um agente ou uma skill obrigatória indisponível DEVE ser reportado como lacuna, sem
simular o papel nem pular a etapa. A política YAML NÃO concede permissões bloqueadas
pelo ambiente nem substitui os controles reais da sessão.

A aprovação humana da especificação vigente DEVE anteceder o planejamento. O merge
do PR na branch base DEVE ser realizado pelo humano. Agentes NÃO DEVEM fazer esse merge,
ativar auto-merge, executar force push, rebase, reset destrutivo ou deploy. Atualizações
de contexto pelo Spec Kit DEVEM preservar as instruções da fábrica em `AGENTS.md`,
incluindo os caminhos dos agentes e da política.

## Restrições da demonstração

A demonstração DEVE priorizar execução local, dados fictícios e instruções suficientes
para reproduzir o comportamento e seus testes. Credenciais reais NÃO DEVEM ser incluídas
nos artefatos. A tecnologia e os diretórios de código e testes DEVEM ser definidos no
plano da futura feature, sem pressupor uma aplicação existente nesta configuração.

O `plan.md` e o `quickstart.md` DEVEM registrar pré-requisitos, preparação do ambiente
e comandos exatos de execução e verificação. O plano DEVE indicar os comandos de testes,
lint e build aplicáveis; qualquer categoria não aplicável DEVE ter justificativa explícita
antes da implementação. A verificação DEVE usar os mesmos comandos documentados.

Preparar ou alterar a constituição NÃO inicia uma feature e NÃO autoriza criar
especificações, branches, tarefas de produto ou PRs. Mudanças na própria configuração
da fábrica dependem de solicitação explícita e NÃO DEVEM ser usadas durante uma feature
para contornar os limites dos papéis ou os critérios de qualidade.

## Fluxo e critérios de conclusão

Quando solicitado pelo usuário, o fluxo DEVE passar por especificação, aprovação humana,
plano, tarefas, análise de consistência, implementação por fase, revisão, QA e PR/CI,
seguindo as etapas e os limites de devolução do orquestrador. Os seis especialistas são
`analista_requisitos`, `arquiteto`, `criador_tarefas`, `desenvolvedor`, `revisor_codigo`
e `qa`. Antes de cada delegação, o orquestrador DEVE conferir a branch e a feature ativa
e informar entradas, escopo, diretório absoluto, permissões do papel e critérios de término.

Uma tarefa só DEVE ser marcada como concluída quando os arquivos previstos existirem,
o comportamento exigido estiver implementado e as verificações aplicáveis tiverem sucesso.
Uma feature só DEVE ser apresentada como pronta para o checkpoint de merge quando:

1. A especificação vigente tiver aprovação humana registrada, sem mudança posterior
   de requisitos ainda não aprovada.
2. O plano, as tarefas e a análise de consistência estiverem concluídos e coerentes
   com a especificação e esta constituição.
3. Todas as tarefas previstas estiverem concluídas com evidências verificadas.
4. Todos os critérios de aceite tiverem testes automatizados aprovados e rastreáveis,
   e a suíte existente não apresentar regressões.
5. Os comandos de testes, lint e build aplicáveis tiverem sucesso, com resultados
   registrados; categorias não aplicáveis tiverem a justificativa exigida no plano.
6. A revisão de código e o QA tiverem aprovado a entrega, incluindo a revisão dos
   testes adicionados pelo QA, sem pendências que violem requisitos ou esta constituição.
7. As instruções de reprodução estiverem atualizadas, o PR estiver aberto e as
   verificações obrigatórias de CI estiverem aprovadas, quando configuradas.
8. O `state.json` indicar corretamente as etapas e evidências, aguardando o merge humano.

PR aberto, testes locais aprovados ou intenção de merge NÃO comprovam entrega.
O estado `ENTREGUE` só DEVE ser registrado após consulta que confirme o PR como `MERGED`.

## Governance

Esta constituição estabelece os critérios de qualidade do projeto e complementa as
instruções da fábrica. Ela NÃO substitui `AGENTS.md`, os limites por papel da política
ou as permissões reais da sessão. O plano DEVE avaliar a conformidade antes da
implementação; revisão, QA e revisão do PR DEVEM conferir os princípios e as evidências.
Desvios DEVEM ser registrados e devolvidos ao responsável conforme o fluxo, sem declarar
a etapa aprovada enquanto o impedimento permanecer.

Emendas DEVEM decorrer de solicitação ou aprovação humana explícita, registrar motivação
e impacto sobre os artefatos dependentes e atualizar a versão e a data de alteração.
A ratificação original DEVE ser preservada. O versionamento DEVE seguir `MAJOR.MINOR.PATCH`:
`MAJOR` para remoção ou redefinição incompatível de princípios; `MINOR` para novos
princípios, seções ou ampliação material das regras; `PATCH` para esclarecimentos sem
mudança de obrigação. Artefatos afetados DEVEM ser identificados para revisão antes
da próxima etapa técnica. Alterar a constituição NÃO substitui a aprovação de uma spec.

**Version**: 1.0.0 | **Ratified**: 2026-11-18 | **Last Amended**: 2026-11-18
