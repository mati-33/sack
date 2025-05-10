from argparse import ArgumentParser
from typing import Callable, Protocol, Sequence

sack_ascii = r"""
                    _    
     ___  __ _  ___| | __
    / __|/ _` |/ __| |/ /
    \__ \ (_| | (__|   < 
    |___/\__,_|\___|_|\_\

"""


class HasHostPort(Protocol):
    host: str
    port: int


def get_args(
    *,
    server_callback: Callable[[HasHostPort], None],
    client_callback: Callable[[HasHostPort], None],
    args: Sequence[str] | None = None,
):
    def call_help(_):
        print(sack_ascii)
        parser.print_help()

    parser = ArgumentParser()
    parser.set_defaults(func=call_help)
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
    server_subparser.set_defaults(func=server_callback)

    client_subparser = subparsers.add_parser("client")
    client_subparser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        default=8080,
    )
    client_subparser.add_argument("--host", required=False, default="localhost")
    client_subparser.set_defaults(func=client_callback)

    arguments = parser.parse_args(args)
    return arguments
