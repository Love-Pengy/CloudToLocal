VERBOSE = False
FAIL_ON_WARNING = False
QUIET = False

class ReportStatus:
    DOWNLOAD_FAILURE = 0
    DOWNLOAD_SUCCESS = 1
    DOWNLOAD_NO_UPDATE = 2
    SEARCH_FOUND_NOTHING = 3
    SINGLE = 4
    ALBUM_FOUND = 5

def get_report_status_str(val):
    return(ReportStatus.__dict__.keys()[dict.values().index(val)])
