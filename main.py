import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from zq import tui


def main():
    tui.main()


if __name__ == "__main__":
    main()
