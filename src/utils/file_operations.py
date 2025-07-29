import os
import shutil
import urllib
import base64
from pprint import pprint
from mutagen.mp3 import MP3
from ytmusicapi import YTMusic
from utils.printing import info
from mutagen.oggopus import OggOpus
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import TIT2, TOPE, TALB, TRCK, TDAT, APIC
from youtube_title_parse import get_artist_title

from utils.common import (
    get_diff_count,
    sanitize_string,
    increase_img_req_res)

# Add entry to record
def add_to_record(context, record):
    record[context["url"]] = context


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


def replace_filename(title, uploader, filepath, extension, provider,
                     url, duration, generate_playlists,
                     output_dir, handler, record):
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
            generate_playlists (bool)
            output_dir (str)
            handler (PlaylistHandler)
            record (dict): dictionary of download status reports


    """

    with YTMusic() as ytmusic:
        result = get_artist_title(title,
                                  {"defaultArtist": uploader,
                                   "defaultTitle": title
                                   })
        if (all(result)):
            artist = result[0]
            title = result[1]
            search = ytmusic.search(
                artist + " " + title, filter="songs", limit=1)

            if (search):
                single = True
                if ("album" in search[0] and search[0]["album"] is not None):
                    single = False
                    album = ytmusic.get_album(
                        search[0]["album"]["id"])["tracks"]

                    # See if track is in the album we found
                    album_name = [
                        track for track in album
                        if track["title"].lower() == title.lower()
                        and track["artists"][0]["name"].lower() == artist.lower()
                    ]

                if (not album_name and ("album" in search[0])):
                    closest_match_miss_count = 99999
                    closest_match = None
                    for album_entry in album:
                        diff_num = get_diff_count(title, album_entry["title"])
                        if (diff_num < closest_match_miss_count):
                            closest_match = album_entry
                            closest_match_miss_count = diff_num

                    closest_match["album_len"] = len(album)

                    add_to_record({
                        "status": "DOWNLOAD_NO_UPDATE",
                        "found_artist": artist,
                        "found_title": title,
                        "closest_match": closest_match,
                        "provider": provider,
                        "ext": extension,
                        "url": url,
                        "duration": duration,
                        "uploader": uploader
                    }, record)
                    info(f"ALBUM MISSED: {title} {artist}")
                else:
                    if (single):
                        track_num=1
                        thumbs=search[0]["thumbnails"]
                        album_name=[{"album": None}]
                        status = "SINGLE"
                    else:
                        status = "ALBUM_FOUND"
                        track_num=album_name[0]["trackNumber"]
                        if (("thumbnails" in album_name[0])
                                and (album_name[0]["thumbnails"] is not None)):
                            thumbs=album_name[0]["thumbnails"]
                        else:
                            thumbs=search[0]["thumbnails"]

                    if (("year" in search[0])
                       and (search[0]["year"] is not None)):
                        year=search[0]["year"]
                    else:
                        year=None

                    artists=[sanitize_string(artist["name"])
                               for artist in search[0]["artists"]]

                    tag_file(filepath,
                             artists,
                             album_name[0]["album"],
                             search[0]["title"],
                             track_num,
                             len(album),
                             year,
                             increase_img_req_res(thumbs[len(thumbs)-1]),
                             extension)

                    new_fname=(f"{output_dir}{artists[0]}_"
                                 f"{sanitize_string(album_name[0]["album"])}"
                                 f"_{album_name[0]["trackNumber"]:02d}_"
                                 f"{sanitize_string(search[0]["title"])}"
                                 f".{extension}")

                    info(f"{os.path.basename(filepath)} -> "
                         f"{os.path.basename(new_fname)}")

                    shutil.move(filepath, new_fname)

                    if (generate_playlists):
                        handler.write_to_playlists(url, duration,
                                                   artist, title,
                                                   track_num,
                                                   album_name[0]["album"],
                                                   new_fname,
                                                   output_dir)
                    add_to_record({
                        "status": status,
                        "found_artist": artist,
                        "found_title": title,
                        "provider": provider,
                        "ext": extension,
                        "url": url,
                        "duration": duration,
                        "uploader": uploader
                    }, record)

        # NOTE: This occurs when both title and artist cannot be parsed.
        # Should only happen when you have a delimiter that can't clearly
        # be used to distinguish betwen artist and title such as a space
        else:
            info(f"ARTIST AND SONG NOT FOUND: {title}")
            add_to_record({
                "status": "SEARCH_FOUND_NOTHING",
                "found_title": title,
                "provider": provider,
                "ext": extension,
                "url": url,
                "duration": duration,
                "uploader": uploader
            }, record)


def user_replace_filename(self, title, artists, filepath, extension,
                          album_name, url, duration, track_number, album_len,
                          album_date, thumbnail_url, generate_playlists):
    """
        User Initiated Filename Replacement Method. Replaces filename, tags
            file with relevant metadata, and adds to playlist if desired

        Args:
            title (str)
            artists (str)
            filepath (str)
            extension (str)
            album_name (str)
            url (str)
            duration (int)
            track_number (int)
            album_len (int)
            album_date (str)
            thumbnail_url (dict)
            generate_playlists (bool)

    """

    tag_file(filepath,
             artists,
             album_name,
             title,
             track_number,
             album_len,
             album_date,
             increase_img_req_res(thumbnail_url),
             extension)

    if (not album_name):
        album_name=title

    info(f"{os.path.basename(filepath)} -> {artists[0]}_"
         f"{sanitize_string(album_name)}_"
         f"{track_number:02d}_"
         f"{title}"
         f".{extension}")

    shutil.move(filepath, f"{self.output_dir}"
                f"{artists[0]}_"
                f"{album_name}_"
                f"{track_number:02d}_"
                f"{title}"
                f".{extension}")

    if (generate_playlists):
        self.playlist_handler.write_to_playlists(url, duration,
                                                 artists[0], title,
                                                 track_number,
                                                 album_name,
                                                 filepath,
                                                 self.output_dir)
