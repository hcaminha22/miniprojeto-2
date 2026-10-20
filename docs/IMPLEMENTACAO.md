# Registro técnico — Mini-Projeto 2

## Contexto e objetivo

Evoluir o sistema bancário enviado em ZIP, que mantinha clientes, contas, saldos e histórico em memória. A versão atual preserva a interface de terminal e usa PostgreSQL para persistência, iniciado junto com a aplicação pelo Docker Compose.

## Mudanças

| Original | Versão atual |
|---|---|
| Dicionários em memória | Consultas e gravações PostgreSQL |
| Saldo `float` | `Decimal` e coluna `NUMERIC` |
| Contador de contas no processo | Identidade gerada pelo banco |
| Interface altera Conta diretamente | Interface chama operações persistentes de Banco |
| Histórico em lista | Tabela de movimentações recuperada no extrato |
| Sem containers | Dockerfile, Compose, variáveis e volume |

O polimorfismo permanece em `sacar()`: corrente permite saldo negativo até o limite; poupança limita o saque ao saldo. As entidades não executam SQL. O repositório carrega a entidade, aplica a regra e grava saldo e histórico na mesma transação. A interface informa sucesso após o retorno da operação persistente.

## Verificações realizadas em 20/10/2026

- `docker compose config --quiet`: configuração aceita pelo Docker Compose.
- `docker compose up -d --build`: imagem construída e serviços iniciados. O PostgreSQL 17 ficou `healthy` e a aplicação ficou `Up`.
- Fluxo pelo terminal: cliente e conta cadastrados; depósito de R$ 100,00; saque de R$ 20,00; extrato mostrou saldo de R$ 80,00 e as duas movimentações.
- Persistência: após `docker compose down` e nova inicialização do mesmo projeto, cliente, conta, saldo e histórico continuaram disponíveis.
- `docker compose -p m2-review-final run --rm -T -e RUN_POSTGRES_TESTS=1 app python -m unittest discover -v`: 16 testes passaram — 8 de regras e 8 de integração PostgreSQL.

O fluxo manual e a persistência foram verificados no projeto Compose isolado `m2-persist-check`. A suíte completa mais recente foi executada no projeto isolado `m2-review-final`. Ambos usaram volumes descartáveis, sem alterar o banco já existente do projeto; os ambientes isolados foram removidos após as verificações.

O resultado detalhado dos testes está em [`RESULTADO_TESTES.txt`](RESULTADO_TESTES.txt).

## Limitações conhecidas

- Não foram adicionados frontend, API, autenticação ou autorização.
- A validação de CPF aceita apenas dígitos ASCII, confere o formato e rejeita números repetidos, mas não calcula os dígitos verificadores.
- O schema é inicial e não há ferramenta de migração de banco.
- O extrato carrega o histórico completo da conta; para um volume maior, seria necessário paginar ou otimizar a leitura.
- A persistência foi confirmada em um volume novo e isolado. O volume pré-existente do usuário não foi alterado durante essa verificação.

## Preparação do ZIP

Inclua o código-fonte, `README.md`, `docs/`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `sql/`, `.env.example` e os demais arquivos de projeto. Não inclua `.env` (contém configuração local), `.git/`, `.venv/` nem `__pycache__/`.
