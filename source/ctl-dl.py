#!/usr/bin/env python3

import os
import sys
import time
import json
import atexit
import signal
from datetime import datetime
from zoneinfo import ZoneInfo

import pycron
import globals
import configargparse
from tui import ctl_tui
from playlists import PlaylistHandler
from downloader import DownloadManager
from metadata import fill_report_metadata
from music_brainz import construct_user_agent
from utils.printing import error, success, info

from utils.common import (
    check_ytdlp_update,
    connectivity_check,
    delete_folder_contents,
    clean_ytdlp_artifacts
)


class CloudToLocal:
    def __init__(self, arguments):
        self.playlists_info = []
        self.output_dir = arguments.outdir
        self.retries = arguments.retry_amt
        self.user_agent = construct_user_agent(arguments.email)
        self.playlist_handler = PlaylistHandler(self.retries,
                                                arguments.playlists,
                                                self.playlists_info,
                                                arguments.request_sleep)
        self.report_fpath = self.output_dir+"ctl_report"

        if (os.path.exists(self.report_fpath)):
            with open(self.report_fpath, 'r') as fptr:
                self.report = json.load(fptr)
        else:
            info("No Existing Report, Creating New One...")
            self.report = {}

        self.downloader = DownloadManager({
            "playlists_info": self.playlists_info,
            "output_dir": self.output_dir,
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
                                 self.report)

        clean_ytdlp_artifacts(self.output_dir)
        self.dump_report()
        self.reset_exit_handlers()
        success("Download Completed")

    def dump_report(self):
        info("Dumping Report")
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
        error("Internet Connection Could Not Be Established! Please Check Your Connection")
    info("INTERNET CONNECTION VERIFIED")

    ctl = CloudToLocal(arguments)

    check_ytdlp_update()
    info("STARTING DOWNLOAD")
    ctl.run_download_sequence()


def main(arguments):

    arguments.outdir = os.path.expanduser(arguments.outdir)
    if (not (arguments.outdir[-1] == '/')):
        arguments.outdir += '/'

    # TO-DO: Add Option To Server Over Localhost ~ BEF
    if (arguments.start_tui):
        ctl_tui(arguments).run()
        exit()
    if (arguments.fresh
            and os.path.exists(arguments.outdir)):
        info("Cleaning Existing Directory")
        delete_folder_contents(arguments.outdir)

    if (arguments.verbose):
        info(vars(arguments))

    # Always Run Once On Container Start
    download(arguments)
    if (arguments.cron_spec):
        while (True):
            dt_spec = datetime.now() if not arguments.timezone else datetime.now(
                tz=ZoneInfo(arguments.timezone))
            if (pycron.is_now(arguments.cron_spec, dt=dt_spec)):
                download(arguments)
            time.sleep(60)


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

    parser.add_argument("--outdir", "-o", type=str,
                        required=True, help="Directory To Output Unverified Songs To")

    parser.add_argument("--retry_amt", "-retry", default=10, type=int,
                        help="Amount Of Times To Retry Non-Fatal Download Errors")

    parser.add_argument("--start_tui", "-t", action="store_true",
                        help="Start Tui To Edit Metadata")

    parser.add_argument("--fail_on_warning", "-w", action="store_true",
                        help="Exit Program On Failure")

    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable Verbose Output")

    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress Everything But Warnings and Errors")

    parser.add_argument("--download_sleep", "-ds", default=5, type=int,
                        help="Maximum Amount Of Seconds To Sleep Before A Download")

    parser.add_argument("--request_sleep", "-rs", default=1, type=int,
                        help="Amount Of Seconds To Sleep Between Requests")

    parser.add_argument("--fresh", "-f", action="store_true",
                        help="Delete Directory Before Downloading (Mainly For Testing)")

    parser.add_argument("--timezone", "-tz", type=str, default="ETC/UTC",
                        help="Timezone to use for cron")
    parser.add_argument("--cron_spec", "-cn", type=str, help="Cron specifier")

    parser.add_argument("--email",
                        type=str,
                        required=True,
                        help="Email to be used for MusicBrainz api queries")

    args = parser.parse_args()
    globals.QUIET = args.quiet
    globals.VERBOSE = args.verbose
    globals.FAIL_ON_WARNING = args.fail_on_warning

    main(args)
