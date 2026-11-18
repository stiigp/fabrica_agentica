"""Fronteira CLI/processos: US1; FR-001 a FR-005, FR-008 a FR-012; SC-001/003."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


RAIZ = Path(__file__).resolve().parents[2]


class CliProcessoTests(unittest.TestCase):
    def setUp(self):
        temporario = tempfile.TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.diretorio = Path(temporario.name)
        self.arquivo = self.diretorio / "dados-ficticios.json"
        self.ambiente = dict(os.environ)
        self.ambiente.update(
            HOME=str(self.diretorio / "home-ficticio"),
            USERPROFILE=str(self.diretorio / "home-ficticio"),
            PYTHONUTF8="1",
        )

    def executar(self, *argumentos):
        return subprocess.run(
            [sys.executable, "-X", "utf8", *argumentos],
            cwd=RAIZ, env=self.ambiente, capture_output=True,
            text=True, encoding="utf-8", timeout=10, check=False,
        )

    def executar_cli(self, *argumentos, arquivo=None):
        caminho = self.arquivo if arquivo is None else arquivo
        return self.executar("-m", "tarefas", "--arquivo", str(caminho), *argumentos)

    def conferir_sucesso(self, resultado, stdout):
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stdout, stdout)
        self.assertEqual(resultado.stderr, "")

    def test_us1_tres_adicoes_e_novo_id_entre_processos_sc001(self):
        self.conferir_sucesso(self.executar_cli("listar"), "Nenhuma tarefa cadastrada.\n")
        self.assertEqual(list(self.diretorio.iterdir()), [])
        descricoes = ["Preparar relatório", "Preparar relatório", "Revisar seção técnica"]
        for identificador, descricao in enumerate(descricoes, start=1):
            self.conferir_sucesso(
                self.executar_cli("adicionar", descricao), f"Tarefa {identificador} adicionada.\n"
            )
        antes = self.arquivo.read_bytes()
        esperado = "".join(
            f"{identificador} | pendente | {json.dumps(descricao, ensure_ascii=False)}\n"
            for identificador, descricao in enumerate(descricoes, start=1)
        )
        self.conferir_sucesso(self.executar_cli("listar"), esperado)
        self.assertEqual(self.arquivo.read_bytes(), antes)
        self.conferir_sucesso(self.executar_cli("adicionar", "Nova tarefa"), "Tarefa 4 adicionada.\n")
        self.conferir_sucesso(
            self.executar_cli("listar"), esperado + '4 | pendente | "Nova tarefa"\n'
        )
        documento = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(documento["tarefas"], [
            {"id": identificador, "descricao": descricao, "status": "pendente"}
            for identificador, descricao in enumerate([*descricoes, "Nova tarefa"], start=1)
        ])

    def test_descricao_exata_com_acentos_espacos_e_controles_fr002_fr008(self):
        descricao = '  Seção técnica | "A" \\ caminho\nB\tC\rD  '
        self.conferir_sucesso(self.executar_cli("adicionar", descricao), "Tarefa 1 adicionada.\n")
        resultado = self.executar_cli("listar")
        self.conferir_sucesso(resultado, f"1 | pendente | {json.dumps(descricao, ensure_ascii=False)}\n")
        self.assertEqual(json.loads(resultado.stdout.split(" | ", 2)[2]), descricao)
        documento = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(documento["tarefas"][0]["descricao"], descricao)

    def test_caminhos_distintos_e_relativo_mantem_conjuntos_independentes_fr008(self):
        outro = self.diretorio / "outro-conjunto.json"
        relativo = os.path.relpath(self.arquivo, RAIZ)
        self.conferir_sucesso(self.executar_cli("adicionar", "Primeiro", arquivo=relativo), "Tarefa 1 adicionada.\n")
        self.conferir_sucesso(self.executar_cli("listar", arquivo=outro), "Nenhuma tarefa cadastrada.\n")
        self.assertFalse(outro.exists())
        self.conferir_sucesso(self.executar_cli("adicionar", "Outro", arquivo=outro), "Tarefa 1 adicionada.\n")
        self.conferir_sucesso(self.executar_cli("adicionar", "Segundo"), "Tarefa 2 adicionada.\n")
        self.conferir_sucesso(self.executar_cli("listar", arquivo=relativo), '1 | pendente | "Primeiro"\n2 | pendente | "Segundo"\n')
        self.conferir_sucesso(self.executar_cli("listar", arquivo=outro), '1 | pendente | "Outro"\n')

    def test_descricao_invalida_sem_criar_ou_alterar_dados_sc003(self):
        for restante in ([], [""], [" \t\n"]):
            with self.subTest(estado="ausente", restante=restante):
                resultado = self.executar_cli("adicionar", *restante)
                self.assertEqual(resultado.returncode, 2)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, "Erro: a descrição é obrigatória.\n")
                self.assertEqual(list(self.diretorio.iterdir()), [])
        self.conferir_sucesso(self.executar_cli("adicionar", "Existente"), "Tarefa 1 adicionada.\n")
        antes = self.arquivo.read_bytes()
        for restante in ([], [""], [" \t\n"]):
            with self.subTest(estado="existente", restante=restante):
                resultado = self.executar_cli("adicionar", *restante)
                self.assertEqual(resultado.returncode, 2)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, "Erro: a descrição é obrigatória.\n")
                self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_dados_invalidos_nao_viram_vazio_nem_sao_substituidos_fr009(self):
        for conteudo in (b"", b"{invalido", b'{"schema_version":9,"tarefas":[]}'):
            self.arquivo.write_bytes(conteudo)
            for argumentos in (("listar",), ("adicionar", "Tarefa fictícia")):
                with self.subTest(conteudo=conteudo, argumentos=argumentos):
                    resultado = self.executar_cli(*argumentos)
                    self.assertEqual(resultado.returncode, 1)
                    self.assertEqual(resultado.stdout, "")
                    self.assertEqual(resultado.stderr, "Erro: não foi possível ler os dados locais.\n")
                    self.assertEqual(self.arquivo.read_bytes(), conteudo)
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_destino_diretorio_informa_erro_sem_sucesso_fr009(self):
        self.arquivo.mkdir()
        for argumentos in (("listar",), ("adicionar", "Tarefa fictícia")):
            with self.subTest(argumentos=argumentos):
                resultado = self.executar_cli(*argumentos)
                self.assertEqual(resultado.returncode, 1)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, "Erro: não foi possível ler os dados locais.\n")
                self.assertEqual(list(self.arquivo.iterdir()), [])

    def test_falha_real_de_replace_traduzida_sem_sucesso_original_intacto_fr009(self):
        from tarefas.cli import main

        original = b'{"schema_version":1,"tarefas":[]}\n '
        self.arquivo.write_bytes(original)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("tarefas.armazenamento.os.replace", side_effect=PermissionError("falha fictícia")), patch(
            "pathlib.Path.home", side_effect=AssertionError("consulta indevida ao default")
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            codigo = main(["--arquivo", str(self.arquivo), "adicionar", "Tarefa fictícia"])
        self.assertEqual(codigo, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "Erro: não foi possível salvar os dados locais.\n")
        self.assertEqual(self.arquivo.read_bytes(), original)
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_ajuda_real_em_portugues_sem_criar_dados_fr001_fr012(self):
        resultado = self.executar(
            "-m", "tarefas", "--arquivo", str(self.arquivo), "--help"
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertTrue(resultado.stdout.startswith("uso: python -m tarefas"))
        for texto in ("opções:", "adicionar", "listar", "concluir", "--arquivo"):
            self.assertIn(texto, resultado.stdout)
        self.assertEqual(resultado.stderr, "")
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_erro_real_propaga_saida_nao_zero_fr010(self):
        resultado = self.executar("-m", "tarefas", "--opcao-inexistente")
        self.assertEqual(resultado.returncode, 2)
        self.assertEqual(resultado.stdout, "")
        self.assertIn("Erro:", resultado.stderr)
        self.assertNotIn("Traceback", resultado.stderr)
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_importacao_e_ajuda_com_guards_em_novo_processo_fr011(self):
        script = """
from contextlib import ExitStack
import importlib
import runpy
import sys
from unittest.mock import patch

with ExitStack() as guards:
    for alvo in (
        'builtins.open', 'io.open', 'os.open', 'os.mkdir', 'os.makedirs',
        'os.replace', 'pathlib.Path.home', 'pathlib.Path.expanduser',
    ):
        guards.enter_context(patch(
            alvo, side_effect=AssertionError('Acesso indevido: ' + alvo)
        ))
    importlib.import_module('tarefas')
    importlib.import_module('tarefas.cli')
    sys.argv = ['tarefas', '--arquivo', sys.argv[1], '--help']
    runpy.run_module('tarefas', run_name='__main__')
"""
        resultado = self.executar("-c", script, str(self.arquivo))
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertTrue(resultado.stdout.startswith("uso: python -m tarefas"))
        self.assertIn("mostrar esta ajuda e sair", resultado.stdout)
        self.assertEqual(resultado.stderr, "")
        self.assertEqual(list(self.diretorio.iterdir()), [])
