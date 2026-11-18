"""Ajuda e ponto de entrada da interface de terminal."""

import argparse
import sys


class _Parser(argparse.ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace("usage: ", "uso: ", 1)

    def format_help(self):
        return super().format_help().replace("usage: ", "uso: ", 1)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "Erro: entrada inválida. Consulte --help.\n")


def main(argv=None) -> int:
    """Executa a interface inicial sem consultar dados locais."""
    parser = _Parser(
        prog="python -m tarefas",
        add_help=False,
        description="Gerenciar tarefas pelo terminal.",
        epilog=(
            "Operações previstas: adicionar, listar e concluir. "
            "A opção global --arquivo CAMINHO selecionará os dados locais. "
            "Nesta etapa, somente a ajuda está disponível."
        ),
    )
    opcoes = parser.add_argument_group("opções")
    opcoes.add_argument(
        "-h", "--help", action="help", help="mostrar esta ajuda e sair"
    )
    try:
        parser.parse_args(argv)
    except SystemExit as saida:
        return int(saida.code)
    parser.print_usage(sys.stderr)
    print("Erro: informe um comando. Consulte --help.", file=sys.stderr)
    return 2
