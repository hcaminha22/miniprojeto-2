import unittest
from decimal import Decimal
from entidades.cliente import Cliente
from entidades.conta import ContaCorrente, ContaPoupanca, dinheiro
from utilitarios.exceptions import SaldoInsuficienteError
from utilitarios.validacoes import solicitar_valor
from unittest.mock import patch


class TestContas(unittest.TestCase):
    def setUp(self):
        self.cliente = Cliente('Cliente Teste', '12345678901')

    def test_decimal_sem_erro_binario(self):
        conta = ContaPoupanca(1, self.cliente)
        conta.depositar('0.10')
        conta.depositar('0.20')
        self.assertEqual(conta.saldo, Decimal('0.30'))

    def test_saque_corrente_utiliza_limite(self):
        conta = ContaCorrente(1, self.cliente)
        conta.sacar('500.00')
        self.assertEqual(conta.saldo, Decimal('-500.00'))
        with self.assertRaises(SaldoInsuficienteError):
            conta.sacar('0.01')
        self.assertEqual(len(conta._historico), 1)

    def test_poupanca_nao_utiliza_limite(self):
        conta = ContaPoupanca(1, self.cliente)
        conta.depositar('100.00')
        with self.assertRaises(SaldoInsuficienteError):
            conta.sacar('100.01')
        self.assertEqual(conta.saldo, Decimal('100.00'))
        self.assertEqual(len(conta._historico), 1)

    def test_saque_integral(self):
        conta = ContaPoupanca(1, self.cliente)
        conta.depositar('50')
        conta.sacar('50')
        self.assertEqual(conta.saldo, Decimal('0.00'))

    def test_valores_invalidos_nao_alteram_conta(self):
        conta = ContaCorrente(1, self.cliente)
        for valor in ('0', '-1', 'nan', 'inf', '-inf', '1.001', 'abc', '1e1000000'):
            for operacao in (conta.depositar, conta.sacar):
                with self.subTest(valor=valor, operacao=operacao.__name__):
                    with self.assertRaises(ValueError):
                        operacao(valor)
        self.assertEqual(conta.saldo, Decimal('0.00'))
        self.assertEqual(conta._historico, [])

    def test_entrada_com_virgula(self):
        with patch('builtins.input', return_value='10,25'):
            self.assertEqual(solicitar_valor('Valor: '), Decimal('10.25'))

    def test_estouro_nao_altera_saldo(self):
        conta = ContaPoupanca(1, self.cliente, saldo='999999999999999.99')
        with self.assertRaises(ValueError):
            conta.depositar('0.01')
        self.assertEqual(conta.saldo, dinheiro('999999999999999.99'))
        self.assertEqual(conta._historico, [])
