from argparse import ArgumentParser
from typing import Sequence

from sack.client import client_controller
from sack.server import server_controller

SACK_ASCII = r"""
                    _    
     ___  __ _  ___| | __
    / __|/ _` |/ __| |/ /
    \__ \ (_| | (__|   < 
    |___/\__,_|\___|_|\_\

"""


def main() -> None:
    args = get_args()
    args.func(args)


def get_args(args: Sequence[str] | None = None):
    def call_help(_):
        print(SACK_ASCII)
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
