# pzq

Easy peasy queue for tutors using Penji and Zoom with two devices.

Since Penji's queue can be somewhat confusing and isolating for students waiting for help, this queueing app makes it easy to immediately admit all students into Zoom from Penji, where they will see more detailed info with a welcome message and approximate wait times. pzq only runs locally, so the user's screen must stay shared even when they are helping a student in a breakout room (they must use a second device). Student info is saved regularly, so the application can easily be restarted if needed.

![demo](docs/demo1.png)

## keyboard shortcuts

* `h` toggles keyboard shortcut help
* `a` changes your keyboard input mode to allow you to type a student's name. You will see "name: " and what you type appear in the bottom-left corner. When you have finished typing their name, press `enter` to add the student to the queue. You can also delete all of what you typed to cancel.
* `n` brings the next student to the front of the queue, and rotates the previously front student to the end.
* `z` undoes the previous `n` keypress.
* `!` removes the last student in the queue.
* `$` randomizes the order of the queue.
* `m` toggles the meeting mode between group and individual meetings.
* `end` changes the meeting mode to display a message saying tutoring hours will soon end.
* `k` pauses/continues the individual meetings timer.
* `j` adds 5 seconds to the individual meetings timer.
* `l` subtracts 5 seconds from the individual meetings timer.
* `r` resets the individual meetings timer.
