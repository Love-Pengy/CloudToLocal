from pprint import pprint

import globals
from textual import log


def info(*args, **kwargs):
    if (not globals.QUIET):
        print("'\033[94m")
        print("ⓘ  ", end="")
        pprint(*args, **kwargs)
        print("\033[0m")


def warning(*args, **kwargs):
    print("\033[93m")
    print("⚠️", end="")
    pprint(*args, **kwargs)
    print("\033[0m")
    if (globals.FAIL_ON_WARNING):
        exit()


def success(*args, **kwargs):
    if (not globals.QUIET):
        print("\033[92m")
        print("✅", end="")
        pprint(*args, **kwargs)
        print("\033[0m")


def error(*args, **kwargs):
    print("\033[91m")
    print("❌", end="")
    pprint(*args, **kwargs)
    print("\033[0m")
    exit()


def tui_log(*args, **kwargs):
    if (not globals.QUIET):
        log(*args, **kwargs)
