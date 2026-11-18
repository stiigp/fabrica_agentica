# Modelo de dados

**Feature**: 001-gerenciar-tarefas-terminal | **Fase**: 1 de `$speckit-plan` | **Data**: 2026-11-18

## Tarefa

| Campo | Tipo persistido | Regra |
|---|---|---|
| `id` | inteiro positivo | automático, único no conjunto e estável; rejeitar booleano |
| `descricao` | string Unicode | pelo menos um caractere não whitespace; validar com strip sem alterar a string aceita; sem limite ou unicidade |
| `status` | string enum | `pendente` ou `concluida`; nova tarefa sempre pendente |

Uma tarefa pertence a um conjunto local, sem outras relações. IDs não precisam ser únicos entre arquivos. Descrições duplicadas representam tarefas distintas. Acentos, espaços externos/internos, tabulações e quebras de linha são preservados; a CLI apresenta caracteres de controle por escape reversível.

## Conjunto local

Documento raiz JSON UTF-8 com exatamente dois campos:

| Campo | Tipo | Regra |
|---|---|---|
| `schema_version` | inteiro | exatamente 1, sem booleano; outra versão é erro, sem conversão automática |
| `tarefas` | lista de Tarefa | todos os registros válidos e IDs distintos; lista vazia válida |

Cada tarefa tem exatamente os três campos definidos. Rejeitar campos extras, ausentes, tipos errados, chaves JSON repetidas, IDs duplicados e status desconhecido antes de qualquer operação. Não descartar informações desconhecidas silenciosamente. Ordem no arquivo não determina identidade; a CLI ordena por ID. Não há contador ou timestamps.

Fixture fictícia válida:

```json
{
  "schema_version": 1,
  "tarefas": [
    {"id": 1, "descricao": "Preparar relatório", "status": "pendente"},
    {"id": 2, "descricao": "Preparar relatório", "status": "concluida"}
  ]
}
```

## Transições e persistência

1. Adicionar: validar descrição, carregar documento válido, calcular `max(ids, default=0) + 1`, criar tarefa pendente em nova coleção, salvar e só então confirmar (FR-002/003/004/008). Sem exclusão, não há reciclagem de IDs.
2. Concluir pendente: alterar somente status da selecionada para `concluida`, preservar demais campos/registros, salvar e confirmar (FR-006/008).
3. Concluir concluída: informar estado sem mutação ou escrita. ID inexistente gera erro sem alteração; ID inválido é rejeitado antes de carregar (FR-006/007).
4. Listar: mostrar todos os registros uma vez, sem escrita (FR-005).

Arquivo ausente representa coleção vazia apenas em memória. Listar não cria arquivo. Arquivo vazio, JSON inválido, diretório no lugar do arquivo ou falha de acesso são erros; nunca converter falha em vazio (FR-009).

Salvar em temporário exclusivo no mesmo diretório, serializar UTF-8 com `ensure_ascii=False`, fechar e substituir por `os.replace`. Criar pais apenas em alteração válida. Confirmar só após substituição. Em falha, preservar original e tentar remover somente temporário próprio, sem mascarar o erro principal. Operações rejeitadas e conclusão repetida preservam os bytes do arquivo, sem reserialização. Sem garantia de concorrência ou queda abrupta.

Sem banco ou migração inicial: esquema 1, sem dados legados. Rejeitar versões desconhecidas sem sobrescrever; futura mudança exigirá plano próprio de migração versionada e reversível.

## Dados de teste

Fixtures em TemporaryDirectory independentes: vazio; três tarefas com duplicatas/acentos; duas pendentes e uma concluída para US2 sem depender de US1; IDs fora de ordem; documentos malformados e esquemas inválidos. Caminho obrigatório nas funções de armazenamento; testes da CLI usam `--arquivo`. Default somente em home fictício. Nenhuma credencial, variável sensível ou dado pessoal (FR-010/011).
