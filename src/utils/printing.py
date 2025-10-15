from pprint import pformat

import globals
from textual import log


def pretty_print(*args, **kwargs):
    print(pformat(*args, **kwargs).replace("'", ""))


def info(*args, **kwargs):
    if (not globals.QUIET):
        print("\033[94m")
        print("ⓘ  ", end="")
        pretty_print(*args, **kwargs)
        print("\033[0m")


def warning(*args, **kwargs):
    print("\033[93m")
    print("⚠️", end="")
    pretty_print(*args, **kwargs)
    print("\033[0m")
    if (globals.FAIL_ON_WARNING):
        exit()


def success(*args, **kwargs):
    if (not globals.QUIET):
        print("\033[92m")
        print("✅", end="")
        pretty_print(*args, **kwargs)
        print("\033[0m")


def error(*args, **kwargs):
    print("\033[91m")
    print("❌", end="")
    pretty_print(*args, **kwargs)
    print("\033[0m")
    exit()


def tui_log(*args, **kwargs):
    if (not globals.QUIET):
        log(*args, **kwargs)
