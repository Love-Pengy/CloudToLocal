import io
import urllib
from PIL import Image


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
        Replace Thumbnail object of size 120x120 with 1480x1480

        Args:
            low_res (dict)

        Returns:
            Dictionary of increased size
    """

    high_res = {}
    high_res["height"] = 1480
    high_res["width"] = 1480
    high_res["url"] = low_res["url"].replace("w120-h120",
                                             "w1480-h1480")
    return (high_res)
