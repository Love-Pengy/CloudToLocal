import io
import os
import time
import glob
import urllib
import shutil
import requests

import globals
from PIL import Image
from utils.printing import warning, info
from yt_dlp import version as yt_dlp_version

CONNECTIVITY_CHECK_RETRIES = 5


class Providers:
    YT = "Youtube"
    SC = "Soundcloud"


def get_diff_count(in1, in2):
    """
        Get Amount Of Characters That Differ Between Two Strings
            Taking Into Account Position

        Arguments:
            in1 (str)
            in2 (str)

        Returns:
            Amount Of Characters That Are Different
    """

    if (len(in1) < len(in2)):
        str1 = in1
        str2 = in2
    else:
        str1 = in2
        str2 = in1

    count = 0
    for index, char in enumerate(str1):
        if (char != str2[index]):
            count += 1

    count += len(str2) - (index+1)
    return (count)


def sanitize_string(string):
    """Sanitize String For Usage In Filename
        replacing / with division slash
        and \0 with reverse solidus and 0"""

    return (string.replace('/', '∕').replace('\0', '\\'))


def get_img_size_url(url):
    """
        Get image dimensions from url

        Args:
            url (str)

        Returns:
            Tuple of dimensions (width, height)
    """

    with urllib.request.urlopen(url) as response:
        image_data = response.read()
    image_size = Image.open(
        io.BytesIO(image_data)).size
    return (image_size)


def increase_img_req_res(low_res):
    """
        Replace Thumbnail object of size 120x120 with 4000x4000

        Args:
            low_res (dict)

        Returns:
            Dictionary of increased size
    """

    thumbnail_exists = False
    width = globals.REQUEST_RESOLUTION
    height = globals.REQUEST_RESOLUTION
    while (not thumbnail_exists):
        high_res = {}
        high_res["width"] = width
        high_res["height"] = height
        high_res["url"] = low_res["url"].replace("w120-h120",
                                                 f"w{high_res["width"]}-h{high_res["height"]}")
        try:
            response = requests.head(high_res["url"], timeout=1)
            if (response.status_code == 200):
                thumbnail_exists = True
            else:
                width = width - 100
                height = height - 100
        except requests.exceptions.ReadTimeout:
            pass

    return (high_res)


def check_ytdlp_update():
    local_version = yt_dlp_version.__version__
    release_page = requests.get(
        "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest")
    latest_release = release_page.json()["tag_name"]
    if (not (local_version == latest_release)):
        warning(f"Newer yt_dlp Version Available, Please Update "
                f"If You Experience Download Issues"
                f"({local_version} -> {latest_release})")
    else:
        info(f"yt_dlp Is Up To Date (Version {latest_release})")


def connectivity_check():
    """ Request all used services to ensure a proper connection both locally and server side. """
    for i in range(0, CONNECTIVITY_CHECK_RETRIES):
        try:
            sc_req = requests.get("https://soundcloud.com/")
            yt_req = requests.get("https://www.youtube.com/")
            mb_req = requests.get("https://musicbrainz.org/ws/2/")

            if ((200 == yt_req.status_code)
                and (200 == mb_req.status_code)
                    and (200 == sc_req.status_code)):
                return True

        except requests.exceptions.ConnectionError:
            pass

        info(f"Failed to connect. Retrying in: {(i+2)**2} seconds....")
        time.sleep((i+2)**2)
        continue
    return False


def list_to_comma_str(input: list):
    if (not input):
        return (None)

    output = str(input[0]) + ','
    for value in input[1:]:
        output += ' ' + str(value) + ','

    return (output[:-1])


def comma_str_to_list(input: str):
    return (input.split(','))


def url_from_youtube_id(id: str):
    return (f"https://www.youtube.com/watch?v={id}")


def delete_folder_contents(path: str):
    """ Delete entire contents of a directory """
    glob_spec = glob.glob(path+"/*") if not path[-1] == '/' else glob.glob(path+'*')

    for file in glob_spec:
        if (not os.path.isdir(file)):
            os.remove(file)
        else:
            shutil.rmtree(file)


def clean_ytdlp_artifacts(path):
    """Delete .ytdl And .part Files From Download Director."""

    if path[-1] == '/':
        fixed_path = path
    else:
        fixed_path = path + '/'

    for f in (glob.glob(fixed_path+"*.part") + glob.glob(path+"*.ytdl") +
              glob.glob(fixed_path+"*.webp")):
        os.remove(f)


def validate_args(args: dict, possible_keys: list[str], required_keys: list[str] = None):

    if (not (len(args) == len(set(args).intersection(possible_keys)))):
        raise KeyError(f"Invalid Key in {args}. \n Possible Keys: {possible_keys}")

    if (required_keys):
        if (not (len(required_keys) == len(set(args).intersection(required_keys)))):
            raise KeyError(f"Required Keys: {required_keys}\n Passed Keys: {args}")
