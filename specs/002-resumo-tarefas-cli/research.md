# Research — resumo

Fase 0 realizada no próprio papel sobre cli.py, servico.py, armazenamento.py, modelo.py, README e testes existentes. Nenhuma pesquisa externa necessária ou dúvida pendente.

## Contagem
- Decision: função pura resumir no serviço existente, retornando tupla total/pendentes/concluidas, calculada em O(n) com memória adicional O(1).
- Rationale: regra separada da apresentação, testável e sem nova estrutura.
- Alternatives considered: contar na CLI mistura responsabilidades; dataclass Resumo/módulo novo acrescentam estrutura sem necessidade.

## Leitura
- Decision: reutilizar _resolver_caminho e carregar; ramo de resumo retorna antes das operações mutáveis.
- Rationale: carregar já valida todo JSON e distingue ausência legítima de ancestral arquivo via _confirmar_ausencia. Ajuda já encerra antes de consultar home.
- Alternatives considered: JSON separado duplica validação; exists() pode ocultar falhas; refatorar armazenamento amplia escopo.

## Contrato e testes
- Decision: três linhas fixas, esquema intacto, unittest existente; temporários, home fictício e PermissionError simulado; aceite QA separado.
- Rationale: atende spec/constituição sem dependências e com resultados determinísticos.
- Alternatives considered: novos formatos/cache/percentuais fora de escopo; pytest/coverage/linter não necessários; demonstração manual não substitui testes obrigatórios.
