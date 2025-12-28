###
#  @file    playlists.py
#  @author  Brandon Elias Frazier
#  @date    Dec 06, 2025
#
#  @brief   Functionality for m3u playlists
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
import logging

import globals
from yt_dlp import YoutubeDL
from metadata import MetadataCtx
from utils.logging import tui_log


logger = logging.getLogger(__name__)


class PlaylistHandler:

    def __init__(self,  retries, urls=None, info_ret=None, request_sleep=None):
        self.playlists = {}
        self.urls_populated = False
        self.request_sleep = request_sleep

        if (urls):
            self.add_urls(urls, retries, info_ret)

    def add_urls(self, urls, retry_cnt, info_ret=None):
        """ Creates A Dictionary Where The Keys Are Tuples
            (playlist url, playlist name) and the values are lists of song urls
        """

        ydl_opts = {
            "extract_flat": True,
            "skip_download": True,
            "quiet": not globals.VERBOSE,
            "verbose": globals.VERBOSE,
            "sleep_interval_requests": self.request_sleep
        }

        logger.debug("Adding URLS to playlist handler")
        for index, url in enumerate(urls):
            extraction_info = YoutubeDL(ydl_opts).extract_info(url, download=False)

            # Soundcloud long link
            if ("SoundcloudSet" == extraction_info["extractor_key"]):
                if (info_ret is not None):
                    info_ret.append(extraction_info)
                if ("entries" in extraction_info):
                    self.playlists[(url, extraction_info["album"])] = [
                        entry["url"] for entry in
                        extraction_info["entries"]]
                else:
                    logger.warning(f"{url} Does Not Seem To Be A Playlist")

            # Soundcloud short link
            # NOTE: Shortened links on Soundcloud return info of the longer link instead of
            #       the playlist information, so another extraction must be done ~ BEF
            elif ((url.startswith("https://on.soundcloud.com/"))
                  and ("Generic" == extraction_info["extractor_key"])):

                with YoutubeDL(ydl_opts) as ydl:
                    extraction_info = ydl.extract_info(extraction_info["url"], download=False)
                    if (info_ret is not None):
                        info_ret.append(extraction_info)
                    if ("entries" in extraction_info):
                        self.playlists[(url, extraction_info["album"])] = [
                            entry["url"] for entry in extraction_info["entries"]]
                    else:
                        logger.warning(f"{url} Does Not Seem To Be A Playlist")

            # YouTube
            elif ("YoutubeTab" == extraction_info["extractor_key"]):
                if (info_ret is not None):
                    info_ret.append(extraction_info)
                if ("entries" in extraction_info):
                    self.playlists[(url, extraction_info["title"])] = [
                        entry["url"] for entry in extraction_info["entries"]]
                else:
                    logger.warning(f"{url} Does Not Seem To Be A Playlist")
            else:
                logger.warning(
                    f"Unexpected Extraction Key/Domain: {extraction_info["extraction_key"]=}",
                    f"{url=}")

        self.urls_populated = True
        logging.debug("Urls added to playlist handler")

    def check_playlists(self, url):
        """ Returns a list of playlists that 'url' is in (playlist url, playlist name) form. """

        if (not self.urls_populated):
            logger.warning("Urls Have Not Yet Been Populated")
        return (
            [spec for spec in self.playlists if url in self.playlists[spec]])

    def list_playlists_str(self):
        """ Returns list of playlist strings with no duplicates. """
        output = []
        for spec in self.playlists:
            if spec[1] not in output:
                output.append(spec[1])
        return (output)

    def get_playlist_tuple(self, input):
        """ Get playlist tuple from string name. """

        out_list = [playlist for playlist in self.playlists if playlist[1] == input]
        if (out_list is None):
            return (None)

        return (out_list[0])

    def write_to_playlists(self, metadata: MetadataCtx, outdir: str, url):
        """ Write song to all playlist files it belongs to

        """
        if (metadata.path.startswith("#")):
            sanitized_path = "./" + os.path.basename(metadata.path)
        else:
            sanitized_path = os.path.basename(metadata.path)

        if (url):
            for playlist_spec in self.check_playlists(url):
                if (not os.path.exists(f"{outdir}{playlist_spec[1]}.m3u")):
                    with open(f"{outdir}{playlist_spec[1]}.m3u", "w") as f:
                        f.write("#EXTM3U\n")
                        f.write(f"#EXTINF:{metadata.duration},{
                                metadata.artist} - {metadata.title}\n")
                        f.write(sanitized_path + "\n")
                else:
                    with open(f"{outdir}{playlist_spec[1]}.m3u", "a") as f:
                        f.write(f"#EXTINF:{metadata.duration},{
                                metadata.artist} - {metadata.title}\n")
                        f.write(sanitized_path + "\n")
        else:
            for playlist_spec in metadata.playlists:
                if (not os.path.exists(f"{outdir}{playlist_spec[1]}.m3u")):
                    tui_log("Creating new playlist file")
                    with open(f"{outdir}{playlist_spec[1]}.m3u", "w") as f:
                        f.write("#EXTM3U\n")
                        f.write(f"#EXTINF:{metadata.duration},{
                                metadata.artist} - {metadata.title}\n")
                        f.write(sanitized_path + "\n")
                else:
                    tui_log("Appending to existing playlist file")
                    with open(f"{outdir}{playlist_spec[1]}.m3u", "a") as f:
                        f.write(f"#EXTINF:{metadata.duration},{
                                metadata.artist} - {metadata.title}\n")
                        f.write(sanitized_path + "\n")
