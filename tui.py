import os
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


VERSION = "0.1.0"


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
        self.receiving_new_name_input, name = self.text_input(key, "name: ")
        self.widgets.text_input_field.text = self.text_input.text
        if name:
            if name in self.widgets.timer.student_names:
                name += " II"
            self.widgets.timer.student_names.append(name)
            if len(self.widgets.timer.student_names) == 1:
                self.widgets.timer.pause = False

    def get_existing_name_input(self, key: str) -> None:
        self.receiving_existing_name_input, name = self.text_input(
            key, "name to remove: "
        )
        self.widgets.text_input_field.text = self.text_input.text
        if name:
            if name in self.widgets.timer.student_names:
                self.widgets.timer.student_names.remove(name)
                if not len(self.widgets.timer.student_names):
                    self.widgets.timer.pause = True

    def get_minutes_input(self, key: str) -> None:
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
        if self.receiving_new_name_input:
            self.get_new_name_input(event.key)
        elif self.receiving_existing_name_input:
            self.get_existing_name_input(event.key)
        elif self.receiving_minutes_input:
            self.get_minutes_input(event.key)
        else:
            if event.key == "h":
                await self.toggle_help_display()
            elif event.key == "@":
                await self.toggle_about_display()
            elif event.key == "o":
                self.open_settings_file()
            elif event.key == "a":  # add a student to the queue
                self.receiving_new_name_input = True
                self.widgets.text_input_field.text = "name: "
            elif event.key == "n" and len(self.widgets.timer.student_names) > 1:
                self.go_to_next_student()
            elif (
                event.key == "z"
                and self.widgets.timer.previous_individual_seconds is not None
            ):
                self.return_to_previous_meeting()
            elif event.key == "!":
                self.remove_last_student()
            elif event.key == "?":  # remove student by name
                self.receiving_existing_name_input = True
                self.widgets.text_input_field.text = "name to remove: "
            elif event.key == "$":  # randomize the order of the students in the queue
                random.shuffle(self.widgets.timer.student_names)
            elif event.key == "m":
                if self.widgets.timer.current_mode == Mode.GROUP:
                    self.widgets.timer.current_mode = Mode.INDIVIDUAL
                else:
                    self.widgets.timer.current_mode = Mode.GROUP
                    self.widgets.timer.group_seconds = 0
            elif event.key == "home":
                # change the meeting mode to say that tutoring hours start soon
                self.widgets.timer.current_mode = Mode.START
            elif event.key == "end":
                # change the meeting mode to say that tutoring hours end soon
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
            elif event.key == "left":
                # add 30 seconds to the current meeting
                self.widgets.timer.individual_seconds += 30
            elif event.key == "right":
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

    async def toggle_help_display(self) -> None:
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
        """Open's the app's settings file for the user to view."""
        folder_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        )
        settings_path = os.path.join(folder_path, "settings.yaml")
        webbrowser.open(os.path.normpath(settings_path))

    def go_to_next_student(self) -> None:
        self.widgets.timer.student_names.append(self.widgets.timer.student_names.pop(0))
        self.widgets.timer.previous_individual_seconds = (
            self.widgets.timer.individual_seconds
        )
        self.widgets.timer.individual_seconds = (
            self.widgets.timer.max_individual_seconds
        )

    def return_to_previous_meeting(self) -> None:
        temp = self.widgets.timer.individual_seconds
        self.widgets.timer.individual_seconds = (
            self.widgets.timer.previous_individual_seconds
        )
        self.widgets.timer.previous_individual_seconds = temp
        self.widgets.timer.student_names.insert(
            0, self.widgets.timer.student_names.pop()
        )

    def remove_last_student(self) -> None:
        if len(self.widgets.timer.student_names):
            self.widgets.timer.student_names.pop()
        if len(self.widgets.timer.student_names) == 1:
            self.widgets.timer.individual_seconds = (
                self.widgets.timer.max_individual_seconds
            )

    def get_about_text(self) -> str:
        return dedent(
            f"""\
            zq
            
            version [white]{VERSION}[/white]

            Developed by Chris Wheeler and licensed under the MIT license. This app is free and open source. You can find the source code and license, join discussions, submit bug reports or feature requests, and more at https://github.com/wheelercj/zq

            [bright_black]You can close this message by pressing @ again.[/bright_black]
            """
        )

    def get_help_text(self) -> str:
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
