"""Aceite da feature 002 com dados locais fictícios."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tarefas.cli import main


RAIZ = Path(__file__).resolve().parents[2]
ERRO = "Erro: não foi possível ler os dados locais.\n"


class AceiteResumo(unittest.TestCase):
    def setUp(self):
        temporario = tempfile.TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.raiz = Path(temporario.name)
        self.arquivo = self.raiz / "dados.json"
        self.home = self.raiz / "home-ficticio"
        self.env = dict(os.environ, PYTHONUTF8="1", HOME=str(self.home),
                        USERPROFILE=str(self.home))

    def executar(self, *argumentos):
        return subprocess.run([sys.executable, "-m", "tarefas", *map(str, argumentos)],
                              cwd=RAIZ, env=self.env, capture_output=True,
                              text=True, encoding="utf-8", timeout=15)

    def conferir(self, resultado, total, pendentes, concluidas):
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stderr, "")
        self.assertEqual(resultado.stdout,
                         f"Total: {total}\nPendentes: {pendentes}\nConcluídas: {concluidas}\n")

    def gravar(self, caminho, estados):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps({"schema_version": 1, "tarefas": [
            {"id": 9 + 7 * i, "descricao": "Tarefa fictícia", "status": estado}
            for i, estado in enumerate(estados)
        ]}, ensure_ascii=False, indent=3) + "\n \t", encoding="utf-8")

    def test_us1_categorias_e_repeticao_preservam_bytes(self):
        for estados, esperado in (([], (0, 0, 0)),
                                  (["pendente", "concluida", "pendente"], (3, 2, 1)),
                                  (["pendente"] * 2, (2, 2, 0)),
                                  (["concluida"] * 2, (2, 0, 2))):
            with self.subTest(estados=estados):
                self.gravar(self.arquivo, estados)
                antes = self.arquivo.read_bytes()
                for _ in range(2):
                    self.conferir(self.executar("--arquivo", self.arquivo, "resumo"), *esperado)
                    self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_us2_origens_explicitas_relativa_e_padrao(self):
        padrao = self.home / ".tarefas" / "tarefas.json"
        outro = self.raiz / "outro.json"
        self.gravar(self.arquivo, ["pendente", "pendente"])
        self.gravar(outro, [])
        self.gravar(padrao, ["concluida"])
        antes = {p: p.read_bytes() for p in (self.arquivo, outro, padrao)}
        for caminho, esperado in ((self.arquivo, (2, 2, 0)), (outro, (0, 0, 0)),
                                  (os.path.relpath(self.arquivo, RAIZ), (2, 2, 0))):
            with self.subTest(caminho=caminho):
                self.conferir(self.executar("--arquivo", caminho, "resumo"), *esperado)
        self.conferir(self.executar("resumo"), 1, 0, 1)
        self.assertEqual({p: p.read_bytes() for p in antes}, antes)

    def test_us2_ausencia_nao_cria_arquivo_nem_pais(self):
        for caminho in (self.arquivo, self.raiz / "pais" / "filho" / "dados.json"):
            self.conferir(self.executar("--arquivo", caminho, "resumo"), 0, 0, 0)
        self.conferir(self.executar("resumo"), 0, 0, 0)
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_us2_invalidos_e_obstaculos_preservados(self):
        valido = {"id": 5, "descricao": "Fictícia", "status": "pendente"}
        documentos = [b"", b"{invalido", b'{"schema_version":9,"tarefas":[]}']
        for registro in (None, {**valido, "status": "desconhecido"},
                         {**valido, "descricao": " "}, valido):
            documentos.append(json.dumps({"schema_version": 1,
                                          "tarefas": [valido, registro]}).encode())
        for conteudo in documentos:
            with self.subTest(conteudo=conteudo):
                self.arquivo.write_bytes(conteudo)
                self.conferir_erro(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), conteudo)
        diretorio = self.raiz / "diretorio"
        diretorio.mkdir()
        for caminho in (diretorio, self.arquivo / "filho" / "dados.json"):
            self.conferir_erro(caminho)
        self.assertEqual(list(diretorio.iterdir()), [])
        self.assertEqual(set(self.raiz.iterdir()), {self.arquivo, diretorio})

    def conferir_erro(self, caminho):
        resultado = self.executar("--arquivo", caminho, "resumo")
        self.assertEqual((resultado.returncode, resultado.stdout, resultado.stderr), (1, "", ERRO))

    def test_us2_acesso_negado_e_us3_ajudas_sem_io(self):
        for argumentos, codigo in ((["--arquivo", str(self.arquivo), "resumo"], 1),
                                    (["--help"], 0), (["resumo", "--help"], 0)):
            with self.subTest(argumentos=argumentos):
                stdout, stderr = io.StringIO(), io.StringIO()
                with ExitStack() as guards, redirect_stdout(stdout), redirect_stderr(stderr):
                    for alvo in ("pathlib.Path.open", "pathlib.Path.home", "tarefas.cli.salvar"):
                        guards.enter_context(patch(alvo, side_effect=PermissionError("fictício")))
                    self.assertEqual(main(argumentos), codigo)
                if codigo:
                    self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ERRO))
                else:
                    self.assertEqual(stderr.getvalue(), "")
                    self.assertIn("resumo", stdout.getvalue())
                    self.assertIn("consultar contagens", " ".join(stdout.getvalue().split()))
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_us3_executa_comandos_reais_do_readme(self):
        secao = (RAIZ / "README.md").read_text(encoding="utf-8").split(
            "### Consultar um resumo", 1)[1]
        bloco = re.search(r"```powershell\n(.*?)```", secao, re.S).group(1)
        comandos = [shlex.split(linha) for linha in bloco.splitlines()
                    if linha.startswith("python -m tarefas ")]
        self.assertEqual(len(comandos), 5)
        for comando in comandos:
            self.assertEqual(comando[:3], ["python", "-m", "tarefas"])
            argumentos = [str(self.arquivo) if arg == "$arquivoResumo" else arg
                          for arg in comando[3:]]
            antes = self.arquivo.read_bytes() if self.arquivo.exists() else None
            resultado = self.executar(*argumentos)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(resultado.stderr, "")
            if argumentos[-1] == "resumo":
                esperado = re.search(r"```text\n(.*?)```", secao, re.S).group(1)
                self.assertEqual(resultado.stdout, esperado)
                self.conferir(resultado, 3, 2, 1)
                self.assertEqual(self.arquivo.read_bytes(), antes)
        self.assertEqual(comandos[-1][-1], "resumo")
        self.assertIn("somente leitura", secao)


if __name__ == "__main__":
    unittest.main()
