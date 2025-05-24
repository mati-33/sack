import socket


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._open = False

    def connect(self):
        try:
            self._socket.connect((self.host, self.port))
            self._open = True
        except ConnectionRefusedError:
            print("Server is not running")
            return

        while True:
            to_send = input("> ")
            if to_send == ":q":
                self._socket.send(b"")
                break
            self._socket.sendall(to_send.encode())
            data = self._socket.recv(1024)
            if not data:
                print("Server disconnected")
                break
            else:
                print(f"Server: {data.decode()}")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self._open:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
