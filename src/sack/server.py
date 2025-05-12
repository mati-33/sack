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

    def _accept_connection(self):
        conn, addr = self._socket.accept()
        conn.setblocking(False)
        self._registry.register(conn, selectors.EVENT_READ)
        log.info("Accepted connection from %s", addr)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._socket.close()
        self._registry.close()
