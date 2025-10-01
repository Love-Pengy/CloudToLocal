import io
import json
import traceback
import urllib.request

from ytmusicapi import YTMusic
from globals import ReportStatus
from utils.printing import warning
from textual.reactive import reactive
from textual_image.widget import Image
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from globals import get_report_status_str, ReportStatus
from utils.file_operations import user_replace_filename
from utils.common import get_img_size_url, sanitize_string
from textual.widgets import Footer, Header, Pretty, Rule, Static


def format_album_info(report, state) -> dict:
    """Format report into a dict able to be pretty printed as the album info

        Args:
            report (dict): before or after dictionary
            state (str): specifes whether report is before or after
    """
    # FIXME: dawg why didn't I match these to begin with
    # also put docstring for how this works
    output = {}
    match (state):
        case "before":
            output["title"] = report["title"]
            output["uploader"] = report["uploader"]
            output["provider"] = report["provider"]
            output["duration"] = report["duration"]
            output["url"] = report["url"]
            return (output)
        case "after":
            output["title"] = report["title"]
            output["artist"] = report["artist"]
            output["provider"] = report["provider"]
            output["duration"] = report["duration"]
            output["album"] = report["album"]
            output["url"] = report["url"]
            output["filename"] = report["filename"]
            return (output)
        case "closest":
            closest = report["closest_match"]
            output["title"] = closest["title"]
            output["artists"] = closest["artists"]
            output["album"] = closest["album"]
            # TODO: might have to convert this back to seconds to match
            output["duration"] = closest["duration"]
            return (output)
        case _:
            warning("Invalid State For Formatting Album Info")


def correct_missing(report_path):
    """Interactive Function To Fix Albums And Songs That Could Not Be
        Automatically Found With A High Level Of Certainty

        Args:
            report_path (str): Path To Report JSON File
    """

    ytmusic = YTMusic()
    with open(report_path, "r") as f:
        report = json.load(f)

    for entry_idx in list(report):
        spec = report[entry_idx]
        # print(f"OG Path: {song_path}\n"
        #       f"OG Title: {spec["found_title"]}, OG Artist: {
        #           spec["found_artist"]}\n"
        #       f"Matched Title: {spec["closest_match"]["title"]}, "
        #       f"Matched Artist: {[artist["name"]
        #                           for artist in
        #                           spec["closest_match"]["artists"]]}\n"
        #       f"Matched Album: {spec["closest_match"]["album"]}\n")
        # f"Provider: {spec["provider"]}"

        # NOTE: 1920x1080 is assumed here. This gets scaled to term size anyway
        render_comparison(spec, 1920, 1080)
        user_input = None
        while (not (user_input == '1') and
               not (user_input == '2') and
               not (user_input == '3') and
               not (user_input == '4') and
               not (user_input == 'q')):
            user_input = input(
                "1: Accept Closest Match 2: Accept Original (No Album) "
                "3: Search Again 4: Input From Scratch q: Save And Exit ")

        match user_input:
            case '1':
                closest_match = spec["closest_match"]
                artists = [artist["name"]
                           for artist in closest_match["artists"]]

                if ("year" in closest_match):
                    album_date = closest_match["year"]
                else:
                    album_date = None

                if (closest_match["thumbnails"] is not None):
                    thumbnail = closest_match["thumbnails"][len(
                        closest_match["thumbnails"]-1)]
                else:
                    thumbnail = None

                user_replace_filename(closest_match["title"], artists,
                                      song_path, spec["ext"],
                                      closest_match["album"],
                                      spec["url"], spec["duration"],
                                      closest_match["trackNumber"],
                                      closest_match["album_len"],
                                      album_date,
                                      thumbnail)
                report.pop(song_path)

            case '2':
                user_replace_filename(spec["found_title"],
                                      [spec["found_artist"]],
                                      song_path,
                                      spec["ext"],
                                      "", spec["url"],
                                      spec["duration"],
                                      1, 1, None, user_url)
                report.pop(song_path)

            case '3':
                while (1):
                    print(f"Old FilePath: {song_path}\n"
                          f"Old Title: {spec["closest_match"]["title"]}\n"
                          f"Old Artist: {spec["closest_match"]["title"]}")

                    user_title = input("New Title: ")
                    user_artist = input("New Artist: ")
                    search = ytmusic.search(
                        user_artist + " " + user_title, filter="songs", limit=1)
                    if (search):
                        album = ytmusic.get_album(
                            search[0]["album"]["id"])["tracks"]

                        # See if track is in the album we found
                        album_name = [
                            track for track in album
                            if track["title"].lower() == user_title.lower()
                        ]
                        if (album_name):
                            track_num = album_name[0]["trackNumber"]

                            if (("thumbnails" in album_name[0])
                                    and (album_name[0]["thumbnails"]
                                         is not None)):
                                thumbs = album_name[0]["thumbnails"]
                            else:
                                thumbs = search[0]["thumbnails"]

                            artists = [sanitize_string(artist["name"])
                                       for artist in search[0]["artists"]]

                            if (("year" in search[0])
                               and (search[0]["year"] is not None)):
                                year = search[0]["year"]
                            else:
                                year = None

                            print(f"Found: \nTitle: {search[0]["title"]}\n"
                                  f"Artists: {artists}\n"
                                  f"Track Num: {track_num}\n"
                                  f"Album Len: {len(album)}\n"
                                  f"Year: {year}\n"
                                  f"Thumbnail: {thumbs[len(thumbs)-1]}")

                            user_input = ""
                            while ((not user_input.lower() == 'y') and
                                   (not user_input.lower() == 'n')):
                                user_input = input(
                                    "Does The Above Seem Correct? (Y/N) ")

                            if (user_input.lower() == 'y'):
                                image_size = get_img_size_url(
                                    thumbs[len(thumbs-1)]["url"])

                                url = f"http://youtu.be/{
                                    search[0]["videoId"]}"
                                user_replace_filename(search[0]["title"],
                                                      artists,
                                                      song_path,
                                                      spec["ext"],
                                                      album_name[0]["album"],
                                                      url,
                                                      spec["duration"],
                                                      track_num,
                                                      len(album),
                                                      year,
                                                      {"height": image_size[1],
                                                       "width": image_size[0],
                                                       "url": thumbs[len(thumbs)-1]["url"]})
                                report.pop(song_path)
                                break
                        else:
                            print("Album Not Found")
                    else:
                        print("Song Not Found")
            case '4':
                while (1):
                    print(f"Old FilePath: {song_path}\n"
                          f"Old Title: {spec["closest_match"]["title"]}\n"
                          f"Old Artist: {spec["closest_match"]["title"]}")
                    user_title = input("New Title: ")
                    user_artists = [input for input in input(
                        "New Artists (seperated by ,): ").split(',')]
                    user_album = input(
                        "New Album (Leave Blank For None): ")
                    user_url = input("New Song Url: ")
                    user_duration = int(input("New Duration (seconds): "))
                    user_track_num = int(input("New Track Number: "))
                    user_total_tracks = int(
                        input("Total Tracks In Album: "))
                    user_album_date = input("Album Year: ")
                    user_thumbnail_url = input("Thumbnail Url: ")

                    confirmation = input(f"Title: {user_title}\n"
                                         f"Artist: {user_artists}\n"
                                         f"Album: {user_album}\n"
                                         f"Url: {user_url}\n"
                                         f"Duration: {user_duration}\n"
                                         f"Track Num: {user_track_num}\n"
                                         f"Total Tracks: {
                        user_total_tracks}\n"
                        f"Album Year: {user_album_date}\n"
                        "Does Everything Above Look Right? (Y/N) ")

                    if (confirmation.lower() == 'y'):
                        image_size = get_img_size_url(user_thumbnail_url)

                        user_replace_filename(user_title,
                                              user_artists,
                                              song_path,
                                              spec["ext"],
                                              user_album,
                                              user_url,
                                              user_duration,
                                              user_track_num,
                                              user_total_tracks,
                                              user_album_date,
                                              {"height": image_size[1],
                                               "width": image_size[0],
                                               "url": user_thumbnail_url}
                                              )
                        report.pop(song_path)
                        break
            case 'q':
                break
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)


class ctl_tui(App):

    # TODO: should make this a menu or something
    BINDINGS = [
        ("n", "accept_new", "Accept New Generated Option"),
        ("c", "accept_closest", "Accept Closest Match"),
        ("o", "accept_original", "Accept Original (No Album)"),
        ("s", "search_again", "Search Again"),
        ("i", "input_scratch", "Input From Scratch"),
        ("r", "replace_entry", "Retry Download Process With New URL"),
        ("s", "skip_entry", "Skip Entry"),
        ("R", "retry_download", "Retry Download Process"),
        # NOTE: this will require another screen
        ("p", "pick_and_choose", "Pick Elements To Pick From Both Before And After")
    ]

    # Refresh Footer/Bindings and recompose on change
    current_report_key = reactive(None, recompose=True, bindings=True)

    # TODO: this should be moved to a file
    CSS = """

    Screen {
        align: center middle;
    }

    #img1, #img2 {
        width: 50vw;
        height: auto;
    }

    #before_info, #after_info {
        width: 50vw;
        height: auto;
    }

    #album_info {
        width: 100%;
        height: 25vh;
    }

    #status {
        width: 100%;
        text-align: center;
    }

    #album_art {
        width: 100%;
        height: 75vh;
    }
    """

    def __init__(self, report_path, **kwargs):
        super().__init__(**kwargs)
        with open(report_path, "r") as fptr:
            self.report_dict = json.load(fptr)
        self.current_report_key_iter = iter(self.report_dict)
        self.current_report_key = next(self.current_report_key_iter)
        # self.current_report_index = 0
        self.theme = "textual-dark"

    def increment_report_key(self):
        try: 
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            self.exit(1)

    def compose(self) -> ComposeResult:
        current_report = self.report_dict[self.current_report_key]
        after_width = None
        after_height = None
        after_present = False
        closest_match_present = False
        # FIXME: needs to be status based. Will fail on status 2 for instance because of lack of thumbnail_info
        try:
            with urllib.request.urlopen(current_report
                                        ["before"]["thumbnail_url"]) as response:
                request_response = response.read()
                image1_data = io.BytesIO(request_response)

            if ("after" in current_report
                    and not (current_report["status"] == ReportStatus.SEARCH_FOUND_NOTHING)
                    # and current_report["status"] != ReportStatus.DOWNLOAD_NO_UPDATE
                ):
                if (not (current_report["status"] == ReportStatus.DOWNLOAD_NO_UPDATE)):
                    with urllib.request.urlopen(current_report
                                                ["after"]["thumbnail_info"]["url"]) as response:
                        request_response = response.read()
                        image2_data = io.BytesIO(request_response)
                        yield Horizontal(
                            Image(image1_data, id="img1"),
                            Image(image2_data, id="img2"), id="album_art"
                        )
                        title = current_report["after"]["title"]
                        after_width = current_report["after"]["thumbnail_info"]["width"]
                        after_height = current_report["after"]["thumbnail_info"]["height"]
                        after_present = True
                else:
                    yield Horizontal(
                            Image(image1_data, id="img1")
                    )
                    title = current_report["after"]["closest_match"]["title"]
                    closest_match_present = True
            else:
                # TODO: make this take up the whole screen
                yield Image(image1_data, id="img1")
                title = current_report["before"]["title"]

            before_width = current_report["before"]["thumbnail_width"]
            before_height = current_report["before"]["thumbnail_height"]
        except Exception as e:
            # FIXME: this should handle failure
            warning(f"URL Retrieval For Compose Failed: {
                    traceback.format_exc()}")
            warning(e)

        self.title = f"({before_width},{before_height}) {
            title} ({after_width},{after_height})"
        yield Header()
        yield Rule(line_style="ascii")

        # FIXME: fix this when not lazy ~ BEF
        if (after_present):
            yield Vertical(
                Static(get_report_status_str(
                    current_report["status"]), id="status"),
                Horizontal(
                    Pretty(format_album_info(
                        current_report["before"], "before"), id="before_info"),
                    Pretty(format_album_info(
                        current_report["after"], "after"), id="after_info"),
                    id="album_info"
                )
            )
        elif (closest_match_present):
            yield Vertical(
                Static(get_report_status_str(
                    current_report["status"]), id="status"),
                Horizontal(
                    Pretty(format_album_info(
                        current_report["before"], "before"), id="before_info"),
                    Pretty(format_album_info(
                        current_report["after"], "closest"), id="after_info"),
                    id="album_info"
                )
            )
        else:
            yield Vertical(
                Static(get_report_status_str(
                    current_report["status"]), id="status"),
                Pretty(format_album_info(
                    current_report["before"], "before"), id="before_info"), id="album_info"
            )

        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:

        disabled_action_list = None
        match (self.report_dict[self.current_report_key]["status"]):
            case ReportStatus.DOWNLOAD_FAILURE:
                disabled_action_list = ["accept_new", "accept_closest", "accept_original",
                                        "search_again", "input_scratch"]
            case ReportStatus.DOWNLOAD_SUCCESS:
                disabled_action_list = ["accept_new",
                                        "accept_closest", "retry_download"]
            case ReportStatus.DOWNLOAD_NO_UPDATE:
                disabled_action_list = ["accept_new",
                                        "accept_closest", "retry_download"]
            case ReportStatus.SEARCH_FOUND_NOTHING:
                disabled_action_list = ["accept_new",
                                        "accept_closest", "retry_download"]
            case ReportStatus.SINGLE:
                disabled_action_list = ["accept_new",
                                        "accept_closest", "retry_download"]
            case ReportStatus.ALBUM_FOUND:
                disabled_action_list = ["accept_closest", "retry_download"]

        if (action in disabled_action_list):
            return False
        return True

    def action_accept_closest(self):
        current_report = self.report_dict[self.current_report_key]
        closest_match = current_report["after"]["closest_match"]

        artists = [artist["name"]
                   for artist in closest_match["artists"]]

        if ("year" in closest_match):
            album_date = closest_match["year"]
        else:
            album_date = None

        if (closest_match["thumbnails"] is not None):
            thumbnail = closest_match["thumbnails"][len(
                closest_match["thumbnails"]-1)]
        else:
            thumbnail = None

        song_path = current_report["after"]["filepath"]

        user_replace_filename(closest_match["title"], artists,
                              current_report["after"]["filepath"],
                              current_report["after"]["ext"],
                              closest_match["album"],
                              current_report["after"]["url"],
                              current_report["after"]["duration"],
                              closest_match["trackNumber"],
                              closest_match["album_len"],
                              album_date,
                              thumbnail)

        self.report_list.pop(song_path)
        self.increment_report_key()

    def action_accept_original(self):
        pass
        self.increment_report_key()

    def action_search_again(self):
        pass
        self.increment_report_key()

    def action_input_scratch(self):
        pass
        self.increment_report_key()

    def action_replace_entry(self):
        pass
        self.increment_report_key()

    def action_skip_entry(self):
        pass
        self.increment_report_key()

    def action_accept_new(self):
        pass
        self.increment_report_key()

    def action_retry_download(self):
        pass
        self.increment_report_key()

    # def on_mount(self) -> None:
    #     self.title = "Test Application For CloudtoLocal TUI"
