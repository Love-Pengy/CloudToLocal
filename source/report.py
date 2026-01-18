###
#  @file    report.py
#  @author  Brandon Elias Frazier
#  @date    Dec 06, 2025
#
#  @brief   CTLDL report implementation
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


class ReportStatus:
    DOWNLOAD_FAILURE = 0
    DOWNLOAD_SUCCESS = 1
    METADATA_NOT_FOUND = 2
    SINGLE = 3
    ALBUM_FOUND = 4


def get_report_status_str(val):
    rstat_dict = ReportStatus.__dict__
    return (list(rstat_dict.keys())[list(rstat_dict.values()).index(val)])


VALID_REPORT_KEYS = ["title", "uploader", "provider", "ext", "duration", "uploader",
                     "thumbnail_url", "thumbnail_width", "thumbnail_height", "genres", "path",
                     "url", "playlists", "artist", "artists", "album", "single", "release_date",
                     "track_num", "total_tracks", "mbid", "lyrics"]


def verify_search_report_keys(context: dict, verify_list: list):
    for key in context:
        if (key not in verify_list):
            raise ValueError(f"Invalid Search Key: {key}")


def add_to_report_pre_search(context, report, url, status):
    verify_search_report_keys(context, VALID_REPORT_KEYS)
    report[url] = {}
    report[url]["pre"] = context
    report[url]["status"] = status


def add_to_report_post_search(context, report, url, status):
    verify_search_report_keys(context, VALID_REPORT_KEYS)
    report[url]["post"] = context
    report[url]["status"] = status


def update_report_status(report, url, status):
    report[url]["status"] = status
