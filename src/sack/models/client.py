import socket

from sack.models.protocol import SackMessage, receive_message


class SackClient:
    def __init__(self, *, host: str, port: int, username: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        self._socket.connect((self.host, self.port))  # ConnectionRefused, OSError106
        msg = SackMessage("CONNECT", self.username)
        self._socket.sendall(msg.to_bytes())
        ok_no = self._socket.recv(2).decode()
        if ok_no == "NO":
            self.disconnect()
            raise Exception("username not unique")

    def disconnect(self) -> None:
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def send_text(self, text: str) -> None:
        msg = SackMessage("TEXT", self.username, text)
        self._socket.sendall(msg.to_bytes())

    def receive_message(self) -> SackMessage | None:
        def on_empty():
            raise Exception("server is down")

        return receive_message(self._socket, on_empty)
