###
#  @file    globals.py
#  @author  Brandon Elias Frazier
#  @date    Dec 18, 2025
#
#  @brief   Globals
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

import pathlib

CTLDL_VERSION = "0.1.0"
ENABLE_YTDLP_LOG = False
REQUEST_RESOLUTION = 1200
SHELF_NAME = "ctldl_shelf"
CONTAINER_MUSIC_PATH = None
MUSICBRAINZ_USER_AGENT = None
PROJECT_ROOT_DIR = pathlib.Path(__file__).parents[1]
GENRE_PATH = pathlib.Path(PROJECT_ROOT_DIR, "genres.json")
