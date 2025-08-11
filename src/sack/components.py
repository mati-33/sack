from typing import Literal
from datetime import datetime

from textual import events
from textual.app import ComposeResult
from textual.color import Color
from textual.widget import Widget
from textual.widgets import Label, Button, Static, TextArea
from textual.containers import Container, HorizontalGroup

from sack.assets import SACK_ASCII


class SackHeader(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Static(classes="filler")
        yield Static(SACK_ASCII, id="header")
        yield Static(classes="filler")


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
        new_line = "shift+enter"
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
        container = Container(classes="msg")
        if self.color:
            setattr(
                container.styles,
                f"outline_{self.orientation}",
                ("solid", self.color),
            )
        with container:
            yield Label(self.msg, classes="msg-text")
            yield Label(
                f"{self.author} ({datetime.now().strftime('%H:%M')})",
                classes="msg-author",
            )


class ModalOption(HorizontalGroup):
    def __init__(self, label: str, option_key: str) -> None:
        super().__init__()
        self.label = label
        self.option_key = option_key

    def compose(self) -> ComposeResult:
        yield Label(">", classes="option-arrow")
        yield Label(self.label, classes="option-label")
        yield Button(id=self.option_key)
