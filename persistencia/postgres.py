"""SQL parametrizado, conexão curta por operação e transações atômicas."""
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from entidades.cliente import Cliente
from entidades.conta import ContaCorrente, ContaPoupanca, dinheiro
from utilitarios.exceptions import ContaInexistenteError


class RepositorioPostgres:
    def __init__(self):
        obrigatorias = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
        if any(not os.environ.get(chave) for chave in obrigatorias):
            raise ValueError("Configure DB_HOST, DB_NAME, DB_USER e DB_PASSWORD.")
        self.config = dict(host=os.environ["DB_HOST"], port=os.getenv("DB_PORT", "5432"),
                           dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
                           password=os.environ["DB_PASSWORD"], connect_timeout=5,
                           row_factory=dict_row)

    def conectar(self):
        return psycopg.connect(**self.config)

    def inicializar(self):
        schema = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
        with self.conectar() as conn:
            conn.execute(schema.read_text(encoding="utf-8"))

    @staticmethod
    def _cliente(row):
        return Cliente(row["nome"], row["cpf"]) if row else None

    def buscar_cliente(self, cpf):
        with self.conectar() as conn:
            row = conn.execute("SELECT nome, cpf FROM clientes WHERE cpf = %s", (cpf,)).fetchone()
        return self._cliente(row)

    def adicionar_cliente(self, nome, cpf):
        with self.conectar() as conn:
            row = conn.execute(
                "INSERT INTO clientes (nome, cpf) VALUES (%s, %s) "
                "ON CONFLICT (cpf) DO NOTHING RETURNING nome, cpf", (nome, cpf)).fetchone()
            if not row:
                raise ValueError("Cliente com este CPF já cadastrado.")
        return self._cliente(row)

    def criar_conta(self, cliente, tipo):
        tipo = tipo.strip().lower()
        if tipo not in ("corrente", "poupanca"):
            raise ValueError("Escolha 'corrente' ou 'poupanca'.")
        with self.conectar() as conn:
            row = conn.execute(
                "INSERT INTO contas (cliente_cpf, tipo, limite) VALUES (%s, %s, %s) RETURNING numero",
                (cliente.cpf, tipo, dinheiro(500 if tipo == "corrente" else 0))).fetchone()
            return self._carregar_conta(conn, row["numero"])

    def _carregar_conta(self, conn, numero, bloquear=False):
        sql = ("SELECT c.*, cl.nome FROM contas c JOIN clientes cl ON cl.cpf = c.cliente_cpf "
               "WHERE c.numero = %s")
        if bloquear:
            sql += " FOR UPDATE OF c"
        row = conn.execute(sql, (numero,)).fetchone()
        if not row:
            raise ContaInexistenteError(numero)
        historico = []
        for mov in conn.execute(
            "SELECT tipo, valor, criado_em FROM movimentacoes WHERE conta_numero = %s ORDER BY id",
            (numero,)).fetchall():
            rotulo = "Depósito" if mov["tipo"] == "deposito" else "Saque"
            historico.append((mov["criado_em"], f"{rotulo} de R${mov['valor']:.2f}"))
        cliente = Cliente(row["nome"], row["cliente_cpf"])
        if row["tipo"] == "corrente":
            conta = ContaCorrente(numero, cliente, row["limite"], row["saldo"], historico)
        else:
            conta = ContaPoupanca(numero, cliente, row["saldo"], historico)
        cliente.adicionar_conta(conta)
        return conta

    def buscar_conta(self, numero):
        with self.conectar() as conn:
            # Uma única visão consistente de saldo e histórico durante a leitura.
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            return self._carregar_conta(conn, numero)

    def movimentar(self, numero, tipo, valor):
        if tipo not in ("deposito", "saque"):
            raise ValueError("Operação desconhecida.")
        valor = dinheiro(valor)
        with self.conectar() as conn:
            # Serializa alterações da mesma conta para evitar perda de atualização.
            conta = self._carregar_conta(conn, numero, bloquear=True)
            if tipo == "deposito":
                conta.depositar(valor)
            else:
                conta.sacar(valor)
            conn.execute("UPDATE contas SET saldo = %s WHERE numero = %s", (conta.saldo, numero))
            conn.execute(
                "INSERT INTO movimentacoes (conta_numero, tipo, valor, saldo_apos) VALUES (%s, %s, %s, %s)",
                (numero, tipo, valor, conta.saldo))
        # Sucesso só é informado depois do commit.
        return conta
