# Registro técnico — versão inicial

## Contexto e objetivo

Evoluir o sistema bancário enviado em ZIP, que mantinha clientes, contas, saldos e histórico em memória. Preservar a interface de terminal e acrescentar PostgreSQL em serviço separado, com Docker Compose.

## Mudanças

| Original | Versão preparada |
|---|---|
| Dicionários em memória | Consultas e gravações PostgreSQL |
| Saldo `float` | `Decimal` e coluna `NUMERIC` |
| Contador de contas no processo | Identidade gerada pelo banco |
| Interface altera Conta diretamente | Interface chama operações persistentes de Banco |
| Histórico em lista | Tabela de movimentações recuperada no extrato |
| Sem containers | Dockerfile, Compose, variáveis e volume |

O polimorfismo permanece em `sacar()`: corrente permite saldo negativo até o limite; poupança limita o saque ao saldo. As entidades não executam SQL. O repositório carrega a entidade, aplica a regra e grava saldo e histórico na mesma transação. A interface informa sucesso após o retorno da operação persistente.

## Verificações efetivamente realizadas

- Python 3.12.14.
- Psycopg e psycopg-binary 3.2.10 instalados; importações verificadas.
- `python -m compileall -q .`: sem erros de sintaxe.
- YAML lido por PyYAML 6.0.3 sem erro; **não equivale** à validação pelo Compose.
- Sete testes de regras aprovados: precisão decimal, vírgula na entrada, limite de corrente, saldo insuficiente em poupança, saque integral, valores inválidos e estouro monetário.
- Oito testes de integração incluídos, mas **ignorados** por falta de servidor PostgreSQL disponível.
- Docker indisponível: imagem, Compose, healthcheck e volume **não foram executados nem validados**.

Saída real da suíte em `RESULTADO_TESTES.txt`.

## Pendências de conclusão

- [ ] Validar `docker compose config --quiet` com `.env` local preenchido.
- [ ] Construir a imagem e iniciar os serviços no Docker Desktop.
- [ ] Confirmar `db` saudável e acesso ao terminal.
- [ ] Executar os oito testes de integração PostgreSQL.
- [ ] Validar manualmente cadastro, criação de contas, depósitos, saques e extrato.
- [ ] Recriar os containers preservando o volume e confirmar os registros.
- [ ] Registrar evidências reais.
- [ ] Revisar as mudanças com Hiram e explicar o fluxo de execução.
- [ ] Versionar código e documentação no repositório autorizado.

## Limitações

Não foram adicionados frontend, API, autenticação nem validação completa de CPF. As validações originais de nome e CPF ficam no terminal; chamadas diretas ao serviço não equivalem a uma API com validação de payload. O schema é inicial, sem ferramenta de migração. Não há evidência de execução com PostgreSQL 17 nem com containers nesta versão. A tarefa permanece em andamento.
