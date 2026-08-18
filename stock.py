from pathlib import Path

PATH_SOURCE = Path(__file__).parent
PATH_TRANS = PATH_SOURCE / 'invent_trans'
PATH_STOCK = PATH_SOURCE / 'stock'


def main() -> None:
    print("Папка проекта:", PATH_SOURCE)
    print("Папка движений:", PATH_TRANS)
    print("Папка остатков:", PATH_STOCK)


if __name__ == "__main__":
    main()