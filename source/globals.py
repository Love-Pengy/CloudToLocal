QUIET = False
VERBOSE = False
CTLDL_VERSION = "0.0.0"
FAIL_ON_WARNING = False
REQUEST_RESOLUTION = 4000
MUSICBRAINZ_USER_AGENT = None


class ReportStatus:
    DOWNLOAD_FAILURE = 0
    DOWNLOAD_SUCCESS = 1
    DOWNLOAD_NO_UPDATE = 2
    SEARCH_FOUND_NOTHING = 3
    SINGLE = 4
    ALBUM_FOUND = 5

def get_report_status_str(val):
    rstat_dict = ReportStatus.__dict__
    return (list(rstat_dict.keys())[list(rstat_dict.values()).index(val)])
