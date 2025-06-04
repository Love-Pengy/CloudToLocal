import mutagen
import urllib
import base64


def tag_file(filepath, artist, album, title, track_num,
             total_tracks, year, thumbnail):
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
    """

    audio = mutagen.File(filepath)

    if (isinstance(audio, mutagen.oggvorbis.OggVorbis)
            or isinstance(audio, mutagen.oggopus.OggOpus)):
        picture = mutagen.flac.Picture()

        audio["album"] = album
        audio["artist"] = artist
        audio["title"] = title
        audio["tracknumber"] = f"{track_num}/{total_tracks}"
        if (year):
            audio["date"] = year

        header = urllib.request.urlopen(thumbnail["url"])
        picture.data = header.read()
        header.close()
        picture.type = 17
        picture.desc = u"Cover"
        picture.mime = u"image/jpeg"
        picture.width = thumbnail["width"]
        picture.height = thumbnail["height"]
        picture.depth = 8

        picture_data = picture.write()
        encoded_data = base64.b64encode(picture_data)
        comment_val = encoded_data.decode("ascii")
        audio["metadata_block_picture"] = [comment_val]

    elif (isinstance(audio, mutagen.mp4.MP4)):
        audio['\xa9nam'] = title
        audio['\xa9alb'] = album
        audio['\xa9ART'] = artist
        if (year):
            audio['\xa9day'] = year
        header = urllib.request.urlopen(thumbnail["url"])
        audio['covr'] = [mutagen.mp4.MP4Cover(header.read(),
                                              imageformat=mutagen.mp4.MP4Cover.FORMAT_JPEG)]
        header.close()

    else:
        audio.add_picture(mutagen.APIC(
                          encoding=3,  # utf-8
                          mime="image/jpeg",
                          type=3,
                          desc="Cover",
                          data=urllib.request
                          .urlopen(thumbnail["url"]).read()
                          ))

    audio.save()
