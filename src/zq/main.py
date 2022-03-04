from rich.align import Align  # https://github.com/Textualize/rich
from rich.markdown import Markdown
from textual.app import App  # https://github.com/Textualize/textual
from textual.events import Key
from textual.widget import Widget
from textual.reactive import Reactive
from textual.views import GridView
from textwrap import dedent
import random
from typing import Callable
import chime  # https://pypi.org/project/chime/
import sqlite3
from enum import Enum
from settings import settings, save_settings  # internal import


class Mode(Enum):
    """Meeting modes."""

    GROUP = 0
    INDIVIDUAL = 1
    START = 2
    END = 3


def main():
    TimerApp.run(log="textual.log")


def format_time(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02}"


class TextInput:
    def __init__(self) -> Callable:
        self.text = ""

    def __call__(self, key: str, field_label: str = None) -> tuple[bool, str]:
        """Gets text input from the user one key at a time.

        Parameters
        ----------
        key : str
            The key pressed.
        field_label : str, None
            Any text that must appear at the front of the text input field.

        Returns
        -------
        bool
            Whether text input is still being received.
        str, None
            The text input without surrounding whitespace characters. This is None if
            text input is still being received. If the user cancels text input by
            pressing backspace, this is an empty string.
        """
        if field_label and not self.text:
            self.text = field_label
        if key == "enter":
            if field_label:
                self.text = self.text[len(field_label) :]
            result = self.text.strip()
            self.text = ""
            return False, result
        elif key == "ctrl+h":  # backspace
            start_index = len(field_label) if field_label else 0
            if len(self.text) > start_index:
                self.text = self.text[:-1]
            else:
                self.text = ""
                return False, ""
        elif len(key) == 1:
            self.text += key
        return True, None


class TextInputField(Widget):
    text = Reactive("")

    def render(self) -> Markdown:
        return Markdown(self.text)


class Welcome(Widget):
    message = Reactive(
        settings["empty lines above"] * "\n" + settings["welcome message"]
    )

    def render(self) -> Align:
        return Align.center(self.message)


class Timer(Widget):
    MAX_INDIVIDUAL_SECONDS = (
        settings["meeting minutes"] * 60 + settings["transition seconds"]
    )
    MIN_EMPTY_WAITLIST_SECONDS = settings["meeting minutes"] / 2 * 60
    individual_seconds = MAX_INDIVIDUAL_SECONDS  # counts down
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
                or self.individual_seconds > self.MIN_EMPTY_WAITLIST_SECONDS
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
        else:
            timer_message = f"[bright_black]{self.MODE_NAMES[self.current_mode.value]}[/bright_black]"
            if self.current_mode == Mode.GROUP:
                timer_message += f"       [bright_black]{format_time(self.group_seconds)}[/bright_black]"
            timer_message += "\n\n[u][b]meeting in progress with:[/b][/u]\n"
            if self.current_mode == Mode.INDIVIDUAL and len(self.student_names) == 1:
                timer_message += f"[bright_black]{format_time(self.individual_seconds)}[/bright_black] "
            timer_message += f"{self.student_names[0]}"
            if len(self.student_names) > 1:
                if self.current_mode == Mode.GROUP:
                    for i, name in enumerate(self.student_names[1:]):
                        timer_message += f"\n{name}"
                elif self.current_mode == Mode.INDIVIDUAL:
                    timer_message += f"\n\n[u][b]waiting:[/b][/u]\n"
                    for i, name in enumerate(self.student_names[1:]):
                        next_seconds = self.individual_seconds + (
                            i * self.MAX_INDIVIDUAL_SECONDS
                        )
                        timer_message += f"{format_time(next_seconds)} {name}\n\n"
            return Align.center(
                settings["empty lines above"] * "\n" + "\n" + timer_message
            )


class TimerAppWidgets(GridView):
    welcome = Welcome()
    timer = Timer()
    text_input_field = TextInputField()

    def on_mount(self) -> None:
        self.grid.set_gap(8, 1)
        self.grid.set_gutter(3)
        self.grid.set_align("center", "center")

        self.grid.add_column("col", repeat=2)
        self.grid.add_row("row", repeat=15)
        self.grid.add_areas(
            text_input_field="col1-start|col2-end,row15",
            welcome="col1,row1-start|row14-end",
            timer="col2,row1-start|row14-end",
        )

        self.grid.place(
            text_input_field=self.text_input_field,
            welcome=self.welcome,
            timer=self.timer,
        )


class TimerApp(App):
    receiving_name_input = False
    receiving_minutes_input = False
    text_input = TextInput()
    displaying_help = False
    widgets = TimerAppWidgets()

    async def on_mount(self) -> None:
        try:
            self.load_students()
        except sqlite3.OperationalError:
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
        await self.view.dock(self.widgets)

    def load_students(self) -> None:
        with sqlite3.connect("students.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT name FROM students")
                self.widgets.timer.student_names = [row[0] for row in cursor.fetchall()]
                cursor.execute("SELECT seconds FROM students")
                self.widgets.timer.individual_seconds = cursor.fetchall()[0][0]
            except IndexError:
                pass

    async def on_key(self, event: Key) -> None:
        if self.receiving_name_input:
            self.receiving_name_input, name = self.text_input(event.key, "name: ")
            self.widgets.text_input_field.text = self.text_input.text
            if name:
                if name in self.widgets.timer.student_names:
                    name += " II"
                self.widgets.timer.student_names.append(name)
                if len(self.widgets.timer.student_names) == 1:
                    self.widgets.timer.pause = False
        elif self.receiving_minutes_input:
            self.receiving_minutes_input, minutes = self.text_input(
                event.key, "minutes: "
            )
            self.widgets.text_input_field.text = self.text_input.text
            if minutes and minutes.isdigit() and int(minutes) > 0:
                settings["meeting minutes"] = int(minutes)
                self.widgets.timer.MAX_INDIVIDUAL_SECONDS = (
                    settings["meeting minutes"] * 60 + settings["transition seconds"]
                )
                self.widgets.timer.MIN_EMPTY_WAITLIST_SECONDS = (
                    settings["meeting minutes"] / 2 * 60
                )
                save_settings()
        else:
            if event.key == "h":
                # toggle displaying keyboard shortcuts help
                if self.displaying_help:
                    self.displaying_help = False
                    self.widgets.welcome.message = (
                        settings["empty lines above"] * "\n"
                        + settings["welcome message"]
                    )
                else:
                    self.displaying_help = True
                    self.widgets.welcome.message = dedent(
                        """\
                        [u][b]keyboard shortcuts:[/b][/u]
                        [b][green]h[/green][/b] — toggles this help message.
                        [b][green]a[/green][/b] — allows you to enter a student's name to add them to the queue.
                        [b][green]n[/green][/b] — brings the next student to the front of the queue, and rotates the previously front student to the end.
                        [b][green]z[/green][/b] — undoes the previous [green]n[/green] keypress.
                        [b][green]![/green][/b] — removes the last student in the queue.
                        [b][green]$[/green][/b] — randomizes the order of the queue.
                        [b][green]m[/green][/b] — toggles the meeting mode between group and individual meetings.
                        [b][green]home[/green][/b] — changes the meeting mode to display a message saying tutoring hours will start soon.
                        [b][green]end[/green][/b] — changes the meeting mode to display a message saying tutoring hours will soon end.
                        [b][green]k[/green][/b] — pauses/unpauses the individual meetings timer.
                        [b][green]space[/green][/b] — pauses/unpauses the individual meetings timer.
                        [b][green]j[/green][/b] — adds [white]5[/white] seconds to the individual meetings timer.
                        [b][green]l[/green][/b] — subtracts [white]5[/white] seconds from the individual meetings timer.
                        [b][green]up[/green][/b] — adds [white]30[/white] seconds to the individual meetings timer.
                        [b][green]down[/green][/b] — subtracts [white]30[/white] seconds from the individual meetings timer.
                        [b][green]r[/green][/b] — resets the individual meetings timer.
                        [b][green]d[/green][/b] — allows you to change the individual meetings duration (in minutes).
                        [b][green]s[/green][/b] — saves student info; for if you have autosave disabled.
                        """
                    )
            elif event.key == "a":
                # add a student to the queue
                self.receiving_name_input = True
                self.widgets.text_input_field.text = "name: "
            elif event.key == "n" and len(self.widgets.timer.student_names) > 1:
                # go to the next student in queue
                self.widgets.timer.student_names.append(
                    self.widgets.timer.student_names.pop(0)
                )
                self.widgets.timer.previous_individual_seconds = (
                    self.widgets.timer.individual_seconds
                )
                self.widgets.timer.individual_seconds = (
                    self.widgets.timer.MAX_INDIVIDUAL_SECONDS
                )
            elif (
                event.key == "z"
                and self.widgets.timer.previous_individual_seconds is not None
            ):
                # return to the previous meeting
                temp = self.widgets.timer.individual_seconds
                self.widgets.timer.individual_seconds = (
                    self.widgets.timer.previous_individual_seconds
                )
                self.widgets.timer.previous_individual_seconds = temp
                self.widgets.timer.student_names.insert(
                    0, self.widgets.timer.student_names.pop()
                )
            elif event.key == "!":
                # remove the student at the end of the queue
                if len(self.widgets.timer.student_names):
                    self.widgets.timer.student_names.pop()
                if len(self.widgets.timer.student_names) == 1:
                    self.widgets.timer.individual_seconds = (
                        self.widgets.timer.MAX_INDIVIDUAL_SECONDS
                    )
            elif event.key == "$":
                # randomize the order of the students in the queue
                random.shuffle(self.widgets.timer.student_names)
            elif event.key == "m":
                if self.widgets.timer.current_mode == Mode.GROUP:
                    self.widgets.timer.current_mode = Mode.INDIVIDUAL
                else:
                    self.widgets.timer.current_mode = Mode.GROUP
                    self.widgets.timer.group_seconds = 0
            elif event.key == "home":
                # change the queue mode to say that tutoring hours start soon
                self.widgets.timer.current_mode = Mode.START
            elif event.key == "end":
                # change the queue mode to say that tutoring hours end soon
                self.widgets.timer.current_mode = Mode.END
            elif event.key == "k" or event.key == " ":
                # pause the timers
                self.widgets.timer.pause = not self.widgets.timer.pause
            elif event.key == "j":
                # add 5 seconds to the current meeting
                self.widgets.timer.individual_seconds += 5
            elif event.key == "l":
                # subtract up to 5 seconds from the current meeting
                if self.widgets.timer.individual_seconds >= 5:
                    self.widgets.timer.individual_seconds -= 5
                else:
                    self.widgets.timer.individual_seconds = 0
            elif event.key == "up":
                # add 30 seconds to the current meeting
                self.widgets.timer.individual_seconds += 30
            elif event.key == "down":
                # subtract up to 30 seconds from the current meeting
                if self.widgets.timer.individual_seconds >= 30:
                    self.widgets.timer.individual_seconds -= 30
                else:
                    self.widgets.timer.individual_seconds = 0
            elif event.key == "r":
                # reset the timer
                self.widgets.timer.individual_seconds = (
                    self.widgets.timer.MAX_INDIVIDUAL_SECONDS
                )
                self.widgets.timer.pause = True
            elif event.key == "d":
                # change the individual meetings duration (in minutes)
                self.receiving_minutes_input = True
                self.widgets.text_input_field.text = "minutes: "
            elif event.key == "s":
                self.widgets.timer.save_all_students()


if __name__ == "__main__":
    main()
