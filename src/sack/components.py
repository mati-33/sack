from typing import Literal
from datetime import datetime

from textual import events
from textual.app import ComposeResult
from textual.color import Color
from textual.widget import Widget
from textual.binding import Binding
from textual.widgets import Label, Button, Static, TextArea
from textual.containers import Center, Container, VerticalScroll, HorizontalGroup

from sack.assets import SACK_ASCII


class SackHeader(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Static(classes="filler")
        yield Static(SACK_ASCII, id="header")
        yield Static(classes="filler")


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


class Options(Center):
    BINDINGS = [
        Binding("down, tab, j", "app.focus_next"),
        Binding("up, shift+tab, k", "app.focus_previous"),
    ]


class Option(HorizontalGroup):
    def __init__(self, label: str, option_key: str) -> None:
        super().__init__()
        self.label = label
        self.option_key = option_key

    def compose(self) -> ComposeResult:
        yield Label(">", classes="option-arrow")
        yield Label(self.label, classes="option-label")
        yield Button(id=self.option_key)


class VimVerticalScroll(VerticalScroll):
    BINDINGS = [
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("g", "scroll_home", "Scroll Home", show=False),
        Binding("G", "scroll_end", "Scroll End", show=False),
        Binding("u", "page_up", "Page Up", show=False),
        Binding("d", "page_down", "Page Down", show=False),
    ]


class FormErrors(Center):
    def __init__(self):
        super().__init__()
        self._errors: dict[int, str] = {}

    def compose(self) -> ComposeResult:
        label = Label(classes="form-error")
        label.display = False
        yield label

    def reset(self) -> None:
        self._errors = {}
        self._update(display=False)

    def set_error(self, err_id: int, err_message: str):
        self._errors[err_id] = err_message
        self._update(display=True)

    def clear_error(self, err_id: int) -> None:
        if err_id not in self._errors:
            return
        del self._errors[err_id]
        self._update(display=bool(self._errors))

    def has_errors(self, *err_ids: int) -> bool:
        if not err_ids:
            return bool(self._errors)
        for err_id in err_ids:
            if err_id in self._errors:
                return True
        return False

    def _update(self, *, display: bool) -> None:
        label = self.query_one(".form-error", Label)
        label.update("\n".join(self._errors.values()))
        label.display = display
