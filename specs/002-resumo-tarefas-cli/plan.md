# Implementation Plan: Resumo de tarefas no terminal

**Branch**: 002-resumo-tarefas-cli | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from /specs/002-resumo-tarefas-cli/spec.md

**Note**: Fluxo speckit-plan 1.4.2; setup-plan.ps1 -Json executado. Aprovação do Checkpoint 1 informada pelo orquestrador prevalece sobre o cabeçalho histórico Draft da spec, que permanece preservado.

## Summary

Adicionar resumo ao parser existente, reutilizar resolução de caminho e carregar, calcular contagens em função pura no serviço e retornar antes de qualquer gravação. Atualizar ajuda, exemplo README e testes. Nenhuma dependência, migração ou mudança de esquema.

## Technical Context

**Language/Version**: Python 3.10+ existente.

**Primary Dependencies**: Biblioteca padrão, sem novas dependências.

**Storage**: JSON local schema_version 1, somente leitura nesta feature.

**Testing**: unittest; Desenvolvedor em tests/unit/ e tests/integration/; QA em tests/acceptance/ com __init__.py para descoberta.

**Target Platform**: CLI local, inclusive Windows/PowerShell UTF-8.

**Project Type**: CLI Python.

**Performance Goals**: Contagem O(n) sem ordenação, memória adicional O(1); leitura mantém O(n). Nenhuma nova meta de latência.

**Constraints**: Validar integralmente antes de imprimir; nenhuma escrita, refatoração ou recurso extra.

**Scale/Scope**: Um conjunto por consulta, três contagens, FR-001–008.

Preparação: Python 3.10+ no PATH, comandos na raiz, nenhuma instalação. PYTHONUTF8=1 nos subprocessos; HOME e USERPROFILE fictícios e TemporaryDirectory para testes. Sem variáveis sensíveis, credenciais de produto ou banco. Sem migrações; fixtures JSON temporárias existentes.

Comandos de verificação:
- python -m unittest discover -s tests -t . -v
- python -m unittest discover -s tests/unit -t . -v
- python -m unittest discover -s tests/integration -t . -v
- python -m unittest discover -s tests/acceptance -t . -v (após criação pelo QA)
- python -m compileall -q tarefas tests

Exigir código 0, quantidade positiva de testes e nenhum teste obrigatório ignorado. Compileall verifica sintaxe; saídas em __pycache__ sob tarefas/ e tests/. Lint e typecheck não aplicáveis: nenhuma ferramenta configurada, conforme README existente; não adicionar dependências para esta extensão. Constituição exige cobertura funcional de todos FR, sem percentual numérico ou ferramenta de cobertura.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Antes da Fase 0 | Após Fase 1 |
|---|---|---|
| I Simplicidade | PASS: extensão mínima | PASS: serviço e CLI existentes, sem dependências |
| II Testes | PASS: três níveis planejados | PASS: matriz FR e erros/bordas abaixo |
| III Aceite | PASS: spec aprovada | PASS: contrato e quickstart observáveis |
| IV Rastreabilidade | PASS: somente documentação | PASS: requisitos e comandos definidos; resultados futuros não declarados executados |
| V Papéis | PASS: branch confirmada e aprovação informada | PASS: sem produto/state/tasks/config alterados; merge humano |

Gates documentais aprovados, sem violações. Testes e aceite do produto dependem das etapas posteriores.

## Project Structure

### Documentation (this feature)

- specs/002-resumo-tarefas-cli/plan.md
- specs/002-resumo-tarefas-cli/research.md
- specs/002-resumo-tarefas-cli/data-model.md
- specs/002-resumo-tarefas-cli/contracts/cli-resumo.md
- specs/002-resumo-tarefas-cli/quickstart.md
- tasks.md: futuro, exclusivamente Criador de Tarefas.

### Source Code (repository root)

- tarefas/servico.py: resumir(tarefas: list[Tarefa]) -> tuple[int, int, int], ordem total/pendentes/concluidas; sem I/O ou mutação.
- tarefas/cli.py: registrar resumo com descrição; após carregar, calcular/imprimir e retornar 0 antes de adicionar/concluir/salvar.
- tarefas/armazenamento.py e modelo.py: reutilizados sem alteração.
- tests/unit/: Desenvolvedor, função pura e guards CLI.
- tests/integration/: Desenvolvedor, subprocessos/leitura real.
- tests/acceptance/: QA, aceite independente; incluir __init__.py.
- README.md: exemplo fictício reproduzível e somente leitura.

**Structure Decision**: Preservar organização atual. Sequência incremental: serviço e unitários, CLI e integração, README, aceite QA. Sem nova classe Resumo, módulo ou esquema.

| Rastreabilidade | Evidência automatizada exigida |
|---|---|
| US1 FR-001/002/004 SC-001 | vazio, misto 2/1, só pendentes/concluídas, IDs não sequenciais; três linhas exatas, código 0, stderr vazio |
| US2 FR-003 SC-002 | arquivos distintos, caminho relativo, explícito sem consultar home e padrão com home fictício |
| US1/US2 FR-005 SC-003 | salvar não chamado, coleção e bytes preservados em repetição/sucesso/falha; pais ausentes não criados |
| US2 FR-006 SC-004 | vazio em bytes, JSON malformado, versão inválida, registros/status inválidos, IDs repetidos, diretório e ancestral arquivo; PermissionError simulado; stdout vazio/erro exato/código 1 |
| US3 FR-007 SC-005 | --help e resumo --help com guards proibindo acesso a dados/home; código 0 |
| US3 FR-008 SC-005 | aceite reproduz sequência README em temporário, confere 3/2/1 e preservação |

Riscos: resumo cair no else de concluir; mitigar retorno antecipado e spy salvar. Permissões variam entre sistemas: simular PermissionError deterministicamente e testar diretório/ancestral arquivo reais. Não substituir carregar por exists() ou ocultar erro com zeros. Desenvolvedor não altera testes QA.

## Complexity Tracking

Nenhuma violação; nenhuma complexidade adicional a justificar.
