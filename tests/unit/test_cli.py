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

    def conferir_erro_sem_dados(self, argumentos, mensagem=None):
        self.stdout.seek(0)
        self.stdout.truncate()
        self.stderr.seek(0)
        self.stderr.truncate()
        with self.sem_acesso_a_dados():
            cli = importlib.import_module("tarefas.cli")
            self.assertEqual(cli.main(argumentos), 2)
        self.assertEqual(self.stdout.getvalue(), "")
        if mensagem is not None:
            self.assertEqual(self.stderr.getvalue(), mensagem + "\n")
        else:
            self.assertIn("Erro: entrada inválida.", self.stderr.getvalue())
        self.assertNotIn("Traceback", self.stderr.getvalue())
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_rejeicoes_sintaticas_antes_de_io_fr001_fr011(self):
        arquivo = str(self.diretorio / "dados-ficticios.json")
        for argumentos in (
            ["desconhecido"], ["listar", "extra"], ["--arquivo"],
            ["--arquivo", arquivo], ["--opcao-inexistente"],
            ["adicionar", "A", "B"], ["concluir", "1", "2"],
            ["listar", "--arquivo", arquivo], ["--arq", arquivo, "listar"],
        ):
            with self.subTest(argumentos=argumentos):
                self.conferir_erro_sem_dados(argumentos)

    def test_descricao_obrigatoria_antes_de_io_fr002_fr011(self):
        for restante in ([], [""], [" \t\n"], ["\u2003"]):
            with self.subTest(restante=restante):
                self.conferir_erro_sem_dados(
                    ["adicionar", *restante], "Erro: a descrição é obrigatória."
                )

    def test_id_invalido_antes_de_io_fr007_fr011(self):
        for restante in (
            [], [""], ["abc"], ["1.5"], ["0"], ["-1"], ["+1"],
            ["01"], [" 1"], ["1 "], ["١"], ["１"], ["1\n"],
        ):
            with self.subTest(restante=restante):
                self.conferir_erro_sem_dados(
                    ["concluir", *restante],
                    "Erro: informe um identificador inteiro positivo.",
                )

    def test_parser_preserva_argumentos_validos_sem_io_fr002_fr007(self):
        descricao = "  Preparar relatório\ncom revisão\t  "
        arquivo = str(self.diretorio / "dados-ficticios.json")
        with self.sem_acesso_a_dados():
            cli = importlib.import_module("tarefas.cli")
            adicionar = cli._interpretar_argumentos([
                "--arquivo", arquivo, "adicionar", descricao
            ])
            listar = cli._interpretar_argumentos(["listar"])
            concluir = cli._interpretar_argumentos(["concluir", str(10**100)])
        self.assertEqual(adicionar.comando, "adicionar")
        self.assertEqual(adicionar.descricao, descricao)
        self.assertEqual(adicionar.arquivo, arquivo)
        self.assertEqual(listar.comando, "listar")
        self.assertIsNone(listar.arquivo)
        self.assertEqual(concluir.id, 10**100)

    def test_ajuda_dos_subcomandos_sem_io_ou_home_fr001_fr011(self):
        with self.sem_acesso_a_dados():
            cli = importlib.import_module("tarefas.cli")
            for comando in ("adicionar", "listar", "concluir"):
                for opcao in ("-h", "--help"):
                    with self.subTest(comando=comando, opcao=opcao):
                        self.stdout.seek(0)
                        self.stdout.truncate()
                        self.assertEqual(cli.main([comando, opcao]), 0)
                        ajuda = self.stdout.getvalue()
                        self.assertIn(f"uso: python -m tarefas {comando}", ajuda)
                        self.assertIn("opções:", ajuda)
                        self.assertNotIn("positional arguments", ajuda)
                        self.assertNotIn("options:", ajuda)
        self.assertEqual(self.stderr.getvalue(), "")

    def test_caminho_explicito_independe_de_home_fr011(self):
        caminhos = (str(self.diretorio / "dados.json"), "relativo/dados.json", "~/dados.json")
        with self.sem_acesso_a_dados():
            cli = importlib.import_module("tarefas.cli")
            for arquivo in caminhos:
                with self.subTest(arquivo=arquivo):
                    self.assertEqual(cli._resolver_caminho(arquivo), Path(arquivo))

    def test_default_resolvido_somente_em_home_ficticio_fr011(self):
        home = self.diretorio / "home-ficticio"
        with self.sem_acesso_a_dados(), patch("pathlib.Path.home", return_value=home) as obter:
            cli = importlib.import_module("tarefas.cli")
            self.assertEqual(cli._resolver_caminho(None), home / ".tarefas" / "tarefas.json")
        obter.assert_called_once_with()
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_falha_de_home_ficticio_informa_erro_sem_traceback_fr009(self):
        for falha in (OSError("home fictício"), RuntimeError("home fictício")):
            with self.subTest(falha=type(falha).__name__):
                self.stdout.seek(0)
                self.stdout.truncate()
                self.stderr.seek(0)
                self.stderr.truncate()
                with self.sem_acesso_a_dados(), patch("pathlib.Path.home", side_effect=falha):
                    cli = importlib.import_module("tarefas.cli")
                    self.assertEqual(cli.main(["listar"]), 1)
                self.assertEqual(self.stdout.getvalue(), "")
                self.assertEqual(self.stderr.getvalue(), "Erro: não foi possível ler os dados locais.\n")
