from rich.align import Align  # https://github.com/Textualize/rich
import chime  # https://pypi.org/project/chime/
from textual.widget import Widget
import sqlite3
from zq.common import Mode, get_timer_message
from zq.settings import settings


class Timer(Widget):
    chime.theme("material")
    max_individual_seconds = (
        settings["meeting minutes"] * 60 + settings["transition seconds"]
    )
    min_empty_waitlist_seconds = settings["meeting minutes"] / 2 * 60
    individual_seconds = max_individual_seconds  # counts down
    group_seconds = 0  # counts up
    mode_names = [
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

    def save_all_students(self) -> None:
        """Saves all student names and the next's wait time to the database.

        Every row of the seconds column receives the same number: the next student's
        wait time.
        """
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
        """Render the timer."""
        self.tick()
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
                settings["empty lines above"] * "\n" + "(no students in queue)"
            )
        timer_message = get_timer_message(
            self.current_mode,
            self.mode_names,
            self.student_names,
            self.group_seconds,
            self.individual_seconds,
            self.max_individual_seconds,
        )
        return Align.center(settings["empty lines above"] * "\n" + "\n" + timer_message)

    def tick(self) -> None:
        """Called once each second; controls the timer."""
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
            chime.warning()
        elif self.individual_seconds == 1:
            chime.error()
