import socket

from typing import Literal, overload
from collections.abc import Callable


class SackMessage:
    type: Literal["CONNECT", "DISCONNECT", "TEXT"]
    username: str
    text: str | None

    @overload
    def __init__(self, type: Literal["CONNECT", "DISCONNECT"], username: str) -> None: ...
    @overload
    def __init__(self, type: Literal["TEXT"], username: str, text: str) -> None: ...

    def __init__(self, type, username, text=None) -> None:
        self.type = type
        self.username = username
        self.text = text

    def to_bytes(self) -> bytes:
        message = f"{self.type}\n{self.username}".encode()
        message = len(message).to_bytes(1, "big") + message
        if self.type != "TEXT":
            return message
        assert self.text is not None
        text = self.text.encode()
        message += b"\n" + len(text).to_bytes(2, "big") + text
        return message


def receive_message(socket: socket.socket, on_empty: Callable) -> SackMessage | None:
    message_len = socket.recv(1)  # ConnectionResetError
    if not message_len:
        return on_empty()
    message_len = int.from_bytes(message_len, "big")
    raw_message = socket.recv(message_len)
    raw_message = raw_message.decode()
    message_parts = raw_message.split("\n")
    if not len(message_parts) == 2:
        return None
    type = message_parts[0]
    username = message_parts[1]
    if type not in ("CONNECT", "TEXT", "DISCONNECT"):
        return None
    if type != "TEXT":
        return SackMessage(type, username)
    sep = socket.recv(1)
    if sep != b"\n":
        return None
    text_len = socket.recv(2)
    text_len = int.from_bytes(text_len, "big")
    text = socket.recv(text_len).decode()
    return SackMessage(type, username, text)
