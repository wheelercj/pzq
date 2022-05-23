import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from textual.app import App  # https://github.com/Textualize/textual
from textual.events import Key
from textual.widgets import ScrollView
from textwrap import dedent
import random
import sqlite3
import webbrowser
from zq.settings import settings, save_settings
from zq.text_input import TextInput
from zq.timer import Mode
from zq.timer_app_widgets import TimerAppWidgets


VERSION = "0.2.1"


def main():
    TimerApp.run(log="textual.log")


class TimerApp(App):
    receiving_new_name_input = False
    receiving_existing_name_input = False
    receiving_minutes_input = False
    text_input = TextInput()
    displaying_help = False
    displaying_about = False
    widgets = TimerAppWidgets()

    async def on_mount(self) -> None:
        self.widgets.welcome = ScrollView(gutter=1)
        await self.widgets.welcome.update(
            settings["empty lines above"] * "\n" + settings["welcome message"]
        )
        try:
            self.load_students()
        except sqlite3.OperationalError:
            self.create_students_table()
        await self.view.dock(self.widgets)

    def create_students_table(self) -> None:
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

    def load_students(self) -> None:
        """Loads student names and wait times from the database."""
        with sqlite3.connect("students.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT name FROM students")
                self.widgets.timer.student_names = [row[0] for row in cursor.fetchall()]
                cursor.execute("SELECT seconds FROM students")
                self.widgets.timer.individual_seconds = cursor.fetchall()[0][0]
            except IndexError:
                pass

    def get_new_name_input(self, key: str) -> None:
        """Gets the name of a new student from the user, one key per call.

        Parameters
        ----------
        key : str
            The key pressed by the user.
        """
        self.receiving_new_name_input, name = self.text_input(key, "name: ")
        self.widgets.text_input_field.text = self.text_input.text
        if name:
            if name in self.widgets.timer.student_names:
                name += " II"
            self.widgets.timer.student_names.append(name)
            if len(self.widgets.timer.student_names) == 1:
                self.widgets.timer.pause = False

    def add_5_minute_break(self) -> None:
        """Adds a 5-minute break to the end of the list of students.

        If there is already an n-minute break there, it is changed to an
        n+5-minute break.
        """
        names = self.widgets.timer.student_names
        if names and names[-1].endswith("-minute break"):
            minutes = int(names[-1].split("-")[0])
            names[-1] = f"{minutes + 5}-minute break"
        else:
            names.append("5-minute break")

    def get_existing_name_input(self, key: str) -> None:
        """Gets a name from the user one key per call and removes the student.

        Parameters
        ----------
        key : str
            The key pressed by the user.
        """
        self.receiving_existing_name_input, name = self.text_input(
            key, "name to remove: "
        )
        self.widgets.text_input_field.text = self.text_input.text
        if name:
            if name in self.widgets.timer.student_names:
                if name == self.widgets.timer.student_names[0]:
                    names = self.widgets.timer.student_names
                    if len(names) > 1 and names[1].endswith("-minute break"):
                        self.widgets.timer.individual_seconds = (
                            int(names[1].split("-")[0]) * 60
                        )
                    else:
                        self.widgets.timer.individual_seconds = (
                            self.widgets.timer.max_individual_seconds
                        )
                self.widgets.timer.student_names.remove(name)
                if not len(self.widgets.timer.student_names):
                    self.widgets.timer.pause = True

    def get_minutes_input(self, key: str) -> None:
        """Gets minutes input one key per call and updates the interface & settings.

        Parameters
        ----------
        key : str
            The key pressed by the user.
        """
        self.receiving_minutes_input, minutes = self.text_input(key, "minutes: ")
        self.widgets.text_input_field.text = self.text_input.text
        if minutes and minutes.isdigit() and int(minutes) > 0:
            minutes = int(minutes)
            settings["meeting minutes"] = minutes
            self.widgets.timer.max_individual_seconds = (
                minutes * 60 + settings["transition seconds"]
            )
            self.widgets.timer.min_empty_waitlist_seconds = minutes / 2 * 60
            self.widgets.timer.mode_names[
                Mode.INDIVIDUAL.value
            ] = f"{minutes}-minute individual meetings"
            save_settings()

    async def on_key(self, event: Key) -> None:
        """Handles key press events from the user via Textual.

        Parameters
        ----------
        event : Key
            The key pressed by the user.
        """
        await self.on_key_str(event.key)

    async def on_key_str(self, key: str) -> None:
        """Handles key presses.

        Parameters
        ----------
        key : str
            The key pressed by the user.
        """
        if self.receiving_new_name_input:
            self.get_new_name_input(key)
            return
        elif self.receiving_existing_name_input:
            self.get_existing_name_input(key)
            return
        elif self.receiving_minutes_input:
            self.get_minutes_input(key)
            return
        if key == "h":
            await self.toggle_help_display()
        elif key == "@":
            await self.toggle_about_display()
        elif key == "o":
            self.open_settings_file()
        elif key == "a":  # add a student to the queue
            self.receiving_new_name_input = True
            self.widgets.text_input_field.text = "name: "
        elif key == "n" and len(self.widgets.timer.student_names) > 1:
            self.go_to_next_student()
        elif key == "z" and self.widgets.timer.previous_individual_seconds is not None:
            self.return_to_previous_meeting()
        elif key == "!":
            self.remove_last_student()
        elif key == "?":  # remove student by name
            self.receiving_existing_name_input = True
            self.widgets.text_input_field.text = "name to remove: "
        elif key == "b":
            self.add_5_minute_break()
        elif key == "$":  # randomize the order of the students in the queue
            random.shuffle(self.widgets.timer.student_names)
        elif key == "m":
            if self.widgets.timer.current_mode == Mode.GROUP:
                self.widgets.timer.current_mode = Mode.INDIVIDUAL
            else:
                self.widgets.timer.current_mode = Mode.GROUP
                self.widgets.timer.group_seconds = 0
        elif key == "home":
            # change the meeting mode to say that tutoring hours start soon
            self.widgets.timer.current_mode = Mode.START
        elif key == "end":
            # change the meeting mode to say that tutoring hours end soon
            self.widgets.timer.current_mode = Mode.END
        elif key == "k" or key == " ":
            # pause the timers
            self.widgets.timer.pause = not self.widgets.timer.pause
        elif key == "j":
            # add 5 seconds to the current meeting
            self.widgets.timer.individual_seconds += 5
        elif key == "l":
            # subtract up to 5 seconds from the current meeting
            if self.widgets.timer.individual_seconds >= 5:
                self.widgets.timer.individual_seconds -= 5
            else:
                self.widgets.timer.individual_seconds = 0
        elif key == "left":
            # add 30 seconds to the current meeting
            self.widgets.timer.individual_seconds += 30
        elif key == "right":
            # subtract up to 30 seconds from the current meeting
            if self.widgets.timer.individual_seconds >= 30:
                self.widgets.timer.individual_seconds -= 30
            else:
                self.widgets.timer.individual_seconds = 0
        elif key == "r":
            # reset the timer
            self.widgets.timer.individual_seconds = (
                self.widgets.timer.max_individual_seconds
            )
            self.widgets.timer.pause = True
        elif key == "d":
            # change the individual meetings duration (in minutes)
            self.receiving_minutes_input = True
            self.widgets.text_input_field.text = "minutes: "
        elif key == "s":
            self.widgets.timer.save_all_students()

    async def toggle_help_display(self) -> None:
        """Toggles the help display."""
        if self.displaying_help:
            self.displaying_help = False
            await self.widgets.welcome.update(
                settings["empty lines above"] * "\n" + settings["welcome message"]
            )
        else:
            self.displaying_help = True
            self.displaying_about = False
            await self.widgets.welcome.update(self.get_help_text())

    async def toggle_about_display(self) -> None:
        """Toggles the about display."""
        if self.displaying_about:
            self.displaying_about = False
            await self.widgets.welcome.update(
                settings["empty lines above"] * "\n" + settings["welcome message"]
            )
        else:
            self.displaying_about = True
            self.displaying_help = False
            await self.widgets.welcome.update(
                settings["empty lines above"] * "\n" + self.get_about_text()
            )

    def open_settings_file(self) -> None:
        """Opens the app's settings file for the user to view."""
        if not os.path.exists("settings.yaml"):
            save_settings()
        webbrowser.open("settings.yaml")

    def go_to_next_student(self) -> None:
        """Rotates the queue forwards."""
        names = self.widgets.timer.student_names
        names.append(names.pop(0))
        self.widgets.timer.previous_individual_seconds = (
            self.widgets.timer.individual_seconds
        )
        if names[0].endswith("-minute break"):
            self.widgets.timer.individual_seconds = int(names[0].split("-")[0]) * 60
        else:
            self.widgets.timer.individual_seconds = (
                self.widgets.timer.max_individual_seconds
            )

    def return_to_previous_meeting(self) -> None:
        """Rotates the queue backwards."""
        temp = self.widgets.timer.individual_seconds
        self.widgets.timer.individual_seconds = (
            self.widgets.timer.previous_individual_seconds
        )
        self.widgets.timer.previous_individual_seconds = temp
        self.widgets.timer.student_names.insert(
            0, self.widgets.timer.student_names.pop()
        )

    def remove_last_student(self) -> None:
        """Removes the last student from the queue."""
        if len(self.widgets.timer.student_names):
            self.widgets.timer.student_names.pop()
        if len(self.widgets.timer.student_names) == 1:
            self.widgets.timer.individual_seconds = (
                self.widgets.timer.max_individual_seconds
            )

    def get_about_text(self) -> str:
        """Returns the about text."""
        return dedent(
            f"""\
            zq
            
            version [white]{VERSION}[/white]

            Developed by Chris Wheeler and licensed under the MIT license. This app is free and open source. You can find the source code and license, join discussions, submit bug reports or feature requests, and more at https://github.com/wheelercj/zq

            [bright_black]You can close this message by pressing @ again.[/bright_black]
            """
        )

    def get_help_text(self) -> str:
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
            [b][green]b[/green][/b] — adds a 5 minute break to the end of the queue.
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


if __name__ == "__main__":
    main()
