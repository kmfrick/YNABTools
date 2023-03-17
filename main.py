import csv
import sys
import os
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import argparse


@dataclass
class N26Transaction:
    date: datetime
    recipient: str
    account_number: str
    transaction_type: str
    reference: str
    amount: float
    amount_foreign_currency: Optional[float]
    foreign_currency: str
    exchange_rate: Optional[float]

    def is_fx_transaction(self) -> bool:
        return bool(self.foreign_currency) and self.foreign_currency.lower() != "eur"


@dataclass
class YNABTransaction:
    date: str
    payee: str
    memo: str
    amount: str


def parse_data(input_csv: str) -> List[N26Transaction]:
    if not os.path.exists(input_csv):
        sys.stderr.write("Could not find input file\n")
        sys.exit(-1)

    records = []

    print(f"Trying to parse input file {input_csv}")
    try:
        with open(input_csv, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # skip header
            for row in reader:
                records.append(N26Transaction(
                    date=datetime.strptime(row[0], '%Y-%m-%d'),
                    recipient=row[1],
                    account_number=row[2],
                    transaction_type=row[3],
                    reference=row[4],
                    amount=float(row[5]),
                    amount_foreign_currency=float(row[6]) if row[6] else None,
                    foreign_currency=row[7],
                    exchange_rate=float(row[8]) if row[8] else None
                ))

    except Exception as e:
        sys.stderr.write(f"Could read / parse input file!{os.linesep}Exception: {e}{os.linesep}")
        sys.exit(-1)

    print(f"Found {len(records)} N26 transactions")
    return records


def convert_models(n26_transactions: List[N26Transaction]) -> List[YNABTransaction]:
    ynab_records = []

    for transaction in n26_transactions:
        ynab_records.append(YNABTransaction(
            amount=str(transaction.amount),
            payee=transaction.recipient,
            date=transaction.date.strftime('%Y-%m-%d'),
            memo=create_ynab_memo(transaction)
        ))

    print("Converting to YNAB transactions")
    return ynab_records


def create_ynab_memo(transaction: N26Transaction) -> str:
    memo = f"{transaction.transaction_type}"
    if transaction.is_fx_transaction():
        memo += f" | FX: {transaction.amount_foreign_currency}{transaction.foreign_currency} @ {transaction.exchange_rate}"
    return memo


def create_ynab_csv(ynab_transactions: List[YNABTransaction], output_csv_path: str, input_csv_path: str):
    if not output_csv_path:
        output_csv_path = create_output_file_path(input_csv_path, "ynab")
        print(f"No output file specified, using: {output_csv_path}")

    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for transaction in ynab_transactions:
            writer.writerow([transaction.date, transaction.payee, transaction.memo, transaction.amount])


def create_output_file_path(input_csv_path: str, suffix: str) -> str:
    if not input_csv_path:
        raise ValueError("Path cannot be None or empty!")

    folder_path = os.path.dirname(input_csv_path)
    file_name = os.path.splitext(os.path.basename(input_csv_path))[0]
    file_name += f"_{suffix}.csv"

    return os.path.join(folder_path, file_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help="Path to N26 CSV file")
    parser.add_argument('-o', '--output', required=False, help="Path to generated YNAB csv (optional)")
    args = parser.parse_args()

    print("Started Conversion")
    n26_transactions = parse_data(args.input)
    ynab_transactions = convert_models(n26_transactions)
    create_ynab_csv(ynab_transactions, args.output, args.input)
    print("Finished Conversion")


if __name__ == "__main__":
    main()

