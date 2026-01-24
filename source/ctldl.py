#!/usr/bin/env -S python3 -u

###
#  @file    ctldl.py
#  @author  Brandon Elias Frazier
#  @date    Dec 01, 2025
#
#  @brief   CTLDL
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
import sys
import time
import json
import atexit
import signal
import shelve
import logging
import datetime
from pathlib import PurePath

import globals
import configargparse
from tui import ctl_tui
from playlists import PlaylistHandler
from downloader import DownloadManager
from metadata import fill_report_metadata, LyricHandler
from utils.logging import setup_logging, get_log_level
from music_brainz import musicbrainz_construct_user_agent

from utils.common import (
    check_ytdlp_update,
    connectivity_check,
    clean_ytdlp_artifacts,
    delete_folder_contents,
)

logger = logging.getLogger(__name__)


class CloudToLocal:
    def __init__(self, arguments):
        self.playlists_info = []
        self.retries = arguments.retry_amt
        self.user_agent = musicbrainz_construct_user_agent(arguments.email)
        self.playlist_handler = PlaylistHandler(self.retries,
                                                arguments.playlists,
                                                self.playlists_info,
                                                arguments.request_sleep)
        self.lyric_handler = LyricHandler(arguments.genius_api_key,
                                          verbosity=(True if logger.getEffectiveLevel() < logging.INFO else False))
        self.report_fpath = PurePath(globals.CONTAINER_MUSIC_PATH, "ctl_report")

        if (os.path.exists(self.report_fpath)):
            with open(self.report_fpath, 'r') as fptr:
                self.report = json.load(fptr)
        else:
            logger.debug("No Existing Report, Creating New One...")
            self.report = {}

        self.downloader = DownloadManager({
            "playlists_info": self.playlists_info,
            "output_dir": globals.CONTAINER_MUSIC_PATH,
            "download_sleep": arguments.download_sleep,
            "request_sleep": arguments.request_sleep,
            "retry_amt": arguments.retry_amt,
            "playlist_handler": self.playlist_handler,
            "report": self.report
        })

        self.set_exit_handlers()

    def run_download_sequence(self):

        for download_info in self.downloader.download_generator():
            fill_report_metadata(self.user_agent,
                                 download_info.title,
                                 download_info.uploader,
                                 download_info.provider,
                                 download_info.url,
                                 self.report,
                                 self.lyric_handler)

        clean_ytdlp_artifacts(globals.CONTAINER_MUSIC_PATH)
        self.dump_report()
        self.reset_exit_handlers()
        logger.info("Download Completed")

    def dump_report(self):
        logger.info("Dumping Report")
        with open(self.report_fpath, "w") as f:
            json.dump(self.report, f, indent=2)

    def dump_and_exit(self, sig_number, frame):
        self.dump_report()
        sys.exit(0)

    def set_exit_handlers(self):
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)
        self.original_sigterm_handler = signal.getsignal(signal.SIGTERM)

        atexit.register(self.dump_and_exit, None, None)
        signal.signal(signal.SIGINT, self.dump_and_exit)
        signal.signal(signal.SIGTERM, self.dump_and_exit)

    def reset_exit_handlers(self):
        atexit.unregister(self.dump_and_exit)
        signal.signal(signal.SIGINT, self.original_sigint_handler)
        signal.signal(signal.SIGTERM, self.original_sigterm_handler)


def download(arguments):
    if (not connectivity_check()):
        logging.warning(
            "Internet Connection Could Not Be Established! Please Check Your Connection")
        return

    logging.info("Internet connection verified")

    ctl = CloudToLocal(arguments)

    check_ytdlp_update()
    logging.info("Starting download sequence")
    ctl.run_download_sequence()


def clear_shelf():
    logging.info("Clearing shelf...")
    with shelve.open(globals.SHELF_NAME) as db:
        db.clear()


def main(arguments):

    setup_logging(arguments.log_config)

    globals.VERBOSE = (True if get_log_level() <= logging.INFO else False)

    arguments.host_outdir = os.path.expanduser(arguments.host_outdir)
    if (not (arguments.host_outdir[-1] == '/')):
        arguments.host_outdir += '/'

    if (arguments.start_tui):
        logger.debug("Starting Tui")
        ctl_tui(arguments).run()
        exit()
    if (arguments.fresh
            and os.path.exists(arguments.host_outdir)):
        logging.debug("Cleaning Existing Directory")
        delete_folder_contents(arguments.host_outdir)
        clear_shelf()

    logging.debug(vars(arguments))

    download_loop(arguments)


def set_wakeup_time(interval):
    """ Add wakeup time to ctldl shelf. """
    logging.info("Setting next wakeup time")
    dt_now = datetime.datetime.now()
    dt_future = dt_now + datetime.timedelta(hours=interval)

    with shelve.open(globals.SHELF_NAME) as db:
        db["wakeup_time"] = dt_future

    return ((dt_future - dt_now).total_seconds())


def remove_wakeup_time():
    """ Remove wakeup time from ctldl shelf. """
    logging.info("Removing previous wakeup time from shelf")
    with shelve.open(globals.SHELF_NAME) as db:
        db.pop("wakeup_time")


def download_loop(arguments):
    with shelve.open(globals.SHELF_NAME) as db:
        dl_wakeup_time = db.get("wakeup_time", None)

    if (dl_wakeup_time):
        sleep_time = (dl_wakeup_time - datetime.datetime.now()).total_seconds()
        if (0 < sleep_time):
            logging.info(f"Previous instance was set to sleep. Continuing to sleep for: {
                         sleep_time/3600:.2f} hours")
            time.sleep(sleep_time)
        remove_wakeup_time()

    download(arguments)

    if (arguments.interval):
        while (True):
            sleep_time = set_wakeup_time(arguments.interval)
            logging.info(f"Sleeping for {sleep_time/3600} hours...")
            time.sleep(sleep_time)
            remove_wakeup_time()
            download(arguments)


if __name__ == "__main__":

    parser = configargparse.ArgParser(
        description="Automated Youtube and Soundcloud Downloader",
        config_file_parser_class=configargparse.YAMLConfigFileParser
    )

    parser.add_argument("config", type=str,
                        is_config_file=True, default="ctlConfig.yaml",
                        help="Configuration File Path")

    parser.add_argument("--playlists", "-i", type=str,
                        nargs="+",
                        help="List of Playlists To Download"
                             "  Can Be Either Youtube or Soundcloud")

    parser.add_argument("--host_outdir", "-o", type=str,
                        required=True, help="Directory To Output Unverified Songs To")

    parser.add_argument("--retry_amt", "-retry", default=10, type=int,
                        help="Amount Of Times To Retry Non-Fatal Download Errors")

    parser.add_argument("--start_tui", "-t", action="store_true",
                        help="Start Tui To Edit Metadata")

    parser.add_argument("--download_sleep", "-ds", default=5, type=int,
                        help="Maximum Amount Of Seconds To Sleep Before A Download")

    parser.add_argument("--request_sleep", "-rs", default=1, type=int,
                        help="Amount Of Seconds To Sleep Between Requests")

    parser.add_argument("--fresh", "-f", action="store_true",
                        help="Bypass previous sleep records and Delete Directory Before           \
                        Downloading (Mainly For Testing)")

    parser.add_argument("--interval", type=int, default=None,
                        help="Amount of time between ctldl runs in hours")

    parser.add_argument("--email",
                        type=str,
                        required=True,
                        help="Email to be used for MusicBrainz api queries")

    parser.add_argument("--log_config", type=str,
                        default="source/configs/ctl_log_config.json",
                        help="Path to logging config")

    parser.add_argument("--genius_api_key", type=str, required=True,
                        help="Genius api key for lyric retrieval")

    args = parser.parse_args()

    globals.CONTAINER_MUSIC_PATH = os.environ.get("CONTAINER_OUTDIR", None)
    main(args)
