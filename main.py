import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "gui":
            from zq import gui
            gui.main()
        else:
            from zq import tui
            tui.main()
    except Exception as e:
        from zq.settings import save_settings
        save_settings()
        raise e


if __name__ == "__main__":
    main()
