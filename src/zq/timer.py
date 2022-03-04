from rich.align import Align  # https://github.com/Textualize/rich
import chime  # https://pypi.org/project/chime/
from enum import Enum
from textual.widget import Widget
import sqlite3

# internal imports
from settings import settings


def format_time(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02}"


class Mode(Enum):
    """Meeting modes."""

    GROUP = 0
    INDIVIDUAL = 1
    START = 2
    END = 3


class Timer(Widget):
    max_individual_seconds = (
        settings["meeting minutes"] * 60 + settings["transition seconds"]
    )
    min_empty_waitlist_seconds = settings["meeting minutes"] / 2 * 60
    individual_seconds = max_individual_seconds  # counts down
    group_seconds = 0  # counts up
    MODE_NAMES = [
        "group meeting",
        f"{settings['meeting minutes']}-minute individual meetings",
        "start",
        "end",
    ]
    current_mode = Mode.GROUP
    student_names = []
    pause = True
    previous_individual_seconds = None

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)
        self.set_interval(settings["save interval seconds"], self.save_all_students)

    def save_all_students(self) -> None:
        with sqlite3.connect("students.db") as conn:
            conn.execute("DELETE FROM students")
            cursor = conn.cursor()
            for name in self.student_names:
                cursor.execute(
                    "INSERT INTO students (name, seconds) VALUES (?, ?)",
                    (name, self.individual_seconds),
                )
            conn.commit()

    def render(self) -> Align:
        if (
            self.student_names
            and self.individual_seconds
            and not self.pause
            and (
                (self.current_mode == Mode.INDIVIDUAL and len(self.student_names) > 1)
                or self.individual_seconds > self.min_empty_waitlist_seconds
            )
        ):
            self.individual_seconds -= 1
        if self.current_mode == Mode.GROUP and self.student_names:
            self.group_seconds += 1
        if self.individual_seconds == settings["transition seconds"]:
            chime.success()
        elif self.individual_seconds == 1:
            chime.info()

        if self.current_mode == Mode.START:
            return Align.center(
                settings["empty lines above"] * "\n" + settings["starting message"]
            )
        if self.current_mode == Mode.END:
            return Align.center(
                settings["empty lines above"] * "\n" + settings["ending message"]
            )
        if not self.student_names:
            self.group_seconds = 0
            return Align.center(
                settings["empty lines above"] * "\n" + "\n(no students in queue)"
            )

        timer_message = (
            f"[bright_black]{self.MODE_NAMES[self.current_mode.value]}[/bright_black]"
        )
        if self.current_mode == Mode.GROUP:
            timer_message += (
                f"       [bright_black]{format_time(self.group_seconds)}[/bright_black]"
            )
        timer_message += "\n\n[u][b]meeting in progress with:[/b][/u]\n"
        if self.current_mode == Mode.INDIVIDUAL and len(self.student_names) == 1:
            timer_message += (
                f"[bright_black]{format_time(self.individual_seconds)}[/bright_black] "
            )
        timer_message += f"{self.student_names[0]}"
        if len(self.student_names) > 1:
            if self.current_mode == Mode.GROUP:
                for i, name in enumerate(self.student_names[1:]):
                    timer_message += f"\n{name}"
            elif self.current_mode == Mode.INDIVIDUAL:
                timer_message += f"\n\n[u][b]waiting:[/b][/u]\n"
                for i, name in enumerate(self.student_names[1:]):
                    next_seconds = self.individual_seconds + (
                        i * self.max_individual_seconds
                    )
                    timer_message += f"{format_time(next_seconds)} {name}\n\n"
        return Align.center(settings["empty lines above"] * "\n" + "\n" + timer_message)
