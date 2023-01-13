import sys
from importlib import metadata as importlib_metadata

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

try:
    from zq import ZQ
except ImportError:
    from .zq import ZQ


def main():
    # Linux desktop environments use app's .desktop file to integrate the app
    # to their application menus. The .desktop file of this app will include
    # StartupWMClass key, set to app's formal name, which helps associate
    # app's windows to its menu item.
    #
    # For association to work any windows of the app must have WMCLASS
    # property set to match the value set in app's desktop file. For PySide2
    # this is set with setApplicationName().

    # Find the name of the module that was used to start the app
    app_module = sys.modules["__main__"].__package__
    # Retrieve the app's metadata
    metadata = importlib_metadata.metadata(app_module)

    QApplication.setApplicationName(metadata["Formal-Name"])

    app = QApplication(sys.argv)
    main_window = ZQ()
    p = main_window.palette()
    p.setColor(main_window.backgroundRole(), QColor(30, 30, 30))
    main_window.setPalette(p)
    sys.exit(app.exec())
