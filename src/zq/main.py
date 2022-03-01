from rich.align import Align  # https://github.com/Textualize/rich
from rich.markdown import Markdown
from textual.app import App  # https://github.com/Textualize/textual
from textual.events import Key
from textual.widget import Widget
from textual.reactive import Reactive
from textual.views import GridView
from textwrap import dedent
import random
import chime  # https://pypi.org/project/chime/
import sqlite3
import subprocess
import webbrowser
import settings  # internal import


def main():
    open_other_apps()
    TimerApp.run(log="textual.log")


def open_other_apps():
    for path in settings.STARTUP_APP_PATHS:
        subprocess.run([path])
    for url in settings.STARTUP_URLS:
        webbrowser.open(url, new=2)


def format_time(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02}"


class TextInput(Widget):
    text = Reactive("")

    def render(self) -> Markdown:
        return Markdown(self.text)


class Welcome(Widget):
    message = Reactive(settings.EMPTY_LINES_ABOVE * "\n" + settings.WELCOME_MESSAGE)

    def render(self) -> Align:
        return Align.center(self.message)


class Timer(Widget):
    MAX_INDIVIDUAL_SECONDS = settings.MEETING_MINUTES * 60 + settings.TRANSITION_SECONDS
    MIN_EMPTY_WAITLIST_SECONDS = settings.MEETING_MINUTES / 2 * 60
    individual_seconds = MAX_INDIVIDUAL_SECONDS  # counts down
    group_seconds = 0  # counts up
    MODES = [
        "group meeting",
        f"{settings.MEETING_MINUTES}-minute individual meetings",
        "end",
    ]
    current_mode_index = 0
    student_names = []
    pause = True
    previous_individual_seconds = None

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)
        self.set_interval(settings.SAVE_INTERVAL_SECONDS, self.save_all_students)

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
                (self.current_mode_index == 1 and len(self.student_names) > 1)
                or self.individual_seconds > self.MIN_EMPTY_WAITLIST_SECONDS
            )
        ):
            self.individual_seconds -= 1
        if self.current_mode_index == 0 and self.student_names:
            self.group_seconds += 1
        if self.individual_seconds == settings.TRANSITION_SECONDS:
            chime.success()
        elif self.individual_seconds == 1:
            chime.info()
        if self.current_mode_index == 2:
            return Align.center(
                settings.EMPTY_LINES_ABOVE * "\n" + settings.ENDING_MESSAGE
            )
        if not self.student_names:
            self.group_seconds = 0
            return Align.center(
                settings.EMPTY_LINES_ABOVE * "\n" + "\n(no students in queue)"
            )
        else:
            timer_message = (
                f"[bright_black]{self.MODES[self.current_mode_index]}[/bright_black]"
            )
            if self.current_mode_index == 0:
                timer_message += f"       [bright_black]{format_time(self.group_seconds)}[/bright_black]"
            timer_message += "\n\n[u][b]meeting in progress with:[/b][/u]\n"
            if self.current_mode_index == 1 and len(self.student_names) == 1:
                timer_message += f"[bright_black]{format_time(self.individual_seconds)}[/bright_black] "
            timer_message += f"{self.student_names[0]}"
            if len(self.student_names) > 1:
                if self.current_mode_index == 0:
                    for i, name in enumerate(self.student_names[1:]):
                        timer_message += f"\n{name}"
                elif self.current_mode_index == 1:
                    timer_message += f"\n\n[u][b]waiting:[/b][/u]\n"
                    for i, name in enumerate(self.student_names[1:]):
                        next_seconds = self.individual_seconds + (
                            i * self.MAX_INDIVIDUAL_SECONDS
                        )
                        timer_message += f"{format_time(next_seconds)} {name}\n\n"
            return Align.center(
                settings.EMPTY_LINES_ABOVE * "\n" + "\n" + timer_message
            )


class TimerAppWidgets(GridView):
    welcome = Welcome()
    timer = Timer()
    text_input = TextInput()

    def on_mount(self) -> None:
        self.grid.set_gap(8, 1)
        self.grid.set_gutter(3)
        self.grid.set_align("center", "center")

        self.grid.add_column("col", repeat=2)
        self.grid.add_row("row", repeat=15)
        self.grid.add_areas(
            text_input="col1-start|col2-end,row15",
            welcome="col1,row1-start|row14-end",
            timer="col2,row1-start|row14-end",
        )

        self.grid.place(
            text_input=self.text_input,
            welcome=self.welcome,
            timer=self.timer,
        )


class TimerApp(App):
    receiving_text_input = False
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
        if self.receiving_text_input:
            if event.key == "enter":
                self.receiving_text_input = False
                name = self.widgets.text_input.text[len("name: ") :].strip()
                self.widgets.text_input.text = ""
                if name:
                    if name in self.widgets.timer.student_names:
                        if not name.endswith(" II"):
                            name += " II"
                        else:
                            name += "I"
                    self.widgets.timer.student_names.append(name)
                    if len(self.widgets.timer.student_names) == 1:
                        self.widgets.timer.pause = False
            elif event.key == "ctrl+h":  # backspace
                if len(self.widgets.text_input.text) > len("name: "):
                    self.widgets.text_input.text = self.widgets.text_input.text[:-1]
                else:
                    self.receiving_text_input = False
                    self.widgets.text_input.text = ""
            elif len(event.key) == 1:
                self.widgets.text_input.text += event.key
        else:
            if event.key == "h":
                # toggle displaying keyboard shortcuts help
                if self.displaying_help:
                    self.displaying_help = False
                    self.widgets.welcome.message = (
                        settings.EMPTY_LINES_ABOVE * "\n" + settings.WELCOME_MESSAGE
                    )
                else:
                    self.displaying_help = True
                    self.widgets.welcome.message = dedent(
                        """\
                        [u][b]keyboard shortcuts:[/b][/u]
                        [b][green]h[/green][/b] — toggles this help message
                        [b][green]a[/green][/b] — changes your keyboard input mode to allow you to type a student's name. You will see [white]"name: "[/white] and what you type appear in the bottom-left corner. When you have finished typing their name, press [green]enter[/green] to add the student to the queue. You can also delete all of what you typed to cancel.
                        [b][green]n[/green][/b] — brings the next student to the front of the queue, and rotates the previously front student to the end.
                        [b][green]z[/green][/b] — undoes the previous [green]n[/green] keypress.
                        [b][green]![/green][/b] — removes the last student in the queue.
                        [b][green]$[/green][/b] — randomizes the order of the queue.
                        [b][green]m[/green][/b] — toggles the meeting mode between group and individual meetings.
                        [b][green]end[/green][/b] — changes the meeting mode to display a message saying tutoring hours will soon end.
                        [b][green]k[/green][/b] — pauses/continues the individual meetings timer.
                        [b][green]j[/green][/b] — adds [white]5[/white] seconds to the individual meetings timer.
                        [b][green]l[/green][/b] — subtracts [white]5[/white] seconds from the individual meetings timer.
                        [b][green]r[/green][/b] — resets the individual meetings timer.
                        """
                    )
            elif event.key == "a":
                # add a student to the queue
                self.receiving_text_input = True
                self.widgets.text_input.text = "name: "
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
                self.widgets.timer.student_names.pop()
            elif event.key == "$":
                # randomize the order of the students in the queue
                random.shuffle(self.widgets.timer.student_names)
            elif event.key == "m":
                # toggle the queue mode between individual and group
                self.widgets.timer.current_mode_index = int(
                    not self.widgets.timer.current_mode_index
                )
                if self.widgets.timer.current_mode_index == 1:
                    self.widgets.timer.group_seconds = 0
            elif event.key == "end":
                # change the queue mode to say that tutoring hours end soon
                self.widgets.timer.current_mode_index = 2
            elif event.key == "k":
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
            elif event.key == "r":
                # reset the timer
                self.widgets.timer.individual_seconds = (
                    self.widgets.timer.MAX_INDIVIDUAL_SECONDS
                )
                self.widgets.timer.pause = True


if __name__ == "__main__":
    main()