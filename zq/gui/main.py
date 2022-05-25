import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QGridLayout,
    QLineEdit,
    QTextBrowser,
)
from PySide6.QtCore import Qt, Signal


def main():
    q_app = QApplication(sys.argv)
    app = MyApp()
    sys.exit(q_app.exec())


class MyLineEdit(QLineEdit):
    __receiving_new_name_input = False
    __receiving_existing_name_input = False
    __receiving_minutes_input = False

    return_new_name = Signal(str)
    return_existing_name = Signal(str)
    return_minutes = Signal(int)
    ctrl_equal_pressed = Signal()
    ctrl_minus_pressed = Signal()
    char_key_pressed = Signal(str)

    def __init__(self):
        super().__init__()
        self.__ctrl_pressed = False

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key_Control:
            self.__ctrl_pressed = False

    def keyPressEvent(self, event) -> None:
        if self.isHidden():
            # key = event.key()
            # key_text = event.text()
            if event.key() == Qt.Key_Control:
                self.__ctrl_pressed = True
            elif self.__ctrl_pressed and event.key() == Qt.Key_Equal:
                self.ctrl_equal_pressed.emit()
            elif self.__ctrl_pressed and event.key() == Qt.Key_Minus:
                self.ctrl_minus_pressed.emit()
            else:
                self.__ctrl_pressed = False
            if event.text() in ('a', '?', 'd'):
                self.setText("")
                self.show()
                if event.text() == 'a':
                    self.__receiving_new_name_input = True
                elif event.text() == '?':
                    self.__receiving_existing_name_input = True
                elif event.text() == 'd':
                    self.__receiving_minutes_input = True
            elif len(event.text()) == 1:
                self.char_key_pressed.emit(event.text())
        else:
            if event.key() == Qt.Key_Return:
                self.hide()
                if self.__receiving_new_name_input:
                    self.__receiving_new_name_input = False
                    self.return_new_name.emit(self.text())
                elif self.__receiving_existing_name_input:
                    self.__receiving_existing_name_input = False
                    self.return_existing_name.emit(self.text())
                elif self.__receiving_minutes_input:
                    self.__receiving_minutes_input = False
                    try:
                        self.return_minutes.emit(int(self.text()))
                    except ValueError:
                        pass
                self.setText("")
            elif event.key() == Qt.Key_Backspace:
                if self.text() == "":
                    self.hide()
                    self.setText("")
                else:
                    self.setText(self.text()[:-1])
            elif len(event.text()) == 1:
                self.setText(self.text() + event.text())


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


if __name__ == "__main__":
    main()
