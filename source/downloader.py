###
#  @file    downloader.py
#  @author  Brandon Elias Frazier
#  @date    Dec 01, 2025
#
#  @brief   Playlist Download Implementation
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

import logging
from time import sleep
from dataclasses import asdict

import globals
from yt_dlp import YoutubeDL
from report import ReportStatus
from utils.common import DownloadInfo
from utils.ctl_logging import tui_log
from yt_dlp.utils import DownloadError
from report import add_to_report_pre_search
from metadata import handle_genre, get_embedded_thumbnail_res

logger = logging.getLogger(__name__)


class DownloadManager:

    YDL_OPTS_DOWNLOAD = {
        "format": "bestaudio/best",
        "postprocessors": [
            # In the case of a video format extract audio with best
            # quality opus
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
                "preferredquality": '0'
            },
            # --parse-metadata
            {
                "key": "MetadataFromField",
                "formats": [
                    # Delete The Following Fields From The Embed List
                    ":(?P<meta_synopsis>)",
                    ":(?P<meta_description>)",
                    ":(?P<meta_purl>)",
                    ":(?P<meta_comment>)",
                    # Trim quotes from title
                    r'title:^(“|")(?P<title>[^“”"]+)(“|”|")$|',
                    # Trim trailing dot from title
                    r"title:^(?P<title>.+[^0-9])\.$|"
                ]
            },
            # --add-metadata
            {
                "key": "FFmpegMetadata",
            },
            # --embed-thumbnail
            {
                "key": "EmbedThumbnail"
            },
        ],

        # Whether to print to standard output
        "quiet": not globals.VERBOSE,
        # Whether to add additional info to standard output
        "verbose": globals.VERBOSE,
        "noplaylist": True,
        "outtmpl": "%(title)s.%(ext)s",
        # Do Not Continue If Fragment Fails
        "skip_unavailable_fragments": False,
        # Write Thumbnail To Disc For Usage With FFmpeg
        "writethumbnail": True,
        "embedthumbnail": True,
        "sleep_interval": 0
    }

    VALID_SETTING_KEYS = ["playlists_info", "output_dir", "download_sleep", "request_sleep",
                          "retry_amt", "report", "playlist_handler"]
    REQUIRED_SETTING_KEYS = ["playlist_info", "output_dir", "report", "playlist_handler"]

    def __init__(self, settings_obj: dict):

        for key in settings_obj:
            if (key in self.VALID_SETTING_KEYS):
                setattr(self, key, settings_obj[key])
            else:
                raise Exception(f"Invalid Download Manager Setting: {key}")

        self.retry_amt = getattr(self, "retry_amt", 0)
        self.YDL_OPTS_DOWNLOAD["paths"] = {"home": self.output_dir}
        self.YDL_OPTS_DOWNLOAD["download_archive"] = self.output_dir+"/archive"
        self.YDL_OPTS_DOWNLOAD["max_sleep_interval"] = self.download_sleep or 0
        self.YDL_OPTS_DOWNLOAD["sleep_interval_requests"] = self.request_sleep or 0

    def download_from_url(self, url) -> DownloadInfo:
        """Download singular song without managing any metadata. """
        if (not url):
            return False
        download_info = DownloadInfo()
        single_dl_opts = self.YDL_OPTS_DOWNLOAD
        single_dl_opts["download_archive"] = None
        info = YoutubeDL(self.YDL_OPTS_DOWNLOAD).extract_info(url, download=False)
        tui_log(info)
        download_info.url = url
        download_info.provider = info["extractor_key"]
        if ("Youtube" == download_info.provider):
            genres = None
            download_info.title = info["title"]
            download_info.uploader = info["uploader"]
            thumbnail_url = info["thumbnails"][len(info["thumbnails"])-1]["url"]
        else:
            # NOTE: Soundcloud API Gives References To Song Instead
            #       Of Song Information For Top Level Entry So We Must
            #       Query Further ~ BEF
            sc_info = YoutubeDL({'simulate': True,
                                 'quiet': not globals.VERBOSE,
                                 'verbose': globals.VERBOSE}
                                ).extract_info(download_info.url)

            download_info.title = sc_info["title"]
            genres = handle_genre(sc_info["genres"])
            thumbnail_url = sc_info["thumbnail"]
            download_info.uploader = sc_info[
                "artist"] if "artist" in sc_info else sc_info["uploader"]

            tui_log(f"Attempting to download: {download_info.title}")

            attempts = 0
            while (True):
                if (not (self.retry_amt == attempts-1)):
                    try:
                        with YoutubeDL(self.YDL_OPTS_DOWNLOAD) as ydl:
                            video_info = ydl.extract_info(download_info.url, download=True)
                            if ((video_info) and ("requested_downloads" in video_info)):
                                video_dl_info = video_info["requested_downloads"][0]
                                # TO-DO: prolly don't need to do all this ~ BEF
                                download_info.src_path = video_dl_info["filepath"]
                                download_info.short_path = download_info.src_path.removeprefix(
                                    globals.CONTAINER_MUSIC_PATH)
                                if (download_info.short_path.startswith('/')):
                                    download_info.short_path = download_info.short_path[1:]
                                download_info.duration = int(round(float(video_info["duration"]),
                                                                   0))
                            else:
                                # Video is present in the archive ~ BEF
                                break
                        break
                    except DownloadError:
                        tui_log(f"(#{attempts+1}) Failed to download... Retrying")
                        sleep(attempts*10)
                    except Exception:
                        tui_log(f"Unexpected error for '{download_info.title}'")
                else:
                    break
                attempts += 1

            if (download_info.src_path):
                thumb_dimensions = get_embedded_thumbnail_res(download_info.src_path)
                thumbnail_width = thumb_dimensions[0]
                thumbnail_height = thumb_dimensions[1]
                return download_info
            return None

    def download_generator(self) -> DownloadInfo:

        for curr_playlist_info in self.playlists_info:
            for index, entry in enumerate(curr_playlist_info["entries"]):
                download_info = DownloadInfo()
                download_info.url = entry["url"]
                if not download_info.url:
                    logger.warning(f"[{index+1}] Skipping: No URL found for {entry['title']}")
                    continue

                download_info.provider = entry["ie_key"]
                if ("Youtube" == download_info.provider):
                    genres = None
                    download_info.title = entry["title"]
                    download_info.uploader = entry["uploader"]
                    thumbnail_url = entry["thumbnails"][len(entry["thumbnails"])-1]["url"]
                else:
                    # NOTE: Soundcloud API Gives References To Song Instead
                    #       Of Song Information For Top Level Entry So We Must
                    #       Query Further ~ BEF
                    sc_info = YoutubeDL({'simulate': True,
                                         'quiet': not globals.VERBOSE,
                                         'verbose': globals.VERBOSE}
                                        ).extract_info(download_info.url)

                    download_info.title = sc_info["title"]
                    genres = handle_genre(sc_info["genres"])
                    thumbnail_url = sc_info["thumbnail"]
                    download_info.uploader = sc_info[
                        "artist"] if "artist" in sc_info else sc_info["uploader"]

                logger.info(f"[{index+1}/{len(curr_playlist_info['entries'])}] Attempting: {
                    download_info.title}")

                attempts = 0
                while (True):
                    if (not (self.retry_amt == attempts-1)):
                        try:
                            with YoutubeDL(self.YDL_OPTS_DOWNLOAD) as ydl:
                                video_info = ydl.extract_info(download_info.url, download=True)
                                if ((video_info) and ("requested_downloads" in video_info)):
                                    video_dl_info = video_info["requested_downloads"][0]
                                    download_info.src_path = video_dl_info["filepath"]
                                    download_info.short_path = download_info.src_path.removeprefix(
                                        globals.CONTAINER_MUSIC_PATH)
                                    if (download_info.short_path.startswith('/')):
                                        download_info.short_path = download_info.short_path[1:]
                                    duration = int(round(float(video_info["duration"]), 0))
                                else:
                                    # Video is present in the archive ~ BEF
                                    logger.info("Skipping...Song already present in the archive")
                                    break
                            break
                        except DownloadError:
                            logger.info(f"(#{attempts+1}) Failed to download... Retrying")
                            sleep(attempts*10)
                        except Exception:
                            logger.error(f"Unexpected error for '{download_info.title}'",
                                         exc_info=True)
                    else:
                        add_to_report_pre_search({"url": download_info.url},
                                                 self.report,
                                                 download_info.url,
                                                 ReportStatus.DOWNLOAD_FAILURE)
                        break
                    attempts += 1

                if (download_info.src_path):
                    thumb_dimensions = get_embedded_thumbnail_res(download_info.src_path)
                    thumbnail_width = thumb_dimensions[0]
                    thumbnail_height = thumb_dimensions[1]
                    add_to_report_pre_search(
                        asdict(download_info) |
                        {
                            "playlists": self.playlist_handler.check_playlists(download_info.url),
                            "genres": genres,
                            "duration": duration,
                            "thumbnail_url": thumbnail_url,
                            "thumbnail_width": thumbnail_width,
                            "thumbnail_height": thumbnail_height
                        },
                        self.report,
                        download_info.url,
                        ReportStatus.DOWNLOAD_SUCCESS)
                    yield (download_info)
        return
