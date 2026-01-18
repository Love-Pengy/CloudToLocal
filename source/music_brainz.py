##
#  @file    music_brainz.py
#  @author  Brandon Elias Frazier
#  @date    Dec 06, 2025
#
#  @brief   Functions for querying music brainz api
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
#  @note    Some important vocab relating to the API: recording is the actual song,
#           releases are things that the song shows up in (usually albums), media
#           is some specifications about the format of the release
#
#################################################################################


import json
import time
from dataclasses import dataclass, field

import globals
from mbzero import mbzerror
from mbzero import mbzrequest as mbr
from utils.printing import info, warning


@dataclass
class MusicbrainzMetadata:
    title: str = None
    album: str = None
    artist: str = None
    track_count: int = 0
    total_tracks: int = 0
    is_single: bool = False
    release_date: str = None
    # NOTE: This is needed to obtain the album art later down the road ~ BEF
    release_mbid: str = None
    artists: list[str] = field(default_factory=list)


# NOTE: This is set so high because it seems as though the API randomly throws errors and
#       then works a bit later, so the thought is to allow exponential backoff to fix this for
#       the time being ~ BEF
MUSICBRAINZ_RETRIES = 10
MUSICBRAINZ_ACCEPTED_FORMATS = ["Digital Media", "CD"]


def construct_user_agent(email: str) -> str:
    """ Construct expected user agent format given email. """
    if (not email):
        return None
    return (f"cloud_to_local/{globals.CTLDL_VERSION} {email}")


def musicbrainz_search(user_agent: str, title: str, artist: str) -> MusicbrainzMetadata:
    """ Search music brainz database for metadata relating to the title and artist specified. """

    content = None
    output = MusicbrainzMetadata()
    for i in range(0, MUSICBRAINZ_RETRIES):
        try:
            content = mbr.MbzRequestSearch(user_agent, "recording",
                                           f'artist:"{artist}" AND recording:"{title}"').send()
            break
        except mbzerror.MbzWebServiceError:
            #  TO-DO: Some sort of service error, should debug/verbose log the specifics ~ BEF
            delay = i ** 2
            info(f"Musicbrainz service error, retrying in {delay}...")
            time.sleep(delay)
            continue

    if (not content):
        info("Failed to retrieve metadata for {title} - {artist}")
        return None

    content_json = json.loads(content.decode("utf-8"))

    recordings = content_json.get("recordings", None)
    if (not recordings):
        info(f"{title} - {artist} has no musicbrainz entry. Consider contributing!")
        return None

    recording = recordings[0]
    release = next(
        (release for release in recording["releases"] if "Official" == release.get("status", None)),
        None)

    if (not release):
        info(f"Official release not found for {title} - {artist}")
        return None

    output.title = recording.get("title", None)
    assert output.title, "Title missing from musicbrainz query"

    artists = recording.get("artist-credit", None)
    assert artists, "Artists missing from musicbrainz query"

    output.artists = [artist["name"] for artist in artists]
    output.artist = output.artists[0]

    output.release_date = release.get("date", None)
    assert output.release_date, "Release date missing from musicbrainz query"

    if ("Album" == release.get("release-group", {}).get("primary-type", None)):
        output.is_single = False
        output.album = release.get("release-group", {}).get("title", None)
        assert output.album, "Album name not found, but single is not specified"
    else:
        output.is_single = True

    if (output.is_single):
        output.track_count = 1
        output.total_tracks = 1
    else:
        media = release.get("media", [None])
        accepted_media = next(
            (accepted for accepted in media if accepted.get(
                "format", None) in MUSICBRAINZ_ACCEPTED_FORMATS),
            None)

        if (not accepted_media):
            info(f"Supported media format not found for {title} - {artist}")
            return None

        output.total_tracks = accepted_media.get("track-count", 1)
        output.track_count = accepted_media.get("track-offset", 1)

    if (output.track_count > output.total_tracks):
        assert output.track_count < output.total_tracks, f"Invalid track_count found \
        {output.track_count=} {output.total_tracks=}"

    output.release_mbid = release.get("id", None)
    assert output.release_mbid, "Somehow release doesn't have an mbid?"

    info(f"Metadata obtained: {title} ~ {artist} -> {output.title} ~ {output.artist}")
    return output
