import logging
import os
import queue
import selectors
import socket
import threading
from typing import Callable, cast

log = logging.getLogger("server")
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(name)s: %(message)s"
)


class Server:
    def __init__(self, host: str, port: int, controller: socket.socket) -> None:
        self.host = host
        self.port = port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        self._socket = s
        self._controller = controller

        self._registry = selectors.DefaultSelector()
        self._registry.register(self._socket, selectors.EVENT_READ)
        self._registry.register(self._controller, selectors.EVENT_READ)

        def get_connections() -> list[socket.socket]:
            sockets = [
                s
                for k in self._registry.get_map().values()
                if (s := k.fileobj) not in (self._socket, self._controller)
            ]
            return cast(list[socket.socket], sockets)

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

                elif key.fileobj is self._controller:
                    self._controller.recv(1)
                    log.info("stopping server")
                    return

                else:
                    assert mask == selectors.EVENT_READ
                    data = key.fileobj.recv(1024)
                    if not data:
                        log.info("client disconnects")
                        key.fileobj.close()
                        self._registry.unregister(key.fileobj)
                    else:
                        data_decoded = data.decode()
                        log.info("message from client: %s", data_decoded)
                        self._broadcaster.broadcast(data)

    def _accept_connection(self):
        conn, addr = self._socket.accept()
        conn.setblocking(False)
        self._registry.register(conn, selectors.EVENT_READ)
        log.info("Accepted connection from %s", addr)

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
            for conn in self._get_connections():
                conn.sendall(msg)
            self._msg_queue.task_done()
