# Projeto OFX - Professor Max - Aula do Dia 19-10-2026

O projeto consiste em uma api em python que pega os dados de um arquivo .ofx e transfere eles para um banco de dados Postgres no NeonDB.

Em cima disso, foi feito uma simples interface usando o React, rodando pelo navegador, para iniciar o projeto:

1 - em (/backend/.env), coloque as informacoes do banco de dados do NEonDB

2 - Inicie a API colocando esse comando em um terminal:

[
    cd backend
    .venv/bin/python api.py
]

3 - Em outro terminal, inicie o App React:

[
    npm run start
]

Feito isso, você deve conseguir acessar o app pela porta indicada