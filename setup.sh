#!/bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -e git+https://github.com/Love-Pengy/youtube_title_parse.git#egg=youtube_title_parse
pip install -r requirements.txt

