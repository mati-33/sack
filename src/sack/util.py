import random

from textual.color import Color


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
