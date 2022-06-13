import json
from PySide6.QtCore import SIGNAL
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFontDialog,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from textwrap import dedent


def format_setting_string(message: str) -> str:
    """Format a string for the settings menu."""
    return dedent(message).replace("\n\n", "␝").replace("\n", " ").replace("␝", "\n\n")


__DEFAULT_SETTINGS = {
    "font": "DejaVu Sans Mono",
    "font size": 22,
    "meeting minutes": 20,
    "transition seconds": 30,  # The time it takes to transition between meetings.
    "welcome message": format_setting_string(
        """\
        Welcome to the LAVC computer science tutoring! My name is Chris Wheeler, and I
        am a computer science student at CSUN and an alumnus of LAVC.
        
        I might be in a breakout room right now, but I will be back soon. You can see
        your approximate wait time on the right.
        """
    ),
    "starting message": format_setting_string(
        """\
        [b]Starting soon![/b]
        """
    ),
    "ending message": format_setting_string(
        """\
        [u][b]wrapping up[/b][/u]
        
        Tutoring hours are now ending. You can find the next time I will be tutoring on
        Penji. If you have questions before then, you can contact me at
        wheelecj@lavc.edu
        """
    ),
}


settings = {}


def save_settings() -> None:
    with open("settings.json", "w", encoding="utf8") as file:
        json.dump(settings, file)


def load_settings() -> None:
    """Load settings from the settings.json file.

    If the file does not exist or cannot be parsed, the default settings are used.
    """
    try:
        with open("settings.json", "r", encoding="utf8") as file:
            settings.update(json.load(file))
        for key in __DEFAULT_SETTINGS:
            if key not in settings:
                settings[key] = __DEFAULT_SETTINGS[key]
    except (FileNotFoundError):
        print("Could not find settings.json. Creating the file with defaults.")
        settings.update(__DEFAULT_SETTINGS)
        save_settings()
    except (json.decoder.JSONDecodeError):
        print("Could not parse settings.json. Using default settings.")
        settings.update(__DEFAULT_SETTINGS)


load_settings()


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("zq settings")
        self.setGeometry(100, 50, 800, 500)
        layout = QVBoxLayout()

        self.font_ = None
        font_button = QPushButton("change font", self)
        font_button.clicked.connect(self.change_font)
        self.meeting_minutes = QLineEdit()
        self.meeting_minutes.setText(str(settings["meeting minutes"]))
        self.transition_seconds = QLineEdit()
        self.transition_seconds.setText(str(settings["transition seconds"]))
        self.welcome_message = QTextEdit()
        self.welcome_message.setText(settings["welcome message"])
        self.starting_message = QTextEdit()
        self.starting_message.setText(settings["starting message"])
        self.ending_message = QTextEdit()
        self.ending_message.setText(settings["ending message"])

        layout.addWidget(font_button)
        layout.addWidget(QLabel("meeting minutes:"))
        layout.addWidget(self.meeting_minutes)
        layout.addWidget(QLabel("transition seconds:"))
        layout.addWidget(self.transition_seconds)
        layout.addWidget(QLabel("welcome message:"))
        layout.addWidget(self.welcome_message)
        layout.addWidget(QLabel("starting message:"))
        layout.addWidget(self.starting_message)
        layout.addWidget(QLabel("ending message:"))
        layout.addWidget(self.ending_message)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.connect(buttons, SIGNAL("accepted()"), self.accept)
        buttons.connect(buttons, SIGNAL("rejected()"), self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.show()

    def exec(self) -> bool:
        """Runs the settings dialog window.

        Returns:
            True if the user clicked the save button, False otherwise.
        """
        super().exec()
        if self.result() != QDialog.Accepted:
            return False
        if self.font_ is not None:
            settings["font"] = self.font_.family()
            settings["font size"] = self.font_.pointSize()
        try:
            settings["meeting minutes"] = int(self.meeting_minutes.text())
        except ValueError:
            pass
        try:
            settings["transition seconds"] = int(self.transition_seconds.text())
        except ValueError:
            pass
        settings["welcome message"] = self.welcome_message.toPlainText()
        settings["starting message"] = self.starting_message.toPlainText()
        settings["ending message"] = self.ending_message.toPlainText()
        save_settings()
        return True

    def change_font(self) -> None:
        ok, font_ = QFontDialog.getFont(
            QFont(settings["font"], settings["font size"]), self
        )
        if ok:
            self.font_ = font_
