import socket

from sack.models.protocol import SackMessage, receive_message


class SackClientError(Exception):
    pass


class SackClientServerError(SackClientError):
    pass


class SackClientUsernameError(SackClientError):
    pass


# todo username setter
class SackClient:
    def __init__(self, *, host: str, port: int, username: str | None = None) -> None:
        self.host = host
        self.port = port
        self.username = username
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        try:
            self._socket.connect((self.host, self.port))
        except Exception as e:
            raise SackClientServerError from e

    def join_request(self) -> None:
        assert self.username
        msg = SackMessage("CONNECT", self.username)
        self._socket.sendall(msg.to_bytes())
        ok_no = self._socket.recv(2).decode()
        if ok_no == "NO":
            self.disconnect()
            raise SackClientUsernameError

    def disconnect(self) -> None:
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def send_text(self, text: str) -> None:
        assert self.username
        msg = SackMessage("TEXT", self.username, text)
        self._socket.sendall(msg.to_bytes())

    def receive_message(self) -> SackMessage | None:
        def on_empty():
            raise SackClientServerError

        return receive_message(self._socket, on_empty)
