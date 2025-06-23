import random
from datetime import datetime
from typing import Literal

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widget import Widget
from textual.widgets import Input, Label


class ChatApp(App):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="messages")
        yield Input(compact=True, id="input")

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
