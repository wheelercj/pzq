import chime  # https://pypi.org/project/chime/
import os
from PySide6.QtCore import Qt, QTimer, QObject, SIGNAL
from PySide6.QtGui import QIcon, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QGridLayout,
    QTextBrowser,
    QWidget,
)
import random
import sqlite3
try:
    from common import (
        add_5_minute_break,
        convert_Rich_style_to_html,
        get_about_text,
        get_help_text,
        get_timer_message,
        go_to_next_student,
        load_students,
        Mode,
        remove_last_student,
        return_to_previous_meeting,
        VERSION,
    )
except ImportError:
    from .common import (
        add_5_minute_break,
        convert_Rich_style_to_html,
        get_about_text,
        get_help_text,
        get_timer_message,
        go_to_next_student,
        load_students,
        Mode,
        remove_last_student,
        return_to_previous_meeting,
        VERSION,
    )
try:
    from line_edit import MyLineEdit
except ImportError:
    from .line_edit import MyLineEdit
try:
    from settings import settings, save_settings, SettingsDialog
except ImportError:
    from .settings import settings, save_settings, SettingsDialog


def set_QTextBrowser_text(tb: QTextBrowser, text: str) -> None:
    """Formats and sets text for a QTextBrowser."""
    # Each line must be appended individually because QTextBrowser.setText does
    # not allow both HTML and newlines in the same string.
    tb.clear()
    tb.setCurrentCharFormat(QTextCharFormat())
    for line in convert_Rich_style_to_html(text).split("\n"):
        tb.append(line)
    tb.scrollToAnchor("top")


class ZQ(QWidget):
    def __init__(self):
        super().__init__()
        chime.theme("material")
        self.__font_size = 18
        self.timer = QTimer(self)
        QObject.connect(self.timer, SIGNAL("timeout()"), self.tick)
        self.timer.start(1000)
        self.max_individual_seconds = 0
        self.update_max_individual_seconds()
        self.min_empty_waitlist_seconds = settings["meeting minutes"] / 2 * 60
        self.group_seconds = 0  # counts up
        self.mode_names = []
        self.update_mode_names()
        self.current_mode = Mode.GROUP
        (self.student_names, self.individual_seconds) = load_students(
            self.max_individual_seconds
        )
        self.paused = True
        self.previous_individual_seconds = None

        self.__showing_help = False
        self.__showing_about = False

        self.line_edit = MyLineEdit()
        self.line_edit.grabKeyboard()
        self.line_edit.hide()
        self.line_edit.return_new_name.connect(self.append_name)
        self.line_edit.return_existing_name.connect(self.remove_name)
        self.line_edit.return_minutes.connect(self.change_minutes)
        self.line_edit.char_key_pressed.connect(self.handle_char_key_pressed)
        self.line_edit.f11_key_pressed.connect(self.toggle_fullscreen)
        self.line_edit.ctrl_w_pressed.connect(self.close)
        self.line_edit.ctrl_c_pressed.connect(self.copy)

        self.welcome = QTextBrowser()
        self.welcome.setAcceptRichText(True)
        self.welcome.setOpenExternalLinks(True)
        self.welcome.setFont(QFont("Cascadia Code", self.__font_size))
        self.welcome.alignment = Qt.AlignLeft
        self.welcome.alignment = Qt.AlignVCenter
        self.welcome.setViewportMargins(25, 25, 25, 25)
        set_QTextBrowser_text(self.welcome, settings["welcome message"])
        self.welcome.setStyleSheet(
            """
                QTextBrowser {
                    border: none;
                    color: rgb(255, 255, 255);
                    background-color: rgb(30, 30, 30);
                }
            """
        )

        self.timer_message = QTextBrowser()
        self.timer_message.setAcceptRichText(True)
        self.timer_message.setOpenExternalLinks(True)
        self.timer_message.setFont(QFont("Cascadia Code", self.__font_size))
        self.timer_message.alignment = Qt.AlignLeft
        self.timer_message.alignment = Qt.AlignVCenter
        self.timer_message.setViewportMargins(100, 25, 25, 25)
        self.timer_message.setStyleSheet(
            """
                QTextBrowser {
                    border: none;
                    color: rgb(255, 255, 255);
                    background-color: rgb(30, 30, 30);
                }
            """
        )
        set_QTextBrowser_text(
            self.timer_message, "[#8E8E8E](no students in queue)[/#8E8E8E]"
        )

        self.layout = QGridLayout(self)
        self.layout.addWidget(self.welcome, 0, 0)
        self.layout.addWidget(self.timer_message, 0, 1)
        self.layout.addWidget(self.line_edit, 1, 0, 1, 2)

        self.setWindowTitle("zq")
        if os.path.exists("app"):
            self.setWindowIcon(QIcon("app/zq/resources/timer.svg"))
        else:
            self.setWindowIcon(QIcon("src/zq/resources/timer.svg"))
        self.setGeometry(
            100, 50, 800, 500
        )  # This forces the window to open on a certain screen (the "primary" screen?).
        self.setContentsMargins(10, 10, 10, 10)
        self.showMaximized()

    def __del__(self):
        self.save_all_students()

    def append_name(self, name: str):
        self.student_names.append(name)
        self.update_timer_message()

    def update_mode_names(self):
        self.mode_names = [0] * len(Mode)
        self.mode_names[Mode.GROUP.value] = "group meeting"
        self.mode_names[
            Mode.INDIVIDUAL.value
        ] = f"{settings['meeting minutes']}-minute individual meetings"
        self.mode_names[Mode.START.value] = "start"
        self.mode_names[Mode.END.value] = "end"

    def update_max_individual_seconds(self):
        self.max_individual_seconds = (
            settings["meeting minutes"] * 60 + settings["transition seconds"]
        )

    def update_timer_message(self):
        if self.current_mode == Mode.START:
            set_QTextBrowser_text(self.timer_message, settings["starting message"])
        elif self.current_mode == Mode.END:
            set_QTextBrowser_text(self.timer_message, settings["ending message"])
        elif not self.student_names:
            set_QTextBrowser_text(
                self.timer_message, "[#8E8E8E](no students in queue)[/#8E8E8E]"
            )
        else:
            set_QTextBrowser_text(
                self.timer_message,
                get_timer_message(
                    self.current_mode,
                    self.mode_names,
                    self.student_names,
                    self.group_seconds,
                    self.individual_seconds,
                    self.max_individual_seconds,
                ),
            )

    def remove_name(self):
        name = self.line_edit.text()
        names = self.student_names
        if name in names:
            names.remove(name)
        if names:
            if names[0].endswith("-minute break"):
                self.individual_seconds = int(names[0].split("-")[0]) * 60
            else:
                self.individual_seconds = self.max_individual_seconds
        self.update_timer_message()

    def change_minutes(self):
        minutes = self.line_edit.text()
        if minutes.isdigit() and int(minutes) > 0:
            settings["meeting minutes"] = int(minutes)
            self.update_max_individual_seconds()
            self.min_empty_waitlist_seconds = int(minutes) / 2 * 60
            self.update_mode_names()
            self.update_timer_message()
            save_settings()

    def increase_font_size(self):
        self.__font_size += 2
        self.welcome.setFont(QFont("Cascadia Code", self.__font_size))
        self.timer_message.setFont(QFont("Cascadia Code", self.__font_size))

    def decrease_font_size(self):
        if self.__font_size <= 2:
            return
        self.__font_size -= 2
        self.welcome.setFont(QFont("Cascadia Code", self.__font_size))
        self.timer_message.setFont(QFont("Cascadia Code", self.__font_size))

    def save_all_students(self):
        """Saves all student names and the next's wait time to the database.

        Every row of the seconds column receives the same number: the next student's
        wait time.
        """
        with sqlite3.connect("students.db") as conn:
            conn.execute("DELETE FROM students")
            cursor = conn.cursor()
            for name in self.student_names:
                cursor.execute(
                    "INSERT INTO students (name, seconds) VALUES (?, ?)",
                    (name, self.individual_seconds),
                )
            conn.commit()

    def tick(self) -> None:
        """Called once each second; controls the timer."""
        if (
            self.student_names
            and self.individual_seconds
            and not self.paused
            and (
                (self.current_mode == Mode.INDIVIDUAL and len(self.student_names) > 1)
                or self.individual_seconds > self.min_empty_waitlist_seconds
            )
        ):
            self.individual_seconds -= 1
            self.update_timer_message()
        if self.current_mode == Mode.GROUP and self.student_names:
            self.group_seconds += 1
            self.update_timer_message()
        if self.individual_seconds == settings["transition seconds"]:
            chime.warning()
        elif self.individual_seconds == 1:
            chime.error()

    def toggle_fullscreen(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def copy(self):
        if self.welcome.hasFocus():
            self.welcome.copy()
        elif self.timer_message.hasFocus():
            self.timer_message.copy()

    def handle_char_key_pressed(self, key: str):
        if key == "h":
            if self.__showing_help:
                set_QTextBrowser_text(self.welcome, settings["welcome message"])
                self.__showing_help = False
            else:
                set_QTextBrowser_text(self.welcome, get_help_text())
                self.__showing_help = True
                self.__showing_about = False
        elif key == "@":
            if self.__showing_about:
                set_QTextBrowser_text(self.welcome, settings["welcome message"])
                self.__showing_about = False
            else:
                set_QTextBrowser_text(self.welcome, get_about_text(VERSION))
                self.__showing_about = True
                self.__showing_help = False
        elif key == "o":
            self.line_edit.releaseKeyboard()
            settings_dialog = SettingsDialog()
            user_clicked_save = settings_dialog.exec()
            if user_clicked_save:
                if not self.__showing_help and not self.__showing_about:
                    set_QTextBrowser_text(self.welcome, settings["welcome message"])
                self.update_mode_names()
                self.update_max_individual_seconds()
                self.update_timer_message()
            self.line_edit.grabKeyboard()
        elif key == "n" and len(self.student_names):
            (
                self.student_names,
                self.individual_seconds,
                self.previous_individual_seconds,
            ) = go_to_next_student(
                self.student_names, self.individual_seconds, self.max_individual_seconds
            )
        elif (
            key == "z"
            and self.previous_individual_seconds is not None
            and self.student_names
        ):
            (
                self.student_names,
                self.individual_seconds,
                self.previous_individual_seconds,
            ) = return_to_previous_meeting(
                self.student_names,
                self.individual_seconds,
                self.previous_individual_seconds,
            )
        elif key == "!":
            (self.student_names, self.individual_seconds) = remove_last_student(
                self.student_names, self.individual_seconds, self.max_individual_seconds
            )
        elif key == "b":
            add_5_minute_break(self.student_names)
        elif key == "$":  # randomize the order of the students in the queue
            random.shuffle(self.student_names)
        elif key == "m":
            if self.current_mode == Mode.GROUP:
                self.current_mode = Mode.INDIVIDUAL
            else:
                self.current_mode = Mode.GROUP
                self.group_seconds = 0
        elif key == "home":
            # change the meeting mode to say that tutoring hours start soon
            self.current_mode = Mode.START
        elif key == "end":
            # change the meeting mode to say that tutoring hours end soon
            self.current_mode = Mode.END
        elif key in ("k", " "):
            # pause the timers
            self.paused = not self.paused
        elif key == "j":
            # add 5 seconds to the current meeting
            self.individual_seconds += 5
        elif key == "l":
            # subtract up to 5 seconds from the current meeting
            if self.individual_seconds >= 5:
                self.individual_seconds -= 5
            else:
                self.individual_seconds = 0
        elif key == "left":
            # add 30 seconds to the current meeting
            self.individual_seconds += 30
        elif key == "right":
            # subtract up to 30 seconds from the current meeting
            if self.individual_seconds >= 30:
                self.individual_seconds -= 30
            else:
                self.individual_seconds = 0
        elif key == "r":
            # reset the timer
            names = self.student_names
            if names and names[0].endswith("-minute break"):
                self.individual_seconds = int(names[0].split("-")[0]) * 60
            else:
                self.individual_seconds = self.max_individual_seconds
            self.paused = True
        elif key == "s":
            self.save_all_students()
        elif key in "=+":
            self.increase_font_size()
        elif key in "-_":
            self.decrease_font_size()
        self.update_timer_message()
