"""Argumentos, ajuda e ponto de entrada da interface de terminal."""

import argparse
import json
from pathlib import Path
import re
import sys

from .modelo import ErroValidacao, validar_descricao
from .armazenamento import ErroGravacao, ErroLeitura, carregar, salvar
from .servico import adicionar


class _Parser(argparse.ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace("usage: ", "uso: ", 1)

    def format_help(self):
        return super().format_help().replace("usage: ", "uso: ", 1)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "Erro: entrada inválida. Consulte --help.\n")


def _opcoes(parser):
    opcoes = parser.add_argument_group("opções")
    opcoes.add_argument(
        "-h", "--help", action="help", help="mostrar esta ajuda e sair"
    )
    return opcoes


def _criar_parser():
    parser = _Parser(
        prog="python -m tarefas",
        add_help=False,
        allow_abbrev=False,
        description="Gerenciar tarefas pelo terminal.",
        epilog="Adicionar e listar disponíveis; concluir será disponibilizado na próxima etapa.",
    )
    _opcoes(parser).add_argument(
        "--arquivo", metavar="CAMINHO", help="selecionar o arquivo de dados locais"
    )
    comandos = parser.add_subparsers(
        dest="comando", title="comandos", metavar="COMANDO", required=True
    )
    for nome, descricao in (
        ("adicionar", "adicionar uma tarefa com descrição obrigatória"),
        ("listar", "listar identificador, descrição e status das tarefas"),
        ("concluir", "marcar uma tarefa como concluída pelo identificador"),
    ):
        subparser = comandos.add_parser(
            nome, add_help=False, allow_abbrev=False,
            description=descricao, help=descricao,
        )
        _opcoes(subparser)
        argumentos = subparser.add_argument_group("argumentos")
        if nome == "adicionar":
            argumentos.add_argument(
                "descricao", nargs="?", metavar="DESCRICAO", help="descrição da tarefa"
            )
        elif nome == "concluir":
            argumentos.add_argument(
                "id", nargs="?", metavar="ID", help="identificador inteiro positivo"
            )
    return parser


def _interpretar_argumentos(argv=None):
    argumentos = _criar_parser().parse_args(argv)
    if argumentos.comando == "adicionar":
        validar_descricao(argumentos.descricao)
    elif argumentos.comando == "concluir":
        if argumentos.id is None or re.fullmatch(r"[1-9][0-9]*", argumentos.id) is None:
            raise ErroValidacao("informe um identificador inteiro positivo.")
        argumentos.id = int(argumentos.id)
    return argumentos


def _resolver_caminho(arquivo):
    if arquivo is not None:
        return Path(arquivo)
    return Path.home() / ".tarefas" / "tarefas.json"


def main(argv=None) -> int:
    """Valida a entrada antes de resolver o caminho dos dados."""
    try:
        argumentos = _interpretar_argumentos(argv)
    except SystemExit as saida:
        return int(saida.code)
    except ErroValidacao as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    if argumentos.comando == "concluir":
        print("Erro: operação ainda não disponível.", file=sys.stderr)
        return 1
    try:
        caminho = _resolver_caminho(argumentos.arquivo)
        tarefas = carregar(caminho)
    except (OSError, RuntimeError, ErroLeitura):
        print("Erro: não foi possível ler os dados locais.", file=sys.stderr)
        return 1
    if argumentos.comando == "listar":
        if not tarefas:
            print("Nenhuma tarefa cadastrada.")
        for tarefa in sorted(tarefas, key=lambda tarefa: tarefa.id):
            status = "concluída" if tarefa.status == "concluida" else "pendente"
            descricao = json.dumps(tarefa.descricao, ensure_ascii=False)
            print(f"{tarefa.id} | {status} | {descricao}")
        return 0
    novas, tarefa = adicionar(tarefas, argumentos.descricao)
    try:
        salvar(caminho, novas)
    except ErroGravacao:
        print("Erro: não foi possível salvar os dados locais.", file=sys.stderr)
        return 1
    print(f"Tarefa {tarefa.id} adicionada.")
    return 0
