# Implementation Plan: Gerenciar tarefas pelo terminal

**Branch**: `001-gerenciar-tarefas-terminal` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-gerenciar-tarefas-terminal/spec.md`

**Note**: Preenchido por `$speckit-plan` 1.4.2 após `setup-plan.ps1 -Json`, preservando as seções do template. Aprovação vigente: Checkpoint 1 em state.json, mensagem `aprovo` em 2026-11-18T20:10:46.2112293Z, commit informado `480bb00`. Rótulos históricos de rascunho/main na spec não alteram aprovação nem branch efetiva; spec preservada.

## Summary

Aplicação de terminal para adicionar, listar e concluir tarefas, preservando ID, descrição e status entre processos sequenciais. Pacote Python sem dependências externas separa regras, JSON e CLI; caminho explícito permite testes e demonstrações sem acessar tarefas de uso. Confirmar alterações somente após salvar. [research.md](research.md) justifica as decisões; este desenho cobre FR-001 a FR-012 e SC-001 a SC-005, sem ampliar o escopo.

## Technical Context

**Language/Version**: Python 3.10 ou superior; compatibilidade mínima com 3.10.11 disponível. Usar versão mantida em novos ambientes; launcher `py` não é necessário.

**Primary Dependencies**: biblioteca padrão: argparse, dataclasses, json, pathlib, tempfile, os, unittest, unittest.mock e subprocess. Sem instalar pacotes, framework, servidor ou ambiente virtual obrigatório.

**Storage**: JSON UTF-8, esquema 1; default `Path.home() / '.tarefas' / 'tarefas.json'`, substituído integralmente por `--arquivo CAMINHO`. Temporário fechado no mesmo diretório e `os.replace`. Sem banco ou migração inicial; rejeitar versão desconhecida sem alterar dados. [data-model.md](data-model.md).

**Testing**: unittest, testes unitários/integração pelo Desenvolvedor e aceite pelo QA. IDs de requisito/cenário nos testes e matriz no relatório QA. Constituição exige cobertura observável, sem percentual de linhas; não instalar medidor externo.

**Target Platform**: terminal local Windows/PowerShell, primário desta entrega. Código Python independente de shell; outras plataformas não integram aceite obrigatório. Arquivos UTF-8; validar acentos no terminal Windows e subprocessos capturados com encoding explícito.

**Project Type**: CLI, uma operação por processo, execução da raiz com `python -m tarefas`.

**Performance Goals**: sem SLO/benchmark ou limite de volume na spec. Leitura, adição e busca O(n); listagem ordenada O(n log n). Sem limite artificial de descrição/tarefas; conjunto compatível com memória local.

**Constraints**: offline, execuções sequenciais, sem concorrência ou recuperação de queda abrupta. Erros sem confirmação falsa; entradas inválidas sem alterações; falha de leitura nunca vira vazio; descrição integralmente preservada.

**Scale/Scope**: uma pessoa, conjuntos locais independentes, 3 operações, 2 estados; sem serviços, credenciais, distribuição empacotada ou abstrações genéricas de backend.

### Preparação e comandos de verificação

Da raiz do repositório, terminal UTF-8, `python` >=3.10. Preparação: `python --version` (saída 0, versão compatível). Sem instalação de dependências. [quickstart.md](quickstart.md) registra preparação e execução. Os comandos de produto abaixo são definidos para implementação/QA; ainda não executados em E2.

| Categoria | Comando exato / aplicação | Critério |
|---|---|---|
| Teste obrigatório (`commands.test`) | `python -m unittest discover -s tests -t . -v` | saída 0, quantidade positiva, todos diretórios descobertos, zero falhas/erros/skips obrigatórios; repetir duas vezes |
| Build/sintaxe (`commands.build`) | `python -m compileall -q tarefas tests` | saída 0, caches somente nos diretórios de produto/testes |
| Lint (`commands.lint`) | não aplicável, registrar null com esta justificativa | não existe linter configurado; escopo mínimo usa revisão de estilo sem dependência exclusiva para lint |
| Typecheck | não aplicável | sem ferramenta estática configurada; anotações não justificam novo verificador |
| Cobertura observável | comando de teste + matriz e relatório QA | 100% dos 16 cenários/casos de borda; sem meta numérica de linhas na constituição |

Prever `__init__.py` em tests e cada subdiretório, arquivos `test_*.py`, descoberta recursiva compatível com 3.10. Saída de zero testes não aprova o gate mesmo se código 0. Não usar skip/expectedFailure para comportamento obrigatório. Desenvolvedor cria .gitignore de produto para `__pycache__/`, `*.pyc` e ambientes opcionais. Nenhuma configuração da fábrica será alterada. Não há build de distribuição; compileall valida sintaxe, sem afirmar verificação de tipos ou negócio.

### Interfaces e responsabilidades

- `tarefas/__main__.py`: chama cli.main e propaga código de saída.
- `tarefas/cli.py`: parser, mensagens, resolução lazy do caminho e composição das operações conforme [contracts/cli.md](contracts/cli.md). `main(argv=None)` retorna inteiro. Importação não abre dados.
- `tarefas/modelo.py`: dataclass Tarefa, campos/status e erros simples de domínio.
- `tarefas/servico.py`: regras puras sobre coleção; adicionar retorna nova coleção/tarefa; concluir retorna nova coleção/indicação de mudança ou erro. Sem I/O/impressão e sem mutar original antes de salvar.
- `tarefas/armazenamento.py`: `carregar(caminho)` e `salvar(caminho, tarefas)`; caminho obrigatório, validação integral do documento, erros de persistência. Sem interface abstrata ou backend adicional.

Fluxo: validar argumentos antes de ler; resolver caminho apenas para operação válida; carregar documento válido; aplicar regra; salvar se alteração efetiva; confirmar após salvar. Listar, ajuda e conclusão repetida não escrevem; ajuda não lê. Apenas ausência real do arquivo inicializa coleção vazia; diretório, vazio, JSON inválido e erro de acesso falham. Não usar exists para mascarar erros de leitura. Criar pais apenas para alteração válida. Gravar temporário exclusivo, fechar, substituir; preservar original em falhas e limpar somente temporário dessa operação quando possível, sem mascarar o erro principal.

Sem variáveis de ambiente próprias/sensíveis. Default usa home do sistema; caminho explícito evita até essa consulta. Nenhum banco: sem migrações aplicáveis no esquema inicial; uma futura mudança de versão exigirá migração versionada/reversível própria. Fixtures fictícias no esquema 1 em diretórios temporários.

### Testes e rastreabilidade

Desenvolvedor é responsável por `tests/unit/` e `tests/integration/`. QA é responsável por `tests/acceptance/` e suas fixtures; Desenvolvedor não os altera. Testes referenciam FR/SC/US; relatório QA relaciona os 16 cenários com nomes finais de testes e resultados reais.

| Requisitos / critérios | Verificações observáveis | Camadas / cenários |
|---|---|---|
| FR-001, FR-005; SC-001/002 | comandos disponíveis, vazio, todos campos/status, cada tarefa uma vez | unitário CLI, subprocessos e aceite US1.1/4, US2.1 |
| FR-002; SC-003 | descrição ausente/vazia/whitespace sem I/O; acentos, espaços externos/internos e caracteres de controle preservados por escape reversível | serviço/CLI e integração; US1.2/5/6 |
| FR-003, FR-004; SC-001 | 3 adições, 2 descrições iguais e 1 acentuada; IDs positivos distintos, pendente; ID novo após reinício e fixture fora de ordem | serviço e persistência/subprocessos; US1.2/3/6 |
| FR-006; SC-002 | fixture independente com 2 pendentes/1 concluída, mudar só 1 status; repetir sem escrita, dados iguais | unitário, integração, aceite US2.1/2/4 |
| FR-007; SC-003 | ID inexistente, ausente, texto, decimal, zero/negativo; erro correto sem criar/alterar dados | parser/serviço, subprocessos; US2.3/5 |
| FR-008; SC-001/002 | novos processos, mesmo arquivo, mesmos IDs/descrições/status; arquivos distintos independentes | integração e aceite US1.6/US2.2 |
| FR-009; SC-003 | ausência vs vazio/corrompido, esquema/tipos/IDs/chaves inválidos; falhas de leitura, mkdir, escrita, fechamento e replace; original preservado, erro sem sucesso | integração com mocks OSError, E2E diretório/JSON inválido; US1.7 |
| FR-010, FR-011; SC-004 | cenários/casos de borda rastreados, suíte positiva e sem omissões, 2 execuções, sentinela fictícia intacta, guards de acesso ao default | unitário/integração, aceite US3.2/3/4 e gate |
| FR-012; SC-005 | executar exemplos reais extraídos de quickstart/README, erros, ajuda, preparação e comandos de suíte/build publicados | aceite US3.1/4 e evidências diretas no gate QA |

Cada teste cria TemporaryDirectory independente e usa caminho explícito. Home fictício por patch de Path.home in-process e HOME/USERPROFILE passados no ambiente de subprocessos; nunca alterar essas variáveis no terminal global. Testes do default usam só home fictício. Guards/mocks detectam consulta indevida ao default ao usar --arquivo. Sentinela de tarefas de uso é fictícia; verificar bytes intactos sem ler/calcular hash de dados reais. Simular falhas de permissão com mocks determinísticos em vez de depender de ACL/chmod. Original deve permanecer intacto em falhas anteriores à substituição e em replace rejeitado.

QA extrai linhas `python -m tarefas ...` dos blocos PowerShell do quickstart e seção de produto do README, substitui somente $arquivo por caminho temporário e executa como argv, sem shell. Compara resultados/códigos na ordem. Verificação de consistência mantém exemplos de produto em blocos reconhecidos. Preparação, versão e comandos completos de suíte/compileall são evidenciados diretamente no gate; nenhum teste chama a própria suíte recursivamente. README preserva a documentação da fábrica e acrescenta seção de produto.

### Sequência incremental e riscos

1. Estrutura e descoberta da suíte; US1 com adição/listagem, JSON, falhas e testes correspondentes.
2. US2 com conclusão, idempotência, IDs e testes; preparação de dados independente de US1.
3. US3 com documentação final, verificação dos exemplos e aceite QA. Isolamento e testes acompanham todas as fases.

Criador de Tarefas detalhará essa sequência. Riscos: Unicode no Windows, tradução de erros sintáticos do argparse, diretórios omitidos por descoberta e JSON inválido convertido em vazio. Contrato e testes cobrem essas fronteiras. Sem bloqueio conhecido; concorrência e recuperação abrupta continuam fora do escopo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / restrição | Pré-Fase 0 | Pós-Fase 1 | Evidência |
|---|---|---|---|
| I. Simplicidade e escopo | aprovado | aprovado | biblioteca padrão, 3 operações, 1 formato; alternativas em research |
| II. Testes automatizados | aprovado no desenho | aprovado no desenho | unitários, integração e aceite; matriz completa; execução é gate posterior |
| III. Aceite verificável | aprovado | aprovado | spec preservada; contrato e quickstart com resultados/códigos; todos SC rastreados |
| IV. Rastreabilidade | aprovado | aprovado | comandos, diretórios, IDs nos testes e QA; state exclusivo do orquestrador |
| V. Papéis e controle humano | aprovado | aprovado | Checkpoint 1 e branch conferidos; E2 somente documentação, sem subagentes/hooks Git |
| Local, fictício, sem segredos | aprovado | aprovado | aplicação offline e fixtures isoladas; sem credenciais |
| Comandos teste/lint/build | aprovado no desenho | aprovado no desenho | suíte obrigatória e compileall; lint/typecheck não aplicáveis justificados |

Resultado pré-pesquisa e pós-design: **APROVADO**, sem violações ou lacunas de requisito. Isto não declara implementação/testes de produto aprovados. Skill 1.4.2 não exige atualização de AGENTS.md nem fornece update-agent-context; nenhuma atualização feita. .specify/extensions.yml ausente nas inspeções prévia e final; nenhum hook before_plan/after_plan a executar.

## Project Structure

### Documentation (this feature)

```text
specs/001-gerenciar-tarefas-terminal/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
├── state.json              # somente orquestrador
└── tasks.md                # futura saída do Criador de Tarefas; não criar em E2
```

### Source Code (repository root)

```text
tarefas/
├── __init__.py
├── __main__.py
├── cli.py
├── modelo.py
├── servico.py
└── armazenamento.py
tests/
├── __init__.py
├── unit/                  # Desenvolvedor; __init__.py e test_*.py
├── integration/           # Desenvolvedor; __init__.py e test_*.py
└── acceptance/            # QA; __init__.py, test_*.py e fixtures fictícias
README.md                  # preservar fábrica; acrescentar seção de produto
.gitignore                 # saídas locais de produto/testes
```

**Structure Decision**: pacote na raiz permite execução sem instalação/PYTHONPATH. Módulos pequenos por responsabilidade. Estrutura planejada, não criada em E2. Testes com propriedade distinta; dados de uso fora do repositório por padrão, teste/demonstração em temporários. Caches somente em tarefas e tests.

## Complexity Tracking

Nenhuma violação do Constitution Check; nenhuma exceção a justificar.
