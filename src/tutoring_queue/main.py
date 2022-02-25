from rich.align import Align
from rich.markdown import Markdown
from textual.app import App
from textual.widget import Widget
from textual.reactive import Reactive
from textual.views import GridView
from textual.widgets import ScrollView
from textwrap import dedent


class TextInput(Widget):
    text = Reactive("")

    def render(self):
        return Markdown(self.text)


class Timer(Widget):
    MAX_SECONDS = 20 * 60
    TRANSITION_SECONDS = 30
    remaining_seconds = MAX_SECONDS
    queue_size = 0
    pause = True
    previous_remaining_seconds = None

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self):
        if self.queue_size and self.remaining_seconds and not self.pause:
            self.remaining_seconds -= 1
        time = ""
        for i in range(self.queue_size):
            next_seconds = (
                self.remaining_seconds
                + (i * self.MAX_SECONDS)
                + (i * self.TRANSITION_SECONDS)
            )
            time += f"up to {next_seconds // 60}:{next_seconds % 60:02}\n\n"
        if self.queue_size:
            return Align.center("\n\n\n\n\n" + time)
        else:
            return Align.center("\n\n\n\n\nup to 00:00")


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
                self.widgets.text_input.text = ""
                self.widgets.timer.queue_size += 1
                if self.widgets.timer.queue_size == 1:
                    self.widgets.timer.pause = False
            elif event.key == "ctrl+h":  # backspace
                if len(self.widgets.text_input.text) > len("name: "):
                    self.widgets.text_input.text = self.widgets.text_input.text[:-1]
            elif not event.key.startswith("ctrl+"):
                self.widgets.text_input.text += event.key
        else:
            if event.key == "a":
                # add a student to the queue
                self.receiving_text_input = True
                self.widgets.text_input.text = "name: "
            elif event.key == "n":
                # go to the next student in queue
                self.widgets.timer.queue_size -= 1
                self.widgets.timer.previous_remaining_seconds = (
                    self.widgets.timer.remaining_seconds
                )
                self.widgets.timer.remaining_seconds = self.widgets.timer.MAX_SECONDS
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
                self.widgets.timer.queue_size += 1


TimerApp.run(log="textual.log")
