import io
import urllib
import requests

import globals
from PIL import Image
from utils.printing import warning, info
from yt_dlp import version as yt_dlp_version


def get_diff_count(in1, in2):
    """
        Get Amount Of Characters That Differ Between Two Strings
            Taking Into Account Position

        Args:
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
    """ Request The Source For CloudToLocal To Check For An Internet Connection! """
    request = requests.get("https://www.github.com/Love-Pengy/CloudToLocal")
    if (request.status_code == 200):
        return True
    return False


def list_to_comma_str(input: list):
    if (not len(input)):
        return (None)

    output = str(input[0]) + ','
    for value in input[1:]:
        output += ' ' + str(value) + ','

    return (output[:-1])


def comma_str_to_list(input: str):
    return (input.split(','))
