# Fábrica de Software Agêntica para Codex

Adaptação dos agentes de [andremenegassi/fabrica-software-agentica](https://github.com/andremenegassi/fabrica-software-agentica) para os clientes locais do Codex. Mantém o orquestrador, os seis especialistas, as etapas E0–E8, os relatórios, os limites de devolução e os dois checkpoints humanos do exemplo da aula.

Esta pasta contém a configuração da fábrica. A configuração deve estar no repositório do software que você pretende desenvolver. Ela não instala o Spec Kit, não cria uma aplicação, não inicializa Git e não publica nada no GitHub por conta própria.

## Arquivos e carregamento

| Arquivo | Função |
| --- | --- |
| `AGENTS.md` | Instrui o chat principal a atuar como orquestrador quando o usuário pedir o fluxo da fábrica. |
| `.codex/agents/orquestrador.md` | Instruções completas do orquestrador. Ele permanece no chat principal para receber as aprovações humanas. |
| `.codex/agents/*.toml` | Seis agentes nativos completos, com `name`, `description` e todas as instruções do papel em `developer_instructions`. |
| `.codex/permissoes.yaml` | Política declarativa de permissões e limites por papel, lida pelo orquestrador e pelos subagentes. |
| `.codex/config.toml` | Padrões nativos persistentes: sandbox `workspace-write` e aprovação `on-request`. |
| `.codex/rules/fabrica.rules` | Regras nativas por prefixo para restringir comandos Git/GitHub. |

Os TOML contêm todas as instruções detalhadas dos subagentes em `developer_instructions`; não dependem de arquivos Markdown auxiliares. O nome nativo é o campo `name` do TOML, não um comando com `@` do OpenCode. Edite o TOML correspondente para alterar o comportamento do subagente. O orquestrador permanece no chat principal e suas instruções ficam em `orquestrador.md`, referenciado por `AGENTS.md`.

| Papel | ID nativo | Instruções |
| --- | --- | --- |
| Orquestrador | chat principal | `.codex/agents/orquestrador.md` |
| Analista de Requisitos | `analista_requisitos` | `.codex/agents/analista-requisitos.toml` |
| Arquiteto | `arquiteto` | `.codex/agents/arquiteto.toml` |
| Criador de Tarefas | `criador_tarefas` | `.codex/agents/criador-tarefas.toml` |
| Desenvolvedor | `desenvolvedor` | `.codex/agents/desenvolvedor.toml` |
| Revisor de Código | `revisor_codigo` | `.codex/agents/revisor-codigo.toml` |
| QA | `qa` | `.codex/agents/qa.toml` |

Modelo e raciocínio são herdados da sessão principal. Não foi mantido o provedor `9router` do exemplo. Não é necessário usar uma chave de API adicional apenas para definir esses papéis.

## O que o YAML faz

**O Codex não interpreta `.codex/permissoes.yaml` como uma configuração nativa de segurança.** O arquivo é uma política de comportamento referenciada explicitamente pelo `AGENTS.md` e pelos agentes. Não há um executor ou hook nesta adaptação que intercepte ferramentas e imponha as regras do YAML.

O arquivo usa `allow`, `deny` e `require_checkpoint_1` nas decisões de permissão. Campos descritivos especificam o escopo e as condições de uma ação. As regras globais prevalecem sobre permissões específicas. Caminhos são relativos à raiz do projeto, e os diretórios de código e teste são os definidos no `plan.md`, sem pressupor uma linguagem ou framework.

- Só o orquestrador delega, cria a branch, faz commits e push e abre o PR.
- Analista escreve a especificação e os checklists usando as skills; a atualização de `.specify/feature.json` é permitida apenas como saída da skill.
- Arquiteto escreve o plano e seus artefatos; a atualização de contexto em `AGENTS.md` só ocorre via script do Spec Kit e deve preservar as instruções da fábrica.
- Criador de Tarefas escreve `tasks.md` e notas.
- Desenvolvedor escreve o produto e seus testes e marca tarefas concluídas; não altera requisitos nem testes do QA.
- Revisor escreve o relatório de revisão e notas; não corrige o código.
- QA escreve testes e o relatório de aceite; não corrige código de produção.
- Ninguém faz merge do PR na base, auto-merge, force push, rebase, reset destrutivo ou deploy.

A sandbox e as aprovações reais são controladas pela sessão e pelas políticas do ambiente. Os subagentes herdam esses controles: um `deny` no YAML não cria uma barreira técnica por papel, e um `allow` não concede acesso bloqueado pela sessão. Os arquivos nativos descritos a seguir acrescentam controles globais; não são um interpretador do YAML nem uma implementação de todas as suas restrições por papel.

O antigo `ask` para chamar o Arquiteto foi adaptado para a exigência de aprovação da especificação vigente. A aprovação registrada no Checkpoint 1 permite o planejamento e as devoluções técnicas sem uma nova pergunta por chamada. Isso preserva o checkpoint, mas não reproduz a segunda barreira mecânica do OpenCode. Permissões reais da sessão ainda podem exigir confirmação de uma ferramenta.

## Configuração nativa e regras de comandos

O `.codex/config.toml` define `sandbox_mode = "workspace-write"` e `approval_policy = "on-request"` como padrões do projeto. Parâmetros da sessão e políticas superiores podem prevalecer. Abra o projeto como confiável e reinicie o Codex para carregar a camada de configuração e suas regras.

O `.codex/rules/fabrica.rules` usa `prefix_rule` com decisão `forbidden` para recusar:

- `gh pr merge`, incluindo seu modo `--auto`;
- `git rebase`;
- `git reset --hard`, incluindo as variantes com `--quiet` ou `-q` antes de `--hard`;
- `git push` com `--force`, `-f`, `--force-with-lease` ou `--mirror` imediatamente após `push`, após `origin` ou após `origin HEAD`.

Há variantes para `git.exe`, `gh.exe` e caminhos convencionais dessas instalações no Windows. Os padrões deixam fora dos bloqueios o commit normal, push normal, criação de branch, `git merge origin/<base>` e leitura/criação de PR. Isso não os libera automaticamente: seguem as demais permissões da sessão e os limites do papel.

As regras são aplicadas ao comando que o motor de políticas avalia, no escopo documentado para execução fora da sandbox. São correspondências de prefixo: outras ordens de argumentos, aliases, outros caminhos de executáveis, refspecs, APIs ou comandos encapsulados em scripts podem não corresponder. Por exemplo, `git push origin feature --force` não corresponde aos prefixos de force push acima. Não trate esse arquivo como uma proteção completa do repositório, uma ACL por papel ou uma restrição de acesso a arquivos. As demais proibições continuam descritas no YAML e nos agentes.

Para testar a política sem executar o comando Git/GitHub, use na raiz do projeto:

```powershell
codex.cmd execpolicy check --pretty --rules .codex/rules/fabrica.rules -- gh pr merge 1
codex.cmd execpolicy check --pretty --rules .codex/rules/fabrica.rules -- git rebase main
codex.cmd execpolicy check --pretty --rules .codex/rules/fabrica.rules -- git push -u origin feature
```

Os dois primeiros devem resultar em `forbidden`; o terceiro não deve corresponder a uma proibição deste arquivo. Essa verificação apenas avalia argumentos e não executa o comando informado depois de `--`.

## Preparação do projeto

1. Use uma versão atual do Codex que ofereça agentes personalizados em `.codex/agents/*.toml` e abra o projeto como confiável quando o cliente solicitar.
2. Instale esta configuração na raiz do projeto: `AGENTS.md` e `.codex/`. Se já houver configuração nesses caminhos, incorpore as instruções sem sobrescrever as existentes.
3. Prepare um repositório Git com pelo menos um commit na branch base, remoto `origin` no GitHub e a CLI `gh` autenticada. O fluxo verifica esses pré-requisitos em E0. Preparar ou publicar o repositório é uma ação separada da conversão dos agentes.
4. Instale o Spec Kit e sua integração Codex, com Python 3.11+ e `uv` disponíveis. No PowerShell, na raiz do projeto:

   ```powershell
   uv tool install specify-cli
   specify version
   specify init --here --integration codex --script ps
   ```

   Se o projeto já usa Spec Kit, adicione a integração sem reinicializar:

   ```powershell
   specify integration install codex
   ```

   Os agentes usam os scripts instalados, sem reescrevê-los. Hooks Git do Spec Kit não podem criar branches ou fazer commits dentro dos subagentes; essas operações pertencem ao orquestrador.

5. Inicie uma nova sessão do Codex na raiz do projeto para carregar `AGENTS.md` e os agentes personalizados. Na CLI:

   ```powershell
   codex
   ```

   Se a instalação via npm exigir o atalho explícito no PowerShell, use `codex.cmd`.

6. No chat do Codex, crie ou aprove a constituição uma vez por projeto:

   ```text
   $speckit-constitution
   Defina os princípios do projeto, comandos de verificação e critérios de qualidade.
   ```

As chamadas `$speckit-*` são prompts de skills no chat, não comandos do PowerShell. As skills devem estar disponíveis em `.agents/skills/`. Se faltarem, a fábrica reporta a lacuna e não substitui o Spec Kit por documentos escritos manualmente.

O núcleo atual do Spec Kit controla a feature ativa por `.specify/feature.json` ou `SPECIFY_FEATURE_DIRECTORY`. Trocar de branch não troca a feature ativa. O orquestrador confere as duas informações antes de cada delegação. Nesta configuração, ele também é responsável pela criação da branch, sem depender da extensão Git do Spec Kit.

A integração instalada é a versão 1.4.2. Nela, `speckit-specify` cria o diretório e a especificação seguindo o template resolvido pela própria skill; não é necessário executar o helper `create-new-feature.ps1` como uma segunda criação. O Analista devolve os caminhos efetivos e o orquestrador usa o nome do diretório como nome da branch. A skill de planejamento dessa versão não exige nem fornece `update-agent-context`; esse script não é um pré-requisito da fábrica. Quando a skill mencionar pesquisas por agentes, o Arquiteto faz as pesquisas no próprio papel, mantendo a regra de que somente o orquestrador delega.

## Primeiro uso

Envie no chat principal:

```text
Use a fábrica configurada neste projeto.
Delegue as etapas aos agentes personalizados, um por vez.

Nova feature: permitir cadastrar tarefas com título obrigatório e marcar
cada tarefa como concluída.

Comece pela especificação e pare para minha aprovação.
```

O Analista usa `speckit-specify`, esclarece as dúvidas e devolve a especificação. O orquestrador salva a análise e encerra o turno no Checkpoint 1. Leia a `spec.md` e responda, por exemplo:

```text
Aprovo a especificação da feature <identificador-gerado>.
Continue pelo plano, tarefas, análise, implementação, revisão e QA.
Abra o PR ao concluir e aguarde meu merge.
```

Substitua o identificador pelo diretório retornado pelo Spec Kit; não fixe a numeração manualmente. A sequência é:

```text
E0 descoberta → E1 especificação → Checkpoint 1
→ E2 plano → E3 tarefas → E3.5 análise → E4 implementação
→ E5 revisão → E6 aceite → E7 PR/CI → Checkpoint 2 → E8 merge humano
```

Em E4, cada chamada ao Desenvolvedor executa apenas uma fase de tarefas. O orquestrador valida os arquivos e os comandos de teste/lint/build antes de avançar. Reprovações voltam ao responsável, com no máximo duas devoluções por etapa e cinco rodadas globais de correção. Depois do QA, os testes criados por ele também passam pelo Revisor.

Com o PR pronto, faça o merge pelo GitHub. Depois peça ao Codex para verificar o PR; somente a confirmação `MERGED` permite registrar `ENTREGUE`.

Para retomar em outro chat:

```text
Retome a fábrica na feature <identificador-gerado>.
Leia o state.json e os artefatos, confira a branch e a feature ativa
e continue da primeira etapa pendente.
```

Pedidos para explicar ou adaptar a própria fábrica não iniciam esse fluxo.

## Avisos de finalizacao no Slack

Cada especialista envia seu proprio aviso ao encerrar um acionamento, incluindo fases de implementacao, correcoes, bloqueios e especificacoes aguardando revisao humana. `scripts/notificar-slack.ps1` usa a Web API do Slack diretamente; nao e necessario instalar o Slack CLI. Um unico bot atende aos seis papeis, identificados no texto da mensagem. Os avisos nao substituem a aprovacao da spec nem o merge humano.

### Preparar o app e o canal

1. Nas configuracoes do app Slack, abra **OAuth & Permissions > Bot Token Scopes** e adicione `chat:write`.
2. Instale/reinstale o app no workspace depois de alterar as permissoes.
3. Copie o **Bot User OAuth Token**, iniciado por `xoxb-`. Client Secret, Signing Secret e App-Level Token nao sao usados por este script.
4. Adicione o bot ao canal que recebera os avisos e copie o **ID do canal** nos detalhes dele (ex.: `C0123456789`). Informe o ID, nao `#nome-do-canal` nem um link.

### Salvar as credenciais localmente

Em um PowerShell interativo, na raiz deste repositorio, execute:

```powershell
.\scripts\configurar-slack.ps1
```

O configurador solicita o token com entrada oculta e depois o ID do canal. Salva `SLACK_BOT_TOKEN` e `SLACK_CHANNEL_ID` nas **variaveis de ambiente do seu usuario Windows**, fora dos arquivos do projeto e do Git, e tambem neste processo PowerShell. Esse armazenamento e o ambiente local do usuario, nao um cofre de segredos. Nao cole o token no chat, na linha de comando ou nos TOMLs/YAML. Para substituir um token expirado ou revogado, execute o configurador novamente.

O notificador procura primeiro as variaveis do processo e, no Windows, consulta tambem as persistidas no usuario. Ele nao carrega `.env` e nao precisa de Client Secret ou Signing Secret. Para configurar apenas o PowerShell atual, use `configurar-slack.ps1 -SomenteSessao`; nessa opcao, um Codex ja aberto nao recebe essas variaveis. Se voce substituir as variaveis persistidas e um processo ainda tiver valores antigos, reinicie esse processo para herdar a configuracao nova. Inicie uma nova sessao do Codex antes de usar os TOMLs atualizados.

### Testar uma mensagem real

Depois de configurar, na raiz do repositorio:

```powershell
$aviso = @{
    Agente = 'teste_manual'
    Feature = 'configuracao-da-fabrica'
    Etapa = 'validacao-do-slack'
    ExecucaoId = [guid]::NewGuid().ToString('N')
    Status = 'TESTE'
    Resumo = 'Teste manual de notificacao; nao representa uma etapa de subagente.'
    Artefato = 'scripts/notificar-slack.ps1'
}
& .\scripts\notificar-slack.ps1 @aviso
```

O script so confirma `NOTIFICACAO: ENVIADA` quando o Slack retorna `ok=true`, o canal esperado e `ts`. A saida inclui `MESSAGE_ID` no formato `canal:ts`, `SLACK_CHANNEL_ID`, `SLACK_TS`, `EXECUCAO_ID` e `NOTIFICACAO_EM`. `ts` e preservado como texto. HTTP 200 com `ok=false` e falha; erros como `missing_scope`, `not_in_channel`, `invalid_auth` e `channel_not_found` incluem orientacao sem revelar o token. Mencoes e previews de links ficam desativados.

Nao ha repeticao automatica. Depois de timeout ou resposta incompleta, confira o canal pelo `ExecucaoId` antes de reenviar, pois a mensagem pode ter sido publicada. A rede continua sujeita as permissoes reais da sessao; se a sandbox bloquear a conexao, use apenas o mecanismo de aprovacao permitido pelo ambiente.

Os seis TOMLs exigem que o proprio especialista envie o aviso antes do bloco final. O orquestrador fornece um ID unico a cada acionamento, confere a evidencia e registra `notifications` no `state.json` da feature, incluindo transporte, canal e `ts`. Uma falha de envio nao reexecuta a implementacao. Registros antigos de outros transportes sao preservados como historico. O Checkpoint 1 continua obrigatorio mesmo com aviso pendente.

A permissao `send_factory_notification` no YAML limita o envio a esse script e canal. No QA, a credencial e exclusiva do aviso de infraestrutura, nao dos testes do produto. O configurador interativo e executado pelo humano, nao durante uma etapa de subagente.

### Verificacoes locais sem publicar mensagens

```powershell
.\scripts\testar-slack.ps1
```

Os testes simulam a API e a entrada do configurador, usam somente credenciais ficticias em memoria e restauram as variaveis do processo. Nao fazem chamadas externas nem alteram as variaveis persistidas do usuario. Referencias: [chat.postMessage](https://docs.slack.dev/reference/methods/chat.postMessage/) e [tipos de tokens](https://docs.slack.dev/authentication/tokens/).

## Verificação e limites desta adaptação

A validação dos arquivos deve conferir a sintaxe TOML/YAML, os IDs dos seis agentes, os caminhos de instruções e a correspondência entre registros e permissões. Isso não comprova uma entrega completa: a execução ponta a ponta requer o projeto, Spec Kit, constituição, Git, acesso ao GitHub e testes reais.

Se o cliente não disponibilizar os agentes personalizados ou as skills, atualize/configure o cliente e reinicie a sessão. A fábrica deve informar a indisponibilidade em vez de simular os seis papéis no mesmo chat.

## Referências

- [Agentes originais do professor](https://github.com/andremenegassi/fabrica-software-agentica/tree/main/src)
- [Agentes personalizados e permissões herdadas no Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Instruções de projeto em AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Configuração persistente do Codex](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Regras nativas de comandos e verificador execpolicy](https://learn.chatgpt.com/docs/agent-configuration/rules)
- [Integração oficial do Spec Kit com Codex](https://github.com/github/spec-kit/blob/main/docs/integrations/codex.md)
- [Instalação do Spec Kit](https://github.com/github/spec-kit/blob/main/docs/installation.md)

## Aplicação de tarefas pelo terminal

Pré-requisitos: Python 3.10 ou superior e PowerShell com terminal UTF-8. Execute os comandos na raiz deste repositório; não é necessário instalar dependências.

```powershell
python --version
$diretorioDemo = Join-Path ([System.IO.Path]::GetTempPath()) ("tarefas-demo-" + [guid]::NewGuid().ToString("N"))
$arquivo = Join-Path $diretorioDemo "tarefas.json"
python -m tarefas --arquivo "$arquivo" listar
python -m tarefas --arquivo "$arquivo" adicionar "Preparar relatório"
python -m tarefas --arquivo "$arquivo" listar
python -m tarefas --arquivo "$arquivo" concluir 1
python -m tarefas --arquivo "$arquivo" concluir 1
python -m tarefas --arquivo "$arquivo" adicionar "   "
python -m tarefas --arquivo "$arquivo" concluir 999
python -m tarefas --help
```

A listagem inicial informa `Nenhuma tarefa cadastrada.`; adicionar confirma `Tarefa 1 adicionada.`. A listagem seguinte mostra `1 | pendente | "Preparar relatório"`. Concluir confirma `Tarefa 1 concluída.`; repetir informa `Tarefa 1 já está concluída.`. Essas operações e a ajuda retornam código 0. A descrição em branco gera `Erro: a descrição é obrigatória.`, código 2; o ID inexistente gera `Erro: tarefa 999 não encontrada.`, código 1. Erros são enviados a stderr, sem confirmação de sucesso. Consulte `$LASTEXITCODE` imediatamente após cada comando.

O JSON preserva as tarefas entre execuções usando o mesmo arquivo. O parâmetro `--arquivo` seleciona dados independentes; sem ele, os dados ficam em `.tarefas/tarefas.json` no diretório pessoal. Use o caminho temporário acima para demonstrações. Listar um arquivo ausente não o cria; falhas de leitura ou gravação são informadas sem substituir dados por uma lista vazia.

Para verificar a aplicação:

```powershell
python -m unittest discover -s tests -t . -v
python -m compileall -q tarefas tests
```

A suíte deve informar uma quantidade positiva de testes e terminar `OK`, código 0. Os testes usam dados fictícios em diretórios temporários, caminhos explícitos e home fictício; execuções consecutivas não dependem de resíduos nem acessam tarefas reais. Compileall deve retornar 0, normalmente sem saída. Lint e typecheck não são aplicáveis: não há ferramentas configuradas para essa CLI sem dependências externas. Mais exemplos e resultados estão no [guia de execução](specs/001-gerenciar-tarefas-terminal/quickstart.md).
