import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

from ofxparse import OfxParser


@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Decimal
    description: str


def read_statement(file_path: Path) -> tuple[list[Transaction], Decimal | None]:
    with file_path.open("rb") as statement_file:
        statement = OfxParser.parse(statement_file).account.statement

    transactions = [
        Transaction(
            date=transaction.date.date(),
            amount=transaction.amount,
            description=(transaction.memo or "").strip() or "(sem descrição)",
        )
        for transaction in statement.transactions
    ]
    return transactions, statement.balance


def format_currency(amount: Decimal) -> str:
    formatted = f"{amount:,.2f}"
    return f"R$ {formatted.replace(',', '_').replace('.', ',').replace('_', '.')}"


def print_statement(
    transactions: list[Transaction], reported_balance: Decimal | None
) -> None:
    total_entries = sum(
        (transaction.amount for transaction in transactions if transaction.amount > 0),
        Decimal("0"),
    )
    total_outflows = sum(
        (-transaction.amount for transaction in transactions if transaction.amount < 0),
        Decimal("0"),
    )
    calculated_balance = total_entries - total_outflows

    print("EXTRATO BANCÁRIO")
    print("=" * 72)
    for transaction in transactions:
        print(
            f"Data: {transaction.date:%d/%m/%Y} | "
            f"Valor: {format_currency(transaction.amount)} | "
            f"Descrição: {transaction.description}"
        )

    print("=" * 72)
    print(f"Quantidade de movimentações: {len(transactions)}")
    print(f"Total de entradas: {format_currency(total_entries)}")
    print(f"Total de saídas: {format_currency(total_outflows)}")
    print(f"Saldo calculado: {format_currency(calculated_balance)}")
    if reported_balance is not None:
        print(f"Saldo informado no OFX: {format_currency(reported_balance)}")
        if calculated_balance != reported_balance:
            difference = reported_balance - calculated_balance
            print(
                "ATENÇÃO: o saldo informado no OFX difere do saldo calculado "
                f"pelas movimentações em {format_currency(difference)}."
            )


def save_transactions(transactions: list[Transaction]) -> tuple[int, int]:
    try:
        psycopg2: Any = import_module("psycopg2")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Driver PostgreSQL ausente. Instale as dependências com "
            "'pip install -r requirements.txt'."
        ) from error

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        connection = psycopg2.connect(database_url)
    else:
        database_name = os.getenv("PGDATABASE")
        user = os.getenv("PGUSER")
        if not database_name or not user:
            raise ValueError(
                "Configure DATABASE_URL ou as variáveis PGDATABASE e PGUSER "
                "para salvar no PostgreSQL."
            )
        connection = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            dbname=database_name,
            user=user,
            password=os.getenv("PGPASSWORD", ""),
        )

    inserted = 0
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS movimentacoes (
                        id SERIAL PRIMARY KEY,
                        data_movimentacao DATE NOT NULL,
                        valor NUMERIC(15, 2) NOT NULL,
                        descricao VARCHAR(255) NOT NULL
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
                for transaction in transactions:
                    if len(transaction.description) > 255:
                        raise ValueError(
                            "Descrição excede o limite de 255 caracteres "
                            f"na movimentação de {transaction.date:%d/%m/%Y}."
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
                            transaction.date,
                            transaction.amount,
                            transaction.description,
                        ),
                    )
                    inserted += cursor.rowcount
    finally:
        connection.close()

    return inserted, len(transactions) - inserted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lê um extrato OFX, calcula o resumo e, opcionalmente, "
        "grava as movimentações no PostgreSQL."
    )
    parser.add_argument(
        "arquivo",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("extrato.ofx"),
        help="caminho do arquivo OFX (padrão: extrato.ofx ao lado do script)",
    )
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="salva as movimentações no PostgreSQL",
    )
    args = parser.parse_args()

    try:
        transactions, reported_balance = read_statement(args.arquivo)
        print_statement(transactions, reported_balance)
        if args.postgres:
            inserted, duplicates = save_transactions(transactions)
            print(
                f"\nPostgreSQL: {inserted} movimentação(ões) inserida(s); "
                f"{duplicates} duplicada(s) ignorada(s)."
            )
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
