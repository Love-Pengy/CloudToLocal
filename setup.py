#!/usr/bin/env python,

from setuptools import setup

setup(
    name="CloudToLocal",
    version="0.0.0",
    description="Automated Online Service Backup Tool",
    long_description_content_type="text/markdown",
    long_description=open("README.md").read(),
    author="Brandon Frazier",
    url="https://github.com/Love-Pengy/CloudToLocal",
    license="MIT",
    py_modules=["src"],
    install_requires=["youtube_title_parse @ https://github.com/Love-Pengy/youtube_title_parse/archive/refs/heads/master.zip",
                      "certifi", "charset_normalizer", "ConfigArgParse",
                      "idna", "mutagen", "PyYAML", "requests", "urllib3",
                      "yt-dlp", "ytmusicapi"
                      ]
)
