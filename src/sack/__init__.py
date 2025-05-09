from sack.cli import get_arguments


def main() -> None:
    args = get_arguments()
    args.func(args)
