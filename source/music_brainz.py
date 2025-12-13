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
#
#################################################################################


import json
from dataclasses import dataclass, field

from utils.printing import info
from mbzero import mbzrequest as mbr
from utils.globals import CTLDL_VERSION


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


def construct_user_agent(email: str) -> str:
    """ Construct expected user agent format given email. """
    if (not email):
        return None
    return (f"cloud_to_local/{CTLDL_VERSION} {email}")


def musicbrainz_search(user_agent: str, title: str, artist: str) -> MusicbrainzMetadata:
    """ Search music brainz database for metadata relating to the title and artist specified. """

    output = MusicbrainzMetadata()

    content = mbr.MbzRequestSearch(user_agent, "recording",
                                   'artist:"f{artist}" AND recording:"f{title}"').send()
    content_json = json.loads(content.decode("utf-8"))
    recordings = content_json.get("recordings", None)

    if (not recordings):
        info(f"{title} - {artist} has no musicbrainz entry. Consider contributing!")
        return None

    recording = recoridngs[0]

    release = next(
        (release for release in recording["releases"] if "Official" == release.get("status", None)),
        None)

    # TO-DO: Should probably take non-official one ~ BEF
    if (not release):
        info(f"Official release not found for {title} - {artist}")
        return None

    output.title = recording.get("title", None)
    assert output.title, "Title missing from musicbrainz query"

    artists = recording.get("artist-credit", None)
    assert artists, "Artists missing from musicbrainz query"

    output.artist = artists[0]
    output.artists = [artist["name"] for artist in artists]

    output.release_date = recording.get("date", None)
    assert output.release_date, "Release date missing from musicbrainz query"

    if ("Album" == recording.get("release-group", {}).get("primary-type", None)):
        output.is_single = False
        output.album = recording.get("release-group", {}).get("title", None)
        assert output.album, "Album name not found, but single is not specified"
    else:
        output.is_single = True

    if (output.is_single):
        output.track_count = 1
        output.total_tracks = 1
    else:
        output.total_tracks = recording.get("track-count", 1)
        output.track_count = recording.get(
            "media", [{}])[0].get("track", {}).get("track-offset", 1)

    if (output.track_count > output.total_tracks):
        assert output.track_count < output.total_tracks, f"Invalid track_count found \
        {output.track_count=} {output.total_tracks=}"

    output.release_mbid = release.get("id", None)
    assert output.release_mbid, "Somehow release doesn't have an mbid?"

    return output
