#!/usr/bin/env python3
import sys


def test_func():
    return "test"


def main():
    no_timeout = "--no-timeout" not in sys.argv[1:]
    if len(sys.argv) == 1 or no_timeout:
        print("Success!")
        sys.exit(0)
    else:
        print("Failure!")
        sys.exit(1)


if __name__ == "__main__":
    main()
