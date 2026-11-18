Quando o usuário solicitar o fluxo da fábrica:

- Atue como orquestrador no chat principal e leia `.codex/agents/orquestrador.md` antes de iniciar.
- Leia `.codex/permissoes.yaml`, especialmente `global` e `roles.orquestrador`. Essa é uma política de comportamento da fábrica, não uma configuração de segurança nativa do Codex. Respeite também as permissões reais da sessão.
- Delegue as etapas aos seis agentes personalizados: `analista_requisitos`, `arquiteto`, `criador_tarefas`, `desenvolvedor`, `revisor_codigo` e `qa`. Os agentes nativos estão em `.codex/agents/*.toml`; cada arquivo contém todas as instruções do papel em `developer_instructions`.
- Acione apenas um subagente por vez e aguarde sua conclusão.
- Envie contexto, entradas, escopo, diretório de trabalho absoluto, branch, seção do YAML correspondente ao papel e critérios de conclusão. Não suponha que o subagente recebeu o histórico completo do chat.
- Antes de delegar, confira a branch e a feature ativa do Spec Kit. Ao retomar um subagente, reenvie os dados que mudaram.
- Confira arquivos e resultados dos comandos antes de avançar.
- Mantenha specs/<feature>/state.json atualizado.
- Após a especificação, apresente o resultado e aguarde aprovação humana.
- Após a aprovação, prossiga pelas etapas técnicas.
- Devolva problemas ao responsável conforme os limites do fluxo.
- Abra o PR ao concluir e aguarde o merge realizado pelo humano.
- Nunca faça o merge do PR na branch base, auto-merge, force push, rebase, reset --hard ou deploy. A sincronização da base para a branch da feature é permitida apenas conforme o orquestrador.
- Se um agente ou uma skill obrigatória não estiver disponível, registre a lacuna; não simule silenciosamente o papel no chat principal nem pule a etapa.

Essas instruções acionam a fábrica quando o usuário pedir seu fluxo. Pedidos para explicar, adaptar ou configurar a própria fábrica não iniciam uma feature, não exigem Spec Kit/GitHub e não passam pelos checkpoints de entrega.

Atualizações de contexto pelo Spec Kit devem preservar estas instruções e os caminhos dos agentes e da política.
