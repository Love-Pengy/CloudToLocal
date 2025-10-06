#!/usr/bin/env python3

import os
import json
import shutil
import traceback
from time import sleep

import globals
from globals import ReportStatus
import configargparse
from pprint import pprint
from yt_dlp import YoutubeDL
from utils.tui import ctl_tui
from yt_dlp.utils import DownloadError
from utils.common import check_ytdlp_update
from utils.printing import warning, error, success, info
from utils.playlist_handler import PlaylistHandler

from utils.file_operations import (
    replace_filename,
    add_to_record_err,
    add_to_record_pre_replace,
    get_embedded_thumbnail_res
)


class CloudToLocal:
    def __init__(self, arguments):
        self.dl_playlists = arguments.playlists
        self.output_dir = arguments.outdir
        if (not (self.output_dir[len(self.output_dir)-1] == '/')):
            self.output_dir += '/'
        self.retries = arguments.retry_amt
        self.playlists_info = []
        self.download_delay = arguments.download_sleep
        self.request_delay = arguments.request_sleep
        self.playlist_handler = PlaylistHandler(self.retries,
                                                self.dl_playlists,
                                                self.playlists_info,
                                                self.request_delay)
        self.report = {}
        self.report_fpath = self.output_dir+"/ctl_report"

    def download(self):
        for curr_playlist_info in self.playlists_info:
            for index, entry in enumerate(curr_playlist_info['entries']):
                url = entry['url']
                if not url:
                    warning(
                        f"[{index+1}] Skipping: No URL found for "
                        f"'{entry['title']}'")
                    continue

                if (entry["ie_key"] == "Youtube"):
                    provider = "Youtube"
                    title = entry['title']
                    uploader = entry["uploader"]
                    thumbnail_url = entry["thumbnails"][len(
                        entry["thumbnails"])-1]["url"]
                else:
                    # NOTE: Soundcloud's API Gives References To Song Instead
                    #       Of Song Information For Top Level Entry So We Must
                    #       Query Further
                    provider = "Soundcloud"
                    sc_info = YoutubeDL({'simulate': True,
                                         'quiet': globals.QUIET,
                                         'verbose': globals.VERBOSE}
                                        ).extract_info(url)
                    if ('artist' in sc_info):
                        uploader = sc_info['artist']
                    else:
                        uploader = sc_info['uploader']

                    # TODO: this can probably just be used to get high res thumbnail
                    thumbnail_url = sc_info["thumbnail"]
                    # thumbnail_url = entry["thumbnails"][len(entry["thumbnails"])-1]["url"]
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
                    'quiet': globals.QUIET,
                    # Whether to add additional info to stdout
                    'verbose': globals.VERBOSE,
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
                    'sleep_interval': 0,
                    'max_sleep_interval': self.download_delay,
                    'sleep_interval_requests': self.request_delay
                }

                info(f"[{index+1}/{len(curr_playlist_info['entries'])}]"
                     f" Attempting: {title}")

                curr_filepath = None
                attempts = 0
                while (True):
                    if (not (self.retries == attempts-1)):
                        try:
                            with YoutubeDL(ydl_opts_download) as ydl:
                                video_info = ydl.extract_info(
                                    url, download=True)

                                if (video_info and
                                        "requested_downloads" in video_info):
                                    video_dl_info = video_info["requested_downloads"][0]
                                    curr_ext = video_dl_info["ext"]
                                    curr_filepath = video_dl_info["filepath"]
                                    curr_duration = int(
                                        round(float(video_info["duration"]), 0))
                                else:
                                    # FIXME: this happens if we skip a download. video_info will
                                    #   be none and requested_downloads won't exist. this should
                                    continue
                            break
                        except DownloadError:
                            info(
                                f"(#{attempts+1}) Failed to download... Retrying")
                            sleep(attempts*10)
                        except Exception as e:
                            print(traceback.format_exc())
                            error(f"Unexpected error for '{title}': {e}")
                    else:
                        add_to_record_err({"url": url},
                                          self.report, url, ReportStatus.DOWNLOAD_FAILURE)
                        break
                    attempts += 1

                if (curr_filepath):
                    thumb_dimensions = get_embedded_thumbnail_res(curr_filepath)
                    add_to_record_pre_replace({
                        "title": title,
                        "uploader": uploader,
                        "provider": provider,
                        "ext": curr_ext,
                        "duration": curr_duration,
                        "uploader": uploader,
                        "thumbnail_url": thumbnail_url,
                        "thumbnail_width": thumb_dimensions[0],
                        "thumbnail_height": thumb_dimensions[1],
                        "path": curr_filepath,
                        "url": url
                    }, self.report, url, ReportStatus.DOWNLOAD_SUCCESS)

                    replace_filename(title, uploader,
                                     curr_filepath, curr_ext,
                                     entry["ie_key"], url, curr_duration,
                                     self.output_dir, self.playlist_handler, self.report)

        with open(self.report_fpath, "w") as f:
            json.dump(self.report, f, indent=2)

        success("Download Completed")


def main(arguments):
    arguments.outdir = os.path.expanduser(arguments.outdir)
    if (arguments.fix_missing):
        ctl_tui(arguments.outdir+"/ctl_report").run()
        # correct_missing(arguments.outdir+"/ctl_report")
        exit()
    elif (arguments.fresh
          and os.path.exists(arguments.outdir)):
        shutil.rmtree(arguments.outdir)

    ctl = CloudToLocal(arguments)

    check_ytdlp_update()
    info("STARTING DOWNLOAD")
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

    parser.add_argument("--quiet", "-q", default=0, type=int,
                        help="Suppress Everything But Warnings and Errors")

    parser.add_argument("--download_sleep", "-ds", default=5, type=int,
                        help="Maximum Amount Of Seconds To Sleep Before A Download")

    parser.add_argument("--request_sleep", "-rs", default=1, type=int,
                        help="Amount Of Seconds To Sleep Between Requests")

    parser.add_argument("--fresh", "-f", default=0, type=int,
                        help="Delete Directory Before Downloading (Mainly For Testing)")

    args = parser.parse_args()
    globals.VERBOSE = bool(args.verbose)
    globals.FAIL_ON_WARNING = bool(args.fail_on_warning)
    globals.QUIET = bool(args.quiet)
    main(args)
