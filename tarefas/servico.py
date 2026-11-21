"""Operações puras sobre coleções de tarefas."""

from .modelo import Tarefa, validar_descricao


class TarefaNaoEncontrada(Exception):
    """Identificador válido que não pertence ao conjunto de tarefas."""


def adicionar(tarefas: list[Tarefa], descricao: str) -> tuple[list[Tarefa], Tarefa]:
    """Cria uma tarefa pendente em nova coleção, preservando a coleção recebida."""
    validar_descricao(descricao)
    identificador = max((tarefa.id for tarefa in tarefas), default=0) + 1
    tarefa = Tarefa(identificador, descricao)
    return [*tarefas, tarefa], tarefa


def concluir(tarefas: list[Tarefa], identificador: int) -> tuple[list[Tarefa], bool]:
    """Retorna a coleção resultante e informa se houve mudança efetiva."""
    for indice, tarefa in enumerate(tarefas):
        if tarefa.id == identificador:
            novas = list(tarefas)
            if tarefa.status == "concluida":
                return novas, False
            novas[indice] = Tarefa(tarefa.id, tarefa.descricao, "concluida")
            return novas, True
    raise TarefaNaoEncontrada(f"tarefa {identificador} não encontrada.")
