from __future__ import annotations
from typing import Callable


class TextInput:
    def __init__(self) -> Callable:
        self.text = ""

    def __call__(self, key: str, field_label: str = None) -> tuple[bool, str]:
        """Gets text input from the user one key at a time.

        Parameters
        ----------
        key : str
            The key pressed.
        field_label : str, None
            Any text that must appear at the front of the text input field.

        Returns
        -------
        bool
            Whether text input is still being received.
        str, None
            The text input without surrounding whitespace characters. This is None if
            text input is still being received. If the user cancels text input with
            backspace, this is an empty string.
        """
        if field_label and not self.text:
            self.text = field_label
        if key == "enter":
            if field_label:
                self.text = self.text[len(field_label) :]
            result = self.text.strip()
            self.text = ""
            return False, result
        elif key == "ctrl+h":  # backspace
            start_index = len(field_label) if field_label else 0
            if len(self.text) > start_index:
                self.text = self.text[:-1]
            else:
                self.text = ""
                return False, ""
        elif len(key) == 1:
            self.text += key
        return True, None
