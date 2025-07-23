from enum import StrEnum

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static

from sack.components import MenuOption
from sack.models import SackClient
from sack.screens import ChatScreen, ClientPromptScreen, ServerPromptScreen

SACK_ASCII = r"""
   ▄████████    ▄████████  ▄████████    ▄█   ▄█▄ 
  ███    ███   ███    ███ ███    ███   ███ ▄███▀ 
  ███    █▀    ███    ███ ███    █▀    ███▐██▀   
  ███          ███    ███ ███         ▄█████▀    
▀███████████ ▀███████████ ███        ▀▀█████▄    
         ███   ███    ███ ███    █▄    ███▐██▄   
   ▄█    ███   ███    ███ ███    ███   ███ ▀███▄ 
 ▄████████▀    ███    █▀  ████████▀    ███   ▀█▀ 
"""


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
        Binding(MenuOptionLabels.SERVER, "server", "Server port prompt"),
        Binding(MenuOptionLabels.JOIN_ROOM, "client", "Client prompt"),
        Binding(MenuOptionLabels.EXIT, "exit", "Quit the app"),
    ]

    def action_server(self):
        def push_chat_screen(x):
            self.push_screen(ChatScreen(**x))

        self.push_screen(ServerPromptScreen(), push_chat_screen)

    def action_client(self):
        def push_chat_screen(client: SackClient | None):
            if client:
                self.push_screen(ChatScreen(client))

        self.push_screen(ClientPromptScreen(), push_chat_screen)

    def compose(self) -> ComposeResult:
        with Container(id="content"):
            yield Static(SACK_ASCII, id="header")
            with Container(id="options"):
                yield MenuOption("Server", "󰒋", MenuOptionLabels.SERVER)
                yield MenuOption("Join room", "", MenuOptionLabels.JOIN_ROOM)
                yield MenuOption("About", "", MenuOptionLabels.ABOUT)
                yield MenuOption("Exit", "󰅖", MenuOptionLabels.EXIT)

    def action_exit(self):
        self.exit()


def main(*_):
    app = SackApp()
    app.run()
