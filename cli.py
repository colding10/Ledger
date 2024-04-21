import argparse

from database import CSVDatabase, CSVEntry
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

VERSION = "0.11"
PROGRAM = "Ledger"


def parse_event(text: str) -> CSVEntry:
    date, change, *reason = text.split()
    reason = " ".join(reason)

    return CSVEntry(date, change, reason)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments, ending if incomplete arguments. Returns a `argparse.Namespace.`"""
    parser = argparse.ArgumentParser(
        prog=f"python3 cli.py",
        description="Manager a ledger using a database file.",
        epilog=f"© {PROGRAM} v{VERSION} Colin Ding 2022",
        prefix_chars="-",
    )

    parser.add_argument(
        "File",
        metavar="file",
        type=str,
        help="filename to the database containing entries",
    )

    parser.add_argument(
        "-e",
        "--event",
        type=parse_event,
        help="add an event in format 'MDY CHANGE REASON'",
    )

    parser.add_argument(
        "-l",
        "--list",
        dest="output_list",
        action="store_true",
        help="output a list of all entries",
    )
    parser.add_argument("-c", "--clear", action="store_true", help="clear the database")

    args = parser.parse_args()

    return args


def print_entries(database: CSVDatabase, console: Console):
    database.update()
    database.apply_interest()

    table = Table(
        title=f"LEDGER: ${database.get_total():.2f}, ({database.get_number_of_entries()} entries)",
        caption=f"LEDGER: ${database.get_total():.2f}, ({database.get_number_of_entries()} entries)",
    )

    table.add_column("Date", style="cyan", justify="left", no_wrap=True)
    table.add_column("Change", style="magenta", justify="right")
    table.add_column("Total", style="magenta", justify="right")
    table.add_column("Reason", style="green", justify="right")

    for entry in database.get_entries():
        table.add_row(
            entry.date.strftime("%m-%d-%Y"), entry.change, entry._total, entry.reason
        )

    console.print(table)


def main(args: argparse.Namespace, console: Console):
    database = CSVDatabase()

    database.connect(args.File)

    if args.output_list:
        print_entries(database, console)

    elif args.event:
        database.add_entries([args.event])

    elif args.clear:
        name = Prompt.ask(
            "[bold red] Do you really want to clear the database? (ALL ENTRIES WILL BE LOST) [bold red]",
            choices=["y", "n"],
            default="n",
        )

        if "y" in name.lower():
            database.clear()


if __name__ == "__main__":
    console = Console()

    args = parse_args()
    main(args, console)
