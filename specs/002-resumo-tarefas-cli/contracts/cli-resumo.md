# Contrato CLI — resumo

Invocações:
- python -m tarefas --arquivo CAMINHO resumo
- python -m tarefas resumo
- python -m tarefas --help
- python -m tarefas resumo --help

--arquivo é global e precede comando; resumo não exige argumentos adicionais. Seleção e validação em ../data-model.md.

Sucesso: código 0, stderr vazio, stdout exatamente três linhas com quebra final:

    Total: N
    Pendentes: P
    Concluídas: C

N/P/C inteiros decimais não negativos e N=P+C. Vazio/ausência legítima resulta em três zeros, sem criar arquivo/pais. Consulta nunca modifica dados ou formato.

Falha: código 1, stdout vazio, stderr exatamente Erro: não foi possível ler os dados locais. seguido de quebra de linha. Não apresentar resultado parcial ou zeros.

Ajuda geral lista resumo e descrição de consulta de contagens; específica descreve consulta. Ambas retornam 0 sem acesso a dados/home. Parser e demais comandos mantêm contratos anteriores. Nenhuma nova opção ou formato.
