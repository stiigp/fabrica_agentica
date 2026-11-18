"""Fronteira de processo inicial: FR-001, FR-010, FR-011 e FR-012."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


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
