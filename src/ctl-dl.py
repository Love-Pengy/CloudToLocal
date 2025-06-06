#!/usr/bin/env python3

import os
import json
import shutil
import requests
import traceback
import configargparse
from time import sleep
from pprint import pprint
from yt_dlp import YoutubeDL
import utils.printing as printing
from yt_dlp import version as yt_dlp_version
from ytmusicapi import YTMusic
from yt_dlp.utils import DownloadError
from utils.tag_handler import tag_file
from utils.playlist_handler import PlaylistHandler
from youtube_title_parse import get_artist_title
from utils.common import get_diff_count, sanitize_string


class CloudToLocal:
    def __init__(self, args):
        self.dl_playlists = args.playlists
        self.output_dir = args.outdir
        if (not (self.output_dir[len(self.output_dir)-1] == '/')):
            self.output_dir += '/'
        self.unavail_file = args.unavail_file
        self.retries = args.retry_amt
        self.playlists_info = []
        self.replace_fname = args.replace_filenames
        self.ytmusic = YTMusic()
        self.not_found = args.not_found
        self.missing_albums_map = {}
        self.missing_albums = args.missing_albums

        if (args.generate_playlists):
            self.playlist_handler = PlaylistHandler(self.dl_playlists,
                                                    self.retries)

        if (self.not_found):
            open(self.not_found, "w")
        if (self.missing_albums):
            open(self.missing_albums, "w")
        if (self.unavail_file):
            open(self.unavail_file, "w")

        ydl_opts_extract = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': (not args.verbose)
        }

        for playlist in self.dl_playlists:
            with YoutubeDL(ydl_opts_extract) as ydl:
                self.playlists_info.append(
                    ydl.extract_info(playlist, download=False))

    def check_ytdlp_update(self):
        local_version = yt_dlp_version.__version__
        release_page = requests.get(
            "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest")
        latest_release = release_page.json()["tag_name"]
        if (local_version != latest_release):
            printing.pwarning(f"Newer yt_dlp Version Available, Please Update If"
                              f" You Experience Download Issues ({
                                  local_version} -> {latest_release})")
        else:
            printing.pinfo(f"yt_dlp Is Up To Date (Version {latest_release})")

    def download(self):
        for info in self.playlists_info:
            for index, entry in enumerate(info['entries']):
                url = entry['url']
                if not url:
                    printing.pwarning(
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
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                    }],
                    'quiet': (not args.verbose),
                    'noplaylist': True,
                    'paths': {"home": args.outdir},
                    'outtmpl': "%(title)s.%(ext)s",
                    'download_archive': args.outdir+"/archive",
                    # Do Not Continue If Fragment Fails
                    'skip_unavailable_fragments': False
                }
                print(f"\n[{index+1}/{len(info['entries'])}]"
                      f" Attempting: {title}")

                curr_filepath = None
                for retry in range(0, args.retry_amt-1):
                    try:
                        with YoutubeDL(ydl_opts_download) as ydl:
                            video_info = ydl.extract_info(url, download=True)

                            if (video_info and
                                    "requested_downloads" in video_info):
                                video_dl_info = video_info["requested_downloads"][0]
                                curr_ext = video_dl_info["ext"]
                                curr_filepath = video_dl_info["filepath"]
                                # TODO: Use To Generate M3U
                                curr_duration = video_info["duration"]
                        break
                    except DownloadError as e:
                        printing.pinfo(f"Failed to download Retrying"
                                       f"({retry}): {title} {url}: {e}")
                        sleep(retry*10)
                        if (not retry):
                            with open(args.unavail_file, "a") as f:
                                f.write(url)
                    except Exception as e:
                        print(traceback.format_exc())
                        printing.perror(f"Unexpected error for '{title}': {e}")
                        exit()

                if (args.replace_filenames and curr_filepath and
                        self.replace_fname):
                    self.replace_filename(title, uploader,
                                          curr_filepath, curr_ext,
                                          entry["ie_key"], url, curr_duration)

        if (self.replace_fname):
            with open(self.missing_albums, "w") as f:
                json.dump(self.missing_albums_map, f, indent=2)

        printing.psuccess("Download Completed")

    def replace_filename(self, title, uploader, filepath, extension, provider,
                         url, duration):

        result = get_artist_title(title,
                                  {"defaultArtist": uploader,
                                   "defaultTitle": title
                                   })
        if (all(result)):
            artist = result[0]
            title = result[1]
            search = self.ytmusic.search(
                artist + " " + title, filter="songs", limit=1)

            if (search):
                album = self.ytmusic.get_album(
                    search[0]["album"]["id"])["tracks"]

                # See if track is in the album we found
                album_name = [
                    track for track in album
                    if track["title"].lower() == title.lower()
                ]

                if (not album_name):
                    closest_match_miss_count = 99999
                    closest_match = None
                    for album_entry in album:
                        diff_num = get_diff_count(title, album_entry["title"])
                        if (diff_num < closest_match_miss_count):
                            closest_match = album_entry
                            closest_match_miss_count = diff_num

                    self.missing_albums_map[title] = {
                        "found_artist": artist,
                        "found_title": title,
                        "closest_match": closest_match,
                        "provider": provider
                    }
                    printing.pinfo(f"ALBUM MISSED: {title} {artist}")
                else:

                    track_num = album_name[0]["trackNumber"]
                    if (("thumbnails" in album_name[0])
                            and (album_name[0]["thumbnails"] is not None)):
                        thumbs = album_name[0]["thumbnails"]
                    else:
                        thumbs = search[0]["thumbnails"]

                    if (("year" in search[0])
                       and (search[0]["year"] is not None)):
                        year = search[0]["year"]
                    else:
                        year = None

                    artists = [sanitize_string(artist["name"])
                               for artist in search[0]["artists"]]
                    tag_file(filepath,
                             artists,
                             album_name[0]["album"],
                             search[0]["title"],
                             album_name[0]["trackNumber"],
                             len(album),
                             year,
                             thumbs[len(thumbs)-1])

                    printing.pinfo(f"{os.path.basename(filepath)} -> {artists[0]}_"
                                   f"{sanitize_string(
                                       album_name[0]["album"])}_"
                                   f"{album_name[0]["trackNumber"]:02d}_"
                                   f"{sanitize_string(search[0]["title"])}"
                                   f".{extension}")

                    shutil.move(filepath, f"{self.output_dir}"
                                f"{artists[0]}_"
                                f"{sanitize_string(album_name[0]["album"])}_"
                                f"{album_name[0]["trackNumber"]:02d}_"
                                f"{sanitize_string(search[0]["title"])}"
                                f".{extension}")

                    if (args.generate_playlists):
                        self.playlist_handler.write_to_playlists(url, duration,
                                                                 artist, title,
                                                                 track_num,
                                                                 album_name[0]["album"],
                                                                 filepath,
                                                                 self.output_dir)

        # NOTE: This occurs when both title and artist cannot be parsed.
        # Should only happen when you have a delimiter that can't clearly
        # be used to distinguish betwen artist and title such as a space
        else:
            printing.pinfo(f"ARTIST AND SONG NOT FOUND: {title}")
            with open("not_found", "a+") as f:
                f.write(f"{title} {uploader}\n")


def main(args):
    ctl = CloudToLocal(args)
    ctl.check_ytdlp_update()
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
                        help="Generate m3u Playlists From Specified Download"
                             " Urls")

    args = parser.parse_args()
    printing.VERBOSE = args.verbose
    printing.FAIL_ON_WARNING = args.fail_on_warning

    main(args)
