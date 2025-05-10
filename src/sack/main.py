import signal
import socket

from sack.cli import HasHostPort, get_args
from sack.server import Server


def main() -> None:
    args = get_args(
        server_callback=server_callback,
        client_callback=client_callback,
    )
    args.func(args)


def server_callback(args: HasHostPort) -> None:
    controller_r, controller_w = socket.socketpair()

    def sigint_handler(*_):
        controller_w.send(b"\0")

    signal.signal(signal.SIGINT, sigint_handler)

    with Server(args.host, args.port, controller_r) as s:
        s.serve()


def client_callback(args: HasHostPort) -> None:
    print("client")
    print(f"host: {args.host}")
    print(f"port: {args.port}")
