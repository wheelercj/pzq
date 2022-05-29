import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "tui":
        from zq import tui
        tui.main()
    else:
        from zq import gui
        gui.main()

if __name__ == "__main__":
    main()
