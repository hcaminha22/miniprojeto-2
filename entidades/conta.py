"""Regras de conta; o serviço Banco coordena a persistência."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from utilitarios.exceptions import SaldoInsuficienteError


def dinheiro(valor):
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
        if not numero.is_finite() or numero.copy_abs() >= Decimal("1000000000000000"):
            raise ValueError("Valor fora do intervalo permitido.")
        centavos = numero.quantize(Decimal("0.01"))
        if numero != centavos:
            raise ValueError("Informe no máximo duas casas decimais.")
        return centavos
    except (InvalidOperation, TypeError):
        raise ValueError("Informe um valor monetário válido.") from None


class Conta(ABC):
    def __init__(self, numero, cliente, saldo="0.00", historico=None):
        self._numero = numero
        self._cliente = cliente
        self._saldo = dinheiro(saldo)
        self._historico = list(historico or [])

    @property
    def saldo(self):
        return self._saldo

    @staticmethod
    def validar_valor(valor):
        valor = dinheiro(valor)
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return valor

    def depositar(self, valor):
        valor = self.validar_valor(valor)
        self._saldo = dinheiro(self._saldo + valor)
        self._historico.append((datetime.now(timezone.utc), f"Depósito de R${valor:.2f}"))

    @abstractmethod
    def sacar(self, valor):
        pass

    def _registrar_saque(self, valor):
        self._saldo = dinheiro(self._saldo - valor)
        self._historico.append((datetime.now(timezone.utc), f"Saque de R${valor:.2f}"))

    def extrato(self):
        print(f"\n--- Extrato da Conta Nº {self._numero} ---")
        print(f"Cliente: {self._cliente.nome}")
        print(f"Saldo atual: R${self.saldo:.2f}")
        print("Histórico de transações (UTC):")
        if not self._historico:
            print("Nenhuma transação registrada.")
        for data, descricao in self._historico:
            print(f"- {data.strftime('%d/%m/%Y %H:%M:%S')}: {descricao}")


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite="500.00", saldo="0.00", historico=None):
        super().__init__(numero, cliente, saldo, historico)
        self.limite = dinheiro(limite)

    def sacar(self, valor):
        valor = self.validar_valor(valor)
        disponivel = self.saldo + self.limite
        if valor > disponivel:
            raise SaldoInsuficienteError(disponivel, valor, "Saldo e limite insuficientes.")
        self._registrar_saque(valor)


class ContaPoupanca(Conta):
    def sacar(self, valor):
        valor = self.validar_valor(valor)
        if valor > self.saldo:
            raise SaldoInsuficienteError(self.saldo, valor)
        self._registrar_saque(valor)
