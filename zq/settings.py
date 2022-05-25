import os
from textwrap import dedent
import webbrowser
import yaml  # https://pyyaml.org/wiki/PyYAMLDocumentation


def format_setting_string(message: str) -> str:
    """Format a string for the settings menu."""
    return dedent(message).replace("\n\n", "␝").replace("\n", " ").replace("␝", "\n\n")


def open_settings_file() -> None:
    """Opens the app's settings file for the user to view."""
    if not os.path.exists("settings.yaml"):
        save_settings()
    webbrowser.open("settings.yaml")


__DEFAULT_SETTINGS = {
    "meeting minutes": 20,
    "transition seconds": 30,  # The time it takes to transition between meetings.
    "save interval seconds": 3,  # The names and meeting timer are saved once per n seconds.
    "empty lines above": 4,  # Number of empty lines inserted above the messages.
    "welcome message": format_setting_string(
        """\
        Welcome to the LAVC computer science tutoring! My name is Chris Wheeler, and I
        am a computer science student at CSUN and an alumnus of LAVC.
        
        I might be in a breakout room right now, but I will be back soon. You can see
        your approximate wait time on the right.
        """
    ),
    "starting message": format_setting_string(
        """\
        [b]Starting soon![/b]
        """
    ),
    "ending message": format_setting_string(
        """\
        [u][b]wrapping up[/b][/u]
        
        Tutoring hours are now ending. You can find the next time I will be tutoring on
        Penji. If you have questions before then, you can contact me at
        wheelecj@lavc.edu
        """
    ),
}


settings = {}


def save_settings() -> None:
    with open("settings.yaml", "w") as file:
        yaml.dump(settings, file, indent=4)


def load_settings() -> None:
    """Load settings from the settings.yaml file.
    
    If the file does not exist or cannot be parsed, the default settings are used.
    """
    try:
        with open("settings.yaml", "r") as file:
            settings.update(yaml.load(file, Loader=yaml.FullLoader))
    except (FileNotFoundError):
        print("Could not find settings.yaml. Creating the file with defaults.")
        settings.update(__DEFAULT_SETTINGS)
        save_settings()
    except (yaml.YAMLError):
        print("Could not parse settings.yaml. Using default settings.")
        settings.update(__DEFAULT_SETTINGS)


load_settings()
