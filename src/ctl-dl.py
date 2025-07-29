#!/usr/bin/env python3

import os
import json
import traceback
import sys
from time import sleep

import configargparse
# from pprint import pprint
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from ytmusicapi import YTMusic
from utils.common import check_ytdlp_update
from utils import printing
from utils.printing import warning, error, success
from utils.playlist_handler import PlaylistHandler
from utils.file_operations import replace_filename, add_to_record


class CloudToLocal:
    def __init__(self, arguments):
        self.dl_playlists = arguments.playlists
        self.output_dir = os.path.expanduser(arguments.outdir)
        if (not (self.output_dir[len(self.output_dir)-1] == '/')):
            self.output_dir += '/'
        self.retries = arguments.retry_amt
        self.playlists_info = []
        self.ytmusic = YTMusic()
        self.download_delay = arguments.download_sleep
        self.request_delay = arguments.request_sleep
        self.verbose = arguments.verbose
        self.debug = bool(arguments.debug)

        self.generate_playlists = arguments.generate_playlists
        if (self.generate_playlists):
            self.playlist_handler = PlaylistHandler(self.retries,
                                                    self.dl_playlists,
                                                    self.playlists_info,
                                                    self.request_delay
                                                    )

        self.report = {}
        self.report_fpath = self.output_dir+"/ctl_report"

    def download(self):
        for info in self.playlists_info:
            for index, entry in enumerate(info['entries']):
                url = entry['url']
                if not url:
                    warning(
                        f"[{index+1}] Skipping: No URL found for "
                        f"'{entry['title']}'")
                    continue

                if (entry["ie_key"] == "Youtube"):
                    title = entry['title']
                    uploader = entry["uploader"]
                else:
                    # NOTE: Soundcloud's API Gives References To Song Instead
                    #       Of Song Information For Top Level Entry So We Must
                    #       Query Further
                    sc_info = YoutubeDL({'simulate': True,
                                         'quiet': not self.verbose, }
                                        ).extract_info(url)
                    if ('artist' in sc_info):
                        uploader = sc_info['artist']
                    else:
                        uploader = sc_info['uploader']

                    title = sc_info['title']

                ydl_opts_download = {
                    # Download Best audio format and fallback to best video
                    'format': 'bestaudio/best',
                    'postprocessors': [
                        {
                            'key': 'FFmpegMetadata',
                            'add_metadata': True
                        },
                        # In the case of a video format extract audio with best
                        # quality opus
                        {
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'opus',
                            'preferredquality': '0'
                        },
                        {
                            'key': 'EmbedThumbnail'
                        }
                    ],
                    # Whether to print to stdout
                    'quiet': not self.verbose,
                    # Whether to add additional info to stdout
                    'verbose': self.debug,
                    'noplaylist': True,
                    'paths': {"home": self.output_dir},
                    'outtmpl': "%(title)s.%(ext)s",
                    'download_archive': self.output_dir+"/archive",
                    # Do Not Continue If Fragment Fails
                    'skip_unavailable_fragments': False,
                    # Write Thumbnail To Disc For Usage With FFMPEG
                    'writethumbnail': True,
                    # By Default Use The Song Thumbnail
                    'embedthumbnail': True,
                }
                if (self.download_delay):
                    ydl_opts_download["sleep_interval"] = 0
                    ydl_opts_download["max_sleep_interval"] = self.download_delay
                if (self.request_delay):
                    ydl_opts_download["sleep_interval_requests"] = self.request_delay

                print(f"\n[{index+1}/{len(info['entries'])}]"
                      f" Attempting: {title}")

                curr_filepath = None
                attempts = 0
                while (True):
                    if(not (self.retries == attempts-1)):
                        try:
                            with YoutubeDL(ydl_opts_download) as ydl:
                                video_info = ydl.extract_info(url, download=True)

                                if (video_info and
                                        "requested_downloads" in video_info):
                                    video_dl_info = video_info["requested_downloads"][0]
                                    curr_ext = video_dl_info["ext"]
                                    curr_filepath = video_dl_info["filepath"]
                                    curr_duration = video_info["duration"]
                                else:
                                    curr_ext = None
                                    curr_duration = None
                            break
                        except DownloadError:
                            printing.info(f"(#{attempts+1}) Failed to download... Retrying")
                            sleep(attempts*10)
                        except Exception as e:
                            print(traceback.format_exc())
                            error(f"Unexpected error for '{title}': {e}")
                    else:
                        add_to_record({"status": "DOWNLOAD_FAILURE", "url": url},
                                      self.report)
                        break
                    attempts += 1

                if (curr_filepath):
                    replace_filename(title, uploader,
                                     curr_filepath, curr_ext,
                                     entry["ie_key"], url, curr_duration,
                                     self.generate_playlists,
                                     self.output_dir, self.playlist_handler, self.report)

        with open(self.report_fpath, "w") as f:
            json.dump(self.report, f, indent=2)

        success("Download Completed")


def main(arguments):
    ctl = CloudToLocal(arguments)
    if (arguments.fix_missing):
        # FIXME: correct_missing has been moved.
        ctl.correct_missing()
        sys.exit()
    check_ytdlp_update()
    print("STARTING DOWNLOAD")
    ctl.download()


if __name__ == "__main__":
    parser = configargparse.ArgParser(
        description="Automated Youtube and Soundcloud Downloader",
        config_file_parser_class=configargparse.YAMLConfigFileParser
    )

    parser.add_argument("--config", "-c", type=str,
                        is_config_file=True, default="ctlConfig.yaml",
                        help="Configuration File Path")

    parser.add_argument("--playlists", "-i", type=str,
                        nargs="+",
                        help="List of Playlists To Download"
                             "  Can Be Either Youtube or Soundcloud")

    parser.add_argument("--outdir", "-o", type=str,
                        required=True, help="Directory To Output Unverified Songs To")

    parser.add_argument("--retry_amt", "-retry", default=10, type=int,
                        help="Amount Of Times To Retry Non-Fatal Download"
                        " Errors")

    parser.add_argument("--fix-missing", "-fm", type=int,
                        help="Fix Missing Albums From File Path Specified")

    parser.add_argument("--fail_on_warning", "-w", type=int,
                        default=0, help="Exit Program On Failure")

    parser.add_argument("--verbose", "-v", default=0, type=int,
                        help="Enable Verbose Output")

    parser.add_argument("--generate_playlists", "-gp", default=1, type=int,
                        help="Generate M3U Playlists From Specified Download"
                             " Urls")

    parser.add_argument("--download_sleep", "-ds", default=5, type=int,
                        help="Maximum Amount Of Seconds To Sleep Before A Download")

    parser.add_argument("--request_sleep", "-rs", default=1, type=int,
                        help="Amount Of Seconds To Sleep Between Requests")
    
    parser.add_argument("--debug", "-d", default=0, type=int,
                        help="Enable Debug Printing For Downloads")

    args = parser.parse_args()
    printing.VERBOSE = args.verbose
    printing.FAIL_ON_WARNING = args.fail_on_warning

    main(args)
