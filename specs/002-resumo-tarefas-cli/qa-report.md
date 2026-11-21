# QA — E6 — Resumo de tarefas

Parecer: **aprovado**. Execução em 2026-11-21 na branch `002-resumo-tarefas-cli`, implementação aprovada na E5, HEAD do handoff `cf3a50b`. Nenhum defeito encontrado.

## Plano e rastreabilidade

Aceite independente em `tests/acceptance/test_resumo.py`, com unittest e subTests, processos reais da CLI, JSON fictício e TemporaryDirectory. HOME/USERPROFILE apontam para home fictício e PYTHONUTF8=1 nos subprocessos. Sem serviços externos ou credenciais nos testes.

| Caso automatizado (prefixo test_) | Histórias/requisitos/critérios | Verificação |
|---|---|---|
| us1_categorias_e_repeticao_preservam_bytes | US1; FR-001/002/004/005; SC-001/003 | Vazio, misto 2/1, somente pendentes/concluídas, IDs não sequenciais; três linhas exatas, código 0, stderr vazio; duas consultas preservam bytes e formato |
| us2_origens_explicitas_relativa_e_padrao | US2; FR-003/005; SC-002/003 | Dois arquivos e padrão com contagens distintas; absoluto/relativo/padrão; todos os bytes preservados |
| us2_ausencia_nao_cria_arquivo_nem_pais | US2; FR-004/005; SC-001/003 | Arquivo ausente, pais ausentes e padrão ausente: zeros e árvore permanece vazia |
| us2_invalidos_e_obstaculos_preservados | US2; FR-005/006; SC-003/004 | Bytes vazios, JSON malformado, versão desconhecida, registro inválido, status desconhecido, descrição branca, IDs repetidos; diretório e ancestral arquivo; erro exato, código 1 e nenhum resumo parcial; conteúdo/árvore preservados |
| us2_acesso_negado_e_us3_ajudas_sem_io | US2/US3; FR-005/006/007; SC-003/004/005 | PermissionError determinístico em Path.open; ajuda geral/específica encerra com 0, descreve contagens, sem abrir dados, consultar home ou salvar |
| us3_executa_comandos_reais_do_readme | US3; FR-001/002/005/008; SC-001/003/005 | Extrai os cinco comandos Python do bloco real do README, tokeniza e executa com caminho temporário substituindo a variável documental; três adições, conclusão e resumo; compara saída ao bloco text documentado e a 3/2/1, preserva bytes e verifica indicação somente leitura |

Todos os cenários da spec e quickstart estão cobertos pelo aceite e suíte existente: os testes de integração acrescentam chaves repetidas, tipos/estruturas inválidos e guards de I/O em novo processo; os unitários verificam ausência de salvar, mutação e home indevido. A reprodução do README executa os comandos do documento, usando TemporaryDirectory no lugar de sua preparação PowerShell para isolamento e limpeza automática.

## Execução real

Raiz: `C:\Users\Usuario\Desktop\CODING\fabrica_agentica`. Python 3.13.13 via prefixo temporário de PATH `$env:USERPROFILE/.pyenv/pyenv-win/versions/3.13.13`; PYTHONUTF8=1. Nenhuma instalação.

| Comando | Código | Aprovados / reprovados / ignorados |
|---|---|---|
| `python -m unittest discover -s tests -t . -v` | 0 | 85 / 0 / 0; 24.236s |
| `python -m unittest discover -s tests/acceptance -t . -v` | 0 | 6 / 0 / 0; 5.884s |
| `python -m compileall -q tarefas tests` | 0 | Sintaxe aprovada; não é teste |
| `git diff --check` | 0 | Sem erro de whitespace em arquivos rastreados |

São 85 testes distintos (79 existentes e 6 novos); 91 execuções de métodos contando a repetição separada do aceite, sem falhas/erros/ignorados. SubTests representam múltiplas fixtures, sem inflar o total informado pelo unittest. Cobertura funcional: FR-001–008 (8/8), SC-001–005 (5/5), US1–US3 (3/3); não se declara percentual de linhas. Lint/typecheck não aplicáveis conforme plano, sem ferramenta configurada.

`git -c core.hooksPath=NUL switch 002-resumo-tarefas-cli` inicialmente teve acesso ao index negado; repetido com elevação autorizada, código 0. `git branch --show-current` confirmou a branch, código 0. Nenhuma alteração de produção, artefato Spec Kit ou state pelo QA.

## Defeitos e limites

Nenhum defeito identificado; nenhuma severidade ou reprodução de falha de produto a registrar. Segurança básica verificada por ausência de gravação, validação de entradas e isolamento dos dados. Usabilidade verificada por ajuda, README e mensagens exatas. Aplicação textual sem interface visual; nenhuma meta adicional de desempenho/acessibilidade definida. PermissionError simulado conforme plano, evitando dependência de permissões específicas do sistema operacional.

## Arquivos para revisão

- `tests/acceptance/__init__.py` (novo, descoberta).
- `tests/acceptance/test_resumo.py` (novo, seis testes).
- `specs/002-resumo-tarefas-cli/qa-report.md` (este relatório).

Próximo: revisão dos testes adicionados pelo QA. Aceite local não substitui revisão, PR/CI ou merge humano.
