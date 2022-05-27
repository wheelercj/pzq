from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit


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
            if event.key() == Qt.Key_Control:
                self.__ctrl_pressed = True
            elif self.__ctrl_pressed and event.key() == Qt.Key_Equal:
                self.ctrl_equal_pressed.emit()
            elif self.__ctrl_pressed and event.key() == Qt.Key_Minus:
                self.ctrl_minus_pressed.emit()
            else:
                self.__ctrl_pressed = False
            if event.text() in ("a", "?", "d"):
                self.setText("")
                self.show()
                if event.text() == "a":
                    self.__receiving_new_name_input = True
                elif event.text() == "?":
                    self.__receiving_existing_name_input = True
                elif event.text() == "d":
                    self.__receiving_minutes_input = True
            elif len(event.text()) == 1:
                self.char_key_pressed.emit(event.text())
            elif event.key() == Qt.Key_Left:
                self.char_key_pressed.emit("left")
            elif event.key() == Qt.Key_Right:
                self.char_key_pressed.emit("right")
            elif event.key() == Qt.Key_Home:
                self.char_key_pressed.emit("home")
            elif event.key() == Qt.Key_End:
                self.char_key_pressed.emit("end")
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
            elif len(event.text()) == 1 and event.key() != Qt.Key_Delete:
                self.setText(self.text() + event.text())
