from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Grid, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Input, Label

from sack.components import ChatMessage, TextInput
from sack.models import SackClient, SackMessage


class ServerPromptScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Center(Label("Set up a server")),
            Label("Port: "),
            Input(type="integer", compact=True),
            Center(Button("Create", compact=True)),
            id="server-prompt",
        )


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
        except:
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

    def __init__(self, client: SackClient) -> None:
        super().__init__()
        self.client = client
        self.username = client.username

    def compose(self) -> ComposeResult:
        yield Container(
            VerticalScroll(id="messages"),
            TextInput(compact=True),
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
        self.app.exit()

    @on(MessageReceived)
    def on_message_received(self, event: MessageReceived):
        msg = event.msg
        messages = self.query_one("#messages", VerticalScroll)
        if msg.type == "CONNECT":
            notif = Label(f"{msg.username} joined", classes="notification")
            messages.mount(notif)
            notif.scroll_visible()
        if msg.type == "DISCONNECT":
            notif = Label(f"{msg.username} disconnected", classes="notification")
            messages.mount(notif)
            notif.scroll_visible()
        if msg.type == "TEXT":
            assert msg.text
            new_msg = ChatMessage(
                orientation="right" if msg.username == self.username else "left",
                msg=msg.text,
                author=msg.username,
                color="",  # todo color registry
            )
            messages.mount(new_msg)
            new_msg.scroll_visible()

    def on_mount(self):
        self.run_worker(self.update_messages, thread=True, exclusive=True)
        self.query_one(TextInput).focus()

    def update_messages(self):
        while True:
            msg = self.client.receive_message()
            if msg is None:
                continue
            self.post_message(self.MessageReceived(msg))
