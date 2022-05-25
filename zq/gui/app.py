from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QTextBrowser,
)
from zq.common import (
    load_students,
    add_5_minute_break,
    get_help_text,
    get_about_text,
    VERSION,
)
from zq.gui.line_edit import MyLineEdit


class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        
        self.line_edit = MyLineEdit()
        self.line_edit.grabKeyboard()
        self.line_edit.hide()
        self.line_edit.return_new_name.connect(self.append_name)
        self.line_edit.return_existing_name.connect(self.remove_name)
        self.line_edit.return_minutes.connect(self.change_minutes)
        self.line_edit.ctrl_equal_pressed.connect(self.increase_font_size)
        self.line_edit.ctrl_minus_pressed.connect(self.decrease_font_size)

        self.welcome = QTextBrowser()
        self.welcome.setAcceptRichText(True)
        self.welcome.setOpenExternalLinks(True)

        self.timer = QTextBrowser()
        self.timer.setAcceptRichText(True)
        self.timer.setOpenExternalLinks(True)

        layout = QGridLayout()
        layout.addWidget(self.welcome, 0, 0)
        layout.addWidget(self.timer, 0, 1)
        layout.addWidget(self.line_edit, 1, 0, 1, 2)

        self.setLayout(layout)
        self.setWindowTitle("zq")
        self.setGeometry(100, 50, 800, 500)
        self.show()

    def append_name(self):
        text = self.line_edit.text()
        self.timer.append(text)  # TODO
        self.line_edit.clear()

    def remove_name(self):
        text = self.line_edit.text()
        self.timer.remove(text)  # TODO
        self.line_edit.clear()

    def change_minutes(self):
        pass  # TODO

    def show_settings(self):
        print('yes')

    def increase_font_size(self):
        font = self.timer.currentFont()
        size = font.pointSize()
        font.setPointSize(size + 5)
        self.timer.setFont(font)
        font = self.welcome.currentFont()
        font.setPointSize(size + 5)
        self.welcome.setFont(font)

    def decrease_font_size(self):
        font = self.timer.currentFont()
        size = font.pointSize()
        if size <= 5:
            return
        font.setPointSize(size - 5)
        self.timer.setFont(font)
        font = self.welcome.currentFont()
        font.setPointSize(size - 5)
        self.welcome.setFont(font)
