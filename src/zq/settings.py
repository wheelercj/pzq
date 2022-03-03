from textwrap import dedent


MEETING_MINUTES = 20
TRANSITION_SECONDS = 30  # The time it takes to transition between meetings.
SAVE_INTERVAL_SECONDS = 3  # The names and meeting timer are saved once per n seconds.
EMPTY_LINES_ABOVE = 4  # Number of empty lines inserted above the messages.
WELCOME_MESSAGE = dedent(
    """\
    Welcome to the LAVC computer science tutoring! My name is Chris Wheeler, and I am a computer science student at CSUN and an alumnus of LAVC.

    I might be in a breakout room right now, but I will be back soon. You can see your approximate wait time on the right.
    """
)
ENDING_MESSAGE = dedent(
    """\
    [u][b]wrapping up[/b][/u]
    Tutoring hours are now ending. You can find the next time I will be tutoring on Penji. If you have questions before then, you can contact me at wheelecj@lavc.edu
    """
)
