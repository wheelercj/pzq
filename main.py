import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys
from zq import tui, gui


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        gui.main()
    else:
        tui.main()


if __name__ == "__main__":
    main()
