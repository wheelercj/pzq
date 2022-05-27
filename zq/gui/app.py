import chime  # https://pypi.org/project/chime/
from PySide6.QtCore import Qt, QTimer, QObject, SIGNAL
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QTextBrowser,
)
import random
import sqlite3
from zq.common import (
    Mode,
    load_students,
    get_timer_message,
    add_5_minute_break,
    get_help_text,
    get_about_text,
    convert_Rich_style_to_html,
    go_to_next_student,
    return_to_previous_meeting,
    remove_last_student,
    VERSION,
)
from zq.gui.line_edit import MyLineEdit
from zq.settings import settings, open_settings_file, save_settings


def set_QTextBrowser_text(tb: QTextBrowser, text: str) -> None:
    """Formats and sets text for a QTextBrowser."""
    # Each line must be appended individually because QTextBrowser.setText does
    # not allow both HTML and newlines in the same string.
    tb.clear()
    for line in convert_Rich_style_to_html(text).split("\n"):
        tb.append(line)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        chime.theme("material")
        self.timer = QTimer(self)
        QObject.connect(self.timer, SIGNAL("timeout()"), self.tick)
        self.timer.start(1000)
        self.autosave_timer = QTimer(self)
        QObject.connect(
            self.autosave_timer, SIGNAL("timeout()"), self.save_all_students
        )
        self.autosave_timer.start(settings["save interval seconds"])
        self.max_individual_seconds = (
            settings["meeting minutes"] * 60 + settings["transition seconds"]
        )
        self.min_empty_waitlist_seconds = settings["meeting minutes"] / 2 * 60
        self.group_seconds = 0  # counts up
        self.mode_names = [
            "group meeting",
            f"{settings['meeting minutes']}-minute individual meetings",
            "start",
            "end",
        ]
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
        self.line_edit.ctrl_equal_pressed.connect(self.increase_font_size)
        self.line_edit.ctrl_minus_pressed.connect(self.decrease_font_size)
        self.line_edit.char_key_pressed.connect(self.handle_char_key_pressed)

        self.welcome = QTextBrowser()
        self.welcome.setAcceptRichText(True)
        self.welcome.setOpenExternalLinks(True)
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
        self.timer_message.alignment = Qt.AlignLeft
        self.timer_message.alignment = Qt.AlignVCenter
        self.timer_message.setViewportMargins(25, 25, 25, 25)
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
        self.setGeometry(100, 50, 800, 500)
        self.setContentsMargins(10, 10, 10, 10)
        self.show()

    def append_name(self, name: str):
        self.student_names.append(name)
        self.update_timer_message()

    def update_timer_message(self):
        if not self.student_names:
            set_QTextBrowser_text(
            self.timer_message, "[#8E8E8E](no students in queue)[/#8E8E8E]"
        )
            return
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
            self.max_individual_seconds = (
                int(minutes) * 60 + settings["transition seconds"]
            )
            self.min_empty_waitlist_seconds = int(minutes) / 2 * 60
            self.mode_names[
                Mode.INDIVIDUAL.value
            ] = f"{minutes}-minute individual meetings"
            self.update_timer_message()
            save_settings()

    def increase_font_size(self):
        font = self.timer_message.currentFont()
        size = font.pointSize()
        font.setPointSize(size + 2)
        self.timer_message.setFont(font)
        font = self.welcome.currentFont()
        font.setPointSize(size + 2)
        self.welcome.setFont(font)

    def decrease_font_size(self):
        font = self.timer_message.currentFont()
        size = font.pointSize()
        if size <= 2:
            return
        font.setPointSize(size - 2)
        self.timer_message.setFont(font)
        font = self.welcome.currentFont()
        font.setPointSize(size - 2)
        self.welcome.setFont(font)

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
            open_settings_file()
        elif key == "n" and len(self.student_names):
            (
                self.student_names,
                self.individual_seconds,
                self.previous_individual_seconds,
            ) = go_to_next_student(
                self.student_names, self.individual_seconds, self.max_individual_seconds
            )
        elif key == "z" and self.previous_individual_seconds is not None:
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
        if self.current_mode == Mode.START:
            set_QTextBrowser_text(self.timer_message, settings["starting message"])
        elif self.current_mode == Mode.END:
            set_QTextBrowser_text(self.timer_message, settings["ending message"])
        else:
            self.update_timer_message()
