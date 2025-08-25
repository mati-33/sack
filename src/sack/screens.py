import socket
import multiprocessing

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input, Label, Button, TabPane, TabbedContent
from textual.containers import (
    Right,
    Center,
    Container,
    HorizontalGroup,
)

from sack.util import ColorsManager
from sack.models import (
    SackServer,
    SackMessage,
    AsyncSackClient,
    SackClientServerError,
    SackClientUsernameError,
)
from sack.components import (
    Option,
    Options,
    FormField,
    TextInput,
    FormButton,
    FormErrors,
    ChatMessage,
    VimVerticalScroll,
)


if TYPE_CHECKING:
    from sack.main import SackApp


COMMON_BINDINGS = [
    Binding("escape", "app.pop_screen"),
    Binding("tab, ctrl+j", "app.focus_next", priority=True),
    Binding("shift+tab, ctrl+k", "app.focus_previous", priority=True),
]


class ServerPromptScreen(Screen):
    app: "SackApp"

    BINDINGS = COMMON_BINDINGS

    def compose(self) -> ComposeResult:
        yield from self.app.get_header()
        with Container(id="form"):
            yield Label("Create server", classes="form-title")
            yield FormErrors()
            yield FormField("port", "Port:", type="integer", max_length=5)
            yield FormButton("Next")

    def on_input_changed(self, _) -> None:
        form_error = self.query_one(FormErrors)
        form_error.reset()

    async def on_button_pressed(self, _):
        await self.app.cleanup()
        port = self.query_one("#port", Input).value
        form_error = self.query_one(FormErrors)
        if not port:
            form_error.set_error(1, "Port is required")
            return
        port = int(port)
        host = socket.gethostname()
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
            form_error.set_error(2, "Port not available")
            return

        form_error.reset()
        client = AsyncSackClient(host=host, port=port)
        await client.connect()
        self.app.client = client
        self.app.push_screen(
            UsernamePromtScreen(
                form_title="Create server",
                button_label="Create",
            )
        )


class ClientPromptScreen(Screen):
    app: "SackApp"

    BINDINGS = COMMON_BINDINGS

    def compose(self) -> ComposeResult:
        yield from self.app.get_header()
        with Container(id="form"):
            yield Label("Join server", classes="form-title")
            yield FormErrors()
            yield FormField("host", "Host:")
            yield FormField("port", "Port:", type="integer", max_length=5)
            yield FormButton("Next")

    def on_input_changed(self, e: Input.Changed) -> None:
        form_error = self.query_one(FormErrors)
        form_error.clear_error(3)
        match e.input.id:
            case "host":
                form_error.clear_error(1)
            case "port":
                form_error.clear_error(2)

    async def on_button_pressed(self, _):
        await self.app.cleanup()
        host = self.query_one("#host", Input).value
        port = self.query_one("#port", Input).value
        form_error = self.query_one(FormErrors)
        if not host:
            form_error.set_error(1, "Host is required")
        if not port:
            form_error.set_error(2, "Port is required")
        if form_error.has_errors(1, 2):
            return
        port = int(port)
        assert isinstance(host, str)

        client = AsyncSackClient(
            host=host,
            port=port,
        )

        try:
            await client.connect(timeout=0.1)
        except SackClientServerError:
            form_error.set_error(3, "Server not found")
            return

        form_error.reset()
        self.app.client = client
        self.app.push_screen(
            UsernamePromtScreen(
                form_title="Join server",
                button_label="Join",
            )
        )


class UsernamePromtScreen(Screen):
    app: "SackApp"

    BINDINGS = COMMON_BINDINGS

    def __init__(self, form_title: str, button_label: str) -> None:
        super().__init__()
        self.form_title = form_title
        self.button_label = button_label

    def on_input_changed(self, _) -> None:
        form_error = self.query_one(FormErrors)
        form_error.reset()

    def compose(self) -> ComposeResult:
        yield from self.app.get_header()
        with Container(id="form"):
            yield Label(self.form_title, classes="form-title")
            yield FormErrors()
            yield FormField("username", "Username:", max_length=15)
            yield FormButton(self.button_label)

    async def on_button_pressed(self, _):
        username = self.query_one("#username", Input).value
        form_error = self.query_one(FormErrors)
        if not username:
            form_error.set_error(1, "Username is required")
            return

        client = self.app.client
        assert client
        client.username = username
        try:
            await client.join_request()
        except SackClientUsernameError:
            form_error.set_error(2, "Username already taken")
            return

        form_error.reset()
        self.app.push_screen(ChatScreen())


class ChatScreen(Screen):
    app: "SackApp"

    BINDINGS = [
        Binding("enter", "send", priority=True),
        Binding("ctrl+c", "quit", priority=True),
        Binding("f1", "show_help", priority=True),
        Binding("ctrl+b", "to_menu", priority=True),
        Binding("escape", "open_menu"),
        Binding("ctrl+j", "app.focus_next", priority=True),
        Binding("ctrl+k", "app.focus_previous", priority=True),
    ]

    class MessageReceived(Message):
        def __init__(self, msg: SackMessage) -> None:
            super().__init__()
            self.msg = msg

    class ServerDown(Message):
        pass

    def __init__(self) -> None:
        super().__init__()
        assert self.app.client
        self.client = self.app.client
        self.username = self.app.client.username
        self.colors_manager = ColorsManager()

    def compose(self) -> ComposeResult:
        with Container(id="chat"):
            with HorizontalGroup(id="chat-header"):
                yield Label(
                    f"[$foreground-muted]server[/] {self.client.host}:{self.client.port}"
                )
                with Right(id="right"):
                    yield Label(
                        "[$foreground-muted]sack[/] v0.1.0  [$foreground-muted]help[/] f1"
                    )
            yield VimVerticalScroll(id="messages")
            with HorizontalGroup(id="input-wrapper"):
                yield Label("[bold]>[/]", id="prompt-char")
                yield TextInput(compact=True)

    async def action_send(self):
        textarea = self.query_one(TextInput)
        if not textarea.text:
            return
        await self.client.send_text(textarea.text)
        textarea.clear()

    async def action_quit(self):
        await self.app.cleanup()
        self.app.exit()

    def action_show_help(self):
        self.app.push_screen(ChatHelpScreen())

    async def action_to_menu(self):
        await self.app.cleanup()
        self.app.back_to_first_screen()

    def action_open_menu(self):
        self.app.push_screen(MenuScreen())

    def on_mount(self):
        self.app.message_worker = self.run_worker(self.update_messages)
        self.query_one(TextInput).focus()

    async def update_messages(self):
        while True:
            try:
                msg = await self.client.receive_message()
            except SackClientServerError:
                self.post_message(self.ServerDown())
                break
            if msg is None:
                continue
            self.post_message(self.MessageReceived(msg))

    @on(ServerDown)
    async def on_server_down(self):
        await self.app.cleanup()
        self.app.back_to_first_screen()
        self.app.push_screen(ServerDownScreen())

    @on(MessageReceived)
    def on_message_received(self, event: MessageReceived):
        msg = event.msg
        messages = self.query_one("#messages", VimVerticalScroll)
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


class ChatHelpScreen(ModalScreen):
    BINDINGS = COMMON_BINDINGS

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            with Center():
                yield Label("Help", classes="modal-title")


class ThemeChangeScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen"),
        Binding("enter", "app.pop_screen", priority=True),
        Binding("down, tab, j", "focus_next", priority=True),
        Binding("up, shift+tab, k", "focus_previous", priority=True),
    ]

    def action_focus_next(self) -> None:
        self.focus_next()
        self.change_theme_from_focused()

    def action_focus_previous(self) -> None:
        self.focus_previous()
        self.change_theme_from_focused()

    def change_theme_from_focused(self):
        focused = self.focused
        if isinstance(focused, Button) and focused.id:
            assert focused.id in self.app.available_themes
            self.app.theme = focused.id

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            with Center():
                yield Label("Change theme", classes="modal-title")
            for theme in self.app.available_themes:
                yield Option(theme, theme)


class MenuScreen(ModalScreen):
    app: "SackApp"

    BINDINGS = COMMON_BINDINGS

    def compose(self) -> ComposeResult:
        with Options(classes="modal"):
            with Center():
                yield Label("Menu", classes="modal-title")
            yield Option("Exit app", "exit")
            yield Option("Exit to menu", "exit_to_menu")
            yield Option("Help", "help")

    async def on_button_pressed(self, e: Button.Pressed):
        action_id = e.button.id
        assert action_id
        if action_id == "exit":
            await self.app.cleanup()
            self.app.exit()
        elif action_id == "exit_to_menu":
            await self.app.cleanup()
            self.app.back_to_first_screen()
        elif action_id == "help":
            self.app.pop_screen()
            self.app.push_screen(ChatHelpScreen())


class ServerDownScreen(ModalScreen):
    BINDINGS = [Binding("enter, escape", "app.pop_screen", priority=True)]

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            with Center():
                yield Label("Connection to the server was lost", classes="modal-title")
