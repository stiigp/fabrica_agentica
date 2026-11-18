"""JSON, arquivos e falhas determinísticas: FR-008/009/010/011; SC-003."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from tarefas import armazenamento
from tarefas.armazenamento import ErroGravacao, ErroLeitura, carregar, salvar
from tarefas.modelo import ErroValidacao, Tarefa


class _TemporarioComFalha:
    def __init__(self, arquivo, etapa, falha):
        self.arquivo = arquivo
        self.name = arquivo.name
        self.etapa = etapa
        self.falha = falha

    def __enter__(self):
        return self

    def write(self, conteudo):
        if self.etapa == "escrita":
            self.arquivo.write(conteudo[:10])
            raise self.falha
        return self.arquivo.write(conteudo)

    def __exit__(self, *args):
        self.arquivo.close()
        if self.etapa == "fechamento":
            raise self.falha


class ArmazenamentoTests(unittest.TestCase):
    def setUp(self):
        temporario = tempfile.TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.diretorio = Path(temporario.name)
        self.arquivo = self.diretorio / "tarefas-ficticias.json"
        self.original = b'{"schema_version":1,"tarefas":[]}\n  '
        self.tarefas = [
            Tarefa(8, '  Revisar relatório | "A"\nB\t  ', "concluida"),
            Tarefa(2, "Repetida"), Tarefa(10, "Repetida"),
        ]

    def conferir_original(self):
        self.assertEqual(self.arquivo.read_bytes(), self.original)

    def test_ausencia_inicial_nao_cria_arquivo_ou_pais_fr008_fr011(self):
        destino = self.diretorio / "pais-ausentes" / "dados.json"
        self.assertEqual(carregar(destino), [])
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_lista_vazia_valida_sem_reescrever_fr008(self):
        self.arquivo.write_bytes(self.original)
        self.assertEqual(carregar(self.arquivo), [])
        self.conferir_original()

    def test_roundtrip_utf8_preserva_ids_status_descricao_e_ordem_fr008(self):
        salvar(self.arquivo, self.tarefas)
        antes = self.arquivo.read_bytes()
        self.assertIn("relatório".encode("utf-8"), antes)
        self.assertEqual(carregar(self.arquivo), self.tarefas)
        self.assertEqual(carregar(self.arquivo), self.tarefas)
        self.assertEqual(self.arquivo.read_bytes(), antes)
        documento = json.loads(antes)
        self.assertEqual(set(documento), {"schema_version", "tarefas"})
        self.assertEqual(documento["schema_version"], 1)
        self.assertEqual([registro["id"] for registro in documento["tarefas"]], [8, 2, 10])
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_salvar_cria_pais_para_colecao_valida_fr008(self):
        destino = self.diretorio / "novo" / "subdiretorio" / "dados.json"
        salvar(destino, self.tarefas)
        self.assertEqual(carregar(destino), self.tarefas)

    def test_rejeita_json_vazio_malformado_e_utf8_invalido_fr009(self):
        for conteudo in (b"", b"   ", b"{", b"texto", b"\xff"):
            with self.subTest(conteudo=conteudo):
                self.arquivo.write_bytes(conteudo)
                with self.assertRaises(ErroLeitura):
                    carregar(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), conteudo)

    def test_valida_documento_inteiro_tipos_campos_e_ids_fr009(self):
        registro = {"id": 1, "descricao": "Tarefa fictícia", "status": "pendente"}
        documentos = [None, True, [], "texto", {}, {"schema_version": 1},
                      {"tarefas": []}, {"schema_version": 1, "tarefas": [], "extra": 0}]
        for versao in (True, False, 0, 2, -1, 1.0, "1", None):
            documentos.append({"schema_version": versao, "tarefas": []})
        for colecao in (None, {}, "texto", True):
            documentos.append({"schema_version": 1, "tarefas": colecao})
        registros_invalidos = [None, [], {}, 1, True, "texto", {**registro, "extra": 0}]
        for campo in registro:
            registros_invalidos.append({k: v for k, v in registro.items() if k != campo})
        for campo, valores in (
            ("id", (True, False, 0, -1, 1.0, "1", None)),
            ("descricao", (None, "", " \t\n", 1, True, [])),
            ("status", (None, "concluída", "desconhecido", 1, True, [])),
        ):
            registros_invalidos.extend({**registro, campo: valor} for valor in valores)
        for invalido in registros_invalidos:
            documentos.append({"schema_version": 1, "tarefas": [registro, invalido]})
        documentos.append({"schema_version": 1, "tarefas": [registro, registro]})
        for indice, documento in enumerate(documentos):
            with self.subTest(caso=indice):
                conteudo = json.dumps(documento, ensure_ascii=False).encode("utf-8")
                self.arquivo.write_bytes(conteudo)
                with self.assertRaises(ErroLeitura):
                    carregar(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), conteudo)

    def test_rejeita_chaves_repetidas_em_qualquer_objeto_fr009(self):
        documentos = [
            '{"schema_version":1,"schema_version":1,"tarefas":[]}',
            '{"schema_version":1,"tarefas":[],"tarefas":[]}',
        ]
        for campo, valor in (("id", "1"), ("descricao", '"A"'), ("status", '"pendente"')):
            documentos.append(
                '{"schema_version":1,"tarefas":[{"id":1,"descricao":"A",'
                '"status":"pendente",' + json.dumps(campo) + ':' + valor + '}]}'
            )
        for documento in documentos:
            with self.subTest(documento=documento):
                self.arquivo.write_text(documento, encoding="utf-8")
                with self.assertRaises(ErroLeitura):
                    carregar(self.arquivo)
                self.assertEqual(self.arquivo.read_text(encoding="utf-8"), documento)

    def test_diretorio_no_lugar_do_arquivo_e_erro_fr009(self):
        self.arquivo.mkdir()
        with self.assertRaises(ErroLeitura):
            carregar(self.arquivo)
        self.assertEqual(list(self.arquivo.iterdir()), [])

    def test_pai_que_e_arquivo_nao_e_conjunto_vazio_fr009(self):
        self.arquivo.write_bytes(self.original)
        for sufixo in ("dados.json", "subdiretorio/dados.json"):
            with self.subTest(sufixo=sufixo):
                with self.assertRaises(ErroLeitura):
                    carregar(self.arquivo / sufixo)
        self.conferir_original()

    def test_erro_ao_verificar_ausencia_nao_vira_vazio_fr009(self):
        falha = PermissionError("stat fictício negado")
        with patch.object(Path, "stat", side_effect=falha):
            with self.assertRaises(ErroLeitura) as capturado:
                carregar(self.arquivo)
        self.assertIs(capturado.exception.__cause__, falha)
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_falha_de_abertura_nao_vira_lista_vazia_fr009(self):
        self.arquivo.write_bytes(self.original)
        falha = PermissionError("leitura fictícia negada")
        with patch.object(Path, "open", side_effect=falha):
            with self.assertRaises(ErroLeitura) as capturado:
                carregar(self.arquivo)
        self.assertIs(capturado.exception.__cause__, falha)
        self.conferir_original()

    def test_falhas_durante_leitura_e_fechamento_nao_viram_vazio_fr009(self):
        self.arquivo.write_bytes(self.original)
        for etapa, falha in (
            ("read", OSError("falha de leitura fictícia")),
            ("read", FileNotFoundError("arquivo aberto não é ausência inicial")),
            ("__exit__", OSError("falha de fechamento fictícia")),
        ):
            with self.subTest(etapa=etapa, falha=type(falha).__name__):
                arquivo = MagicMock()
                arquivo.__enter__.return_value = arquivo
                arquivo.read.return_value = self.original.decode("utf-8")
                getattr(arquivo, etapa).side_effect = falha
                with patch.object(Path, "open", return_value=arquivo):
                    with self.assertRaises(ErroLeitura) as capturado:
                        carregar(self.arquivo)
                self.assertIs(capturado.exception.__cause__, falha)
                self.conferir_original()

    def test_colecao_invalida_nao_cria_pais_ou_altera_original_fr009(self):
        self.arquivo.write_bytes(self.original)
        for tarefas in (None, (), {}, [None], [{"id": 1}], [Tarefa(1, "A"), Tarefa(1, "B")]):
            with self.subTest(tarefas=tarefas):
                with patch.object(Path, "mkdir") as mkdir, patch(
                    "tarefas.armazenamento.tempfile.NamedTemporaryFile"
                ) as criar:
                    with self.assertRaises(ErroGravacao) as capturado:
                        salvar(self.arquivo, tarefas)
                self.assertIsInstance(capturado.exception.__cause__, ErroValidacao)
                mkdir.assert_not_called()
                criar.assert_not_called()
                self.conferir_original()

    def test_falha_de_serializacao_antes_de_criar_pais_fr009(self):
        self.arquivo.write_bytes(self.original)
        falha = ValueError("serialização fictícia")
        with patch("tarefas.armazenamento.json.dumps", side_effect=falha), patch.object(
            Path, "mkdir"
        ) as mkdir:
            with self.assertRaises(ErroGravacao) as capturado:
                salvar(self.arquivo, self.tarefas)
        mkdir.assert_not_called()
        self.assertIs(capturado.exception.__cause__, falha)
        self.conferir_original()

    def test_falha_ao_criar_pais_preserva_original_fr009(self):
        self.arquivo.write_bytes(self.original)
        falha = OSError("mkdir fictício")
        with patch.object(Path, "mkdir", side_effect=falha), patch(
            "tarefas.armazenamento.tempfile.NamedTemporaryFile"
        ) as criar:
            with self.assertRaises(ErroGravacao) as capturado:
                salvar(self.arquivo, self.tarefas)
        criar.assert_not_called()
        self.assertIs(capturado.exception.__cause__, falha)
        self.conferir_original()

    def test_falha_ao_criar_temporario_preserva_original_fr009(self):
        self.arquivo.write_bytes(self.original)
        falha = PermissionError("temporário fictício")
        with patch("tarefas.armazenamento.tempfile.NamedTemporaryFile", side_effect=falha):
            with self.assertRaises(ErroGravacao) as capturado:
                salvar(self.arquivo, self.tarefas)
        self.assertIs(capturado.exception.__cause__, falha)
        self.conferir_original()
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_falhas_de_escrita_e_fechamento_limpam_so_temporario_proprio_fr009(self):
        self.arquivo.write_bytes(self.original)
        sentinela = self.diretorio / "temporario-de-outra-operacao.tmp"
        sentinela.write_bytes(b"sentinela ficticia")
        criar_real = armazenamento.tempfile.NamedTemporaryFile
        for etapa in ("escrita", "fechamento"):
            with self.subTest(etapa=etapa):
                abertos = []
                falha = OSError(f"falha fictícia em {etapa}")

                def criar(*args, **kwargs):
                    arquivo = criar_real(*args, **kwargs)
                    abertos.append(arquivo)
                    return _TemporarioComFalha(arquivo, etapa, falha)

                with patch("tarefas.armazenamento.tempfile.NamedTemporaryFile", side_effect=criar):
                    with self.assertRaises(ErroGravacao) as capturado:
                        salvar(self.arquivo, self.tarefas)
                self.assertIs(capturado.exception.__cause__, falha)
                self.assertTrue(abertos)
                self.assertTrue(all(arquivo.closed for arquivo in abertos))
                self.conferir_original()
                self.assertEqual(sentinela.read_bytes(), b"sentinela ficticia")
                self.assertEqual(set(self.diretorio.iterdir()), {self.arquivo, sentinela})

    def test_substituicao_usa_temporario_fechado_no_mesmo_diretorio_fr008_fr009(self):
        self.arquivo.write_bytes(self.original)
        criar_real = armazenamento.tempfile.NamedTemporaryFile
        substituir_real = armazenamento.os.replace
        abertos = []

        def criar(*args, **kwargs):
            arquivo = criar_real(*args, **kwargs)
            abertos.append(arquivo)
            return arquivo

        def substituir(origem, destino):
            self.assertEqual(Path(origem).parent, self.arquivo.parent)
            self.assertEqual(destino, self.arquivo)
            self.assertNotEqual(origem, destino)
            self.assertTrue(abertos[0].closed)
            self.conferir_original()
            self.assertEqual(carregar(origem), self.tarefas)
            substituir_real(origem, destino)

        with patch("tarefas.armazenamento.tempfile.NamedTemporaryFile", side_effect=criar), patch(
            "tarefas.armazenamento.os.replace", side_effect=substituir
        ) as substituir_mock:
            salvar(self.arquivo, self.tarefas)
        substituir_mock.assert_called_once()
        self.assertEqual(carregar(self.arquivo), self.tarefas)
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_falha_de_replace_preserva_original_e_limpa_temporario_fr009(self):
        self.arquivo.write_bytes(self.original)
        falha = PermissionError("replace fictício")
        with patch("tarefas.armazenamento.os.replace", side_effect=falha):
            with self.assertRaises(ErroGravacao) as capturado:
                salvar(self.arquivo, self.tarefas)
        self.assertIs(capturado.exception.__cause__, falha)
        self.conferir_original()
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])

    def test_falha_de_limpeza_nao_mascara_erro_principal_fr009(self):
        self.arquivo.write_bytes(self.original)
        falha = OSError("replace é o erro principal fictício")
        with patch("tarefas.armazenamento.os.replace", side_effect=falha) as substituir, patch.object(
            Path, "unlink", side_effect=PermissionError("limpeza fictícia")
        ) as limpar:
            with self.assertRaises(ErroGravacao) as capturado:
                salvar(self.arquivo, self.tarefas)
        self.assertIs(capturado.exception.__cause__, falha)
        temporario = substituir.call_args.args[0]
        limpar.assert_called_once_with(missing_ok=True)
        self.assertEqual(set(self.diretorio.iterdir()), {self.arquivo, temporario})
        self.conferir_original()

    def test_falha_de_replace_sem_original_nao_cria_destino_fr009(self):
        with patch("tarefas.armazenamento.os.replace", side_effect=OSError("replace fictício")):
            with self.assertRaises(ErroGravacao):
                salvar(self.arquivo, self.tarefas)
        self.assertEqual(list(self.diretorio.iterdir()), [])

    def test_salvar_sobre_diretorio_preserva_seu_conteudo_fr009(self):
        self.arquivo.mkdir()
        sentinela = self.arquivo / "sentinela-ficticia.txt"
        sentinela.write_bytes(b"inalterado")
        with self.assertRaises(ErroGravacao):
            salvar(self.arquivo, self.tarefas)
        self.assertEqual(sentinela.read_bytes(), b"inalterado")
        self.assertEqual(list(self.diretorio.iterdir()), [self.arquivo])
