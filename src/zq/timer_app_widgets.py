from rich.markdown import Markdown  # https://github.com/Textualize/rich
from textual.widget import Widget
from textual.reactive import Reactive
from textual.views import GridView

# internal imports
from timer import Timer


class TextInputField(Widget):
    text = Reactive("")

    def render(self) -> Markdown:
        return Markdown(self.text)


class TimerAppWidgets(GridView):
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
