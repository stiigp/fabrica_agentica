# Data model — resumo

Tarefa existente e imutável: id inteiro positivo (bool inválido), descricao string não branca, status pendente ou concluida. IDs únicos na coleção; ordem/valor do ID não alteram contagens.

JSON permanece objeto com exatamente schema_version inteiro 1 e tarefas lista; registros com exatamente id, descricao e status. Leitura existente rejeita chaves repetidas e dados inválidos. Sem transição, alteração de validação ou migração.

Resumo é resultado efêmero tuple[int, int, int] em ordem total, pendentes, concluidas. Inteiros não negativos; total = pendentes + concluidas; cada registro conta uma vez. Vazio retorna (0, 0, 0); não criar classe ou persistência.

Origem: Path de --arquivo, relativo ao diretório de trabalho quando relativo; sem opção, Path.home() / .tarefas / tarefas.json. Ausência legítima equivale a vazio; falhas não. Sem nova expansão de caminho. Fixtures fictícias em temporários; nenhum banco ou segredo.
