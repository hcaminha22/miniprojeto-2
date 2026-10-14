CREATE TABLE IF NOT EXISTS clientes (
    cpf VARCHAR(11) PRIMARY KEY CHECK (cpf ~ '^[0-9]{11}$'),
    nome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contas (
    numero BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_cpf VARCHAR(11) NOT NULL REFERENCES clientes(cpf),
    tipo TEXT NOT NULL CHECK (tipo IN ('corrente', 'poupanca')),
    saldo NUMERIC(17,2) NOT NULL DEFAULT 0,
    limite NUMERIC(17,2) NOT NULL DEFAULT 0 CHECK (limite >= 0),
    CHECK ((tipo = 'poupanca' AND limite = 0 AND saldo >= 0)
        OR (tipo = 'corrente' AND saldo >= -limite))
);
CREATE TABLE IF NOT EXISTS movimentacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conta_numero BIGINT NOT NULL REFERENCES contas(numero),
    tipo TEXT NOT NULL CHECK (tipo IN ('deposito', 'saque')),
    valor NUMERIC(17,2) NOT NULL CHECK (valor > 0),
    saldo_apos NUMERIC(17,2) NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_conta ON movimentacoes(conta_numero, id);
