import random

from collections.abc import Collection

from textual.color import Color
from textual.widgets import Label
from textual.containers import Container

from sack.keybindings import FORMS_KB


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


def make_keybinding_text(keybindings: Collection[tuple[str, str]]):
    return "  ".join(f"[$secondary]{key}[/] {desc}" for key, desc in keybindings)


def get_common_footer():
    with Container(id="footer-container"):
        yield Label(make_keybinding_text(FORMS_KB), classes="container")


def get_sidebar_user(username: str, color: Color, *, is_you: bool = False):
    color_ = color.hex
    username_label = username
    if is_you:
        color_ = "$primary"
        username_label = f"{username} (you)"
    return Label(f"[{color_}]::[/] {username_label}", id=get_id_from_color(color))


def get_id_from_color(color: Color):
    return color.hex.replace("#", "_")
