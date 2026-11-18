"""Invariantes canônicas de Tarefa: FR-002, FR-003, FR-004, FR-006, FR-009."""

import unittest

from tarefas.modelo import ErroValidacao, Tarefa, validar_descricao


class ModeloTests(unittest.TestCase):
    def test_nova_tarefa_pendente_preserva_descricao_fr002_fr004(self):
        for descricao in (
            "Preparar relatório", "  Rever seção 1  ", 'Aspas " | barra \\',
            "A\nB\tC\rD\x00E", "x" * 10000,
        ):
            with self.subTest(descricao=descricao[:40]):
                tarefa = Tarefa(1, descricao)
                self.assertEqual(tarefa.id, 1)
                self.assertEqual(tarefa.descricao, descricao)
                self.assertEqual(tarefa.status, "pendente")
                self.assertEqual(validar_descricao(descricao), descricao)

    def test_registros_validos_sem_restringir_id_ou_duplicatas_fr003_fr006(self):
        primeira = Tarefa(10**100, "Repetida", "concluida")
        segunda = Tarefa(1, "Repetida", "pendente")
        self.assertEqual(primeira.status, "concluida")
        self.assertEqual(primeira.descricao, segunda.descricao)
        self.assertEqual(primeira.id, 10**100)

    def test_ids_invalidos_inclusive_booleanos_fr003_fr009(self):
        for identificador in (True, False, 0, -1, 1.0, "1", None, []):
            with self.subTest(identificador=identificador):
                with self.assertRaises(ErroValidacao):
                    Tarefa(identificador, "Tarefa fictícia")

    def test_descricao_invalida_na_criacao_e_na_validacao_fr002_fr009(self):
        for descricao in (None, "", " \t\r\n", "\u2003", 1, True, [], {}):
            with self.subTest(descricao=descricao):
                with self.assertRaisesRegex(ErroValidacao, "descrição é obrigatória"):
                    Tarefa(1, descricao)
                with self.assertRaisesRegex(ErroValidacao, "descrição é obrigatória"):
                    validar_descricao(descricao)

    def test_status_desconhecidos_ou_tipos_invalidos_fr006_fr009(self):
        for status in ("concluída", "Pendente", "", None, 0, True, [], {}):
            with self.subTest(status=status):
                with self.assertRaises(ErroValidacao):
                    Tarefa(1, "Tarefa fictícia", status)
