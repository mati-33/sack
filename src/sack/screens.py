import random
import multiprocessing

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.color import Color
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input, Label, Button, Select
from textual.containers import (
    Right,
    Center,
    Container,
    VerticalGroup,
    VerticalScroll,
    HorizontalGroup,
)

from sack.models import (
    SackClient,
    SackServer,
    SackMessage,
    SackClientServerError,
    SackClientUsernameError,
)
from sack.components import TextInput, ChatMessage


if TYPE_CHECKING:
    from sack.main import SackApp


COMMON_BINDINGS = [
    Binding("escape", "app.pop_screen"),
    Binding("ctrl+n", "focus_next", "Focus Next"),
    Binding("ctrl+p", "focus_previous", "Focus Previous"),
]


class BaseScreen(Screen):
    app: "SackApp"  # type: ignore
    BINDINGS = COMMON_BINDINGS

    def action_focus_next(self) -> None:
        self.focus_next()

    def action_focus_previous(self) -> None:
        self.focus_previous()


class ServerPromptScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        with Center(id="form"):
            with Center(classes="form-title"):
                yield Label("Set up a server")
            yield Label(classes="form-error")
            with Center():
                with VerticalGroup(classes="form-field"):
                    yield Label("Host", classes="form-label")
                    yield Select(
                        [("0.0.0.0", "0.0.0.0"), ("localhost", "localhost")],
                        value="0.0.0.0",
                        compact=True,
                        allow_blank=False,
                        classes="select",
                        id="host",
                    )
            with Center():
                with VerticalGroup(classes="form-field"):
                    yield Label("Port", classes="form-label")
                    yield Input(type="integer", compact=True, id="port", max_length=5)
            with Right():
                yield Button("Next ->", compact=True)

    def on_button_pressed(self, _):
        if self.app.server_process:
            self.app.server_process.kill()
            self.app.server_process = None
        host = self.query_one("#host", Select).selection
        port = self.query_one("#port", Input).value
        form_error = self.query_one(".form-error", Label)
        if not port:
            form_error.update("Please fill Port field")
            return
        port = int(port)
        assert isinstance(host, str)

        event = multiprocessing.Event()

        def server_launcher():
            try:
                with SackServer(host, port) as server:
                    server.serve()
            except Exception:
                event.set()

        server_process = multiprocessing.Process(target=server_launcher, daemon=True)
        self.app.server_process = server_process
        server_process.start()
        if event.wait(0.1):
            form_error.update("Could not start server, try changing port")
            return

        client = SackClient(host=host, port=port)
        client.connect()
        self.app.push_screen(UsernamePromtScreen(client))


class ClientPromptScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        with Center(id="form"):
            with Center(classes="form-title"):
                yield Label("Join server")
            yield Label(classes="form-error")
            with Center():
                with VerticalGroup(classes="form-field"):
                    yield Label("Host", classes="form-label")
                    yield Input(compact=True, id="host")
            with Center():
                with VerticalGroup(classes="form-field"):
                    yield Label("Port", classes="form-label")
                    yield Input(type="integer", compact=True, id="port", max_length=5)
            with Right():
                yield Button("Next ->", compact=True)

    def on_button_pressed(self, _):
        host = self.query_one("#host", Input).value
        port = self.query_one("#port", Input).value
        form_error = self.query_one(".form-error", Label)
        if not host:
            form_error.update("Please fill Host field")
            return
        if not port:
            form_error.update("Please fill Port field")
            return
        port = int(port)
        assert isinstance(host, str)

        client = SackClient(
            host=host,
            port=port,
        )

        try:
            client.connect()
        except SackClientServerError:
            form_error.update("Server not found")
            return

        self.app.push_screen(UsernamePromtScreen(client))


class UsernamePromtScreen(BaseScreen):
    def __init__(self, client: SackClient) -> None:
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        with Center(id="form"):
            yield Center(Label("Set up a server"), classes="form-title")
            yield Label(classes="form-error")
            with Center():
                with VerticalGroup(classes="form-field"):
                    yield Label("Username", classes="form-label")
                    yield Input(compact=True, id="username", max_length=15)
            with Right():
                yield Button("Create", compact=True)

    def on_button_pressed(self, _):
        username = self.query_one("#username", Input).value
        form_error = self.query_one(".form-error", Label)
        if not username:
            form_error.update("Please fill Username field")
            return

        self.client.username = username
        try:
            self.client.join_request()
        except SackClientUsernameError:
            form_error.update("Username already taken")
            return

        self.app.push_screen(ChatScreen(self.client))


class ChatScreen(Screen):
    app: "SackApp"  # type: ignore

    BINDINGS = [
        Binding("enter", "send", "Send message", priority=True),
        Binding("ctrl+c", "quit", "Quit app", priority=True),
        Binding("ctrl+underscore", "show_help", "Show help", priority=True),
    ]

    class MessageReceived(Message):
        def __init__(self, msg: SackMessage) -> None:
            super().__init__()
            self.msg = msg

    def __init__(self, client: SackClient) -> None:
        super().__init__()
        self.client = client
        self.username = client.username
        self.colors_manager = ColorsManager()

    def compose(self) -> ComposeResult:
        with Container(id="chat"):
            with HorizontalGroup(id="chat-header"):
                yield Label(
                    f"[$foreground-muted]server[/] {self.client.host}:{self.client.port}"
                )
                with Right(id="right"):
                    yield Label(
                        "[$foreground-muted]sack[/] v0.1.0  [$foreground-muted]help[/] ctrl-?"
                    )
            yield VerticalScroll(id="messages")
            with HorizontalGroup(id="input-wrapper"):
                yield Label("[bold]>[/]", id="prompt-char")
                yield TextInput(compact=True)

    def action_send(self):
        textarea = self.query_one(TextInput)
        if not textarea.text:
            return
        self.client.send_text(textarea.text)
        textarea.clear()

    def action_quit(self):
        self.client.disconnect()
        self.app.exit()

    def action_show_help(self):
        self.app.push_screen(ChatHelpScreen())

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
        self.run_worker(self.update_messages, thread=True, exclusive=True)
        self.query_one(TextInput).focus()

    def update_messages(self):
        while True:
            # try: except post_message(ServerDown)
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
        random.shuffle(self.color_stack)

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


class ChatHelpScreen(ModalScreen):
    BINDINGS = COMMON_BINDINGS

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            with Center():
                yield Label("Help", classes="modal-title")
            with HorizontalGroup(classes="help-label help-header"):
                yield Label("KEYS", classes="help-keys")
                yield Label("ACTION", classes="help-desc")
            with HorizontalGroup(classes="help-label"):
                yield Label("Enter", classes="help-keys")
                yield Label("Send message", classes="help-desc")
            with HorizontalGroup(classes="help-label"):
                yield Label("ctrl+n", classes="help-keys")
                yield Label("New line", classes="help-desc")
            with HorizontalGroup(classes="help-label"):
                yield Label("ctrl+c", classes="help-keys")
                yield Label("Quit application", classes="help-desc")
            with HorizontalGroup(classes="help-label"):
                yield Label("ctrl+q", classes="help-keys")
                yield Label("Back to menu", classes="help-desc")


class ThemeOption(HorizontalGroup):
    def __init__(self, theme: str) -> None:
        super().__init__()
        self.theme = theme

    def compose(self) -> ComposeResult:
        yield Label(">", classes="theme-arrow")
        yield Label(self.theme, classes="theme-name")
        yield Input(id=self.theme)


class ThemeChangeScreen(ModalScreen):
    BINDINGS = COMMON_BINDINGS + [
        Binding("down", "focus_next", "Focus Next"),
        Binding("up", "focus_previous", "Focus Previous"),
        Binding("tab", "focus_next", "Focus Next"),
        Binding("shift+tab", "focus_previous", "Focus Previous"),
        Binding("enter", "app.pop_screen", priority=True),
    ]

    def action_focus_next(self) -> None:
        self.focus_next()
        self.change_theme_from_focused()

    def action_focus_previous(self) -> None:
        self.focus_previous()
        self.change_theme_from_focused()

    def change_theme_from_focused(self):
        focused = self.focused
        if isinstance(focused, Input) and focused.id:
            assert focused.id in self.app.available_themes
            self.app.theme = focused.id

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            with Center():
                yield Label("Change theme", classes="modal-title")
            for theme in self.app.available_themes:
                yield ThemeOption(theme)
