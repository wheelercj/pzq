from textual.app import App  # https://github.com/Textualize/textual
from textual.events import Key
from textwrap import dedent
import random
import sqlite3

# internal imports
from settings import settings, save_settings
from text_input import TextInput
from timer import Mode
from timer_app_widgets import TimerAppWidgets


def main():
    TimerApp.run(log="textual.log")


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
                self.widgets.timer.max_individual_seconds = (
                    settings["meeting minutes"] * 60 + settings["transition seconds"]
                )
                self.widgets.timer.min_empty_waitlist_seconds = (
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
                    self.widgets.timer.max_individual_seconds
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
                        self.widgets.timer.max_individual_seconds
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
                    self.widgets.timer.max_individual_seconds
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
