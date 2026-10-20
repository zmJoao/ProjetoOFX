import os
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Protocol

import psycopg2


class Movimento(Protocol):
    date: date
    amount: Decimal
    description: str


def salvar_movimentacoes(movimentacoes: Iterable[Movimento]) -> tuple[int, int]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL não configurada. Copie .env.example para .env "
            "e informe a URL de conexão do NeonDB."
        )

    connection = psycopg2.connect(
        database_url,
        sslmode=os.getenv("PGSSLMODE", "require"),
    )
    inseridas = 0
    duplicadas = 0
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS movimentacoes (
                        id SERIAL PRIMARY KEY,
                        data_movimentacao DATE,
                        valor NUMERIC(15,2),
                        descricao VARCHAR(255)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                        uq_movimentacoes_data_valor_descricao
                    ON movimentacoes (data_movimentacao, valor, descricao)
                    """
                )

                for movimento in movimentacoes:
                    if len(movimento.description) > 255:
                        raise ValueError(
                            "Descrição com mais de 255 caracteres na "
                            f"movimentação de {movimento.date:%d/%m/%Y}."
                        )
                    cursor.execute(
                        """
                        INSERT INTO movimentacoes
                            (data_movimentacao, valor, descricao)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (data_movimentacao, valor, descricao)
                        DO NOTHING
                        """,
                        (
                            movimento.date,
                            movimento.amount,
                            movimento.description,
                        ),
                    )
                    if cursor.rowcount:
                        inseridas += 1
                    else:
                        duplicadas += 1
    finally:
        connection.close()

    return inseridas, duplicadas
