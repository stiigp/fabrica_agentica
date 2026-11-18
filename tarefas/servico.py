"""Operações puras sobre coleções de tarefas."""

from .modelo import Tarefa, validar_descricao


def adicionar(tarefas: list[Tarefa], descricao: str) -> tuple[list[Tarefa], Tarefa]:
    """Cria uma tarefa pendente em nova coleção, preservando a coleção recebida."""
    validar_descricao(descricao)
    identificador = max((tarefa.id for tarefa in tarefas), default=0) + 1
    tarefa = Tarefa(identificador, descricao)
    return [*tarefas, tarefa], tarefa
