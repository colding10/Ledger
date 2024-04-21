import os
import datetime
from dateutil import rrule
from io import TextIOWrapper

import pandas

INTREST_PERCENTAGE = 0.01


class TextEntry:
    """
    An class containing the following:
    `name`: `str`
    `date`: `datetime.date`
    `value`: `int`
    """

    total: float = 0

    name: str
    date: datetime.date
    value: str

    def __init__(self, date: str, value: str, name: str) -> None:
        self.name = name
        self.date = self.parse_date(date)
        self.value = f"{float(value):+.2f}"

        TextEntry.total += float(value)
        TextEntry.set_total(self)

    def to_string(self) -> str:
        return f"{self.date.isoformat().ljust(30)} {self.value.rjust(30)} {str(self._total).rjust(30)} {self.name.rjust(30)}"

    def to_db_format(self) -> str:
        return f"{self.name}|{self.date.isoformat()}|{self.value}"

    def set_total(self=None) -> None:
        self._total = f"{TextEntry.total:.02f}"

    def parse_date(self, date_string: str) -> datetime.date:
        if "-" in date_string:
            m, d, y = date_string.split("-")
            if len(y) == 4:
                return datetime.datetime.strptime(date_string, "%m-%d-%Y")
            elif len(y) == 2:
                return datetime.datetime.strptime(date_string, "%m-%d-%y")

        else:
            m, d, y = date_string.split("/")
            if len(y) == 4:
                return datetime.datetime.strptime(date_string, "%m/%d/%Y")
            else:
                return datetime.datetime.strptime(date_string, "%m/%d/%y")

        return datetime.date.today()


class CSVEntry:
    """An entry class for the CSV Database."""

    total: float = 0
    change: str
    date: datetime.date
    reason: str

    def __init__(self, date: str, value: float | str, reason: str, *args) -> None:
        value = float(value)

        self.reason = str(reason)
        self.change = f"{value:+.2f}"
        self.date = self.parse_date(date)

        CSVEntry.total += value
        CSVEntry.set_total(self)

    def set_total(self) -> None:
        self._total = f"{CSVEntry.total:.02f}"

    def to_pandas(self) -> pandas.Series:
        return pandas.Series(
            {
                "Date": self.date.strftime("%m-%d-%Y"),
                "Change": float(self.change),
                "Reason": self.reason,
                "sort_col": self.date.isoformat(),
            }
        )

    def parse_date(self, date_string: str) -> datetime.date:
        if "-" in date_string:
            m, d, y = date_string.split("-")
            if len(y) == 4:
                return datetime.datetime.strptime(date_string, "%m-%d-%Y")
            elif len(y) == 2:
                return datetime.datetime.strptime(date_string, "%m-%d-%y")

        else:
            m, d, y = date_string.split("/")
            if len(y) == 4:
                return datetime.datetime.strptime(date_string, "%m/%d/%Y")
            else:
                return datetime.datetime.strptime(date_string, "%m/%d/%y")

        return datetime.date.today()


class TextIODatabase:
    """A database class that controls files."""

    file: TextIOWrapper

    def connect(self, filename: str) -> None:
        """Opens a file `filename` to `self.file`."""
        self.file = (
            open(filename, "r") if os.path.exists(filename) else open(filename, "w")
        )

    def connect_file(self, file: TextIOWrapper) -> None:
        """Sets a `TextIOWrapper` `file` to `self.file`."""
        self.file = file

    def close(self) -> None:
        """Closes an open file `self.file`."""
        self.file.close()

    def read_lines(self) -> list[str]:
        """Reads the lines from `self.file`."""
        return [line.replace("\n", "") for line in self.file.readlines()]

    def read(self) -> str:
        """Reads all text from `self.file`."""
        return self.file.read()

    def get_entries(self) -> list[TextEntry]:
        """Reads the lines and parses to `Entry`s from `self.file`."""
        return [TextEntry(*line.split("|")) for line in self.read_lines()]

    def write_lines(self, lines: list[str]) -> None:
        """Writes lines `lines` to file `self.file`."""
        if not self.file.writable():
            self.close()
            self.file = open(self.file.name, "w")

        self.file.write("\n".join(lines))

    def write_entries(self, entries: list[TextEntry]) -> None:
        """Writes entries `entries` to the file `self.file`, sorted by date."""
        self.write_lines(
            [entry.to_db_format() for entry in sorted(entries, key=lambda e: e.date)]
        )

    def add_entries(self, entries: list[TextEntry]) -> None:
        """Adds entries `entries` to the database."""
        self.write_entries(self.get_entries() + entries)

    def clear(self) -> None:
        """Clears the database."""
        self.write_lines([])

    def __enter__(self):
        """`with` context manager."""
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Exiting `with` context manager."""

        self.close()


class CSVDatabase:
    """A database file that controls csv files."""

    frame: pandas.DataFrame
    path: str

    def connect(self, filename: str) -> None:
        """Reads a CSV file to `self.frame`."""
        self.frame = pandas.read_csv(filename)
        self.path = filename

    def connect_file(self, file: TextIOWrapper) -> None:
        """Reads a opened file to `self.frame.`"""
        if len(file.read()) <= 1:
            file.write("Name")

        self.frame = pandas.read_csv(file.read())
        self.path = file.name

        print(self.frame.to_string())

    def get_entries(self) -> list[CSVEntry]:
        """Reads entries from the frame."""
        CSVEntry.total = 0
        return [CSVEntry(*self.frame.iloc[i]) for i in range(len(self.frame))]

    def get_total(self) -> float:
        """Returns the total value in the ledger."""
        return float(self.get_entries()[-1]._total)

    def get_number_of_entries(self) -> int:
        """Returns the total number of entries in the ledger."""
        return len(self.get_entries())

    def write_entries(self, entries: list[CSVEntry]) -> None:
        """Writes a list of entries to the csv."""
        df = pandas.DataFrame([e.to_pandas() for e in entries], dtype=object)
        df.sort_values(by=["sort_col"], inplace=True)
        df.drop_duplicates(inplace=True)

        df.to_csv(self.path, index=False)

    def add_entries(self, entries: list[CSVEntry]) -> None:
        """Adds a list of entries to the CSV."""
        self.update()

        self.write_entries(self.get_entries() + entries)

    def apply_interest(self) -> None:
        self.update()

        first_entry, last_entry = self.get_entries()[0], self.get_entries()[-1]
        first_date, last_date = first_entry.date, last_entry.date

        first_date = (first_date.replace(day=1) + datetime.timedelta(days=32)).replace(
            day=1
        )
        last_date = (last_date.replace(day=1) - datetime.timedelta(days=32)).replace(
            day=1
        )
        last_date = (datetime.date.today().replace(day=1))
        
        for dt in rrule.rrule(rrule.MONTHLY, dtstart=first_date, until=last_date):
            existing = [e for e in self.get_entries() if e.date == dt]
            if existing:
                skip = False
                for e in existing:
                    if e.reason == "INTEREST":
                        skip = True
                        break

                if skip:
                    continue

            prev_total = [e for e in self.get_entries() if e.date < dt][-1]._total

            interest_entry = CSVEntry(
                dt.strftime("%m-%d-%Y"),
                float(prev_total) * INTREST_PERCENTAGE,
                "INTEREST",
            )

            self.add_entries([interest_entry])
            self.update()

    def update(self) -> None:
        """Refreshes `self.frame` from the file."""
        self.frame = pandas.read_csv(self.path)
        self.frame.fillna("UNKNOWN", inplace=True)

    def clear(self) -> None:
        """Clears the database file (writes empty)"""
        self.frame.head(0).to_csv(self.path)


if __name__ == "__main__":
    db = TextIODatabase()
    db.connect("db.database")

    db.close()
