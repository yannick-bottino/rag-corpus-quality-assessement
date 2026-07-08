import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="cqg")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("corpus", nargs="?")
    parser.parse_args()
    return 0
