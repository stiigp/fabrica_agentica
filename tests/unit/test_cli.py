"""Contrato inicial da CLI: FR-001, FR-010, FR-011 e FR-012."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import importlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tarefas.armazenamento import ErroGravacao, ErroLeitura
from tarefas.modelo import Tarefa


class CliOperacoesTests(unittest.TestCase):
    def setUp(self):
        temporario = tempfile.TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.arquivo = Path(temporario.name) / "dados-ficticios.json"
        self.cli = importlib.import_module("tarefas.cli")
        self.tarefas = [
            Tarefa(8, '  Revisar relatório | "A"\nB\t  ', "concluida"),
            Tarefa(2, "Repetida"), Tarefa(5, "Repetida"),
        ]
        guards = ExitStack()
        self.addCleanup(guards.close)
        self.carregar = guards.enter_context(patch.object(self.cli, "carregar", return_value=self.tarefas))
        self.salvar = guards.enter_context(patch.object(self.cli, "salvar"))
        for alvo in (
            "builtins.open", "io.open", "os.open", "os.mkdir", "os.makedirs",
            "os.replace", "pathlib.Path.home", "pathlib.Path.expanduser",
        ):
            guards.enter_context(patch(alvo, side_effect=AssertionError(f"I/O indevido: {alvo}")))
        self.stdout, self.stderr = io.StringIO(), io.StringIO()

    def executar(self, *argumentos):
        self.stdout.seek(0)
        self.stdout.truncate()
        self.stderr.seek(0)
        self.stderr.truncate()
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return self.cli.main(["--arquivo", str(self.arquivo), *argumentos])

    def test_listar_vazio_sem_escrita_fr005(self):
        self.carregar.return_value = []
        self.assertEqual(self.executar("listar"), 0)
        self.assertEqual(self.stdout.getvalue(), "Nenhuma tarefa cadastrada.\n")
        self.assertEqual(self.stderr.getvalue(), "")
        self.carregar.assert_called_once_with(self.arquivo)
        self.salvar.assert_not_called()

    def test_resumo_contagens_sem_salvar_ou_mutar(self):
        casos = (
            (self.tarefas, "Total: 3\nPendentes: 2\nConcluídas: 1\n"),
            ([], "Total: 0\nPendentes: 0\nConcluídas: 0\n"),
            ([Tarefa(9, "A")], "Total: 1\nPendentes: 1\nConcluídas: 0\n"),
            ([Tarefa(4, "B", "concluida")], "Total: 1\nPendentes: 0\nConcluídas: 1\n"),
        )
        self.salvar.side_effect = AssertionError("resumo não pode salvar")
        for tarefas, esperado in casos:
            with self.subTest(esperado=esperado):
                antes = list(tarefas)
                self.carregar.return_value = tarefas
                self.carregar.reset_mock()
                self.assertEqual(self.executar("resumo"), 0)
                self.assertEqual(self.stdout.getvalue(), esperado)
                self.assertEqual(self.stderr.getvalue(), "")
                self.carregar.assert_called_once_with(self.arquivo)
                self.salvar.assert_not_called()
                self.assertEqual(tarefas, antes)

    def test_listar_ordenado_todos_campos_escape_reversivel_sem_mutacao_fr005(self):
        antes = list(self.tarefas)
        self.assertEqual(self.executar("listar"), 0)
        linhas = self.stdout.getvalue().splitlines()
        self.assertEqual(len(linhas), 3)
        self.assertEqual([linha.split(" | ", 2)[0] for linha in linhas], ["2", "5", "8"])
        for tarefa, linha in zip(sorted(antes, key=lambda tarefa: tarefa.id), linhas):
            identificador, status, descricao = linha.split(" | ", 2)
            self.assertEqual(int(identificador), tarefa.id)
            self.assertEqual(status, "concluída" if tarefa.status == "concluida" else "pendente")
            self.assertEqual(json.loads(descricao), tarefa.descricao)
        self.assertEqual(self.stderr.getvalue(), "")
        self.assertEqual(self.tarefas, antes)
        self.carregar.assert_called_once_with(self.arquivo)
        self.salvar.assert_not_called()

    def test_adicionar_confirma_somente_apos_salvar_nova_colecao_fr008(self):
        antes = list(self.tarefas)
        descricao = '  Seção técnica | "A"\nB\t\x00  '

        def salvar(caminho, novas):
            self.assertEqual(self.stdout.getvalue(), "")
            self.assertEqual(self.stderr.getvalue(), "")
            self.assertEqual(caminho, self.arquivo)
            self.assertEqual(novas, [*antes, Tarefa(9, descricao)])
            self.assertIsNot(novas, self.tarefas)
            self.assertEqual(self.tarefas, antes)

        self.salvar.side_effect = salvar
        self.assertEqual(self.executar("adicionar", descricao), 0)
        self.assertEqual(self.stdout.getvalue(), "Tarefa 9 adicionada.\n")
        self.assertEqual(self.stderr.getvalue(), "")
        self.salvar.assert_called_once()
        self.assertEqual(self.tarefas, antes)

    def test_falha_de_leitura_sem_escrita_ou_sucesso_fr009(self):
        self.carregar.side_effect = ErroLeitura("falha fictícia")
        for argumentos in (("listar",), ("adicionar", "Tarefa fictícia"), ("concluir", "2")):
            with self.subTest(argumentos=argumentos):
                self.assertEqual(self.executar(*argumentos), 1)
                self.assertEqual(self.stdout.getvalue(), "")
                self.assertEqual(self.stderr.getvalue(), "Erro: não foi possível ler os dados locais.\n")
                self.salvar.assert_not_called()

    def test_falha_de_gravacao_sem_confirmacao_ou_mutacao_fr009(self):
        antes = list(self.tarefas)
        self.salvar.side_effect = ErroGravacao("falha fictícia")
        for argumentos in (("adicionar", "Tarefa fictícia"), ("concluir", "2")):
            with self.subTest(argumentos=argumentos):
                self.assertEqual(self.executar(*argumentos), 1)
                self.assertEqual(self.stdout.getvalue(), "")
                self.assertEqual(self.stderr.getvalue(), "Erro: não foi possível salvar os dados locais.\n")
                self.assertEqual(self.tarefas, antes)

    def test_concluir_confirma_somente_apos_salvar_sem_mutar_original_fr006_fr008(self):
        antes = list(self.tarefas)
        esperado = [antes[0], Tarefa(2, antes[1].descricao, "concluida"), antes[2]]

        def salvar(caminho, novas):
            self.assertEqual(self.stdout.getvalue(), "")
            self.assertEqual(self.stderr.getvalue(), "")
            self.assertEqual(caminho, self.arquivo)
            self.assertEqual(novas, esperado)
            self.assertIsNot(novas, self.tarefas)
            self.assertEqual(self.tarefas, antes)

        self.salvar.side_effect = salvar
        self.assertEqual(self.executar("concluir", "2"), 0)
        self.assertEqual(self.stdout.getvalue(), "Tarefa 2 concluída.\n")
        self.assertEqual(self.stderr.getvalue(), "")
        self.salvar.assert_called_once_with(self.arquivo, esperado)
        self.assertEqual(self.tarefas, antes)

    def test_conclusao_repetida_sem_escrita_ou_reeserializacao_fr006(self):
        antes = list(self.tarefas)
        with patch("tarefas.cli.json.dumps", side_effect=AssertionError("reeserialização indevida")):
            self.assertEqual(self.executar("concluir", "8"), 0)
        self.assertEqual(self.stdout.getvalue(), "Tarefa 8 já está concluída.\n")
        self.assertEqual(self.stderr.getvalue(), "")
        self.salvar.assert_not_called()
        self.assertEqual(self.tarefas, antes)

    def test_id_inexistente_sem_escrita_ou_sucesso_fr007(self):
        antes = list(self.tarefas)
        self.assertEqual(self.executar("concluir", "999"), 1)
        self.assertEqual(self.stdout.getvalue(), "")
        self.assertEqual(self.stderr.getvalue(), "Erro: tarefa 999 não encontrada.\n")
        self.salvar.assert_not_called()
        self.assertEqual(self.tarefas, antes)


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
