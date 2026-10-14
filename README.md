# Mini Projeto 2 — Sistema bancário com Docker Compose

Versão inicial da evolução do sistema enviado por Hiram. Preserva a interface de terminal, clientes, conta corrente com limite de R$ 500, conta poupança, depósitos, saques e extrato. Acrescenta persistência PostgreSQL e configuração de execução em dois serviços. Não possui interface web nem API.

**Status:** sete testes de regras aprovados. Oito testes de integração ignorados por falta de servidor PostgreSQL. Docker, comunicação entre containers e volume ainda precisam ser validados. Nenhum envio a repositório remoto foi realizado; o DoD continua pendente.

## Comece aqui — PowerShell

Pré-requisito: Docker Desktop em execução com containers Linux e Docker Compose v2. Extraia o ZIP e abra o terminal na pasta com `docker-compose.yml`.

```powershell
docker --version
docker compose version
Copy-Item .env.example .env
```

Edite `.env` e substitua a senha de exemplo por uma senha local. Não versione esse arquivo. O Compose usa `.env` para interpolar o YAML; `environment` injeta as variáveis em cada serviço.

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
docker compose attach app
```

A aplicação é interativa. Se o menu foi impresso antes da conexão ao terminal, pressione Enter para reapresentá-lo. Use a opção **4 — Sair** do menu principal para encerrar a aplicação. O banco permanece ativo. Para abrir outra sessão depois de sair:

```powershell
docker compose run --rm app
```

Não há endereço para abrir no navegador. A aplicação usa o terminal. O banco usa a rede interna do Compose: host `db`, porta 5432. Não é necessário publicar essa porta no computador.

## Estrutura

| Arquivo/pasta | Responsabilidade |
|---|---|
| `mini_projeto2.py` | Menus e interação com o usuário |
| `entidades/` | Cliente e regras de corrente/poupança |
| `operacoes/banco.py` | Coordenação das operações persistentes |
| `persistencia/postgres.py` | Conexões, consultas SQL e transações |
| `sql/schema.sql` | Tabelas e restrições iniciais |
| `utilitarios/` | Validações e exceções |
| `Dockerfile` | Imagem Python 3.12 e usuário sem privilégios |
| `docker-compose.yml` | Serviços, rede padrão, healthcheck e volume |
| `tests/` | Testes de regras e integração |
| `docs/` | Resultados confirmados e pendências |

O terminal chama `Banco`, que coordena o repositório e as entidades. As regras de saldo continuam nas subclasses de conta. **Para persistir, a interface chama `Banco.depositar()` e `Banco.sacar()`**. Modificar um objeto Conta isolado altera apenas esse objeto.

## Configuração e decisões

- `app`: imagem construída pelo Dockerfile; comando `python mini_projeto2.py`; `stdin_open` e `tty` para interação pelo terminal.
- `db`: imagem oficial `postgres:17`; healthcheck com `pg_isready`; `depends_on` com `service_healthy` para aguardar disponibilidade inicial.
- `dados_postgres`: volume nomeado em `/var/lib/postgresql/data`, caminho da imagem PostgreSQL 17. Não trocar a versão principal do PostgreSQL mantendo o volume sem planejar migração.
- `POSTGRES_*`: configura o banco na primeira inicialização de um volume vazio. Alterar a senha no `.env` depois disso não altera automaticamente a senha já existente no banco.
- `DB_*`: configura a conexão da aplicação. Usamos `db`, pois `localhost` dentro de um container aponta para ele próprio.
- A aplicação cria tabelas ausentes ao iniciar. `CREATE TABLE IF NOT EXISTS` não substitui migrações de schema.
- Valores usam `Decimal` no Python e `NUMERIC(17,2)` no banco. São rejeitados valores não finitos, fora do intervalo e frações menores que um centavo; depósitos e saques exigem valor positivo.
- Conexões curtas por operação. Saldo e movimentação são gravados em uma única transação. `FOR UPDATE` bloqueia a conta durante alterações; falhas provocam rollback. O funcionamento precisa ser confirmado com os testes reais do banco.
- O número da conta é gerado pelo PostgreSQL; não depende de contador em memória. Lacunas são normais.
- As datas do extrato usam UTC.
- A validação original de CPF verifica formato e repetição; não calcula dígitos verificadores. Autenticação, autorização e funcionalidades web não foram adicionadas. A configuração é para desenvolvimento local.
- O histórico completo é carregado em cada operação: escolha simples para este exercício, com possibilidade de otimização e paginação se o volume crescer.

## Testes

Testes de regras pelo container:

```powershell
docker compose run --rm -T app python -m unittest tests.test_contas -v
```

Suíte completa, incluindo PostgreSQL real:

```powershell
docker compose run --rm -T -e RUN_POSTGRES_TESTS=1 app python -m unittest discover -v
```

Os testes de integração criam um schema aleatório isolado das tabelas da aplicação e o removem ao final. Testam reconexão e recuperação de dados, sequência de contas, CPF duplicado, saldo insuficiente, limite, depósitos concorrentes e rollback quando a gravação do histórico falha. Exigem permissão para criar schema no banco local. Não executar contra dados corporativos ou produção.

Para rodar apenas as regras com Python local:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest tests.test_contas -v
```

## Teste manual de persistência

1. Inicie os serviços e acesse a aplicação.
2. Cadastre um cliente fictício, crie uma conta e anote o número.
3. Deposite R$ 100,00, saque R$ 20,00 e confirme saldo R$ 80,00 com duas movimentações.
4. Saia pelo menu e execute:

```powershell
docker compose down
docker compose up -d --build
docker compose attach app
```

5. Acesse a mesma conta. Confirme cliente, saldo R$ 80,00 e histórico anterior.
6. Crie outra conta e confirme que recebeu outro número.

`docker compose down` preserva o volume nomeado. **Não use `docker compose down -v` nesse teste: `-v` remove o volume e apaga os dados.** Reconectar ao banco comprova persistência entre sessões; recriar os containers é necessário para verificar o volume.

## Diagnóstico

```powershell
docker compose ps -a
docker compose logs --tail=100 db app
docker compose config --quiet
```

`config --quiet` valida a configuração sem imprimir variáveis resolvidas com senha. Ler YAML com um parser não comprova que o Compose aceita sua configuração.

Após sair pelo menu, `Exited (0)` é esperado para a aplicação. Para problemas de conexão, confira o serviço `db`, o healthcheck e `.env`. Depois de uma falha de comunicação durante uma operação, consulte saldo e extrato antes de repetir: a confirmação do commit pode ter sido perdida.

Para abrir o `psql` no serviço de banco, pelo PowerShell:

```powershell
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Consultas no `psql`:

```sql
SELECT numero, tipo, saldo FROM contas ORDER BY numero;
SELECT conta_numero, tipo, valor, saldo_apos FROM movimentacoes ORDER BY id;
```

Digite `\q` para sair.

## Versionamento

Use o repositório autorizado para a atividade e o fluxo da equipe. Se já existe, trabalhe nele. Para uma pasta nova, sem repositório:

```powershell
git init
git status --short
git add .
git diff --cached --stat
git commit -m "Adiciona persistencia PostgreSQL e configuracao Docker Compose"
```

Antes do commit, confira que `.env`, caches e dados não foram incluídos. Não execute `git init` dentro de outro repositório. Remoto, branch e envio dependem do fluxo da equipe. O ZIP não inclui histórico Git nem credenciais reais.

## Referências oficiais

- https://docs.docker.com/compose/how-tos/startup-order/
- https://docs.docker.com/reference/compose-file/services/
- https://www.psycopg.org/psycopg3/docs/basic/transactions.html
- https://hub.docker.com/_/postgres
