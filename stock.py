from pathlib import Path
import re
from datetime import date, timedelta
import csv
from decimal import Decimal
from collections import defaultdict
import calendar
import shutil


PATH_SOURCE = Path(__file__).parent
PATH_TRANS = PATH_SOURCE / "invent_trans"
PATH_STOCK = PATH_SOURCE / "stock"
PATH_OUTPUT = PATH_SOURCE / "output"


STOCK_FILE_RE = re.compile(
    r"^stock_(\d{4})_(\d{2})_(\d{2})\.csv$"
)

TRANS_FILE_RE = re.compile(
    r"^invent_trans_(\d{4})_(\d{2})\.csv$"
)


def last_day_of_month(year: int, month: int) -> date:
    return date(
        year,
        month,
        calendar.monthrange(year, month)[1],
    )


def stock_date(path: Path) -> date:
    match = STOCK_FILE_RE.fullmatch(path.name)

    if not match:
        raise ValueError(
            f"Некорректное имя файла: {path.name}"
        )

    return date(
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
    )


def transaction_month(path: Path) -> tuple[int, int]:
    match = TRANS_FILE_RE.fullmatch(path.name)

    if not match:
        raise ValueError(
            f"Некорректное имя файла: {path.name}"
        )

    return (
        int(match.group(1)),
        int(match.group(2)),
    )


def find_opening_stock() -> tuple[Path, date]:
    candidates = []

    for path in PATH_STOCK.glob("stock_*.csv"):
        file_date = stock_date(path)
        candidates.append((path, file_date))

    if not candidates:
        raise FileNotFoundError(
            "Файлы начальных остатков не найдены"
        )

    return min(
        candidates,
        key=lambda item: item[1],
    )


def find_transaction_files() -> dict:
    files = {}

    for path in PATH_TRANS.glob("invent_trans_*.csv"):
        files[path.name] = path

    if not files:
        raise FileNotFoundError(
            "Файлы движений не найдены"
        )

    return files


def prepare_output_dir() -> None:
    if PATH_OUTPUT.exists():
        shutil.rmtree(PATH_OUTPUT)

    PATH_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )


def read_opening_stock(path: Path) -> dict:
    balances = {}

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
        )

        for row in reader:
            key = (
                row["item_id"],
                row["location_id"],
            )

            qty = Decimal(row["qty"])
            cost_amount = Decimal(row["cost_amount"])

            balances[key] = [
                qty,
                cost_amount,
            ]

    return balances


def aggregate_transactions(path: Path) -> dict:
    changes = defaultdict(
        lambda: defaultdict(
            lambda: [
                Decimal("0"),
                Decimal("0"),
            ]
        )
    )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
        )

        for row in reader:
            trans_date = row["trans_date"]

            key = (
                row["item_id"],
                row["location_id"],
            )

            changes[trans_date][key][0] += Decimal(
                row["qty"]
            )

            changes[trans_date][key][1] += Decimal(
                row["cost_amount"]
            )

    return changes


def apply_changes(
    balances: dict,
    changes: dict,
    current_date: str,
) -> None:
    for key, change in changes.get(
        current_date,
        {},
    ).items():

        if key not in balances:
            balances[key] = [
                Decimal("0"),
                Decimal("0"),
            ]

        balances[key][0] += change[0]
        balances[key][1] += change[1]


def write_snapshot(
    path: Path,
    snapshot_date: date,
    balances: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.writer(
            file,
            delimiter=";",
        )

        writer.writerow([
            "item_id",
            "location_id",
            "trans_date",
            "qty",
            "cost_amount",
        ])

        for (
            item_id,
            location_id,
        ), (
            qty,
            cost_amount,
        ) in balances.items():

            writer.writerow([
                item_id,
                location_id,
                snapshot_date.isoformat(),
                qty,
                cost_amount,
            ])


def calculate_daily_balances(
    balances: dict,
    changes: dict,
    start_date: date,
    end_date: date,
) -> None:
    current_date = start_date

    while current_date <= end_date:
        date_text = current_date.isoformat()

        apply_changes(
            balances,
            changes,
            date_text,
        )

        print(
            "Обработана дата:",
            current_date,
        )

        output_path = (
            PATH_OUTPUT
            / f"stock_{current_date:%Y_%m_%d}.csv"
        )

        write_snapshot(
            output_path,
            current_date,
            balances,
        )

        print(
            "Сохранён файл:",
            output_path,
        )

        current_date += timedelta(days=1)


def main() -> None:
    prepare_output_dir()

    opening_file, opening_date = find_opening_stock()

    print(
        "Начальный файл:",
        opening_file,
    )

    print(
        "Дата начального остатка:",
        opening_date,
    )

    balances = read_opening_stock(
        opening_file
    )

    print(
        "Количество товар/подразделение:",
        len(balances),
    )

    transaction_files = find_transaction_files()

    print("Файлы движений:")

    for name, path in transaction_files.items():
        print(
            name,
            "->",
            path,
        )

    sorted_files = sorted(
        transaction_files.values(),
        key=transaction_month,
    )

    for transaction_file in sorted_files:
        year, month = transaction_month(
            transaction_file
        )

        start_date = date(
            year,
            month,
            1,
        )

        end_date = last_day_of_month(
            year,
            month,
        )

        print(
            f"Обработка периода: "
            f"{start_date} - {end_date}"
        )

        changes = aggregate_transactions(
            transaction_file
        )

        calculate_daily_balances(
            balances,
            changes,
            start_date,
            end_date,
        )


if __name__ == "__main__":
    main()