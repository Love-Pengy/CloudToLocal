###
#  @file    printing.py
#  @author  Brandon Elias Frazier
#  @date    Dec 18, 2025
#
#  @brief   Printing Functions
#
#
#  @copyright (c) 2025 Brandon Elias Frazier
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#
#
#################################################################################

from pprint import pformat

import globals
from textual import log


def pretty_print(*args, **kwargs):
    if (type(*args) is str):
        print(pformat(*args, **kwargs)[1:-1])
    else:
        print(pformat(*args, **kwargs))


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
