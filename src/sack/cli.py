from argparse import ArgumentParser
from typing import Sequence

sack_ascii = r"""
                    _    
     ___  __ _  ___| | __
    / __|/ _` |/ __| |/ /
    \__ \ (_| | (__|   < 
    |___/\__,_|\___|_|\_\

"""


def get_arguments(args: Sequence[str] | None = None):
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
    server_subparser.set_defaults(func=call_server)

    client_subparser = subparsers.add_parser("client")
    client_subparser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        default=8080,
    )
    client_subparser.add_argument("--host", required=False, default="localhost")
    client_subparser.set_defaults(func=call_client)

    arguments = parser.parse_args(args)
    return arguments


def call_server(args):
    print("server")
    print(f"host: {args.host}")
    print(f"port: {args.port}")


def call_client(args):
    print("client")
    print(f"host: {args.host}")
    print(f"port: {args.port}")
