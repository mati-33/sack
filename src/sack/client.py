import socket
import threading
from typing import Protocol

from sack.protocol import Message, receive_message


class SPClient:
    def __init__(self, *, host: str, port: int, username: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        self._socket.connect((self.host, self.port))  # ConnectionRefused
        msg = Message("CONNECT", self.username)
        self._socket.sendall(msg.to_bytes())

    def disconnect(self) -> None:
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def send_text(self, text: str) -> None:
        msg = Message("TEXT", self.username, text)
        self._socket.sendall(msg.to_bytes())

    def receive_message(self) -> Message | None:
        def on_empty():
            raise Exception("server is down")

        return receive_message(self._socket, on_empty)


class ClientControllerArgs(Protocol):
    host: str
    port: int
    username: str


def client_controller(args: ClientControllerArgs) -> None:
    client = SPClient(host=args.host, port=args.port, username=args.username)
    client.connect()

    def listen():
        while True:
            msg = client.receive_message()
            if msg is None:
                continue
            if msg.username == args.username:
                continue
            if msg.type == "CONNECT":
                print(f"{msg.username} joined")
            if msg.type == "DISCONNECT":
                print(f"{msg.username} disconnected")
            if msg.type == "TEXT":
                print(f"{msg.username}: {msg.text}")

    listener = threading.Thread(target=listen, daemon=True)
    listener.start()

    while True:
        text = input()
        if text == "q":
            exit()
        client.send_text(text)
