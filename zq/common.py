import sqlite3
from textwrap import dedent
from typing import Tuple, List


VERSION = "0.2.1"


def create_students_table() -> None:
    """Creates the students table in the database.

    Assumes the database does not exist. The seconds column will have the
    same value in every row: the remaining seconds of the next waiting student.
    """
    with sqlite3.connect("students.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                seconds INTEGER NOT NULL);
            """
        )
        conn.commit()


def load_students(max_meeting_seconds: int) -> Tuple[List[str], int]:
    """Loads student names and wait times from the database."""
    try:
        with sqlite3.connect("students.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT name FROM students")
                student_names = [row[0] for row in cursor.fetchall()]
                cursor.execute("SELECT seconds FROM students")
                individual_seconds = cursor.fetchall()[0][0]
                return student_names, individual_seconds
            except IndexError:
                pass
    except sqlite3.OperationalError:
        create_students_table()
    return [], max_meeting_seconds


def add_5_minute_break(names: List[str]) -> None:
    """Adds a 5-minute break to the end of the list of students.

    If there is already an n-minute break there, it is changed to an
    n+5-minute break.
    """
    if names and names[-1].endswith("-minute break"):
        minutes = int(names[-1].split("-")[0])
        names[-1] = f"{minutes + 5}-minute break"
    else:
        names.append("5-minute break")


def get_help_text() -> str:
    """Returns the help text."""
    return dedent(
        """\
        [u][b]keyboard shortcuts:[/b][/u]
        [b][green]h[/green][/b] — toggles this help message.
        [b][green]@[/green][/b] — shows info about this app.
        [b][green]o[/green][/b] — opens the settings file. Restart to apply changes.
        [b][green]a[/green][/b] — allows you to enter a student's name to add them to the queue.
        [b][green]n[/green][/b] — brings the next student to the front of the queue, and rotates the previously front student to the end.
        [b][green]z[/green][/b] — undoes the previous [green]n[/green] key press.
        [b][green]![/green][/b] — removes the last student in the queue.
        [b][green]?[/green][/b] — removes a student from the queue by name.
        [b][green]b[/green][/b] — adds a [white]5[/white] minute break to the end of the queue.
        [b][green]$[/green][/b] — randomizes the order of the queue.
        [b][green]m[/green][/b] — toggles the meeting mode between group and individual meetings.
        [b][green]home[/green][/b] — changes the meeting mode to display a message saying tutoring hours will start soon.
        [b][green]end[/green][/b] — changes the meeting mode to display a message saying tutoring hours will soon end.
        [b][green]k[/green][/b] or [b][green]space[/green][/b] — pauses/unpauses the individual meetings timer.
        [b][green]j[/green][/b] — adds [white]5[/white] seconds to the individual meetings timer.
        [b][green]l[/green][/b] — subtracts [white]5[/white] seconds from the individual meetings timer.
        [b][green]left[/green][/b] — adds [white]30[/white] seconds to the individual meetings timer.
        [b][green]right[/green][/b] — subtracts [white]30[/white] seconds from the individual meetings timer.
        [b][green]r[/green][/b] — resets the individual meetings timer.
        [b][green]d[/green][/b] — allows you to change the individual meetings duration (in minutes).
        [b][green]s[/green][/b] — saves student info; for if you have autosave disabled.
        """
    )


def get_about_text(VERSION: str) -> str:
    """Returns the about text."""
    return dedent(
        f"""\
        zq
        
        version [white]{VERSION}[/white]

        Developed by Chris Wheeler and licensed under the MIT license. This app is free and open source. You can find the source code and license, join discussions, submit bug reports or feature requests, and more at https://github.com/wheelercj/zq

        [bright_black]You can close this message by pressing @ again.[/bright_black]
        """
    )
