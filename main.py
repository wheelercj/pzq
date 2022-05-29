import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
import sys
from zq.app import MyApp


def main():
    q_app = QApplication(sys.argv)
    app = MyApp()
    p = app.palette()
    p.setColor(app.backgroundRole(), QColor(30, 30, 30))
    app.setPalette(p)
    sys.exit(q_app.exec())


if __name__ == "__main__":
    main()
