import sqlite3
from typing import Tuple, List


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


def load_students() -> Tuple[List[str], int]:
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
    return [], 0
