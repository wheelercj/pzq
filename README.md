# zq

Easy Zoom queueing for tutors (and others!) using breakout rooms and two devices.

Some meeting waitlists are confusing and isolating for students waiting for help, but this queueing app makes it easy to immediately bring all students into Zoom where they will see a welcome message and approximate wait times. zq only runs locally, so the user's screen must stay shared even when they are helping a student in a breakout room (they must use a second device).

![demo](docs/demo1.png)

## features

* Simple controls with a smart queue. For example, the timers automatically pause, unpause, or reset in many situations when they should.
* Many intuitive keyboard shortcuts (see below), but you will probably only need a few of them.
* A sound notifies you when a timer has run out.
* Names and wait times are saved automatically, so the app can be restarted any time if needed.

## usage

This is a terminal app that is currently only being provided as source code. With Python on your device, you can download the source code and run it with the terminal command `python3 main.py` while in the app's folder. If you will use this often, I recommend creating your own custom terminal command to make running zq easier. For example, I did this with my Windows computer by creating a file called `zq.bat` with the content `py -3.10 C:\Users\chris\Documents\programming\zq\src\zq\main.py`, and adding the file to the PATH user environment variable. Now I can run zq by just opening Windows Terminal and entering `zq` (it doesn't matter what the current working directory is).

## keyboard shortcuts

* `h` toggles keyboard shortcut help.
* `o` opens the settings file. Restart to apply changes.
* `a` allows you to enter a student's name to add them to the queue.
* `n` brings the next student to the front of the queue, and rotates the previously front student to the end.
* `z` undoes the previous `n` keypress.
* `!` removes the last student in the queue.
* `$` randomizes the order of the queue.
* `m` toggles the meeting mode between group and individual meetings.
* `home` changes the meeting mode to display a message saying tutoring hours will start soon.
* `end` changes the meeting mode to display a message saying tutoring hours will soon end.
* `k` pauses/unpauses the individual meetings timer.
* `space` pauses/unpauses the individual meetings timer.
* `j` adds 5 seconds to the individual meetings timer.
* `l` subtracts 5 seconds from the individual meetings timer.
* `up` adds 30 seconds to the individual meetings timer.
* `down` subtracts 30 seconds from the individual meetings timer.
* `r` resets the individual meetings timer.
* `d` allows you to change the individual meetings duration (in minutes).
* `s` saves student info; for if you have autosave disabled.

## third-party dependencies

* [Textual](https://github.com/Textualize/textual) for the text user interface
* [Rich](https://github.com/Textualize/rich), which is used by Textual
* [chime](https://pypi.org/project/chime/) for notification sounds when a timer runs out
