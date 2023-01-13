import re
import sqlite3
from enum import Enum
from textwrap import dedent


VERSION = "1.0.0"
color_pattern = re.compile(
    r"\[(?P<color>#[0-9a-fA-F]{6})\](?P<body>[^\[]*?)\[/(?:#[0-9a-fA-F]{6})?\]"
)


def format_time(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02}"


def remove_bracketed_text(text: str) -> str:
    """Removes text between brackets and the brackets from a string."""
    return re.sub(r"\[[^\]]*\]", "", text)


def convert_Rich_style_to_html(text: str) -> str:
    """Converts Rich style tags to HTML tags.

    For example, [#00ff00]text[/#00ff00] becomes
    <span style="color: #00ff00">text</span>
    and [b]text[/b] becomes <b>text</b>.
    """
    text = color_pattern.sub(r'<span style="color: \g<color>;">\g<body></span>', text)
    text = (
        text.replace("[b]", "<b>")
        .replace("[/b]", "</b>")
        .replace("[u]", "<u>")
        .replace("[/u]", "</u>")
    )
    return text


class Mode(Enum):
    """Meeting modes."""

    GROUP = 0
    INDIVIDUAL = 1
    START = 2
    END = 3


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


def load_students(max_meeting_seconds: int) -> tuple[list[str], int]:
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


def add_5_minute_break(names: list[str]) -> int:
    """Adds a 5-minute break to the end of the list of students.

    If there is already an n-minute break there, it is changed to an
    n+5-minute break. Returns the number of minutes in the break.
    """
    if names and names[-1].endswith("-minute break"):
        minutes = int(names[-1].split("-")[0]) + 5
        names[-1] = f"{minutes}-minute break"
    else:
        names.append("5-minute break")
        minutes = 5
    return minutes


def get_help_text() -> str:
    """Returns the help text."""
    return dedent(
        """\
        <h3>keyboard shortcuts:</h3>
        [b][#008000]h[/#008000][/b] — toggles this help message.
        [b][#008000]@[/#008000][/b] — shows info about this app.
        [b][#008000]+[/#008000][/b] — increases font size.
        [b][#008000]-[/#008000][/b] — decreases font size.
        [b][#008000]o[/#008000][/b] — opens the settings.
        [b][#008000]a[/#008000][/b] — allows you to enter a student's name to add them to the queue.
        [b][#008000]n[/#008000][/b] — brings the next student to the front of the queue, and rotates the previously front student to the end.
        [b][#008000]z[/#008000][/b] — undoes the previous [#008000]n[/#008000] key press.
        [b][#008000]![/#008000][/b] — removes the last student in the queue.
        [b][#008000]?[/#008000][/b] — removes a student from the queue by name.
        [b][#008000]b[/#008000][/b] — adds a 5 minute break to the end of the queue.
        [b][#008000]$[/#008000][/b] — randomizes the order of the queue.
        [b][#008000]m[/#008000][/b] — toggles the meeting mode between group and individual meetings.
        [b][#008000]home[/#008000][/b] — changes the meeting mode to display a message saying tutoring hours will start soon.
        [b][#008000]end[/#008000][/b] — changes the meeting mode to display a message saying tutoring hours will soon end.
        [b][#008000]k[/#008000][/b] or [b][#008000]space[/#008000][/b] — pauses/unpauses the individual meetings timer.
        [b][#008000]j[/#008000][/b] — adds 5 seconds to the individual meetings timer.
        [b][#008000]l[/#008000][/b] — subtracts 5 seconds from the individual meetings timer.
        [b][#008000]left arrow[/#008000][/b] — adds 30 seconds to the individual meetings timer.
        [b][#008000]right arrow[/#008000][/b] — subtracts 30 seconds from the individual meetings timer.
        [b][#008000]r[/#008000][/b] — resets the individual meetings timer.
        [b][#008000]d[/#008000][/b] — allows you to change the individual meetings duration (in minutes).
        [b][#008000]Ctrl/Cmd+w[/#008000][/b] — closes the app.
        [b][#008000]F11[/#008000][/b] — toggles fullscreen.

        For more tips and help, visit <a style="color: white" href="https://github.com/wheelercj/zq">zq's GitHub page</a>.
        """  # noqa: E501
    )


def get_about_text(VERSION: str) -> str:
    """Returns the about text."""
    return dedent(
        f"""\
        zq

        version {VERSION}

        Developed by Chris Wheeler and licensed under the MIT license. This app is free and open source. You can find the source code and license, join discussions, submit bug reports or feature requests, and more at <a style="color: white" href="https://github.com/wheelercj/zq">github.com/wheelercj/zq</a>.

        <a style="color: white" href="https://github.com/wheelercj/zq/releases">Check for updates.</a>

        [#8E8E8E]You can close this by pressing @ again.[/#8E8E8E]
        """  # noqa: E501
    )


def get_timer_message(
    current_mode: Mode,
    mode_names: list[str],
    student_names: list[str],
    group_seconds: int,
    individual_seconds: int,
    max_individual_seconds: int,
) -> str:
    """Creates the timer message."""
    timer_message = f"[#8E8E8E]{mode_names[current_mode.value]}[/#8E8E8E]"
    if current_mode == Mode.GROUP:
        timer_message += f"       [#8E8E8E]{format_time(group_seconds)}[/#8E8E8E]"
    timer_message += "\n\n[u][b]meeting in progress with:[/b][/u]\n"
    if current_mode == Mode.INDIVIDUAL and len(student_names) == 1:
        timer_message += f"[#8E8E8E]{format_time(individual_seconds)}[/#8E8E8E] "
    timer_message += f"{student_names[0]}"
    if len(student_names) > 1:
        if current_mode == Mode.GROUP:
            for i, name in enumerate(student_names[1:]):
                timer_message += f"\n{name}"
        elif current_mode == Mode.INDIVIDUAL:
            timer_message += "\n\n[u][b]waiting:[/b][/u]\n"
            next_seconds = individual_seconds
            break_previously = False
            for i, name in enumerate(student_names[1:]):
                if i and not break_previously:
                    next_seconds += max_individual_seconds
                timer_message += (
                    f"[#00ff00]{format_time(next_seconds)}[/#00ff00] {name}\n\n"
                )
                if name.endswith("-minute break"):
                    next_seconds += int(name.split("-minute break")[0]) * 60
                    break_previously = True
                else:
                    break_previously = False
    return timer_message


def go_to_next_student(
    student_names: list[str], individual_seconds: int, max_individual_seconds: int
) -> tuple[list[str], int, int]:
    """Rotates the queue forwards.

    Parameters
    ----------
    student_names : list[str]
        The list of student names.
    individual_seconds : int
        The number of seconds remaining for the individual meeting.
    max_individual_seconds : int
        The maximum individual meeting duration in seconds.

    Returns
    -------
    list[str]
        The list of student names.
    int
        The number of seconds in the group meeting.
    int
        The number of seconds in the individual meeting.
    """
    student_names.append(student_names.pop(0))
    previous_individual_seconds = individual_seconds
    if student_names[0].endswith("-minute break"):
        individual_seconds = int(student_names[0].split("-")[0]) * 60
    else:
        individual_seconds = max_individual_seconds
    return student_names, individual_seconds, previous_individual_seconds


def return_to_previous_meeting(
    student_names: list[str], individual_seconds: int, previous_individual_seconds: int
) -> tuple[list[str], int, int]:
    """Rotates the queue backwards.

    Parameters
    ----------
    student_names : list[str]
        The list of students in the queue.
    individual_seconds : int
        The number of seconds remaining for the individual meeting.
    previous_individual_seconds : int
        The number of seconds remaining for the individual meeting before the last
        meeting.

    Returns
    -------
    list[str]
        The list of students in the queue.
    int
        The individual meeting duration.
    int
        The individual meeting duration before the last student was removed.
    """
    individual_seconds, previous_individual_seconds = (
        previous_individual_seconds,
        individual_seconds,
    )
    student_names.insert(0, student_names.pop())
    return student_names, individual_seconds, previous_individual_seconds


def remove_last_student(
    student_names: list[str], individual_seconds: int, max_individual_seconds: int
) -> tuple[list[str], int]:
    """Removes the last student from the queue and resets the timer if needed.

    Parameters
    ----------
    student_names : list[str]
        The list of students in the queue.
    individual_seconds : int
        The number of seconds remaining for the individual meeting.
    max_individual_seconds : int
        The maximum individual meeting duration in seconds.

    Returns
    -------
    list[str]
        The list of students in the queue.
    int
        The individual meeting duration.
    """
    if len(student_names):
        student_names.pop()
    if len(student_names) == 1:
        individual_seconds = max_individual_seconds
    return student_names, individual_seconds
