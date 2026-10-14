"""Testes reais em schema temporário; nunca truncam tabelas do sistema."""
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import psycopg
from psycopg import sql
from operacoes.banco import Banco
from persistencia.postgres import RepositorioPostgres
from utilitarios.exceptions import SaldoInsuficienteError, ContaInexistenteError


@unittest.skipUnless(os.getenv('RUN_POSTGRES_TESTS') == '1', 'Defina RUN_POSTGRES_TESTS=1 e DB_* para testar PostgreSQL')
class TestPostgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = RepositorioPostgres()
        cls.schema = 'teste_' + uuid.uuid4().hex
        with cls.repo.conectar() as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(cls.schema)))
        cls.repo.config['options'] = '-c search_path=' + cls.schema
        cls.repo.inicializar()

    @classmethod
    def tearDownClass(cls):
        with cls.repo.conectar() as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(cls.schema)))

    def setUp(self):
        with self.repo.conectar() as conn:
            conn.execute('TRUNCATE movimentacoes, contas, clientes RESTART IDENTITY CASCADE')
        self.banco = Banco('Teste', self.repo)
        self.cliente = self.banco.adicionar_cliente('Cliente Teste', '12345678901')
        self.conta = self.banco.criar_conta(self.cliente, 'poupanca')
        self.numero = self.conta._numero

    def test_reconexao_preserva_saldo_historico_e_cliente(self):
        self.banco.depositar(self.numero, '120.50')
        self.banco.sacar(self.numero, '20.25')
        outro = Banco('Outra sessão', self.repo)
        conta = outro.buscar_conta(self.numero)
        self.assertEqual(conta.saldo, Decimal('100.25'))
        self.assertEqual(len(conta._historico), 2)
        self.assertEqual(outro.buscar_cliente(self.cliente.cpf).nome, self.cliente.nome)
        nova = outro.criar_conta(self.cliente, 'corrente')
        self.assertGreater(nova._numero, self.numero)

    def test_saque_recusado_nao_altera_banco(self):
        self.banco.depositar(self.numero, '10')
        with self.assertRaises(SaldoInsuficienteError):
            self.banco.sacar(self.numero, '11')
        conta = self.banco.buscar_conta(self.numero)
        self.assertEqual(conta.saldo, Decimal('10'))
        self.assertEqual(len(conta._historico), 1)

    def test_corrente_e_limite(self):
        corrente = self.banco.criar_conta(self.cliente, 'corrente')
        self.banco.sacar(corrente._numero, '500')
        with self.assertRaises(SaldoInsuficienteError):
            self.banco.sacar(corrente._numero, '0.01')
        self.assertEqual(self.banco.buscar_conta(corrente._numero).saldo, Decimal('-500'))

    def test_cpf_duplicado(self):
        with self.assertRaises(ValueError):
            self.banco.adicionar_cliente('Outra Pessoa', self.cliente.cpf)
        self.assertEqual(self.banco.buscar_cliente(self.cliente.cpf).nome, self.cliente.nome)

    def test_conta_inexistente(self):
        with self.assertRaises(ContaInexistenteError):
            self.banco.buscar_conta(999999)

    def test_depositos_concorrentes(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda _: self.banco.depositar(self.numero, '1.01'), range(20)))
        conta = self.banco.buscar_conta(self.numero)
        self.assertEqual(conta.saldo, Decimal('20.20'))
        self.assertEqual(len(conta._historico), 20)

    def test_rollback_se_historico_falhar(self):
        with self.repo.conectar() as conn:
            conn.execute('ALTER TABLE movimentacoes ADD CONSTRAINT rejeitar_teste CHECK (valor <> 13)')
        try:
            with self.assertRaises(psycopg.errors.CheckViolation):
                self.banco.depositar(self.numero, '13')
            conta = self.banco.buscar_conta(self.numero)
            self.assertEqual(conta.saldo, Decimal('0'))
            self.assertEqual(conta._historico, [])
        finally:
            with self.repo.conectar() as conn:
                conn.execute('ALTER TABLE movimentacoes DROP CONSTRAINT rejeitar_teste')

    def test_valor_invalido_e_tipo_invalido(self):
        for valor in ('-1', '0', 'nan', '1.001'):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                self.banco.depositar(self.numero, valor)
        with self.assertRaises(ValueError):
            self.banco.criar_conta(self.cliente, 'invalida')
        self.assertEqual(self.banco.buscar_conta(self.numero)._historico, [])
