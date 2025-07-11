import logging
import signal
import socket
import threading
from argparse import ArgumentParser
from typing import Protocol, Sequence

from sack.models import SackClient, SackServer


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    )
    args = get_args()
    args.func(args)


def get_args(args: Sequence[str] | None = None):
    parser = ArgumentParser()
    parser.set_defaults(func=main)
    subparsers = parser.add_subparsers()

    server_subparser = subparsers.add_parser("server")
    server_subparser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        default=8080,
    )
    server_subparser.add_argument("--host", required=False, default="localhost")
    server_subparser.set_defaults(func=server_controller)

    client_subparser = subparsers.add_parser("client")
    client_subparser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        default=8080,
    )
    client_subparser.add_argument("--host", required=False, default="localhost")
    client_subparser.add_argument("--username", required=True)
    client_subparser.set_defaults(func=client_controller)

    arguments = parser.parse_args(args)
    return arguments


class ServerControllerArgs(Protocol):
    host: str
    port: int


def server_controller(args: ServerControllerArgs) -> None:
    controller_r, controller_w = socket.socketpair()

    def sigint_handler(*_):
        controller_w.send(b"\0")

    signal.signal(signal.SIGINT, sigint_handler)

    with SackServer(args.host, args.port, controller_r) as s:
        s.serve()


class ClientControllerArgs(Protocol):
    host: str
    port: int
    username: str


def client_controller(args: ClientControllerArgs) -> None:
    client = SackClient(host=args.host, port=args.port, username=args.username)
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
