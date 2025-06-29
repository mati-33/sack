import random
from datetime import datetime
from typing import Literal

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widget import Widget
from textual.widgets import Input, Label, TextArea


class MyTextArea(TextArea):
    def _on_key(self, event: events.Key) -> None:
        new_line = "ctrl+n"
        if event.key != new_line:
            return

        event.stop()
        event.prevent_default()
        start, end = self.selection
        self._replace_via_keyboard("\n", start, end)

        # self.emit Submit
        # a tutaj jakos wykryc shift+enter


class ChatApp(App):
    CSS_PATH = "styles.css"
    BINDINGS = [
        Binding("enter", "send", "Send message", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            VerticalScroll(id="messages"),
            MyTextArea(
                id="input",
                compact=True,
            ),
            # TextArea(
            #     id="input",
            #     compact=True,
            # ),
            id="content",
        )

    def action_send(self):
        messages = self.query_one("#messages", VerticalScroll)
        textarea = self.query_one(TextArea)
        new_msg = Message(
            orientation="left" if random.random() > 0.5 else "right",
            msg=textarea.text,
            author="Mateusz",
        )
        messages.mount(new_msg)
        new_msg.scroll_visible()
        textarea.clear()

    def on_input_submitted(self, e: Input.Submitted):
        messages = self.query_one("#messages", VerticalScroll)
        new_msg = Message(
            orientation="left" if random.random() > 0.5 else "right",
            msg=e.value,
            author="Mateusz",
        )
        messages.mount(new_msg)
        self.query_one("#input", Input).value = ""
        new_msg.scroll_visible()
        if e.value == "n":
            new_notif = Label("TypeScript Tommy joined", classes="notification")
            messages.mount(new_notif)
            new_notif.scroll_visible()


class Message(Widget):
    def __init__(self, orientation: Literal["left", "right"], msg: str, author: str):
        super().__init__()
        self.orientation = orientation
        self.msg = msg
        self.author = author
        self.add_class("msg-container")
        self.add_class(self.orientation)

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.msg, classes="msg-text"),
            Label(
                f"{self.author} ({datetime.now().strftime('%H:%M')})", classes="author"
            ),
            classes=f"msg {self.orientation}",
        )


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
