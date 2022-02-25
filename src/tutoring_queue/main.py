from rich.align import Align
from textual.app import App
from textual.widget import Widget
from textual.reactive import Reactive
from textual.widgets import ScrollView
from textwrap import dedent


class TextInput(Widget):
    text = Reactive("")

    def render(self):
        return Align.center(self.text)


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
            return Align.center(time, vertical="middle")
        else:
            return Align.center("up to 00:00", vertical="middle")


class TimerApp(App):
    timer = Timer()
    receiving_text_input = False
    text_input = TextInput()
    WELCOME_MESSAGE = dedent(
        """\
        Welcome to the LAVC computer science tutoring! My name is Chris Wheeler, and I am a computer science student at CSUN and an alumnus of LAVC.

        I might be in a breakout room right now, but I will be back soon. You can see your approximate wait time on the right.
        """
    )

    async def on_mount(self):
        await self.view.dock(
            ScrollView(self.WELCOME_MESSAGE, gutter=(5, 5)), self.timer, self.text_input
        )

    async def on_key(self, event):
        if self.receiving_text_input:
            if event.key == "1":
                self.receiving_text_input = False
                self.text_input.text = ""
            elif event.key == "0":
                if self.text_input.text:
                    self.text_input.text = self.text_input.text[:-1]
            else:
                self.text_input.text += event.key
        else:
            if event.key == "a":
                # add a student to the queue
                self.timer.queue_size += 1
                if self.timer.queue_size == 1:
                    self.timer.pause = False
                self.receiving_text_input = True
            elif event.key == "n":
                # go to the next student in queue
                self.timer.queue_size -= 1
                self.timer.previous_remaining_seconds = self.timer.remaining_seconds
                self.timer.remaining_seconds = self.timer.MAX_SECONDS
            elif event.key == "k":
                # pause the timers
                self.timer.pause = not self.timer.pause
            elif event.key == "j":
                # add 5 seconds to the current meeting
                self.timer.remaining_seconds += 5
            elif event.key == "l":
                # subtract up to 5 seconds from the current meeting
                if self.timer.remaining_seconds >= 5:
                    self.timer.remaining_seconds -= 5
                else:
                    self.timer.remaining_seconds = 0
            elif event.key == 'r':
                # reset the timer
                self.timer.remaining_seconds = self.timer.MAX_SECONDS
                self.timer.pause = True
            elif event.key == "z" and self.timer.previous_remaining_seconds is not None:
                # return to the previous meeting
                temp = self.timer.remaining_seconds
                self.timer.remaining_seconds = self.timer.previous_remaining_seconds
                self.timer.previous_remaining_seconds = temp
                self.timer.queue_size += 1


TimerApp.run(log="textual.log")
