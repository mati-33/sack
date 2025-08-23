import socket
import asyncio

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


class AsyncSackClient:
    def __init__(self, *, host: str, port: int, username: str | None = None) -> None:
        self.host = host
        self.port = port
        self.username = username

    async def connect(self, *, timeout: float | None = None) -> None:
        try:
            async with asyncio.timeout(timeout):
                reader, writer = await asyncio.open_connection(self.host, self.port)
        except Exception as e:
            raise SackClientServerError from e
        self._reader, self._writer = reader, writer

    async def join_request(self) -> None:
        assert self.username
        msg = SackMessage("CONNECT", self.username)
        self._writer.write(msg.to_bytes())
        await self._writer.drain()
        ok_no = await self._reader.read(2)
        ok_no = ok_no.decode()
        if ok_no == "NO":
            raise SackClientUsernameError

    async def disconnect(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()

    async def send_text(self, text: str) -> None:
        assert self.username
        msg = SackMessage("TEXT", self.username, text)
        self._writer.write(msg.to_bytes())
        await self._writer.drain()

    async def receive_message(self) -> SackMessage | None:
        message_len = await self._reader.read(1)
        if not message_len:
            raise SackClientServerError
        message_len = int.from_bytes(message_len, "big")
        raw_message = await self._reader.read(message_len)
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
        sep = await self._reader.read(1)
        if sep != b"\n":
            return None
        text_len = await self._reader.read(2)
        text_len = int.from_bytes(text_len, "big")
        text = await self._reader.read(text_len)
        text = text.decode()
        return SackMessage(type, username, text)
