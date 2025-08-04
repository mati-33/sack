from enum import StrEnum
from multiprocessing import Process

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center

from sack.screens import (
    ThemeChangeScreen,
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
        "3": ThemeChangeScreen,
    }
    BINDINGS = [
        Binding(MenuOptionLabels.SERVER, "push_screen('1')", "Server port prompt"),
        Binding(MenuOptionLabels.JOIN_ROOM, "push_screen('2')", "Client prompt"),
        Binding(MenuOptionLabels.EXIT, "exit", "Quit the app"),
        Binding("ctrl+t", "push_screen('3')", "Change theme modal"),
    ]
    ENABLE_COMMAND_PALETTE = False

    def __init__(self):
        super().__init__()
        self.HEADER_BREAKPOINT = 25
        self.server_process: Process | None = None

    def compose(self) -> ComposeResult:
        yield from self.get_header()
        with Center(id="options"):
            yield MenuOption("Server", "󰒋", MenuOptionLabels.SERVER)
            yield MenuOption("Join room", "", MenuOptionLabels.JOIN_ROOM)
            yield MenuOption("About", "", MenuOptionLabels.ABOUT)
            yield MenuOption("Exit", "󰅖", MenuOptionLabels.EXIT)

    def action_exit(self):
        self.exit()

    def on_resize(self, _):
        height = self.size.height
        header = self.query_one(SackHeader)
        header.display = height >= self.HEADER_BREAKPOINT

    def get_header(self):
        header = SackHeader()
        header.display = self.size.height >= self.HEADER_BREAKPOINT
        yield header


def main(*_):
    app = SackApp()
    app.run()


if __name__ == "__main__":
    main()
