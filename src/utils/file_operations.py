import os
import shutil
import urllib
import base64
import pathlib
import traceback
from time import sleep
from io import BytesIO
from pprint import pprint

from PIL import Image
from mutagen import File
from mutagen.mp3 import MP3
from ytmusicapi import YTMusic
from utils.common import warning
from globals import ReportStatus
from mutagen.oggopus import OggOpus
from mutagen.mp4 import MP4, MP4Cover
from utils.printing import info, error
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from youtube_title_parse import get_artist_title
from ytmusicapi.exceptions import YTMusicServerError
from mutagen.id3 import TIT2, TOPE, TALB, TRCK, TDAT, APIC, ID3

from utils.common import (
    get_diff_count,
    sanitize_string,
    increase_img_req_res)


# Add entry to record
def add_to_record_pre_replace(context, record, url, status):
    record[url] = {}
    record[url]["before"] = context
    record[url]["status"] = status


def add_to_record_post_replace(context, record, url, status):
    record[url]["after"] = context
    record[url]["status"] = status


def add_to_record_err(context, record, url, status):
    record[url] = context
    record[url] = status


def get_embedded_thumbnail_res(path) -> tuple:
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


def delete_file_tags(filepath):
    audio = File(filepath)
    audio.delete()
    audio.save()


def tag_file(filepath, artist, album, title, track_num,
             total_tracks, year, thumbnail, ext):
    """Tag File With Information Passed

            Args:
                filepath (str): Path to audio file
                artist (list): list of artists on the track
                album (dict): dictionary of album specifications
                title (str): title
                track_num (int): track number in album
                total_tracks (int): total number of tracks in album
                year (int): year/date released (can be none)
                thumbnail (dict): dictionary of thumbnails
                ext (string): File Extension
    """
    if (ext == "mp3"):
        metadata = MP3(filepath)
        metadata.setall(TIT2(title, encoding=3))
        metadata.setall(TOPE(artist, encoding=3))
        metadata.setall(TALB(album, encoding=3))
        metadata.setall(TRCK(track_num, encoding=3))
        if (year):
            metadata.setall(TDAT(year, encoding=3))
        metadata.setall('APIC', [APIC(
            encoding=0,
            mime="image/jpeg",
            type=3,  # Front Cover
            desc="Cover",
            data=urllib.request
            .urlopen(thumbnail["url"]).read()
        )])
        metadata.save()
    elif (ext in ["m4a", "mp4"]):
        metadata = MP4(filepath)
        metadata['\xa9nam'] = title
        metadata['\xa9alb'] = album
        metadata['\xa9ART'] = artist
        if (year):
            metadata['\xa9day'] = year
        header = urllib.request.urlopen(thumbnail["url"])
        metadata['covr'] = [MP4Cover(header.read(),
                                     imageformat=MP4Cover.FORMAT_JPEG)]
        header.close()
        metadata.save()

    elif (ext in ["ogg", "opus", "flac"]):
        metadata = {'opus': OggOpus, 'flac': FLAC,
                    'ogg': OggVorbis}[ext](filepath)

        picture = Picture()
        if (album):
            metadata["album"] = album
        metadata["artist"] = artist
        metadata["title"] = title
        metadata["tracknumber"] = f"{track_num}/{total_tracks}"
        if (year):
            metadata["date"] = year

        picture.data = urllib.request.urlopen(thumbnail["url"]).read()
        picture.type = 3  # front cover
        picture.desc = u"Cover"
        picture.mime = u"image/jpeg"
        picture.width = thumbnail["width"]
        picture.height = thumbnail["height"]

        if (ext == "flac"):
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


def replace_filename(title, uploader, filepath, extension, provider, url, duration, output_dir,
                     report):
    """
        Filename Replacement Method. Replaces filename, tags file with
            relevant metadata, and adds to playlist if desired

        Args:
            title (str)
            uploader (str)
            filepath (str)
            extension (str)
            provider (str)
            url (str)
            duration (int)
            output_dir (str)
            handler (PlaylistHandler)
            report (dict): dictionary of download status reports


    """

    with YTMusic() as ytmusic:
        artist = uploader
        track_num = 1
        matching_album = []
        new_fname = os.path.basename(filepath)
        result = get_artist_title(title,
                                  {"defaultArtist": uploader,
                                   "defaultTitle": title
                                   })
        single = False
        matching_album_name = None
        if (all(result)):
            artist = result[0]
            title = result[1]
            search = ytmusic.search(
                artist + " " + title, filter="songs", limit=1)

            if (search):
                if ("album" in search[0] and search[0]["album"] is not None):
                    for i in range(0, 5):
                        try:
                            album = ytmusic.get_album(
                                search[0]["album"]["id"])["tracks"]
                            break
                        except YTMusicServerError:
                            info(
                                f"(#{i+1}) Album Search Failed ... Retrying")
                            sleep(i*10)
                        except Exception as e:
                            print(traceback.format_exc())
                            error(f"Unexpected error for '{title}': {e}")

                    if (album is not None):
                        # See if track is in the album we found
                        matching_album = [
                            track for track in album
                            if track["title"].lower() == title.lower()
                            and track["artists"][0]["name"].lower() == artist.lower()
                        ]
                        if (matching_album):
                            matching_album_name = matching_album[0]["album"]
                    else:
                        single = True

                if (not matching_album
                    and "album" in search[0]
                        and search[0]["album"] is not None):
                    closest_match_miss_count = 99999
                    closest_match = None
                    for album_entry in album:
                        diff_num = get_diff_count(title, album_entry["title"])
                        if (diff_num < closest_match_miss_count):
                            closest_match = album_entry
                            closest_match_miss_count = diff_num

                    closest_match["album_len"] = len(album)
                    thumbs = search[0]["thumbnails"]
                    closest_match["thumbnail_info"] = increase_img_req_res(thumbs[len(thumbs)-1])

                    add_to_record_post_replace({
                        "found_artist": artist,
                        "found_title": title,
                        "closest_match": closest_match,
                        "provider": provider,
                        "ext": extension,
                        "duration": duration,
                        "uploader": uploader,
                        "filepath": filepath
                    }, report, url, ReportStatus.DOWNLOAD_NO_UPDATE)
                    info(f"ALBUM MISSED: {title} {artist}")
                else:
                    if (single):
                        track_num = 1
                        thumbs = search[0]["thumbnails"]
                        matching_album = [{"album": None}]
                        status = ReportStatus.SINGLE
                    else:
                        status = ReportStatus.ALBUM_FOUND
                        try:
                            track_num = matching_album[0]["trackNumber"]
                        except:
                            # NOTE: Still tracking this down
                            error(f"UNKNOWN FAILURE: {
                                  matching_album=}, {search[0]=}")
                        if (("thumbnails" in matching_album[0])
                                and (matching_album[0]["thumbnails"] is not None)):
                            thumbs = matching_album[0]["thumbnails"]
                        else:
                            thumbs = search[0]["thumbnails"]

                    if (("year" in search[0])
                       and (search[0]["year"] is not None)):
                        year = search[0]["year"]
                    else:
                        year = None

                    artists = [sanitize_string(artist["name"])
                               for artist in search[0]["artists"]]
                    thumbnail = increase_img_req_res(thumbs[len(thumbs)-1])

                    if (matching_album):
                        tag_file(filepath,
                                 artists,
                                 matching_album[0]["album"],
                                 search[0]["title"],
                                 track_num,
                                 len(album),
                                 year,
                                 thumbnail,
                                 extension)
                    else:
                        tag_file(filepath,
                                 artists,
                                 None,
                                 search[0]["title"],
                                 track_num,
                                 len(album),
                                 year,
                                 thumbnail,
                                 extension)

                    new_fname = (f"{output_dir}{artists[0]}_"
                                 f"{sanitize_string(
                                     matching_album[0]["album"])}"
                                 f"_{matching_album[0]["trackNumber"]:02d}_"
                                 f"{sanitize_string(search[0]["title"])}"
                                 f".{extension}")

                    info(f"{os.path.basename(filepath)} -> "
                         f"{os.path.basename(new_fname)}")

                    shutil.move(filepath, new_fname)

                    add_to_record_post_replace({
                        "artists": artists,
                        "title": title,
                        "provider": provider,
                        "ext": extension,
                        "url": url,
                        "duration": duration,
                        "uploader": uploader,
                        "thumbnail_info": thumbnail,
                        "filename": os.path.basename(new_fname),
                        "filepath": new_fname,
                        "album": matching_album[0]["album"],
                        "track_num": track_num,
                        "total_tracks": len(album),
                        "year": year
                    }, report, url, status)

        # NOTE: This occurs when both title and artist cannot be parsed.
        # Should only happen when you have a delimiter that can't clearly
        # be used to distinguish betwen artist and title such as a space
        else:
            add_to_record_err({"url": url}, report, url, ReportStatus.SEARCH_FOUND_NOTHING)
            info(f"ARTIST AND SONG NOT FOUND: {title}")


# TODO: should probably also take in objects instead of all elements
# TODO: should also rename this to actually match the function
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

    info(f"{os.path.basename(filepath)} -> {artists[0]}_"
         f"{sanitize_string(matching_album)}_"
         f"{track_number:02d}_"
         f"{title}"
         f".{extension}")

    new_filepath = f"{os.path.dirname(
        filepath)}/{artists[0]}_{matching_album}_{track_number:02d}_{title}.{extension}"

    shutil.move(filepath, new_filepath)

    return (new_filepath)
