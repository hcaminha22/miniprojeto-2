"""Interface de terminal; as operações persistentes passam pelo Banco."""

import psycopg
from operacoes.banco import Banco
from utilitarios.exceptions import ContaInexistenteError, SaldoInsuficienteError
from utilitarios.validacoes import (
    solicitar_cpf,
    solicitar_nome,
    solicitar_numero_conta,
    solicitar_valor,
)


def menu_conta(banco):
    numero = solicitar_numero_conta()
    while True:
        conta = banco.buscar_conta(numero)
        print(f"\n--- Conta Nº {numero} ---")
        print(f"Cliente: {conta._cliente.nome} | Saldo: R${conta.saldo:.2f}")
        print("1. Depositar\n2. Sacar\n3. Ver Extrato\n4. Voltar")
        opcao = input("Escolha uma opção: ").strip()
        try:
            if opcao == "1":
                banco.depositar(numero, solicitar_valor("Valor do depósito: "))
                print("Depósito realizado com sucesso.")
            elif opcao == "2":
                banco.sacar(numero, solicitar_valor("Valor do saque: "))
                print("Saque realizado com sucesso.")
            elif opcao == "3":
                conta.extrato()
            elif opcao == "4":
                return
            else:
                print("Opção inválida.")
        except (ValueError, SaldoInsuficienteError) as erro:
            print(f"Erro: {erro}")


def main():
    try:
        banco = Banco("Banco Digital")
    except ValueError as erro:
        print(f"Configuração inválida: {erro}")
        return 1
    except psycopg.Error:
        print(
            "Não foi possível inicializar o banco. Confira o serviço e as variáveis DB_*."
        )
        return 1
    while True:
        print("\n--- Sistema Bancário Digital ---")
        print("1. Adicionar Cliente\n2. Criar Conta\n3. Acessar Conta\n4. Sair")
        try:
            opcao = input("Escolha uma opção: ").strip()
            if opcao == "1":
                nome = solicitar_nome()
                cpf = solicitar_cpf()
                cliente = banco.adicionar_cliente(nome, cpf)
                print(f"Cliente {cliente.nome} adicionado com sucesso!")
            elif opcao == "2":
                cliente = banco.buscar_cliente(solicitar_cpf("CPF do cliente: "))
                if not cliente:
                    print("Cliente não encontrado. Cadastre o cliente primeiro.")
                    continue
                conta = banco.criar_conta(cliente, input("Tipo (corrente/poupanca): "))
                print(f"Conta nº {conta._numero} criada para {cliente.nome}.")
            elif opcao == "3":
                menu_conta(banco)
            elif opcao == "4":
                print("Obrigado por usar o nosso sistema. Até logo!")
                return 0
            else:
                print("Opção inválida.")
        except (ValueError, ContaInexistenteError, SaldoInsuficienteError) as erro:
            print(f"Erro: {erro}")
        except psycopg.Error:
            print(
                "Falha no acesso ao banco. Consulte saldo e extrato antes de repetir a operação."
            )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print("\nSessão encerrada.")
