from persistencia.postgres import RepositorioPostgres


class Banco:
    def __init__(self, nome, repositorio=None):
        self.nome = nome
        self.repositorio = repositorio if repositorio is not None else RepositorioPostgres()
        self.repositorio.inicializar()

    def adicionar_cliente(self, nome, cpf):
        return self.repositorio.adicionar_cliente(nome, cpf)

    def buscar_cliente(self, cpf):
        return self.repositorio.buscar_cliente(cpf)

    def criar_conta(self, cliente, tipo):
        return self.repositorio.criar_conta(cliente, tipo)

    def buscar_conta(self, numero_conta):
        return self.repositorio.buscar_conta(numero_conta)

    def depositar(self, numero_conta, valor):
        return self.repositorio.movimentar(numero_conta, "deposito", valor)

    def sacar(self, numero_conta, valor):
        return self.repositorio.movimentar(numero_conta, "saque", valor)
