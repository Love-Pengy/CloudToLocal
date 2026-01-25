###
#  @file    ctl_logging.py
#  @author  Brandon Elias Frazier
#  @date    Dec 18, 2025
#
#  @brief   Logging Functions
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

import os
import json
import pathlib
import logging
import logging.config
from pprint import pformat

from textual import log

# util dir and source dir
VALID_LOGGER_LIST = [
    file for file in (os.listdir("source") + os.listdir("source/utils")) if ".py" in file
]


class NoExternalLibraryFilter(logging.Filter):
    def filter(self, record):
        if record.filename in VALID_LOGGER_LIST:
            return True
        return False


def setup_logging(in_path: str):
    config_path = pathlib.Path(in_path)
    with open(config_path) as fptr:
        config = json.load(fptr)

    config_filepath = config.get("handlers", {}).get("file", {}).get("filename", None)

    if (config_filepath):
        os.makedirs(os.path.dirname(config_filepath), exist_ok=True)

    logging.config.dictConfig(config)


def get_log_level() -> int:
    return (logging.root.level)


def pretty_print(*args, **kwargs):
    if (type(*args) is str):
        print(pformat(*args, **kwargs, width=100)[1:-1], flush=True)
    else:
        print(pformat(*args, **kwargs, width=100), flush=True)


def tui_log(*args, **kwargs):
    log(*args, **kwargs)
