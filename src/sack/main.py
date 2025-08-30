from multiprocessing import Process

from textual.app import App, ComposeResult
from textual.worker import Worker
from textual.binding import Binding
from textual.widgets import Label, Button
from textual.containers import Container

from sack.util import make_keybinding_text
from sack.models import AsyncSackClient
from sack.screens import (
    HelpScreen,
    AboutScreen,
    ThemeChangeScreen,
    ClientPromptScreen,
    ServerPromptScreen,
)
from sack.components import Option, Options, SackHeader
from sack.keybindings import WELCOME_KB


class SackApp(App):
    CSS_PATH = "styles.css"
    SCREENS = {
        "1": ServerPromptScreen,
        "2": ClientPromptScreen,
        "3": ThemeChangeScreen,
        "4": HelpScreen,
        "5": AboutScreen,
    }
    BINDINGS = [
        Binding("ctrl+c", "exit"),
        Binding("ctrl+t", "push_screen('3')"),
        Binding("f1", "push_screen('4')"),
    ]
    ENABLE_COMMAND_PALETTE = False

    def __init__(self):
        super().__init__()
        self.HEADER_BREAKPOINT = 20
        self.server_process: Process | None = None
        self.client: AsyncSackClient | None = None
        self.message_worker: Worker | None = None

    def compose(self) -> ComposeResult:
        yield from self.get_header()
        with Options(id="options"):
            yield Option("Create server", "server")
            yield Option("Join server", "join")
            yield Option("Help", "help")
            yield Option("About sack", "about")
            yield Option("Exit", "exit")
        with Container(id="footer-container"):
            yield Label(make_keybinding_text(WELCOME_KB), classes="container")

    def action_exit(self):
        self.exit()

    def on_resize(self, _):
        height = self.size.height
        header = self.query_one(SackHeader)
        header.display = height >= self.HEADER_BREAKPOINT

    def on_button_pressed(self, e: Button.Pressed):
        match e.button.id:
            case "server":
                self.push_screen("1")
            case "join":
                self.push_screen("2")
            case "help":
                self.push_screen("4")
            case "about":
                self.push_screen("5")
            case "exit":
                self.exit()

    def get_header(self):
        header = SackHeader()
        header.display = self.size.height >= self.HEADER_BREAKPOINT
        yield header

    async def cleanup(self):
        if self.message_worker:
            self.message_worker.cancel()
            self.message_worker = None
        if self.client:
            await self.client.disconnect()
            self.client = None
        if self.server_process:
            self.server_process.kill()
            self.server_process = None

    def back_to_first_screen(self):
        for _ in range(len(self.screen_stack) - 1):
            self.pop_screen()


def main(*_):
    app = SackApp()
    app.run()


if __name__ == "__main__":
    main()
