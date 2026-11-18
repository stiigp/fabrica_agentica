# Pesquisa técnica — Gerenciar tarefas pelo terminal

**Etapa**: E2, Fase 0 de `$speckit-plan` 1.4.2. **Data**: 2026-11-18.
**Branch**: `001-gerenciar-tarefas-terminal`. Spec vigente aprovada pelo Checkpoint 1 em `state.json` (mensagem `aprovo`, 2026-11-18T20:10:46.2112293Z; handoff: commit `480bb00`). O cabeçalho histórico de rascunho na spec não substitui essa evidência; a spec é preservada.

## Base da pesquisa

Leitura da constituição 1.0.0, spec completa (sem seção de esclarecimentos adicionais), checklist, política, instruções do papel, README e inventário do repositório. Há apenas configuração da fábrica e documentação, sem código de produto, framework, banco ou suíte a preservar. Python disponível na sessão: `3.10.11`; o comando `py` não está instalado. Decisões abaixo resolvem as escolhas técnicas deixadas explicitamente ao planejamento; não ampliam os requisitos.

## 1. Linguagem e execução

**Decision**: pacote Python `tarefas/` na raiz, executado com `python -m tarefas`, compatível com Python 3.10 ou superior. Usar somente biblioteca padrão: `argparse`, `dataclasses`, `json`, `pathlib`, `tempfile`, `os`, `unittest`, `unittest.mock` e `subprocess`. Não instalar dependências, não exigir ambiente virtual nem empacotamento para executar a partir da raiz. Usar versão mantida do Python quando disponível; a compatibilidade mínima permite reproduzir a demonstração com o interpretador existente.

**Rationale**: atende execução local, CLI, persistência e testes sem instalação de pacotes ou serviços (FR-001, FR-010, FR-012; princípio I). `argparse` fornece subcomandos, ajuda e validação sintática. A CLI traduz os erros de negócio conhecidos para português. Python 3.10 é a base de compatibilidade, não uma exigência de downgrade.

**Alternatives considered**: Node.js exigiria outro runtime sem benefício para esse escopo; aplicação compilada acrescentaria build/distribuição; Click/Typer e pytest acrescentariam dependências para recursos já disponíveis. Um único arquivo misturaria parsing, regras e persistência, dificultando os testes de fronteira exigidos.

**Fonte**: [argparse — documentação oficial](https://docs.python.org/3.10/library/argparse.html). Versão instalada verificada com `python --version`, saída 0.

## 2. Interface e identidade

**Decision**: uma operação por processo, subcomandos `adicionar`, `listar`, `concluir`, opção global `--arquivo CAMINHO`, mensagens em português e códigos 0 (sucesso), 1 (tarefa inexistente ou persistência) e 2 (entrada inválida). ID inteiro positivo, gerado como `max(ids, default=0) + 1`; não há exclusão. Ordem de listagem crescente de ID. Status persistidos `pendente` e `concluida`, apresentação `pendente` e `concluída`.

**Rationale**: subprocessos independentes demonstram diretamente FR-008; IDs curtos favorecem uso no terminal e continuam estáveis sem contador separado (FR-003). Descrições repetidas são permitidas. Validar `descricao.strip()` apenas para decidir obrigatoriedade, mantendo a string original; não impor limite nem normalização. Listar a descrição como string JSON com `ensure_ascii=False`, tornando quebras de linha/tabulações distinguíveis sem perder conteúdo. Contrato completo em `contracts/cli.md`.

**Alternatives considered**: menu interativo torna automação mais custosa; UUID é desnecessário sem concorrência; contador persistido acrescenta invariantes sem existir exclusão; saída em tabela com descrição crua torna campos ambíguos quando há caracteres de controle.

## 3. Persistência e falhas

**Decision**: documento JSON UTF-8 versionado, contendo `schema_version: 1` e `tarefas: []`. Default `Path.home() / '.tarefas' / 'tarefas.json'`; `--arquivo` substitui o caminho integralmente sem consultar o default. Caminhos relativos são relativos ao diretório corrente. Arquivo ausente significa conjunto novo; arquivo vazio, JSON inválido, estrutura inválida, versão desconhecida e erro de acesso são falhas, jamais conjunto vazio. Não usar `exists()` para mascarar erro de leitura: abrir e distinguir especificamente ausência de arquivo, verificando que o destino não seja diretório/inacessível.

**Rationale**: JSON inspecionável e biblioteca padrão bastam para dados locais sequenciais (FR-008/009). Validar documento inteiro antes de qualquer alteração. Criar diretórios pais apenas ao salvar uma mudança válida. Serializar a nova coleção para temporário exclusivo no mesmo diretório, fechar o arquivo e substituir com `os.replace`; confirmar sucesso somente depois. Se salvar falhar, preservar arquivo original e tentar limpar apenas o temporário da operação. Falha de limpeza não mascara o erro principal. A leitura/listagem e conclusão repetida não escrevem. Não abrir o destino para truncamento antes da substituição.

**Alternatives considered**: SQLite oferece transações, mas não há consultas, relacionamentos, concorrência ou necessidade de migração que justifiquem banco; CSV não expressa esquema e tipos tão claramente; sobrescrever JSON diretamente pode destruir os dados anteriores ao ocorrer falha de gravação. Não se promete recuperação de queda abrupta nem coordenação entre processos concorrentes, fora do aceite.

**Fontes**: [json — documentação oficial](https://docs.python.org/3.10/library/json.html) e [os.replace — documentação oficial](https://docs.python.org/3.10/library/os.html#os.replace). A substituição no mesmo sistema de arquivos é a escolha para reduzir a janela de perda; isso não implica garantia de durabilidade diante de falta de energia. [pathlib](https://docs.python.org/3.10/library/pathlib.html) fundamenta a resolução do diretório pessoal.

## 4. Esquema e configuração

**Decision**: sem banco de dados ou ferramenta de migração. O esquema inicial é versionado no documento e em `data-model.md`; rejeitar versões desconhecidas, sem converter ou sobrescrever. Não criar mecanismo de migração antecipadamente. Uma futura mudança exigirá migração versionada, cópia de segurança e caminho reversível planejados na respectiva feature.

**Rationale**: apenas um esquema inicial, sem dados legados; preserva escopo mínimo. Não há credenciais nem variáveis sensíveis. Nenhuma variável de ambiente própria da aplicação; somente a resolução padrão de home pelo sistema, substituída por caminho explícito nos testes. Fixtures são documentos fictícios produzidos em diretórios temporários e obedecem ao mesmo esquema.

**Alternatives considered**: migrações SQL não se aplicam; configurar armazenamento apenas por variável de ambiente é menos visível que o parâmetro CLI e facilita contaminação acidental de testes.

## 5. Verificação e isolamento

**Decision**: `unittest` com testes do Desenvolvedor em `tests/unit/` e `tests/integration/`, aceite do QA em `tests/acceptance/`. Todos esses diretórios e `tests/` terão `__init__.py` para descoberta recursiva. Comando único `python -m unittest discover -s tests -t . -v`, executado duas vezes pelo gate. Build/sintaxe: `python -m compileall -q tarefas tests`. Lint e typecheck não se aplicam: não existe ferramenta configurada e o projeto mínimo não precisa introduzir dependência exclusivamente para isso; sintaxe é coberta pelo compileall e estilo/responsabilidades pela revisão. A constituição exige cobertura observável dos requisitos, sem percentual de linhas; a matriz do plano e os IDs nos testes fornecerão essa evidência, sem instalar medidor de cobertura.

**Rationale**: suíte reproduzível sem rede (FR-010/011; SC-004). Cada caso usa `TemporaryDirectory`; repositório recebe caminho obrigatório por parâmetro, CLI resolve o caminho uma vez. Nenhum acesso a dados ocorre na importação. Testes in-process do default substituem `Path.home()` por home fictício; subprocessos recebem `--arquivo` e `HOME`/`USERPROFILE` fictícios por ambiente passado ao processo, sem alterar o ambiente global. Sentinelas de dados de uso ficam nessa home fictícia; mocks/guards reprovam tentativa de abrir o caminho padrão nos testes com caminho explícito. Não usar nem calcular hash de tarefas reais. Falhas de acesso/gravação são simuladas com mocks determinísticos nas fronteiras; erro de destino ser diretório é caso E2E portátil, sem depender de chmod ou usuário administrador.

**Alternatives considered**: usar diretório de uso e depois restaurá-lo já violaria FR-011; arquivos fixos compartilhados deixam resíduos; teste somente de funções não demonstra persistência entre processos; impor porcentagem de cobertura não provaria cenários de aceite.

**Fontes**: [unittest](https://docs.python.org/3.10/library/unittest.html), [tempfile](https://docs.python.org/3.10/library/tempfile.html) e [compileall](https://docs.python.org/3.10/library/compileall.html), documentação oficial. `TemporaryDirectory` permite preparação e limpeza controladas; os testes devem afirmar os resultados de negócio além de executar chamadas.

## 6. Documentação executável e sequência

**Decision**: preservar README da fábrica, acrescentando uma seção de aplicação que referencia o quickstart e fornece os mesmos comandos. QA extrai as linhas `python -m tarefas ...` dos blocos PowerShell do quickstart e da seção de produto do README, substitui somente `$arquivo` pelo caminho temporário e executa como argv (sem shell), conferindo saídas e códigos na ordem. Uma pequena verificação de consistência pode exigir que exemplos de produto não apareçam fora desses blocos reconhecidos. Comandos de preparação e de verificação são executados diretamente nas etapas de implementação/QA com os mesmos textos documentados; a suíte não se invoca recursivamente para testar seu próprio comando. O relatório QA relaciona essas evidências a SC-005.

**Rationale**: evita exemplos divergentes dos testes e cobre FR-012 sem introduzir um framework de documentação. Desenvolvimento incremental: primeiro estrutura/testes e US1 com persistência e falhas; depois US2; depois documentação consolidada e aceite US3. Testes de cada comportamento acompanham sua implementação. Criador de Tarefas detalhará a sequência sem modificar este desenho.

**Alternatives considered**: apenas copiar exemplos para testes permite divergência; executar Markdown inteiro como shell envolve comandos não destinados à aplicação; fazer o teste chamar a suíte inteira causaria recursão.

## Resultado da Fase 0

Todas as escolhas técnicas resolvidas. Nenhum conflito de requisito encontrado. Riscos restantes são de implementação e verificação: tradução de erros sintáticos em português, Unicode no terminal Windows, preservação de bytes em operações rejeitadas e descoberta de todos os testes. O contrato, a matriz e o quickstart definem as verificações correspondentes. Nenhum hook de extensão: `.specify/extensions.yml` ausente na inspeção anterior ao setup.
