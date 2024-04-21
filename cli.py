from database import CSVDatabase, CSVEntry
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

VERSION = "0.11"
PROGRAM = "Ledger"


def parse_event(text: str) -> CSVEntry:
    date, change, *reason = text.split()
    reason = " ".join(reason)

    return CSVEntry(date, change, reason)


def print_entries(database: CSVDatabase, cons: Console):
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

    cons.print(table)


def main(cons: Console):
    database = CSVDatabase()

    database.connect(input("Enter database file name: "))
    print_entries(database, cons)

    inp = input("1: Add an entry, 2: check balance Q: quit ").upper()
    while inp != "Q":
        if inp == "1":
            database.add_entries(
                [
                    CSVEntry(
                        input("Date in m/d/y "),
                        input("Change in value "),
                        input("Reason "),
                    )
                ]
            )
        elif inp == "2":
            print_entries(database, cons)


if __name__ == "__main__":
    console = Console()

    main(console)
