import random
from random import shuffle

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import (Center, Container, Grid, HorizontalGroup,
                                VerticalScroll)
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Input, Label, Rule

from sack.components import ChatMessage, TextInput
from sack.models import SackClient, SackMessage, SackServer


class ServerPromptScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Center(Label("Set up a server")),
            Label("Port: "),
            Input(type="integer", compact=True, id="port"),
            Label("Username: "),
            Input(compact=True, id="username"),
            Center(Button("Create", compact=True)),
            id="server-prompt",
        )

    def on_button_pressed(self, event: Button.Pressed):
        port = self.query_one("#port", Input).value
        username = self.query_one("#username", Input).value

        if not port:
            self.notify("Please fill port field", severity="error")
            return
        if not username:
            self.notify("Please fill username field", severity="error")
            return

        server = SackServer(host="localhost", port=int(port))
        self.server = server
        self.run_worker(self.run_server, thread=True, exclusive=True)
        client = SackClient(host="localhost", port=int(port), username=username)
        self.dismiss({"server": server, "client": client})

    def run_server(self):
        with self.server as s:
            s.serve()


class ClientPromptScreen(ModalScreen[SackClient]):
    BINDINGS = [
        Binding("escape", "app.pop_screen"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Center(Label("Join room")),
            Label("Host: "),
            Input("localhost", compact=True, id="host"),
            Label("Port: "),
            Input("8080", compact=True, type="integer", id="port"),
            Label("Username: "),
            Input(compact=True, id="username"),
            Center(Button("Enter", compact=True)),
            id="client-prompt",
        )

    def on_button_pressed(self, event: Button.Pressed):
        host = self.query_one("#host", Input).value
        port = self.query_one("#port", Input).value
        username = self.query_one("#username", Input).value

        if not host:
            self.notify("Please fill host field", severity="error")
            return
        if not port:
            self.notify("Please fill port field", severity="error")
            return
        if not username:
            self.notify("Please fill username field", severity="error")
            return

        client = SackClient(host=host, port=int(port), username=username)
        try:
            client.connect()
        except:  # todo
            self.notify("error", severity="error")
            return
        self.dismiss(client)


class ChatScreen(Screen):
    BINDINGS = [
        Binding("enter", "send", "Send message", priority=True),
        Binding("ctrl+c", "quit", "Quit app", priority=True),
    ]

    class MessageReceived(Message):
        def __init__(self, msg: SackMessage) -> None:
            super().__init__()
            self.msg = msg

    def __init__(self, client: SackClient, server: SackServer | None = None) -> None:
        super().__init__()
        self.client = client
        self.server = server
        self.username = client.username
        self.colors_manager = ColorsManager()

    def compose(self) -> ComposeResult:
        yield Container(
            Label(
                f"[$secondary]#[/] {self.client.host}:{self.client.port}",
                id="chat-header",
            ),
            VerticalScroll(id="messages"),
            Rule(id="rule"),
            HorizontalGroup(
                Label("[bold]>[/]", id="prompt-char"),
                TextInput(compact=True),
            ),
            id="content",
        )

    def action_send(self):
        textarea = self.query_one(TextInput)
        if not textarea.text:
            return
        self.client.send_text(textarea.text)
        textarea.clear()

    def action_quit(self):
        self.client.disconnect()
        if self.server:
            self.server.stop()
        self.app.exit()

    @on(MessageReceived)
    def on_message_received(self, event: MessageReceived):
        msg = event.msg
        messages = self.query_one("#messages", VerticalScroll)
        if msg.type == "CONNECT":
            if msg.username == self.client.username:
                return
            notif = Label(f"{msg.username} joined", classes="notification")
            messages.mount(notif)
            notif.scroll_visible()
        if msg.type == "DISCONNECT":
            notif = Label(f"{msg.username} disconnected", classes="notification")
            messages.mount(notif)
            notif.scroll_visible()
        if msg.type == "TEXT":
            assert msg.text
            if msg.username == self.username:
                orientation = "right"
                color = None
            else:
                orientation = "left"
                color = self.colors_manager.get(msg.username)
            new_msg = ChatMessage(
                orientation=orientation,
                msg=msg.text,
                author=msg.username,
                color=color,
            )
            messages.mount(new_msg)
            new_msg.scroll_visible()

    def on_mount(self):
        if self.server:
            self.client.connect()
        self.run_worker(self.update_messages, thread=True, exclusive=True)
        self.query_one(TextInput).focus()

    def update_messages(self):
        while True:
            msg = self.client.receive_message()
            if msg is None:
                continue
            self.post_message(self.MessageReceived(msg))


class ColorsManager:
    def __init__(self) -> None:
        self._registry: dict[str, Color] = {}
        self.color_stack = [
            Color.parse("#1E90FF"),  # blue
            Color.parse("#DC143C"),  # red
            Color.parse("#FFFF00"),  # yellow
            Color.parse("#7FFF00"),  # green
            Color.parse("#8A2BE2"),  # violet
            Color.parse("#FF1493"),  # pink
        ]
        shuffle(self.color_stack)

    def get(self, username: str) -> Color:
        if username in self._registry:
            return self._registry[username]
        if self.color_stack:
            color = self.color_stack.pop()
        else:
            color = Color(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
        self._registry[username] = color
        return color
