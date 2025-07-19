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
from utils.file_operations import replace_filename


class CloudToLocal:
    def __init__(self, arguments):
        self.dl_playlists = arguments.playlists
        self.output_dir = os.path.expanduser(arguments.outdir)
        if (not (self.output_dir[len(self.output_dir)-1] == '/')):
            self.output_dir += '/'
        self.unavail_file = arguments.unavail_file
        self.retries = arguments.retry_amt
        self.playlists_info = []
        self.replace_fname = arguments.replace_filenames
        self.ytmusic = YTMusic()
        self.not_found = arguments.not_found
        self.missing_albums_map = {}
        self.missing_albums = arguments.missing_albums
        self.download_delay = arguments.download_sleep
        self.request_delay = arguments.request_sleep
        self.verbose = arguments.verbose

        self.generate_playlists = arguments.generate_playlists
        if (self.generate_playlists):
            self.playlist_handler = PlaylistHandler(self.retries,
                                                    self.dl_playlists,
                                                    self.playlists_info,
                                                    self.request_delay
                                                    )
        if (not arguments.fix_missing):
            if (self.not_found):
                open(self.not_found, "w")
            if (self.missing_albums):
                open(self.missing_albums, "w")
            if (self.unavail_file):
                open(self.unavail_file, "w")

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
                                         'quiet': True, }
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
                    'quiet': (not self.verbose),
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
                    ydl_opts_download["sleep_interval"] = 1
                    ydl_opts_download["max_sleep_interval"] = self.download_delay
                if (self.request_delay):
                    ydl_opts_download["sleep_interval_requests"] = self.request_delay

                print(f"\n[{index+1}/{len(info['entries'])}]"
                      f" Attempting: {title}")

                curr_filepath = None
                for retry in range(0, self.retries-1):
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
                    except DownloadError as e:
                        info(f"Failed to download Retrying"
                             f"({retry}): {title} {url}: {e}")
                        sleep(retry*10)
                        if (not retry):
                            with open(self.unavail_file, "a") as f:
                                f.write(url)
                                f.write('\n')
                    except Exception as e:
                        print(traceback.format_exc())
                        error(f"Unexpected error for '{title}': {e}")
                        sys.exit()

                if (curr_filepath and self.replace_fname):
                    replace_filename(title, uploader,
                                     curr_filepath, curr_ext,
                                     entry["ie_key"], url, curr_duration,
                                     self.generate_playlists,
                                     self.missing_albums_map,
                                     self.output_dir, self.playlist_handler)

        if (self.replace_fname):
            with open(self.missing_albums, "w") as f:
                json.dump(self.missing_albums_map, f, indent=2)

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

    parser.add_argument("--replace_filenames", "-r", default=1,
                        help="Attempt To Replace Filename With Official "
                        "YTMusic Name and embed metadata")

    parser.add_argument("--config", "-c", type=str,
                        is_config_file=True, default="ctlConfig.yaml",
                        help="Configuration File Path")

    parser.add_argument("--playlists", "-i", type=str,
                        nargs="+",
                        help="List of Playlists To Download"
                             "  Can Be Either Youtube or Soundcloud")

    parser.add_argument("--outdir", "-o", type=str,
                        required=True, help="Directory To Output Files To")

    parser.add_argument("--unavail_file", "-u", type=str,
                        default="unavailable_videos",
                        help="List Of Video URLS Unavailable For Download")

    parser.add_argument("--retry_amt", "-retry", default=10,
                        help="Amount Of Times To Retry Non-Fatal Download"
                        " Errors")

    parser.add_argument("--fix-missing", "-fm", type=int,
                        help="Fix Missing Albums From File Path Specified")

    parser.add_argument("--fail_on_warning", "-w", type=int,
                        default=0, help="Exit Program On Failure")

    parser.add_argument("--verbose", "-v", default=0,
                        help="Enable Verbose Output")

    parser.add_argument("--not_found", "-nf", default="not_found",
                        help="File Path To Output Songs That Failed The "
                             " YTMusic Search")

    parser.add_argument("--missing_albums", "-ma", default="missing_albums",
                        help="File Path To Output Songs That Failed To Verify"
                             " The Album")

    parser.add_argument("--generate_playlists", "-gp", default=1,
                        help="Generate M3U Playlists From Specified Download"
                             " Urls")
    parser.add_argument("--download_sleep", "-ds", default=5,
                        help="Maximum Amount Of Seconds To Sleep Before A Download")

    parser.add_argument("--request_sleep", "-rs", default=0,
                        help="Amount Of Seconds To Sleep Before A Download")

    args = parser.parse_args()
    printing.VERBOSE = args.verbose
    printing.FAIL_ON_WARNING = args.fail_on_warning

    main(args)
