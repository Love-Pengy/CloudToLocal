###
#  @file    metadata.py
#  @author  Brandon Elias Frazier
#  @date    Dec 06, 2025
#
#  @brief   Functionality for metadata operations
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
import shutil
import urllib
import base64
import pathlib
import mimetypes
from io import BytesIO
from pathlib import Path


import globals
from PIL import Image
from mutagen import File
from mutagen.mp3 import MP3
from report import ReportStatus
from utils.printing import tui_log
from mutagen.oggopus import OggOpus
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from utils.common import sanitize_string
from music_brainz import musicbrainz_search
from report import add_to_report_post_search
from youtube_title_parse import get_artist_title
from utils.common import warning, validate_args, Providers

from mutagen.id3 import (
    TIT2, TOPE, TALB, TRCK,
    TDAT, APIC, ID3, TCON, TXXX,
    PictureType, Encoding
)


def set_musicbrainz_user_agent(input: str):
    globals.MUSICBRAINZ_USER_AGENT = input


def get_embedded_thumbnail_res(path: str) -> tuple:
    """ Get resolution of a thumbnail from its embedded metadata. """
    ext = pathlib.Path(path).suffix
    match ext:
        case ".mp3":
            audio = ID3(path)
            thumb_data = audio[APIC].data
            return (Image.open(BytesIO(thumb_data)).size)
        case ".mp4" | ".m4a":
            audio = MP4(path)
            thumb_data = BytesIO(audio["covr"])
            return (Image.open(thumb_data).size)
        case ".opus" | ".ogg" | ".flac":
            audio = {".opus": OggOpus, ".ogg": OggVorbis}[ext](path)
            for data in audio.get("metadata_block_picture", []):
                try:
                    data = base64.b64decode(data)
                except (TypeError, ValueError):
                    continue
            picture = Picture(data)
            return (picture.width, picture.height)
        case ".flac":
            pic = audio.pictures[0]
            width = pic.width
            height = pic.height
            return (width, height)
        case _:
            warning(f"Unsupported Filetype: {ext[1:]}")


def delete_file_tags(filepath: str):
    """ Delete tags embedded within the given file. """
    audio = File(filepath)
    audio.delete()
    audio.save()


POSSIBLE_TAG_FILE_ARGS = ["filepath", "artists", "album", "title", "track_number",
                          "date", "thumbnail", "clear", "genres"]

REQUIRED_TAG_FILE_ARGS = ["filepath", "artists", "title", "thumbnail"]


def tag_file(args: dict):
    """ Tag File With Information Passed. """

    try:
        validate_args(args, POSSIBLE_TAG_FILE_ARGS, REQUIRED_TAG_FILE_ARGS)
    except KeyError:
        warning("Invalid Argument Found When Tagging File")
        return

    if (args.clear):
        delete_file_tags(args.filepath)
    extension = Path(args.filepath).suffix

    mimetype = mimetypes.guess_type(args.thumbnail["url"])

    if ("mp3" == extension):
        metadata = MP3(args.filepath)
        metadata.setall(TIT2(args.title, encoding=Encoding.UTF8))
        metadata.setall(TOPE(args.artists[0], encoding=Encoding.UTF8))
        metadata.setall(TDAT(getattr(args, "date", None), encoding=Encoding.UTF8))
        metadata.setall(TXXX("artists", text=args.artists, encoding=Encoding.UTF8))
        metadata.setall(TALB(getattr(args, "album", None), encoding=Encoding.UTF8))
        metadata.setall(TCON(getattr(args, "genres", None), encoding=Encoding.UTF8))
        metadata.setall(TRCK(getattr(args, "track_number", None), encoding=Encoding.UTF8))
        metadata.setall("APIC", [APIC(
            desc="Cover",
            mime=mimetype,
            type=PictureType.COVER_FRONT,
            data=urllib.request.urlopen(args.thumbnail["url"]).read()
        )])
        metadata.save()
    elif (extension in ["m4a", "mp4"]):
        metadata = MP4(args.filepath)
        metadata["\xa9nam"] = args.title
        metadata["\xa9ART"] = args.artists[0]
        metadata["----:TXXX:artists"] = args.artists
        metadata["\xa9day"] = getattr(args, "date", None)
        metadata["\xa9alb"] = getattr(args, "album", None)
        metadata["\xa9gen"] = getattr(args, "genres", None)
        header = urllib.request.urlopen(args.thumbnail["url"])
        image_format = MP4Cover.FORMAT_JPEG if mimetype == "image/jpeg" else MP4Cover.FORMAT_PNG
        metadata["covr"] = [MP4Cover(header.read(), imageformat=image_format)]
        header.close()
        metadata.save()

    elif (extension in ["ogg", "opus", "flac"]):
        metadata = {'opus': OggOpus, 'flac': FLAC, 'ogg': OggVorbis}[extension](args.filepath)

        metadata["title"] = args.title
        metadata["artists"] = args.artists
        metadata["artist"] = args.artists[0]
        metadata["date"] = getattr(args, "date", None)
        metadata["album"] = getattr(args, "album", None)
        metadata["tracknumber"] = getattr(args, "track_number", None)

        picture = Picture()
        picture.desc = u"Cover"
        picture.mime = mimetype
        picture.type = PictureType.COVER_FRONT
        picture.width = args.thumbnail["width"]
        picture.height = args.thumbnail["height"]
        picture.data = urllib.request.urlopen(args.thumbnail["url"]).read()

        if ("flac" == extension):
            metadata.add_picture(picture)
        else:
            picture_data = picture.write()
            encoded_data = base64.b64encode(picture_data)
            comment_val = encoded_data.decode("ascii")
            metadata["metadata_block_picture"] = [comment_val]
        metadata.save()
    else:
        raise ValueError("Unsupported FileType Passed To Tag Handler. "
                         "Supported Types Are: flac, opus, ogg, mp3, and mp4")


def parse_youtube_title(title: str, artist: str):
    return (get_artist_title(title, {"defaultArtist": artist, "defaultTitle": title}))


def fill_report_metadata(user_agent: str,
                         title: str,
                         uploader: str,
                         provider: str,
                         url: str,
                         report: dict):
    """
        Arguments:
            user_agent: Musicbrainz user agent
            title:      Title of song
            uploader:   Uploader of song
            provider:   Provider or download
            url:        Url of song
            report:     Dictionary of download status reports


    """

    title = title
    artist = uploader
    if (Providers.YT == provider):
        artist, title = parse_youtube_title(title, artist)
        if (not (artist and title)):
            title = title
            artist = uploader

    meta = musicbrainz_search(user_agent, title, artist)

    if (not meta):
        add_to_report_post_search({"url": url}, report, url, ReportStatus.METADATA_NOT_FOUND)
        return

    add_to_report_post_search({
        "title": meta.title,
        "artist": meta.artist,
        "artists": meta.artists,
        "album": meta.album,
        "single": meta.is_single,
        "release_date": meta.release_date,
        "track_num": meta.track_count,
        "total_tracks": meta.total_tracks,
        "mbid": meta.release_mbid
    },
        report,
        url,
        ReportStatus.SINGLE if meta.is_single else ReportStatus.ALBUM_FOUND)


# TO-DO: should probably also take in objects instead of all elements ~ BEF
# TO-DO: should also rename this to actually match the function ~ BEF
def user_replace_filename(title, artists, filepath, extension,
                          matching_album, duration, track_number, album_len,
                          album_date, thumbnail_obj):
    """
        User Initiated Filename Replacement Method. Replaces filename, tags
            file with relevant metadata, and adds to playlist if desired

        Args:
            title (str)
            artists (str)
            filepath (str)
            extension (str)
            matching_album (str)
            duration (int)
            track_number (int)
            album_len (int)
            album_date (str)
            thumbnail_obj (dict)

        Returns:
            new filepath in which song resides
    """

    delete_file_tags(filepath)

    tag_file(filepath,
             artists,
             matching_album,
             title,
             track_number,
             album_len,
             album_date,
             thumbnail_obj,
             extension)

    if (not matching_album):
        matching_album = title

    tui_log(f"{os.path.basename(filepath)} -> {artists[0]}_"
            f"{sanitize_string(matching_album)}_"
            f"{track_number:02d}_"
            f"{title}"
            f".{extension}")

    new_filepath = f"{os.path.dirname(
        filepath)}/{artists[0]}_{matching_album}_{track_number:02d}_{title}.{extension}"

    shutil.move(filepath, new_filepath)

    return (new_filepath)
