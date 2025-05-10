import logging
import os
import selectors
import socket

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

    def serve(self):
        self._socket.setblocking(False)
        self._socket.listen()
        log.info("Started at %s:%d", self.host, self.port)
        log.debug("PID: %d", os.getpid())

        while True:
            events = self._registry.select()
            for key, _ in events:
                assert isinstance(key.fileobj, socket.socket)
                if key.fileobj is self._socket:
                    log.info("connection incoming")
                elif key.fileobj is self._controller:
                    self._controller.recv(1)
                    log.info("stopping server")
                    return

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._socket.close()
        self._registry.close()
