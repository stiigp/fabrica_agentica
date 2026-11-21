"""Operações puras: US1/US2; FR-002/003/004/006/007; SC-001/002/003."""

from contextlib import redirect_stderr, redirect_stdout
import io
import unittest
from unittest.mock import patch

from tarefas.modelo import ErroValidacao, Tarefa
from tarefas.servico import TarefaNaoEncontrada, adicionar, concluir, resumir


class ResumoTests(unittest.TestCase):
    def test_contagens_sem_io_ou_mutacao(self):
        casos = (
            ([], (0, 0, 0)),
            ([Tarefa(8, "A", "concluida"), Tarefa(2, "B"), Tarefa(19, "C")], (3, 2, 1)),
            ([Tarefa(9, "A"), Tarefa(3, "B")], (2, 2, 0)),
            ([Tarefa(9, "A", "concluida"), Tarefa(3, "B", "concluida")], (2, 0, 2)),
        )
        for tarefas, esperado in casos:
            with self.subTest(esperado=esperado):
                antes = list(tarefas)
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("builtins.open", side_effect=AssertionError("I/O indevido")), patch(
                    "pathlib.Path.home", side_effect=AssertionError("home indevido")
                ), redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(resumir(tarefas), esperado)
                self.assertEqual(tarefas, antes)
                self.assertTrue(all(atual is original for atual, original in zip(tarefas, antes)))
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(stderr.getvalue(), "")


class AdicaoTests(unittest.TestCase):
    def test_primeira_tarefa_id_um_pendente_descricao_exata_us1(self):
        original = []
        descricao = '  Preparar relatório | "A"\nB\t  '
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("builtins.open", side_effect=AssertionError("I/O indevido")), patch(
            "pathlib.Path.home", side_effect=AssertionError("home indevido")
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            novas, tarefa = adicionar(original, descricao)
        self.assertEqual(tarefa, Tarefa(1, descricao, "pendente"))
        self.assertEqual(novas, [tarefa])
        self.assertEqual(original, [])
        self.assertIsNot(novas, original)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_maior_id_fora_de_ordem_sem_mutar_original_fr003(self):
        original = [Tarefa(8, "A", "concluida"), Tarefa(2, "B"), Tarefa(5, "C")]
        antes = list(original)
        novas, tarefa = adicionar(original, "D")
        self.assertEqual(tarefa, Tarefa(9, "D"))
        self.assertEqual(novas, [*antes, tarefa])
        self.assertEqual(original, antes)
        self.assertIsNot(novas, original)

    def test_descricoes_repetidas_recebem_ids_distintos_fr002_fr003(self):
        original = [Tarefa(1, "Repetida")]
        novas, segunda = adicionar(original, "Repetida")
        seguintes, terceira = adicionar(novas, "Repetida")
        self.assertEqual([tarefa.id for tarefa in seguintes], [1, 2, 3])
        self.assertEqual([tarefa.descricao for tarefa in seguintes], ["Repetida"] * 3)
        self.assertEqual(segunda.status, "pendente")
        self.assertEqual(terceira.status, "pendente")
        self.assertEqual(original, [Tarefa(1, "Repetida")])
        self.assertEqual(novas, [Tarefa(1, "Repetida"), segunda])

    def test_descricao_invalida_rejeitada_sem_mutacao_fr002(self):
        original = [Tarefa(4, "Tarefa fictícia")]
        for descricao in (None, "", " \t\n", "\u2003", 1):
            with self.subTest(descricao=descricao):
                with self.assertRaisesRegex(ErroValidacao, "descrição é obrigatória"):
                    adicionar(original, descricao)
                self.assertEqual(original, [Tarefa(4, "Tarefa fictícia")])


class ConclusaoTests(unittest.TestCase):
    def setUp(self):
        self.original = [
            Tarefa(4, '  Preparar relatório | "A"\nB\t  '),
            Tarefa(2, "Outra pendente"),
            Tarefa(9, "Concluída anterior", "concluida"),
        ]

    def test_concluir_muda_so_status_preserva_original_sem_io_us2_sc002(self):
        antes = list(self.original)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("builtins.open", side_effect=AssertionError("I/O indevido")), patch(
            "pathlib.Path.home", side_effect=AssertionError("home indevido")
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            novas, alterou = concluir(self.original, 4)
        self.assertTrue(alterou)
        self.assertIsNot(novas, self.original)
        self.assertEqual(novas, [Tarefa(4, antes[0].descricao, "concluida"), *antes[1:]])
        self.assertEqual(self.original, antes)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_concluir_ja_concluida_informa_ausencia_de_mudanca_fr006(self):
        antes = list(self.original)
        novas, alterou = concluir(self.original, 9)
        self.assertFalse(alterou)
        self.assertEqual(novas, antes)
        self.assertEqual(self.original, antes)

    def test_identificador_inexistente_nao_muda_colecao_fr007_sc003(self):
        for original in ([], self.original):
            antes = list(original)
            for identificador in (999, 10**100):
                with self.subTest(quantidade=len(original), identificador=identificador):
                    with self.assertRaises(TarefaNaoEncontrada) as capturado:
                        concluir(original, identificador)
                    self.assertEqual(str(capturado.exception), f"tarefa {identificador} não encontrada.")
                    self.assertEqual(original, antes)
