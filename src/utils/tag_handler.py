import mutagen
import urllib
import base64
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import TIT2, TOPE, TALB, TRCK, TDAT, APIC
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis


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
