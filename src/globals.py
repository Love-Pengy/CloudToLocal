VERBOSE = False
FAIL_ON_WARNING = False
QUIET = False
REQUEST_RESOLUTION = 4000

class ReportStatus:
    DOWNLOAD_FAILURE = 0
    DOWNLOAD_SUCCESS = 1
    DOWNLOAD_NO_UPDATE = 2
    SEARCH_FOUND_NOTHING = 3
    SINGLE = 4
    ALBUM_FOUND = 5

def get_report_status_str(val):
    rstat_dict = ReportStatus.__dict__
    return(list(rstat_dict.keys())[list(rstat_dict.values()).index(val)])
