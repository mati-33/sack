from enum import StrEnum

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Rule, Static
from textual.containers import Center, Container, HorizontalGroup

from sack.assets import SACK_ASCII
from sack.models import SackClient
from sack.screens import (
    ChatScreen,
    ClientPromptScreen,
    ServerPromptScreen,
)
from sack.components import MenuOption, SackHeader


class MenuOptionLabels(StrEnum):
    SERVER = "1"
    JOIN_ROOM = "2"
    ABOUT = "3"
    EXIT = "q"


class SackApp(App):
    CSS_PATH = "styles.css"
    SCREENS = {
        "1": ServerPromptScreen,
        "2": ClientPromptScreen,
    }
    BINDINGS = [
        Binding(MenuOptionLabels.SERVER, "push_screen('1')", "Server port prompt"),
        Binding(MenuOptionLabels.JOIN_ROOM, "push_screen('2')", "Client prompt"),
        Binding(MenuOptionLabels.EXIT, "exit", "Quit the app"),
    ]

    def compose(self) -> ComposeResult:
        # yield Static(SACK_ASCII, id="header")
        yield SackHeader()
        with Center(id="options"):
            yield MenuOption("Server", "󰒋", MenuOptionLabels.SERVER)
            yield MenuOption("Join room", "", MenuOptionLabels.JOIN_ROOM)
            yield MenuOption("About", "", MenuOptionLabels.ABOUT)
            yield MenuOption("Exit", "󰅖", MenuOptionLabels.EXIT)

    def action_exit(self):
        self.exit()


def main(*_):
    app = SackApp()
    app.run()


if __name__ == "__main__":
    main()
