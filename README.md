# ProjetoOFX

Aplicação Python que lê um extrato OFX, mostra cada movimentação e calcula
quantidade de lançamentos, entradas, saídas e saldo. Também pode importar os
lançamentos para uma tabela PostgreSQL no NeonDB.

## Requisitos

- Python 3.10 ou superior
- Banco NeonDB (para a importação)

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Ler o extrato

O arquivo `extrato.ofx` na pasta do projeto é usado por padrão:

```bash
python main.py
```

Para processar outro arquivo:

```bash
python main.py caminho/para/extrato.ofx
```

O resumo apresenta entradas, saídas positivas como total de despesas e o saldo
calculado pelas movimentações. Também compara esse saldo com o valor informado
no OFX, se disponível.

## Configurar o NeonDB

1. No painel do Neon, abra **Connect** e copie a connection string PostgreSQL
   (use a conexão pooled para a aplicação).
2. Copie `.env.example` para `.env`.
3. Substitua os valores de exemplo em `DATABASE_URL` pela URL real do NeonDB.
   Mantenha `sslmode=require`.

O `.env` está no `.gitignore`; não compartilhe nem envie esse arquivo ao Git.

## Criar a tabela e importar

Se desejar criar a tabela manualmente, execute o conteúdo de `schema.sql` no
SQL Editor do NeonDB. O programa também cria a tabela automaticamente quando
ela ainda não existe, usando exatamente estas colunas:

```sql
CREATE TABLE movimentacoes (
    id SERIAL PRIMARY KEY,
    data_movimentacao DATE,
    valor NUMERIC(15,2),
    descricao VARCHAR(255)
);
```

Execute a importação:

```bash
python main.py --salvar
```

O índice único em data, valor e descrição evita inserir novamente uma
movimentação idêntica ao importar o mesmo arquivo. Se já houver duplicatas
exatas na tabela, remova-as antes de criar o índice único. Como o formato
solicitado não tem a identificação original do lançamento OFX (`FITID`), dois
lançamentos legítimos com a mesma data, valor e descrição também serão tratados
como duplicados.

## Dados de demonstração

O arquivo OFX inclui quatro transações fictícias identificadas como
`EXEMPLO DEMONSTRACAO`, cuja soma líquida é zero. O saldo final informado no
OFX não coincide com a soma das transações; o programa preserva ambos os
valores e avisa sobre a diferença, sem ajustar dados automaticamente.
