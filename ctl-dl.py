#!/usr/bin/env python3
import json
import shutil
import traceback
import configargparse
from time import sleep
from pprint import pprint
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic
from yt_dlp.utils import DownloadError
from youtube_title_parse import get_artist_title
from utils.common import get_diff_count, sanitize_string
from utils.tag_handler import tag_file

VERBOSE = False
FAIL_ON_WARNING = False


def pinfo(*args, **kwargs):
    if (VERBOSE):
        print(*args, **kwargs)


def pwarning(*args, **kwargs):
    print("\033[93m")
    print("⚠️", end="")
    print(*args, **kwargs)
    print("\033[0m")
    if (FAIL_ON_WARNING):
        exit()


def psuccess(*args, **kwargs):
    print("\033[92m")
    print("✅", end="")
    print(*args, **kwargs)
    print("\033[0m")


def perror(*args, **kwargs):
    print("\033[91m")
    print("❌", end="")
    print(*args, **kwargs)
    print("\033[0m")
    exit()


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

    def download(self):
        for info in self.playlists_info:
            for index, entry in enumerate(info['entries']):
                url = entry['url']
                if not url:
                    pwarning(
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
                        pinfo(f"Failed to download Retrying: {
                              title} {url}: {e}")
                        sleep(retry*10)
                        if (not retry):
                            with open(args.unavail_file, "a") as f:
                                f.write(url)
                    except Exception as e:
                        print(traceback.format_exc())
                        perror(f"Unexpected error for '{title}': {e}")
                        exit()

                if (args.replace_filenames and curr_filepath):
                    self.replace_filename(title, uploader,
                                          curr_filepath, curr_ext,
                                          entry["ie_key"])

        if (self.replace_fname):
            with open(self.missing_albums, "w") as f:
                json.dump(self.missing_albums_map, f, indent=2)

        psuccess("Download Completed")

    def replace_filename(self, title, uploader, filepath, extension, provider):

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
                # track_num = album_name["trackNumber"]

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
                    pinfo(f"ALBUM MISSED: {title} {artist}")
                else:
                    pinfo(f"{title} -> {search[0]["artists"][0]["name"]} "
                          f"{search[0]["title"]} {album_name[0]["album"]} "
                          f"{album_name[0]["trackNumber"]}")

                    # pprint(f"{album_name[0]=}")
                    # input()
                    # pprint(f"{search[0]=}")
                    # input()

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

                    shutil.move(filepath, f"{self.output_dir}"
                                f"{artists}_"
                                f"{sanitize_string(album_name[0]["album"])}_"
                                f"{album_name[0]["trackNumber"]:02d}_"
                                f"{sanitize_string(search[0]["title"])}"
                                f".{extension}")

        # NOTE: This occurs when both title and artist cannot be parsed.
        # Should only happen when you have a delimiter that can't clearly
        # be used to distinguish betwen artist and title such as a space
        else:
            print("\033[91m")
            print(f"ARTIST AND SONG NOT FOUND: {title}")
            print("\033[0m")
            with open("not_found", "a+") as f:
                f.write(f"{title} {uploader}\n")


def main(args):
    ctl = CloudToLocal(args)
    print("STARTING DOWNLOAD")
    ctl.download()


if __name__ == "__main__":
    parser = configargparse.ArgParser(
        description="Automated Youtube and Soundcloud Downloader",
        config_file_parser_class=configargparse.YAMLConfigFileParser
    )

    parser.add_argument("--replace_filenames", "-r", default=1,
                        help="Attempt To Replace Filename With Official "
                        "YTMusic Name")

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

    args = parser.parse_args()
    VERBOSE = args.verbose
    FAIL_ON_WARNING = args.fail_on_warning

    main(args)
