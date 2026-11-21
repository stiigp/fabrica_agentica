"""Persistência JSON validada e substituição segura do arquivo local."""

import json
import os
from pathlib import Path
import stat
import tempfile

from .modelo import ErroValidacao, Tarefa


class ErroLeitura(Exception):
    """Falha ao acessar ou validar os dados locais."""


class ErroGravacao(Exception):
    """Falha ao salvar os dados locais."""


def _objeto_sem_repeticoes(pares):
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise ErroValidacao("chave JSON repetida.")
        objeto[chave] = valor
    return objeto


def _validar_colecao(tarefas):
    if not isinstance(tarefas, list):
        raise ErroValidacao("a coleção de tarefas deve ser uma lista.")
    ids = set()
    for tarefa in tarefas:
        if not isinstance(tarefa, Tarefa):
            raise ErroValidacao("registro de tarefa inválido.")
        if tarefa.id in ids:
            raise ErroValidacao("identificador de tarefa repetido.")
        ids.add(tarefa.id)


def _ler_documento(documento):
    if not isinstance(documento, dict) or set(documento) != {"schema_version", "tarefas"}:
        raise ErroValidacao("estrutura de documento inválida.")
    if type(documento["schema_version"]) is not int or documento["schema_version"] != 1:
        raise ErroValidacao("versão de esquema desconhecida.")
    registros = documento["tarefas"]
    if not isinstance(registros, list):
        raise ErroValidacao("a coleção de tarefas deve ser uma lista.")
    tarefas = []
    for registro in registros:
        if not isinstance(registro, dict) or set(registro) != {"id", "descricao", "status"}:
            raise ErroValidacao("estrutura de tarefa inválida.")
        tarefas.append(Tarefa(**registro))
    _validar_colecao(tarefas)
    return tarefas


def _confirmar_ausencia(caminho):
    # No Windows, um ancestral que é arquivo também pode gerar FileNotFoundError.
    pai = caminho.parent
    while True:
        try:
            modo = pai.stat().st_mode
        except FileNotFoundError:
            if pai == pai.parent:
                raise
            pai = pai.parent
        else:
            if not stat.S_ISDIR(modo):
                raise NotADirectoryError(str(pai))
            return


def carregar(caminho) -> list[Tarefa]:
    """Lê o documento inteiro; somente ausência na abertura significa vazio."""
    caminho = Path(caminho)
    try:
        arquivo = caminho.open("r", encoding="utf-8")
    except FileNotFoundError:
        try:
            _confirmar_ausencia(caminho)
        except OSError as erro:
            raise ErroLeitura("não foi possível ler os dados locais.") from erro
        return []
    except OSError as erro:
        raise ErroLeitura("não foi possível ler os dados locais.") from erro
    try:
        with arquivo:
            documento = json.load(arquivo, object_pairs_hook=_objeto_sem_repeticoes)
        return _ler_documento(documento)
    except (OSError, ValueError, RecursionError) as erro:
        raise ErroLeitura("não foi possível ler os dados locais.") from erro


def salvar(caminho, tarefas: list[Tarefa]) -> None:
    """Valida antes de criar pais e substitui o destino após fechar o temporário."""
    caminho = Path(caminho)
    temporario = None
    try:
        _validar_colecao(tarefas)
        documento = {
            "schema_version": 1,
            "tarefas": [
                {"id": tarefa.id, "descricao": tarefa.descricao, "status": tarefa.status}
                for tarefa in tarefas
            ],
        }
        conteudo = json.dumps(documento, ensure_ascii=False, indent=2) + "\n"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=caminho.parent,
            prefix=f".{caminho.name}.", suffix=".tmp", delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write(conteudo)
        os.replace(temporario, caminho)
        temporario = None
    except (OSError, ValueError, TypeError) as erro:
        raise ErroGravacao("não foi possível salvar os dados locais.") from erro
    finally:
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass
