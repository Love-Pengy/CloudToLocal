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
import time
import json
import shutil
import urllib
import base64
import logging
import pathlib
import mimetypes
from io import BytesIO
from pathlib import Path


import globals
import lyricsgenius
from PIL import Image
from mutagen import File
from mutagen.mp3 import MP3
from utils.logging import tui_log
from utils.common import Providers
from mutagen.oggopus import OggOpus
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from utils.common import sanitize_string
from dataclasses import dataclass, field
from music_brainz import musicbrainz_search
from youtube_title_parse import get_artist_title
from report import ReportStatus, update_report_status, add_to_report_post_search

from mutagen.id3 import (
    TIT2, TOPE, TALB, TRCK,
    TDAT, APIC, ID3, TCON, TXXX,
    USLT, PictureType, Encoding
)


logger = logging.getLogger(__name__)

META_MAX_THUMBNAIL_RETRIES = 5


@dataclass
class MetadataCtx:
    """ All metadata needed for the various metadata operations """
    title: str = None
    path: str = None
    album: str = None
    artist: str = None
    duration: int = None
    track_num: int = None
    album_len: int = None
    album_date: str = None
    thumbnail_url: str = None
    thumbnail_width: int = None
    thumbnail_height: int = None
    genres: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    playlists: list[str] = field(default_factory=list)


class LyricHandler:
    def __init__(self, api_key: str, verbosity: bool = False):
        self.genius_ctx = lyricsgenius.Genius(api_key, verbose=verbosity)

    def obtain_lyrics(self, title: str, artist: str):
        song = self.genius_ctx.search_song(title, artist)
        return (song.lyrics if song else None)


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
            logger.warning(f"Unsupported Filetype: {ext[1:]}")


def delete_file_tags(filepath: str):
    """ Delete tags embedded within the given file. """
    audio = File(filepath)
    audio.delete()
    audio.save()


def request_thumbnail(url):
    for i in range(0, META_MAX_THUMBNAIL_RETRIES):
        try:
            with urllib.request.urlopen(url) as response:
                return (response.read())
        except Exception:
            tui_log(f"{i}: Image obtain failed...retrying")
            time.sleep(i+1**3)
            continue

        tui_log(f"{i}: Image obtain failed...retrying")
        return None


def obtain_thumbnail_bytes(url: str):
    if (not url):
        logger.warning("Url passed is none")
        return None

        response = request_thumbnail(url)
        return (BytesIO(response))


def tag_file(in_metadata: MetadataCtx, clear: bool, lyric_handler: LyricHandler):
    """ Tag File With Information Passed. """

    if (clear):
        delete_file_tags(in_metadata.path)

    extension = Path(in_metadata.path).suffix

    mimetype, _ = mimetypes.guess_type(in_metadata.thumbnail_url)

    if (lyric_handler):
        lyrics = lyric_handler.obtain_lyrics(in_metadata.title, in_metadata.artist)
        tui_log(f"LYRICS: {lyrics}")

    if (".mp3" == extension):
        file_metadata = MP3(in_metadata.path)
        file_metadata.setall(TIT2(in_metadata.title, encoding=Encoding.UTF8))
        file_metadata.setall(TOPE(in_metadata.artist, encoding=Encoding.UTF8))
        file_metadata.setall(TDAT(getattr(in_metadata, "date", ""), encoding=Encoding.UTF8))
        file_metadata.setall(TXXX("artists", text=in_metadata.artists, encoding=Encoding.UTF8))
        file_metadata.setall(TALB(getattr(in_metadata, "album", ""), encoding=Encoding.UTF8))
        file_metadata.setall(TCON(getattr(in_metadata, "genres", ""), encoding=Encoding.UTF8))
        file_metadata.setall(
            TRCK(getattr(in_metadata, "track_number", ""), encoding=Encoding.UTF8))
        thumbnail = obtain_thumbnail_bytes(in_metadata.thumbnail_url)
        if not thumbnail:
            return False
        file_metadata.setall(USLT(lyrics or "", encoding=Encoding.UTF8))
        file_metadata.setall("APIC", [APIC(
            desc="Cover",
            mime=mimetype,
            type=PictureType.COVER_FRONT,
            data=thumbnail
        )])
        file_metadata.save()
    elif (extension in [".m4a", ".mp4"]):
        file_metadata = MP4(in_metadata.path)
        file_metadata["\xa9nam"] = in_metadata.title
        file_metadata["\xa9ART"] = in_metadata.artist
        file_metadata["----:TXXX:artists"] = in_metadata.artists
        file_metadata["\xa9day"] = getattr(in_metadata, "date", "")
        file_metadata["\xa9alb"] = getattr(in_metadata, "album", "")
        file_metadata["\xa9gen"] = getattr(in_metadata, "genres", "")
        file_metadata["\xa9lyr"] = lyrics or ""
        header = urllib.request.urlopen(in_metadata.thumbnail_url)
        image_format = MP4Cover.FORMAT_JPEG if mimetype == "image/jpeg" else MP4Cover.FORMAT_PNG
        thumbnail = obtain_thumbnail_bytes(in_metadata.thumbnail_url)
        if not thumbnail:
            return False
        file_metadata["covr"] = [MP4Cover(thumbnail, imageformat=image_format)]
        file_metadata.save()

    elif (extension in [".ogg", ".opus", ".flac"]):
        file_metadata = {
            '.opus': OggOpus, '.flac': FLAC, '.ogg': OggVorbis}[extension](in_metadata.path)

        file_metadata["title"] = in_metadata.title
        file_metadata["artists"] = in_metadata.artists
        file_metadata["artist"] = in_metadata.artist
        file_metadata["date"] = getattr(in_metadata, "date", "")
        file_metadata["album"] = getattr(in_metadata, "album", "")
        file_metadata["tracknumber"] = getattr(in_metadata, "track_number", "")
        file_metadata["lyrics"] = lyrics or ""

        picture = Picture()
        picture.desc = u"Cover"
        picture.mime = mimetype
        picture.type = PictureType.COVER_FRONT
        picture.width = in_metadata.thumbnail_width
        picture.height = in_metadata.thumbnail_height
        picture.data = request_thumbnail(in_metadata.thumbnail_url)
        if (not picture.data):
            return False

        if (".flac" == extension):
            file_metadata.add_picture(picture)
        else:
            picture_data = picture.write()
            encoded_data = base64.b64encode(picture_data)
            comment_val = encoded_data.decode("ascii")
            file_metadata["metadata_block_picture"] = [comment_val]
        file_metadata.save()
    else:
        raise ValueError("Unsupported FileType Passed To Tag Handler. "
                         "Supported Types Are: flac, opus, ogg, mp3, and mp4")

    return True


def parse_youtube_title(title: str, artist: str):
    return (get_artist_title(title, {"defaultArtist": artist, "defaultTitle": title}))


def fill_report_metadata(user_agent: str,
                         title: str,
                         uploader: str,
                         provider: str,
                         url: str,
                         report: dict,
                         lyric_handler: LyricHandler):
    """
        Arguments:
            user_agent:    Musicbrainz user agent
            title:         Title of song
            uploader:      Uploader of song
            provider:      Provider or download
            url:           URL of song
            report:        Dictionary of download status reports
            lyric_handler: Handler of lyric retrieval


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
        update_report_status(report, url, ReportStatus.METADATA_NOT_FOUND)
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
        "mbid": meta.release_mbid,
        "thumbnail_url": meta.thumbnail_url,
        "thumbnail_width": meta.thumbnail_resolution,
        "thumbnail_height": meta.thumbnail_resolution,
        "lyrics": lyric_handler.obtain_lyrics(meta.title, meta.artist)
    },
        report,
        url,
        ReportStatus.SINGLE if meta.is_single else ReportStatus.ALBUM_FOUND)


def replace_metadata(metadata: MetadataCtx, lyric_handler: LyricHandler):
    """ Replaces metadata and renames filename to new name provided. Metadata path will also be
        updated with the new filepath. """

    if (not tag_file(metadata, True, lyric_handler)):
        return None

    ext = pathlib.Path(metadata.path).suffix

    new_filepath = f"{os.path.dirname(metadata.path)}/{
        metadata.artist}_{metadata.album}_{metadata.track_num:02d}_{
        sanitize_string(metadata.title)}{ext}"

    tui_log(f"{os.path.basename(metadata.path)} -> {new_filepath}")

    shutil.move(metadata.path, new_filepath)

    metadata.path = new_filepath

    return (new_filepath)


GENRE_MAPPINGS = [
    ('&', "and"),
]


def handle_genre(in_genre: list):
    if (not in_genre):
        logger.debug("No Genres Specified")
        return None

    # Drum & Bass drum and bass
    with open(globals.GENRE_PATH, "r") as fptr:
        genres = json.load(fptr)

    output = []
    # Remove duplicated and make all lowercase to match musicbrainz
    in_genre = list(set([genre.lower() for genre in in_genre]))
    logger.debug(f"Lower In Genres: {in_genre}")
    for genre in in_genre:
        if (genre in genres):
            output.append(genre)
            logger.debug("Genre Found")
            continue

        genre = genre.lstrip().rstrip()
        logger.debug(f"Stripped Genre: {genre}")
        if (genre in genres):
            output.append(genre)
            logger.debug("Genre Found")
            continue

        for item in GENRE_MAPPINGS:
            if (item[0] in genre):
                genre = genre.replace(item[0], item[1])
                logger.debug(f"Mapping Found: {item[0]}->{item[1]}")
                if (genre in genres):
                    output.append(genre)
                    logger.debug("Genre Found")
                    break
        else:
            logger.debug(f"New Genre Found: {genre}...Adding To Genre List")
            genres.append(genre)
            with open(globals.GENRE_PATH, "w") as fptr:
                json.dump(genres, fptr)
            output.append(genre)

    return output
