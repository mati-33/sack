import os
import queue
import socket
import logging
import selectors
import threading

from typing import cast
from dataclasses import dataclass
from collections.abc import Callable

from sack.models.protocol import SackMessage, receive_message


log = logging.getLogger("server")
blog = logging.getLogger("broadcaster")


@dataclass
class ClientData:
    username: str | None = None

    @property
    def is_registered(self) -> bool:
        return self.username is not None


class SackServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        self._socket = s

        sock_read, sock_write = socket.socketpair()
        self._STOP = sock_read
        self._stop_controller = sock_write

        self._registry = selectors.DefaultSelector()
        self._registry.register(self._socket, selectors.EVENT_READ)
        self._registry.register(self._STOP, selectors.EVENT_READ)

        def get_connections() -> list[socket.socket]:
            return cast(list[socket.socket], [key.fileobj for key in self._get_client_keys()])

        self._broadcaster = Broadcaster(connections_getter=get_connections)

    def serve(self):
        self._socket.setblocking(False)
        self._socket.listen()
        self._broadcaster.run()

        log.info("Started at %s:%d", self.host, self.port)
        log.debug("PID: %d", os.getpid())

        while True:
            events = self._registry.select()
            for key, mask in events:
                assert isinstance(key.fileobj, socket.socket)

                if key.fileobj is self._socket:
                    self._accept_connection()

                elif key.fileobj is self._STOP:
                    self._STOP.recv(1)
                    log.info("stopping server")
                    return

                else:
                    assert mask == selectors.EVENT_READ
                    message = self._receive_client_message(key.fileobj)
                    if message is None:
                        continue
                    log.info("received message of type %s", message.type)
                    client_data: ClientData = key.data
                    if message.type != "CONNECT" and not client_data.is_registered:
                        continue
                    if message.type == "DISCONNECT":
                        message.username = key.data.username
                        log.info("client disconnects")
                        self._unregister(key.fileobj)
                    if message.type == "CONNECT":
                        username = message.username
                        if username in self._get_usernames():
                            key.fileobj.sendall(b"NO")
                            continue
                        else:
                            key.fileobj.sendall(b"OK")
                            key.data.username = message.username

                    self._broadcaster.broadcast(message.to_bytes())

    def stop(self):
        self._stop_controller.send(b"\0")

    def _accept_connection(self):
        conn, addr = self._socket.accept()
        conn.setblocking(False)
        self._registry.register(conn, selectors.EVENT_READ, ClientData())
        log.info("Accepted connection from %s", addr)

    def _unregister(self, sock: socket.socket):
        sock.close()
        self._registry.unregister(sock)

    def _receive_client_message(self, socket: socket.socket) -> SackMessage | None:
        def on_empty():
            return SackMessage("DISCONNECT", "")

        return receive_message(socket, on_empty)

    def _get_usernames(self) -> list[str]:
        return [username for key in self._get_client_keys() if (username := key.data.username)]

    def _get_client_keys(self):
        for key in self._registry.get_map().values():
            if isinstance(key.data, ClientData):
                yield key

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._broadcaster.shutdown()
        self._socket.close()
        self._registry.close()


class Broadcaster:
    def __init__(self, connections_getter: Callable[[], list[socket.socket]]) -> None:
        self._msg_queue = queue.Queue()
        self._worker = threading.Thread(target=self._broadcast_worker)
        self._STOP = object()
        self._get_connections = connections_getter

    def run(self):
        self._worker.start()

    def shutdown(self):
        self._msg_queue.put(self._STOP)

    def broadcast(self, message: bytes):
        self._msg_queue.put(message)

    def _broadcast_worker(self):
        while True:
            msg = self._msg_queue.get()
            if msg is self._STOP:
                self._msg_queue.task_done()
                break
            connections = self._get_connections()
            blog.info("broadcasting message to %d clients", len(connections))
            for conn in connections:
                conn.sendall(msg)
            self._msg_queue.task_done()
