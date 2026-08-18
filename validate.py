from pathlib import Path
from decimal import Decimal
from collections import defaultdict
import csv


BASE_DIR = Path(__file__).parent

STOCK_FILE = BASE_DIR / "stock" / "stock_2025_04_30.csv"
TRANS_DIR = BASE_DIR / "invent_trans"
RESULT_FILE = BASE_DIR / "output" / "stock_2025_07_31.csv"


def read_stock(path: Path) -> dict:
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

            balances[key] = (
                Decimal(row["qty"]),
                Decimal(row["cost_amount"]),
            )

    return balances


def read_transactions() -> dict:
    changes = defaultdict(
        lambda: [Decimal("0"), Decimal("0")]
    )

    for path in sorted(
        TRANS_DIR.glob("invent_trans_*.csv")
    ):
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

                changes[key][0] += Decimal(
                    row["qty"]
                )

                changes[key][1] += Decimal(
                    row["cost_amount"]
                )

    return changes


def read_result(path: Path) -> dict:
    result = {}

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

            result[key] = (
                Decimal(row["qty"]),
                Decimal(row["cost_amount"]),
            )

    return result


def main() -> None:
    opening = read_stock(STOCK_FILE)
    changes = read_transactions()
    actual = read_result(RESULT_FILE)

    expected = opening.copy()

    for key, change in changes.items():
        if key not in expected:
            expected[key] = (
                Decimal("0"),
                Decimal("0"),
            )

        qty, cost = expected[key]

        expected[key] = (
            qty + change[0],
            cost + change[1],
        )

    print("Ожидаемых пар:", len(expected))
    print("Фактических пар:", len(actual))

    errors = []

    all_keys = set(expected) | set(actual)

    for key in all_keys:
        expected_value = expected.get(
            key,
            (Decimal("0"), Decimal("0")),
        )

        actual_value = actual.get(
            key,
            (Decimal("0"), Decimal("0")),
        )

        if expected_value != actual_value:
            errors.append(
                (
                    key,
                    expected_value,
                    actual_value,
                )
            )

    print("Несовпадений:", len(errors))

    for error in errors[:10]:
        print(error)

    if not errors:
        print("ПРОВЕРКА ПРОЙДЕНА")
    else:
        print("ПРОВЕРКА НЕ ПРОЙДЕНА")


if __name__ == "__main__":
    main()