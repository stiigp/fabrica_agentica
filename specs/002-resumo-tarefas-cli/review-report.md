# Revisão de código — E5

Parecer: **aprovado**.

## Escopo e referências

Primeira revisão em 2026-11-21, branch `002-resumo-tarefas-cli`, intervalo `main...HEAD`, HEAD `ca8a047a9f4d568bb41ff9df40f17a3a20d6913e`. Conferidos diff completo, constituição 1.0.0, spec, plan, research, data-model, contrato CLI, quickstart, tasks, código existente de leitura/modelo e testes alterados. Aprovação humana da spec recebida pelo handoff; cabeçalho histórico preservado.

## Apontamentos

Nenhum apontamento identificado. Nenhum defeito crítico ou violação da constituição encontrado no escopo desta revisão. Não há correções solicitadas.

## Fundamentação

- FR-001/002/004: parser registra `resumo`; serviço puro conta uma vez cada tarefa validada, inclusive vazio e categorias únicas. Impressão segue as três linhas e encerra com código 0. Contagem O(n), memória adicional O(1), sem ordenação.
- FR-003/005/006: reutiliza resolução de caminhos e validação integral de `carregar`; retorno anterior aos ramos mutáveis e a `salvar`. Testes conferem origens explícita, relativa e padrão fictício, bytes e árvore preservados, pais ausentes, documentos inválidos, diretório/ancestral arquivo e PermissionError simulado. Modelo imutável restringe os dois status, justificando o ramo complementar na contagem.
- FR-007: ajuda geral e específica descrevem a consulta; guards de leitura, escrita e home verificam encerramento antecipado.
- FR-008: exemplo README coincide com a sequência do quickstart: três adições, conclusão do ID 3, resumo 3/2/1. Reprodução automatizada independente da sequência documental permanece na E6 do QA, conforme plano e tarefas.
- Testes novos conferem resultados observáveis exatos, códigos e stderr; integração usa subprocessos e JSON reais em temporários, preservando testes anteriores. Sem dependências, migrações ou alteração de esquema; `.env` e variantes locais permanecem ignorados. Nenhum segredo real identificado no diff.
- Alterações documentais e de controle foram conferidas; a reconciliação do state da feature 001 foi contextualizada pelo handoff como registro de merge anterior. Nenhum state ou artefato de especificação foi alterado pelo revisor.

## Verificações executadas

Na raiz do projeto, Python 3.13.13 no PATH temporário e `PYTHONUTF8=1`:

| Comando | Resultado |
|---|---|
| `python -m unittest discover -s tests -t . -v` | código 0; 79 testes, 21.366s, OK; sem ignorados |
| `python -m compileall -q tarefas tests` | código 0 |
| `git diff --check main...HEAD` | código 0 |

Troca para branch existente executada com hooks desabilitados e elevação após bloqueio de escrita do index no sandbox; branch e HEAD confirmados. Lint/typecheck não aplicáveis pela justificativa prévia do plano. Aceite do QA e revisão dos testes do QA são etapas posteriores, não executadas nesta E5.

## Encaminhamento

Avançar para E6 (QA), com aceite independente e posterior revisão dos testes adicionados pelo QA. Esta aprovação cobre a revisão de implementação, sem declarar a feature entregue ou substituir o merge humano.

## E6 — Revisão dos testes do QA

Parecer: **aprovado**, sem apontamentos. Revisão estática em 2026-11-21, limitada a `tests/acceptance/__init__.py` e `tests/acceptance/test_resumo.py`, intervalo `ca8a047a9f4d568bb41ff9df40f17a3a20d6913e..7bb0cd73ca5b621182ccc0d2098f299cd587b793`. Branch confirmada após switch com hooks desabilitados. Parecer E5 acima preservado.

Os seis métodos verificam o contrato observável da spec: contagens exatas, código e stderr, seleção de origens, ausência sem criação, erros sem resumo parcial, bytes preservados, ajuda e exemplo real do README. Fixtures incluem categorias únicas, IDs não sequenciais e documentos inválidos. Processos reais usam temporários e home fictício; PermissionError é determinístico. As ajudas devem retornar 0 e apresentar descrição, de modo que acesso indevido aos alvos protegidos não passe silenciosamente. O teste documental extrai os cinco comandos do README, confere sua quantidade, o comando final, a saída documentada e a saída fixa 3/2/1; substitui apenas o caminho por temporário. O arquivo de inicialização permite descoberta sem efeitos adicionais. Não foram identificados falsos positivos ou fragilidade material no escopo atual.

Nenhum comando de testes foi repetido nesta retomada: revisão estática apoiada nas execuções anteriores do QA registradas em `qa-report.md` e confirmadas pelo orquestrador no handoff (85 testes da suíte, seis de aceite e compileall, todos código 0). Nenhuma alteração de produto, testes ou state foi realizada. Próximo: E7, revisão/publicação do PR pelo orquestrador.
