from PySide6.QtWidgets import QApplication
import sys
from zq.gui.app import MyApp


def main():
    q_app = QApplication(sys.argv)
    app = MyApp()
    sys.exit(q_app.exec())


if __name__ == "__main__":
    main()
