from typing import Literal
from datetime import datetime

from textual import events
from textual.app import ComposeResult
from textual.color import Color
from textual.widget import Widget
from textual.widgets import Label, TextArea
from textual.containers import Container, HorizontalGroup


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
        self,
        orientation: Literal["left", "right"],
        msg: str,
        author: str,
        color: Color | None = None,
    ):
        super().__init__()
        self.orientation = orientation
        self.msg = msg
        self.author = author
        self.add_class("msg-container")
        self.add_class(self.orientation)
        self.color = color

    def compose(self) -> ComposeResult:
        self.container = Container(
            Label(self.msg, classes="msg-text"),
            Label(
                f"{self.author} ({datetime.now().strftime('%H:%M')})", classes="author"
            ),
            classes="msg",
        )
        yield self.container

    def on_mount(self) -> None:
        if self.color:
            setattr(
                self.container.styles,
                f"border_{self.orientation}",
                ("solid", self.color),
            )
