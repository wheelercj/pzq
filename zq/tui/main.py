from textual.app import App  # https://github.com/Textualize/textual
from textual.events import Key
from textual.widgets import ScrollView
import random
from zq.common import (
    load_students,
    add_5_minute_break,
    get_help_text,
    get_about_text,
    go_to_next_student,
    return_to_previous_meeting,
    remove_last_student,
    VERSION,
)
from zq.settings import settings, save_settings, open_settings_file
from zq.tui.text_input import TextInput
from zq.tui.timer import Mode
from zq.tui.timer_app_widgets import TimerAppWidgets


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
        (
            self.widgets.timer.student_names,
            self.widgets.timer.individual_seconds,
        ) = load_students(settings["meeting minutes"] + settings["transition seconds"])
        await self.view.dock(self.widgets)

    async def shutdown(self):
        self.widgets.timer.save_all_students()
        await super().shutdown()

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
        names = self.widgets.timer.student_names
        if name in names:
            if name == names[0]:
                if len(names) > 1 and names[1].endswith("-minute break"):
                    self.widgets.timer.individual_seconds = (
                        int(names[1].split("-")[0]) * 60
                    )
                else:
                    self.widgets.timer.individual_seconds = (
                        self.widgets.timer.max_individual_seconds
                    )
            names.remove(name)
            if not len(names):
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
            open_settings_file()
        elif key == "a":  # add a student to the queue
            self.receiving_new_name_input = True
            self.widgets.text_input_field.text = "name: "
        elif key == "n" and len(self.widgets.timer.student_names) > 1:
            (
                self.widgets.timer.student_names,
                self.widgets.timer.individual_seconds,
                self.widgets.timer.previous_individual_seconds,
            ) = go_to_next_student(
                self.widgets.timer.student_names,
                self.widgets.timer.individual_seconds,
                self.widgets.timer.max_individual_seconds,
            )
        elif key == "z" and self.widgets.timer.previous_individual_seconds is not None:
            (
                self.widgets.timer.student_names,
                self.widgets.timer.individual_seconds,
                self.widgets.timer.previous_individual_seconds,
            ) = return_to_previous_meeting(
                self.widgets.timer.student_names,
                self.widgets.timer.individual_seconds,
                self.widgets.timer.previous_individual_seconds,
            )
        elif key == "!":
            (
                self.widgets.timer.student_names,
                self.widgets.timer.individual_seconds,
            ) = remove_last_student(
                self.widgets.timer.student_names,
                self.widgets.timer.individual_seconds,
                self.widgets.timer.max_individual_seconds,
            )
        elif key == "?":  # remove student by name
            self.receiving_existing_name_input = True
            self.widgets.text_input_field.text = "name to remove: "
        elif key == "b":
            add_5_minute_break(self.widgets.timer.student_names)
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
            names = self.widgets.timer.student_names
            if names and names[0].endswith("-minute break"):
                self.widgets.timer.individual_seconds = int(names[0].split("-")[0]) * 60
            else:
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
            await self.widgets.welcome.update(get_help_text())

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
                settings["empty lines above"] * "\n" + get_about_text(VERSION)
            )


if __name__ == "__main__":
    main()
