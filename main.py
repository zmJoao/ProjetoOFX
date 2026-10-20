import argparse
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from ofxparse import OfxParser
from psycopg2 import Error as PostgreSQLError


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


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Lê um extrato OFX, calcula o resumo e, opcionalmente, "
        "salva as movimentações no NeonDB."
    )
    parser.add_argument(
        "arquivo",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("extrato.ofx"),
        help="arquivo OFX (padrão: extrato.ofx ao lado do script)",
    )
    parser.add_argument(
        "--salvar",
        action="store_true",
        help="grava as movimentações no banco configurado em DATABASE_URL",
    )
    args = parser.parse_args()

    try:
        transactions, reported_balance = read_statement(args.arquivo)
        print_statement(transactions, reported_balance)
        if args.salvar:
            from api_banco import salvar_movimentacoes

            inseridas, duplicadas = salvar_movimentacoes(transactions)
            print(
                f"\nNeonDB: {inseridas} movimentação(ões) inserida(s); "
                f"{duplicadas} duplicada(s) ignorada(s)."
            )
    except (OSError, ValueError, RuntimeError, PostgreSQLError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
