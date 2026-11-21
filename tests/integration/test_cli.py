"""Fronteira CLI/processos: US1/US2; FR-001 a FR-012; SC-001/002/003."""

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

    def preparar_us2(self):
        documento = {
            "schema_version": 1,
            "tarefas": [
                {"id": 4, "descricao": '  Preparar relatório | "A"\nB\t  ', "status": "pendente"},
                {"id": 2, "descricao": "Outra pendente", "status": "pendente"},
                {"id": 9, "descricao": "Concluída anterior", "status": "concluida"},
            ],
        }
        self.arquivo.write_text(
            json.dumps(documento, ensure_ascii=False, indent=3) + "\n \t", encoding="utf-8"
        )
        return documento

    def test_resumo_contagens_repetidas_preservam_bytes(self):
        misto = self.preparar_us2()["tarefas"]
        casos = (
            (misto, "Total: 3\nPendentes: 2\nConcluídas: 1\n"),
            ([], "Total: 0\nPendentes: 0\nConcluídas: 0\n"),
            ([item for item in misto if item["status"] == "pendente"],
             "Total: 2\nPendentes: 2\nConcluídas: 0\n"),
            ([item for item in misto if item["status"] == "concluida"],
             "Total: 1\nPendentes: 0\nConcluídas: 1\n"),
        )
        for tarefas, esperado in casos:
            with self.subTest(esperado=esperado):
                self.arquivo.write_text(
                    json.dumps({"schema_version": 1, "tarefas": tarefas},
                               ensure_ascii=False, indent=3) + "\n \t", encoding="utf-8"
                )
                antes = self.arquivo.read_bytes()
                for _ in range(2):
                    self.conferir_sucesso(self.executar_cli("resumo"), esperado)
                    self.assertEqual(self.arquivo.read_bytes(), antes)
                self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_resumo_origens_explicitas_relativa_e_padrao_independentes(self):
        self.preparar_us2()
        outro = self.diretorio / "outro.json"
        outro.write_text('{"schema_version":1,"tarefas":[]}', encoding="utf-8")
        padrao = Path(self.ambiente["USERPROFILE"]) / ".tarefas" / "tarefas.json"
        padrao.parent.mkdir(parents=True)
        padrao.write_text(json.dumps({"schema_version": 1, "tarefas": [
            {"id": 10, "descricao": "Fictícia", "status": "concluida"}
        ]}), encoding="utf-8")
        arquivos = (self.arquivo, outro, padrao)
        antes = {arquivo: arquivo.read_bytes() for arquivo in arquivos}
        arvore = sorted(str(item.relative_to(self.diretorio)) for item in self.diretorio.rglob("*"))
        for caminho, esperado in (
            (self.arquivo, "Total: 3\nPendentes: 2\nConcluídas: 1\n"),
            (os.path.relpath(self.arquivo, RAIZ), "Total: 3\nPendentes: 2\nConcluídas: 1\n"),
            (outro, "Total: 0\nPendentes: 0\nConcluídas: 0\n"),
        ):
            with self.subTest(caminho=caminho):
                self.conferir_sucesso(self.executar_cli("resumo", arquivo=caminho), esperado)
        self.conferir_sucesso(self.executar("-m", "tarefas", "resumo"),
                             "Total: 1\nPendentes: 0\nConcluídas: 1\n")
        self.assertEqual({arquivo: arquivo.read_bytes() for arquivo in arquivos}, antes)
        self.assertEqual(sorted(str(item.relative_to(self.diretorio)) for item in self.diretorio.rglob("*")), arvore)

    def test_resumo_ausencia_nao_cria_arquivo_ou_pais(self):
        for caminho in (self.arquivo, self.diretorio / "ausente" / "pais" / "tarefas.json"):
            with self.subTest(caminho=caminho):
                self.conferir_sucesso(self.executar_cli("resumo", arquivo=caminho),
                                     "Total: 0\nPendentes: 0\nConcluídas: 0\n")
                self.assertEqual(list(self.diretorio.iterdir()), [])
        self.conferir_sucesso(self.executar("-m", "tarefas", "resumo"),
                             "Total: 0\nPendentes: 0\nConcluídas: 0\n")
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def conferir_erro_resumo(self, caminho):
        resultado = self.executar_cli("resumo", arquivo=caminho)
        self.assertEqual(resultado.returncode, 1)
        self.assertEqual(resultado.stdout, "")
        self.assertEqual(resultado.stderr, "Erro: não foi possível ler os dados locais.\n")

    def test_resumo_documentos_invalidos_preservados_sem_contagem_parcial(self):
        valido = {"id": 4, "descricao": "Fictícia", "status": "pendente"}
        documentos = [
            {"schema_version": 9, "tarefas": []},
            {"schema_version": True, "tarefas": []},
            {"schema_version": 1, "tarefas": {}},
            {"schema_version": 1, "tarefas": [valido, None]},
            {"schema_version": 1, "tarefas": [valido, {"id": 5}]},
            {"schema_version": 1, "tarefas": [valido, {**valido, "id": 5, "status": "invalido"}]},
            {"schema_version": 1, "tarefas": [valido, {**valido, "id": 5, "descricao": " "}]},
            {"schema_version": 1, "tarefas": [valido, {**valido, "id": True}]},
            {"schema_version": 1, "tarefas": [valido, valido]},
        ]
        conteudos = [b"", b"{invalido", b'{"schema_version":1,"schema_version":1,"tarefas":[]}',
                     b'{"schema_version":1,"tarefas":[{"id":1,"id":2,"descricao":"A","status":"pendente"}]}']
        conteudos.extend(json.dumps(documento).encode("utf-8") for documento in documentos)
        for conteudo in conteudos:
            with self.subTest(conteudo=conteudo):
                self.arquivo.write_bytes(conteudo)
                self.conferir_erro_resumo(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), conteudo)
                self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_resumo_destino_diretorio_e_ancestral_arquivo_preservados(self):
        self.arquivo.mkdir()
        marcador = self.arquivo / "marcador.txt"
        marcador.write_bytes(b"preservar")
        ancestral = self.diretorio / "ancestral.txt"
        ancestral.write_bytes(b"ancestral ficticio")
        antes = sorted(str(item.relative_to(self.diretorio)) for item in self.diretorio.rglob("*"))
        for caminho in (self.arquivo, ancestral / "filho" / "tarefas.json"):
            with self.subTest(caminho=caminho):
                self.conferir_erro_resumo(caminho)
                self.assertEqual(marcador.read_bytes(), b"preservar")
                self.assertEqual(ancestral.read_bytes(), b"ancestral ficticio")
                self.assertEqual(sorted(str(item.relative_to(self.diretorio)) for item in self.diretorio.rglob("*")), antes)

    def test_us2_muda_so_um_status_persiste_e_repete_sem_alteracao_sc002(self):
        inicial = self.preparar_us2()
        self.conferir_sucesso(self.executar_cli("concluir", "4"), "Tarefa 4 concluída.\n")
        esperado = {
            "schema_version": 1,
            "tarefas": [
                {**registro, "status": "concluida"} if registro["id"] == 4 else registro
                for registro in inicial["tarefas"]
            ],
        }
        self.assertEqual(json.loads(self.arquivo.read_text(encoding="utf-8")), esperado)
        depois = self.arquivo.read_bytes()
        linhas = "".join(
            f'{registro["id"]} | '
            f'{"concluída" if registro["status"] == "concluida" else "pendente"} | '
            f'{json.dumps(registro["descricao"], ensure_ascii=False)}\n'
            for registro in sorted(esperado["tarefas"], key=lambda registro: registro["id"])
        )
        self.conferir_sucesso(self.executar_cli("listar"), linhas)
        self.conferir_sucesso(self.executar_cli("concluir", "4"), "Tarefa 4 já está concluída.\n")
        self.assertEqual(self.arquivo.read_bytes(), depois)

    def test_ja_concluida_preserva_bytes_da_fixture_sem_reeserializar_fr006(self):
        inicial = self.preparar_us2()
        antes = self.arquivo.read_bytes()
        self.conferir_sucesso(self.executar_cli("concluir", "9"), "Tarefa 9 já está concluída.\n")
        self.assertEqual(self.arquivo.read_bytes(), antes)
        self.assertEqual(json.loads(antes), inicial)

    def test_id_inexistente_nao_cria_ou_altera_dados_fr007_sc003(self):
        resultado = self.executar_cli("concluir", "999")
        self.assertEqual(resultado.returncode, 1)
        self.assertEqual(resultado.stdout, "")
        self.assertEqual(resultado.stderr, "Erro: tarefa 999 não encontrada.\n")
        self.assertEqual(list(self.diretorio.iterdir()), [])
        self.preparar_us2()
        antes = self.arquivo.read_bytes()
        for identificador in ("999", str(10**100)):
            with self.subTest(identificador=identificador):
                resultado = self.executar_cli("concluir", identificador)
                self.assertEqual(resultado.returncode, 1)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, f"Erro: tarefa {identificador} não encontrada.\n")
                self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_id_ausente_ou_invalido_nao_cria_ou_altera_dados_fr007(self):
        casos = ([], ["abc"], ["1.5"], ["0"], ["-1"], ["01"])
        for restante in casos[:3]:
            with self.subTest(estado="ausente", restante=restante):
                resultado = self.executar_cli("concluir", *restante)
                self.assertEqual(resultado.returncode, 2)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, "Erro: informe um identificador inteiro positivo.\n")
                self.assertEqual(list(self.diretorio.iterdir()), [])
        self.preparar_us2()
        antes = self.arquivo.read_bytes()
        for restante in casos:
            with self.subTest(estado="existente", restante=restante):
                resultado = self.executar_cli("concluir", *restante)
                self.assertEqual(resultado.returncode, 2)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, "Erro: informe um identificador inteiro positivo.\n")
                self.assertEqual(self.arquivo.read_bytes(), antes)

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
            for argumentos in (("listar",), ("adicionar", "Tarefa fictícia"), ("concluir", "4")):
                with self.subTest(conteudo=conteudo, argumentos=argumentos):
                    resultado = self.executar_cli(*argumentos)
                    self.assertEqual(resultado.returncode, 1)
                    self.assertEqual(resultado.stdout, "")
                    self.assertEqual(resultado.stderr, "Erro: não foi possível ler os dados locais.\n")
                    self.assertEqual(self.arquivo.read_bytes(), conteudo)
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_destino_diretorio_informa_erro_sem_sucesso_fr009(self):
        self.arquivo.mkdir()
        for argumentos in (("listar",), ("adicionar", "Tarefa fictícia"), ("concluir", "4")):
            with self.subTest(argumentos=argumentos):
                resultado = self.executar_cli(*argumentos)
                self.assertEqual(resultado.returncode, 1)
                self.assertEqual(resultado.stdout, "")
                self.assertEqual(resultado.stderr, "Erro: não foi possível ler os dados locais.\n")
                self.assertEqual(list(self.arquivo.iterdir()), [])

    def conferir_falha_replace(self, *argumentos):
        from tarefas.cli import main

        original = self.arquivo.read_bytes()
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("tarefas.armazenamento.os.replace", side_effect=PermissionError("falha fictícia")), patch(
            "pathlib.Path.home", side_effect=AssertionError("consulta indevida ao default")
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            codigo = main(["--arquivo", str(self.arquivo), *argumentos])
        self.assertEqual(codigo, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "Erro: não foi possível salvar os dados locais.\n")
        self.assertEqual(self.arquivo.read_bytes(), original)
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_falha_real_de_replace_traduzida_sem_sucesso_original_intacto_fr009(self):
        self.arquivo.write_bytes(b'{"schema_version":1,"tarefas":[]}\n ')
        self.conferir_falha_replace("adicionar", "Tarefa fictícia")

    def test_falha_de_replace_ao_concluir_preserva_original_sem_sucesso_fr009(self):
        self.preparar_us2()
        self.conferir_falha_replace("concluir", "4")

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
