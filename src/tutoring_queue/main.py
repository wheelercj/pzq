from rich.align import Align
from rich.markdown import Markdown
from textual.app import App
from textual.widget import Widget
from textual.reactive import Reactive
from textual.views import GridView
from textual.widgets import ScrollView
from textwrap import dedent
import random
import chime


class TextInput(Widget):
    text = Reactive("")

    def render(self):
        return Markdown(self.text)


class Timer(Widget):
    TRANSITION_SECONDS = 30
    MAX_SECONDS = 20 * 60 + TRANSITION_SECONDS
    MIN_EMPTY_WAITLIST_SECONDS = 10 * 60
    remaining_seconds = MAX_SECONDS
    MODES = ["group meeting", "20-minute individual meetings"]
    current_mode_index = 0
    student_names = []
    pause = True
    previous_remaining_seconds = None

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self):
        if (
            self.student_names
            and self.remaining_seconds
            and not self.pause
            and (
                (self.current_mode_index == 1 and len(self.student_names) > 1)
                or self.remaining_seconds > self.MIN_EMPTY_WAITLIST_SECONDS
            )
        ):
            self.remaining_seconds -= 1
        if self.remaining_seconds == 30:
            chime.success()
        elif self.remaining_seconds == 1:
            chime.info()
        if not self.student_names:
            return Align.center("\n\n\n\n\n(no students in queue)")
        else:
            timer_message = (
                f"[bright_black]{self.MODES[self.current_mode_index]}[/bright_black]"
                "\n\n[u][b]meeting in progress with:[/b][/u]"
                f"\n{self.student_names[0]}"
            )
            if len(self.student_names) > 1:
                if self.current_mode_index == 0:
                    for i, name in enumerate(self.student_names[1:]):
                        timer_message += f"\n{name}"
                else:
                    timer_message += f"\n\n[u][b]waiting:[/b][/u]\n"
                    for i, name in enumerate(self.student_names[1:]):
                        next_seconds = (
                            self.remaining_seconds
                            + ((i) * self.MAX_SECONDS)
                        )
                        timer_message += (
                            f"{next_seconds // 60}:{next_seconds % 60:02} {name}\n\n"
                        )
            return Align.center("\n\n\n\n\n" + timer_message)


class TimerAppWidgets(GridView):
    timer = Timer()
    text_input = TextInput()
    WELCOME_MESSAGE = dedent(
        """\
        Welcome to the LAVC computer science tutoring! My name is Chris Wheeler, and I am a computer science student at CSUN and an alumnus of LAVC.

        I might be in a breakout room right now, but I will be back soon. You can see your approximate wait time on the right.
        """
    )

    def on_mount(self):
        self.grid.set_gap(2, 1)
        self.grid.set_gutter(1)
        self.grid.set_align("center", "center")

        self.grid.add_column("col", repeat=2)
        self.grid.add_row("row", repeat=15)
        self.grid.add_areas(
            text_input="col1-start|col2-end,row15",
            welcome_message="col1,row1-start|row14-end",
            timer="col2,row1-start|row14-end",
        )

        self.grid.place(
            text_input=self.text_input,
            welcome_message=ScrollView(self.WELCOME_MESSAGE, gutter=(5, 5)),
            timer=self.timer,
        )


class TimerApp(App):
    receiving_text_input = False
    widgets = TimerAppWidgets()

    async def on_mount(self):
        await self.view.dock(self.widgets)

    async def on_key(self, event):
        if self.receiving_text_input:
            if event.key == "enter":
                self.receiving_text_input = False
                name = self.widgets.text_input.text[len("name: ") :]
                self.widgets.timer.student_names.append(name)
                self.widgets.text_input.text = ""
                if len(self.widgets.timer.student_names) == 1:
                    self.widgets.timer.pause = False
            elif event.key == "ctrl+h":  # backspace
                if len(self.widgets.text_input.text) > len("name: "):
                    self.widgets.text_input.text = self.widgets.text_input.text[:-1]
                else:
                    self.receiving_text_input = False
                    self.widgets.text_input.text = ""
            elif not event.key.startswith("ctrl+"):
                self.widgets.text_input.text += event.key
        else:
            if event.key == "a":
                # add a student to the queue
                self.receiving_text_input = True
                self.widgets.text_input.text = "name: "
            elif event.key == "n":
                # go to the next student in queue
                self.widgets.timer.student_names.append(
                    self.widgets.timer.student_names.pop(0)
                )
                self.widgets.timer.previous_remaining_seconds = (
                    self.widgets.timer.remaining_seconds
                )
                self.widgets.timer.remaining_seconds = self.widgets.timer.MAX_SECONDS
            elif event.key == "!":
                # remove the student at the end of the queue
                self.widgets.timer.student_names.pop()
            elif event.key == "$":
                # randomize the order of the students in the queue
                random.shuffle(self.widgets.timer.student_names)
            elif event.key == "m":
                # toggle the queue mode
                self.widgets.timer.current_mode_index = int(
                    not self.widgets.timer.current_mode_index
                )
            elif event.key == "k":
                # pause the timers
                self.widgets.timer.pause = not self.widgets.timer.pause
            elif event.key == "j":
                # add 5 seconds to the current meeting
                self.widgets.timer.remaining_seconds += 5
            elif event.key == "l":
                # subtract up to 5 seconds from the current meeting
                if self.widgets.timer.remaining_seconds >= 5:
                    self.widgets.timer.remaining_seconds -= 5
                else:
                    self.widgets.timer.remaining_seconds = 0
            elif event.key == "r":
                # reset the timer
                self.widgets.timer.remaining_seconds = self.widgets.timer.MAX_SECONDS
                self.widgets.timer.pause = True
            elif (
                event.key == "z"
                and self.widgets.timer.previous_remaining_seconds is not None
            ):
                # return to the previous meeting
                temp = self.widgets.timer.remaining_seconds
                self.widgets.timer.remaining_seconds = (
                    self.widgets.timer.previous_remaining_seconds
                )
                self.widgets.timer.previous_remaining_seconds = temp
                self.widgets.timer.student_names.insert(
                    0, self.widgets.timer.student_names.pop()
                )


TimerApp.run(log="textual.log")
