from datetime import datetime
from typing import Literal

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, HorizontalGroup
from textual.widget import Widget
from textual.widgets import Label, TextArea


class MenuOption(HorizontalGroup):
    def __init__(self, text: str, icon: str, shortcut: str):
        super().__init__()
        self.text = text
        self.icon = icon
        self.shortcut = shortcut

    def compose(self) -> ComposeResult:
        yield Label(self.icon + " ")
        yield Label(self.text + " ")
        yield Label(self.shortcut + " ", classes="shortcut")


class TextInput(TextArea):
    def _on_key(self, event: events.Key) -> None:
        new_line = "ctrl+n"
        if event.key != new_line:
            return

        event.stop()
        event.prevent_default()
        start, end = self.selection
        self._replace_via_keyboard("\n", start, end)


class ChatMessage(Widget):
    def __init__(
        self, orientation: Literal["left", "right"], msg: str, author: str, color: str
    ):
        super().__init__()
        self.orientation = orientation
        self.msg = msg
        self.author = author
        self.add_class("msg-container")
        self.add_class(self.orientation)
        self.color = color

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.msg, classes="msg-text"),
            Label(
                f"{self.author} ({datetime.now().strftime('%H:%M')})", classes="author"
            ),
            classes=f"msg {self.orientation}",
        )
