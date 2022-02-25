from rich.align import Align
from textual.app import App
from textual.widget import Widget


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
            time += f"\n{next_seconds // 60}:{next_seconds % 60:02}"
        if self.queue_size:
            message = f"approximate wait time: {time}"
        else:
            message = f"approximate wait time:\n00:00"
        return Align.center(message, vertical="middle")


class TimerApp(App):
    timer = Timer()

    async def on_mount(self):
        await self.view.dock(self.timer)

    async def on_key(self, event):
        if event.key == "a":
            # add a student to the queue
            self.timer.queue_size += 1
            if self.timer.queue_size == 1 and self.timer.pause:
                self.timer.pause = False
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
        elif event.key == "z" and self.timer.previous_remaining_seconds is not None:
            # return to the previous meeting
            self.timer.remaining_seconds = self.timer.previous_remaining_seconds
            self.timer.previous_remaining_seconds = None
            self.timer.queue_size += 1


TimerApp.run(log="textual.log")
