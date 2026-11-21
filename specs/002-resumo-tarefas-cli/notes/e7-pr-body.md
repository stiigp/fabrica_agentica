## Resultado

Adiciona `python -m tarefas --arquivo CAMINHO resumo`, exibindo Total, Pendentes e Concluídas. Reutiliza a leitura e a validação atuais: conjunto vazio ou arquivo ausente retorna zeros sem criar arquivo/diretórios; erros continuam sendo informados sem alteração dos dados. Ajuda e README incluem o comando.

[Especificação](https://github.com/stiigp/fabrica_agentica/blob/002-resumo-tarefas-cli/specs/002-resumo-tarefas-cli/spec.md): FR-001–FR-008 e SC-001–SC-005 cobertos; aprovação humana registrada no estado. Implementação mínima em serviço e CLI, sem novas dependências, esquema, opções ou refatorações.

## Verificação

Python 3.13.13, PYTHONUTF8=1, dados temporários e home fictício:

- `python -m unittest discover -s tests -t . -v`: 85 testes aprovados, sem falhas ou ignorados.
- `python -m unittest discover -s tests/acceptance -t . -v`: 6 testes de aceite aprovados (incluídos nos 85).
- `python -m compileall -q tarefas tests`: código 0.
- `git diff --check main...HEAD`: código 0.
- Exemplo real do README reproduzido automaticamente; contagens 3/2/1 e bytes preservados.

Plano, tarefas e análise de consistência concluídos: cobertura 100% dos 13 FR/SC, sem achados. Revisão da implementação e dos testes QA aprovada sem apontamentos; QA aprovado sem defeitos. Todas as etapas executadas; Setup/Foundational sem tarefas porque a infraestrutura já existia. Lint/typecheck não aplicáveis conforme plano.

## Evidências e limites

Os seis agentes personalizados atuaram sequencialmente. Cada acionamento de trabalho enviou notificações reais ao Slack e Discord: 20 confirmações registradas no `state.json`. A E1 exigiu retomadas exclusivas do Slack, autorizadas pelo humano após correção de escopo e participação no canal; Discord não foi reenviado. Nenhum segredo foi gravado nos artefatos.

CI não configurada no repositório; validação local usada em E7. Não foi criada CI nesta feature. PermissionError é simulado de forma determinística nos testes. Sem filtros, percentuais, exportação, concorrência ou mudanças nos demais comandos. O estado da feature anterior foi reconciliado com o merge confirmado do PR #1. Merge deste PR reservado ao humano.
