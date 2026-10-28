# Mini-Projeto 2 — Sistema bancário

Aplicação bancária de terminal feita em Python. Permite cadastrar clientes, criar contas correntes e poupanças, depositar, sacar e consultar extratos. O PostgreSQL guarda os dados entre execuções; o Docker Compose inicia a aplicação e o banco juntos.

> **Verificado em 20/10/2026:** os 16 testes passaram, incluindo os oito testes de integração com PostgreSQL. A imagem Docker foi construída, o serviço `db` ficou saudável e foi confirmado pelo menu que cliente, saldo e extrato continuam disponíveis após recriar os containers. Os testes manuais usaram um projeto Compose isolado e descartável. Consulte [`docs/IMPLEMENTACAO.md`](docs/IMPLEMENTACAO.md) e [`docs/RESULTADO_TESTES.txt`](docs/RESULTADO_TESTES.txt) para os detalhes.

## Iniciar no Windows

Você precisa do Docker Desktop em execução, configurado para containers Linux, e do Docker Compose v2. Abra o PowerShell na pasta do projeto, onde está `docker-compose.yml`.

### 1. Preparar a configuração

Crie o arquivo local `.env` a partir do exemplo:

```powershell
Copy-Item .env.example .env
```

Abra `.env` e troque `POSTGRES_PASSWORD` por uma senha local. Esse arquivo contém configuração privada: não o envie ao Git.

### 2. Iniciar os serviços

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

`config --quiet` verifica a configuração do Compose sem imprimir os valores das variáveis. O comando `up` constrói a imagem da aplicação e inicia os serviços `db` (PostgreSQL) e `app` (terminal Python). O serviço `app` aguarda o banco ficar saudável.

### 3. Usar o programa

Conecte o terminal à aplicação:

```powershell
docker compose attach app
```

No menu, escolha uma opção para cadastrar cliente, criar conta ou acessar uma conta. Dentro de uma conta, você pode depositar, sacar ou consultar o extrato. Use **4 — Sair** no menu principal para encerrar a aplicação. Se o menu não aparecer ao conectar, pressione Enter.

Para iniciar outra sessão depois de sair:

```powershell
docker compose run --rm app
```

Não há uma página web para abrir no navegador: a interface é o terminal.

## Como o código está organizado

| Caminho | Responsabilidade |
|---|---|
| `mini_projeto2.py` | Menus, entradas e mensagens do terminal |
| `entidades/cliente.py` | Dados do cliente |
| `entidades/conta.py` | Saldo, depósitos, extrato e regras de saque |
| `operacoes/banco.py` | Encaminha as operações entre a interface e a persistência |
| `persistencia/postgres.py` | Conexões, consultas SQL e transações PostgreSQL |
| `sql/schema.sql` | Tabelas e restrições do banco |
| `utilitarios/` | Validações de entrada e exceções da aplicação |
| `tests/` | Testes das regras e testes de integração com PostgreSQL |
| `Dockerfile` | Imagem da aplicação Python |
| `docker-compose.yml` | Serviços da aplicação e do banco |
| `docs/` | Registro de implementação e resultados de verificações |

### Fluxo de uma operação

O menu chama a camada `Banco`; ela encaminha o pedido ao repositório PostgreSQL. Para um depósito ou saque, o repositório carrega a conta, aplica a regra da entidade e grava o novo saldo e a movimentação na mesma transação. Assim, uma falha durante a gravação desfaz as alterações da operação.

Use `Banco.depositar()` e `Banco.sacar()` para operações que precisam ser salvas. Alterar diretamente um objeto `Conta` muda apenas esse objeto em memória; não atualiza o banco.

### Regras das contas

- **Conta corrente:** permite saldo negativo até o limite de R$ 500,00.
- **Conta poupança:** não permite saque acima do saldo disponível.
- Depósitos e saques precisam ser maiores que zero. Os valores usam `Decimal` no Python e `NUMERIC(17,2)` no PostgreSQL para representar centavos sem a imprecisão de `float`.
- O PostgreSQL gera o número da conta. Lacunas na sequência são normais.
- O extrato mostra as movimentações em UTC.

## Banco de dados e configuração

O Compose cria dois serviços na rede interna do projeto:

- `db` executa PostgreSQL 17 e guarda os dados no volume Docker `dados_postgres`.
- `app` conecta ao serviço `db` pela porta 5432. Dentro de um container, `localhost` apontaria para o próprio container, por isso a aplicação usa `db` como host.

As variáveis `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` configuram o PostgreSQL na primeira inicialização do volume. As variáveis `DB_*` configuram a conexão usada pelo Python e são preenchidas pelo Compose a partir dessas mesmas opções. Se você mudar a senha no `.env` depois que o volume já foi criado, a senha gravada no banco não muda automaticamente.

Ao iniciar, a aplicação executa `sql/schema.sql` para criar tabelas que ainda não existem. Esse mecanismo não substitui migrações quando o formato das tabelas precisar mudar.

O volume mantém os dados mesmo quando os containers são removidos com `docker compose down`. Para apagar também os dados, seria necessário remover o volume; evite isso se quiser preservar o banco. A imagem PostgreSQL está fixada na versão principal 17: mudar a versão principal com o mesmo volume requer planejar uma migração.

## Verificar persistência manualmente

1. Inicie os serviços e conecte-se à aplicação.
2. Cadastre um cliente fictício, crie uma conta e anote o número.
3. Deposite R$ 100,00 e saque R$ 20,00. Confira saldo de R$ 80,00 e duas movimentações.
4. Saia pelo menu e recrie os containers:

   ```powershell
   docker compose down
   docker compose up -d --build
   docker compose attach app
   ```

5. Consulte a mesma conta e confirme o saldo e o histórico. Crie outra conta e confira que ela recebeu outro número.

`docker compose down` mantém o volume. **Não use `docker compose down -v` neste procedimento**, pois `-v` remove o volume e os dados nele armazenados.

## Testes

Para executar os testes das regras dentro do container:

```powershell
docker compose run --rm -T app python -m unittest tests.test_contas -v
```

Para executar a suíte completa, incluindo os testes de integração com PostgreSQL:

```powershell
docker compose run --rm -T -e RUN_POSTGRES_TESTS=1 app python -m unittest discover -v
```

Os testes de integração criam e removem um schema isolado. Eles verificam reconexão e recuperação de dados, números de conta, CPF duplicado, saldo insuficiente, limite, depósitos concorrentes e rollback quando a gravação do histórico falha. O usuário do banco precisa poder criar schemas. **Não execute esses testes contra dados corporativos ou de produção.**

Também é possível rodar apenas os testes das regras com Python instalado localmente:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest tests.test_contas -v
```

## Diagnóstico

Veja o estado dos containers e os logs:

```powershell
docker compose ps -a
docker compose logs --tail=100 db app
docker compose config --quiet
```

Se a aplicação aparece como `Exited (0)` depois de escolher **Sair**, ela encerrou normalmente. Se não conectar ao banco, confira se `db` está saudável e se o `.env` está preenchido.

Se houver falha de comunicação durante um depósito ou saque, consulte primeiro o saldo e o extrato antes de repetir a operação: a confirmação da gravação pode ter se perdido mesmo que a transação tenha sido concluída.

Para abrir o console PostgreSQL (`psql`):

```powershell
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Exemplos de consulta:

```sql
SELECT numero, tipo, saldo FROM contas ORDER BY numero;
SELECT conta_numero, tipo, valor, saldo_apos FROM movimentacoes ORDER BY id;
```

Digite `\q` para sair do `psql`.

## Limitações conhecidas

- A validação do CPF aceita dígitos ASCII, confere o formato e rejeita números repetidos, mas não verifica os dígitos verificadores.
- O projeto não tem autenticação, autorização, API nem interface web; foi preparado para desenvolvimento local.
- O extrato carrega o histórico completo da conta em cada consulta. Para um volume maior, seria necessário paginar ou otimizar essa leitura.
- A persistência foi verificada em um volume novo e isolado; o volume pré-existente do usuário não foi alterado durante os testes.

## Git e envio do projeto

O código está publicado no repositório privado [hcaminha22/miniprojeto-2](https://github.com/hcaminha22/miniprojeto-2).

- `main` contém a versão estável do projeto.
- `develop` é a branch de integração para as próximas alterações.
- Para uma nova tarefa, crie uma branch `feat/<descricao>` ou `fix/<descricao>` a partir de `develop`, faça commits com mensagens claras e envie a branch ao GitHub. Depois da revisão, integre-a em `develop`; quando a versão estiver pronta, promova-a para `main`.
- `.gitignore` exclui `.env`, ambientes virtuais e caches Python. Mantenha senhas e configurações locais fora dos commits.

Para obter o projeto e trabalhar na branch de integração:

```powershell
git clone https://github.com/hcaminha22/miniprojeto-2.git
cd miniprojeto-2
git switch develop
```

## Referências

- [Docker Compose: controlar a ordem de inicialização](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker Compose: referência de serviços](https://docs.docker.com/reference/compose-file/services/)
- [Psycopg: transações](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)
- [Imagem oficial do PostgreSQL](https://hub.docker.com/_/postgres)
