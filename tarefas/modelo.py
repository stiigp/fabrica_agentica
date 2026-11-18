"""Dados e validações das tarefas, sem acesso a arquivos."""

from dataclasses import dataclass


class ErroValidacao(ValueError):
    """Entrada ou registro que viola o modelo de dados."""


def validar_descricao(descricao: str) -> str:
    if not isinstance(descricao, str) or not descricao.strip():
        raise ErroValidacao("a descrição é obrigatória.")
    return descricao


@dataclass(frozen=True)
class Tarefa:
    id: int
    descricao: str
    status: str = "pendente"

    def __post_init__(self):
        if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id <= 0:
            raise ErroValidacao("o identificador deve ser um inteiro positivo.")
        validar_descricao(self.descricao)
        if self.status not in ("pendente", "concluida"):
            raise ErroValidacao("status de tarefa inválido.")
