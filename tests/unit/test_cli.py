"""Contrato inicial da CLI: FR-001, FR-010, FR-011 e FR-012."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import importlib
import io
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


class CliSetupTests(unittest.TestCase):
    def setUp(self):
        temporario = tempfile.TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.diretorio = Path(temporario.name)
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def sem_acesso_a_dados(self):
        guards = ExitStack()
        self.addCleanup(guards.close)
        for alvo in (
            "builtins.open", "io.open", "os.open", "os.mkdir", "os.makedirs",
            "os.replace", "pathlib.Path.home", "pathlib.Path.expanduser",
        ):
            guards.enter_context(patch(
                alvo, side_effect=AssertionError(f"Acesso indevido: {alvo}")
            ))
        guards.enter_context(redirect_stdout(self.stdout))
        guards.enter_context(redirect_stderr(self.stderr))
        return guards

    def test_importacao_sem_io_home_ou_saida_fr011(self):
        with self.sem_acesso_a_dados():
            for nome in ("tarefas", "tarefas.cli"):
                importlib.reload(importlib.import_module(nome))
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertEqual(self.stderr.getvalue(), "")
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_ajuda_portuguesa_sem_io_home_fr001_fr012(self):
        with self.sem_acesso_a_dados():
            cli = importlib.import_module("tarefas.cli")
            for opcao in ("--help", "-h"):
                with self.subTest(opcao=opcao):
                    self.stdout.seek(0)
                    self.stdout.truncate()
                    self.assertEqual(cli.main([opcao]), 0)
                    ajuda = " ".join(self.stdout.getvalue().split())
                    for texto in (
                        "uso:", "opções:", "Gerenciar tarefas", "adicionar",
                        "listar", "concluir", "--arquivo CAMINHO",
                        "mostrar esta ajuda e sair",
                    ):
                        self.assertIn(texto, ajuda)
                    self.assertNotIn("usage:", ajuda)
                    self.assertNotIn("options:", ajuda)
        self.assertEqual(self.stderr.getvalue(), "")
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_sem_comando_nao_informa_sucesso_fr001(self):
        with self.sem_acesso_a_dados():
            cli = importlib.import_module("tarefas.cli")
            self.assertEqual(cli.main([]), 2)
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertTrue(self.stderr.getvalue().startswith("uso:"))
        self.assertIn("Erro:", self.stderr.getvalue())

    def test_entrada_propaga_codigo_retornado_pela_cli_fr010(self):
        with self.sem_acesso_a_dados(), patch(
            "tarefas.cli.main", return_value=7
        ) as main:
            with self.assertRaises(SystemExit) as saida:
                runpy.run_module("tarefas", run_name="__main__")
        self.assertEqual(saida.exception.code, 7)
        main.assert_called_once_with()
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertEqual(self.stderr.getvalue(), "")
