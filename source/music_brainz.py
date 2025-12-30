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
import logging
from dataclasses import dataclass, field

import globals
from mbzero import mbzerror
from mbzero import caarequest
from mbzero import mbzrequest as mbr

logger = logging.getLogger(__name__)

MAX_THUMBNAIL_RETRIES = 10
THUMBNAIL_SIZE_PRIO_LIST = ["1200", "500", "250"]

# Statuses that are acceptable to use
MUSICBRAINZ_STATUS_PRIO_LIST = [
    "Official",
    # Applicable to unreleased songs ex. things can't stay the same by brockhampton
    "Bootleg",
    # Occasionally Status isn't filled out
    None,
    # NOTE: Promotional content often doesn't have correct release metadata so we ignore it
    # Promotion
]


@dataclass
class MusicbrainzMetadata:
    title: str = None
    album: str = None
    artist: str = None
    track_count: int = 0
    total_tracks: int = 0
    is_single: bool = False
    release_date: str = None
    release_mbid: str = None
    thumbnail_url: str = None
    thumbnail_resolution: str = None
    artists: list[str] = field(default_factory=list)


def musicbrainz_obtain_caa_image_data(user_agent: str, release_mbid: str) -> (str, int):

    if (not release_mbid):
        logger.warning("Release mbid is none...Can't obtain user_agent.")
        return (None, None)

    logger.info(f"Searching for {release_mbid} in CAA.")
    for i in range(1, MAX_THUMBNAIL_RETRIES+1):
        try:
            request_content = caarequest.CaaRequest(user_agent, "release", release_mbid).send()
            content_json = json.loads(request_content.decode("utf-8"))
            images = content_json.get("images", [])
            if (not images):
                logger.debug("No images found in CAA query.")
                return ((None, None))

            # TO-DO: Potentially add front and back? ~ BEF
            thumbnail_spec = next(
                (element for element in images if "Front" in element.get("types", [])), None)

            if (not thumbnail_spec):
                logger.debug("No front images found in musicbrainz query.")
                return ((None, None))

            thumbnails = thumbnail_spec.get("thumbnails", {})
            for size in THUMBNAIL_SIZE_PRIO_LIST:
                desired_thumbnail_url = thumbnails.get(size, None)
                if (desired_thumbnail_url):
                    logger.info(f"Thumbnail found from CAA: {desired_thumbnail_url} {int(size)}")
                    return (desired_thumbnail_url, int(size))
            else:
                break

        except mbzerror.MbzWebServiceError:
            delay = i ** 2
            logger.exception(f"Musicbrainz service error, retrying in {delay}s...")
            time.sleep(delay)
            continue
        except mbzerror.MbzNotFoundError:
            break

    logger.info("Failed to request image from CAA.")
    return ((None, None))


# NOTE: This is set so high because it seems as though the API randomly throws errors and
#       then works a bit later, so the thought is to allow exponential backoff to fix this for
#       the time being ~ BEF
MUSICBRAINZ_RETRIES = 10
MUSICBRAINZ_ACCEPTED_FORMATS = ["Digital Media", "CD"]


def musicbrainz_construct_user_agent(email: str) -> str:
    """ Construct expected user agent format given email. """
    if (not email):
        return None
    return (f"cloud_to_local/{globals.CTLDL_VERSION} {email}")


def musicbrainz_search(user_agent: str, title: str, artist: str) -> MusicbrainzMetadata:
    """ Search music brainz database for metadata relating to the title and artist specified. """

    content = None
    for i in range(1, MUSICBRAINZ_RETRIES+1):
        try:

            search = mbr.MbzRequestSearch(user_agent, "recording",
                                          f'artist:"{artist}" AND recording:"{title}"')
            content = search.send()
            logger.debug(f"music brainz search url: {
                         search.url}/{search.entity_type}?query={search.query}&fmt=json")
            break
        except mbzerror.MbzWebServiceError:
            delay = i ** 2
            logger.exception(f"Musicbrainz service error, retrying in {delay}...")
            time.sleep(delay)
            continue
        except mbzerror.MbzNotFoundError:
            break

    content_json = json.loads(content.decode("utf-8"))

    recordings = content_json.get("recordings", None)
    if (not recordings):
        logger.info(f"{title} - {artist} has no musicbrainz entry. Consider contributing!")
        return None

    for recording in recordings:
        release = None
        output = MusicbrainzMetadata()
        for search_status in MUSICBRAINZ_STATUS_PRIO_LIST:
            release = next((curr_release for curr_release in recording.get(
                "releases", []) if search_status == curr_release.get("status", None)), None)
            if (release):
                break

        else:
            continue

        output.title = recording.get("title", None)

        artists = recording.get("artist-credit", None)
        output.artists = [artist["name"] for artist in artists]
        output.artist = output.artists[0]

        if ((not output.artist) or (not output.title)):
            logger.debug(
                "Artist or title not found in musicbrainz response... Trying next recording")
            continue

        output.release_date = release.get("date", None) or recording.get("first-release-date", None)

        if ("Album" == release.get("release-group", {}).get("primary-type", None)):
            output.is_single = False
            output.album = release.get("release-group", {}).get("title", None)
        else:
            output.is_single = True
            output.album = output.title

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
                logger.debug(f"Supported media format not found for {
                    title} - {artist}... Trying next recording")
                continue

            output.total_tracks = accepted_media.get("track-count", 1)
            output.track_count = accepted_media.get("track-offset", 1)

        output.release_mbid = release.get("id", None)
        if (output.release_mbid):
            # To give music brainz ample time between requests, sleep based on previous sleep count
            time.sleep(10 if i**2 < 10 else i**2)
            output.thumbnail_url, output.thumbnail_resolution = musicbrainz_obtain_caa_image_data(
                user_agent,
                output.release_mbid)

        logger.info(f"Metadata obtained: {title} ~ {artist} -> {output.title} ~ {output.artist}")
        return output

    logger.info(f"Metadata not found for {title} - {artist}")
    return None
