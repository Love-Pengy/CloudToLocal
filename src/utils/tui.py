import io
import json
import traceback
import urllib.request

from utils.printing import warning
from textual.reactive import reactive
from textual_image.widget import Image
from textual.app import App, ComposeResult
from utils.playlist_handler import PlaylistHandler
from textual.containers import Horizontal, Vertical
from globals import get_report_status_str, ReportStatus
from utils.file_operations import user_replace_filename
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
            output["artists"] = report["artists"]
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
            return ({"closest_match": output})
        case _:
            warning("Invalid State For Formatting Album Info")


class ctl_tui(App):

    # TODO: should make this a menu or something
    BINDINGS = [
        ("n", "accept_new", "Accept New Metadata"),
        ("c", "accept_closest", "Accept Closest Match"),
        # NOTE: this is a little silly, should have user input album.
        ("o", "accept_original", "Accept Original (No Album)"),
        # ("s", "search_again", "Search Again"),
        # ("i", "input_scratch", "Input From Scratch"),
        # ("r", "replace_entry", "Retry Download Process With New URL"),
        ("ctrl+s", "skip_entry", "Skip Entry"),
        # ("ctrl+r", "retry_download", "Retry Download Process"),
        # ("p", "pick_and_choose", "Pick Elements To Pick From Both Before And After")
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
        height: 100vh;
    }

    #full_img {
        width: auto;
        height: auto;
    }

    #album_info {
        width: 100vw;
        height: 25vh;
    }

    #status {
        width: 100%;
        text-align: center;
    }

    #album_art {
        width: 100%;
        height: 75vh;
        align: center middle;
    }
    """

    def __init__(self, arguments, **kwargs):
        super().__init__(**kwargs)

        self.output_filepath = arguments.outdir
        if (not (self.output_filepath[len(self.output_filepath)-1] == '/')):
            self.output_filepath += '/'

        self.report_path = self.output_filepath+"/ctl_report"
        self.playlists_info = []
        self.playlist_handler = PlaylistHandler(arguments.retry_amt,
                                                arguments.playlists,
                                                self.playlists_info,
                                                arguments.request_sleep)

        with open(self.report_path, "r") as fptr:
            self.report_dict = json.load(fptr)
        self.current_report_key_iter = iter(list(self.report_dict))
        self.current_report_key = next(self.current_report_key_iter)
        self.theme = "textual-dark"

    def pop_and_increment_report_key(self):
        try:
            self.report_dict.pop(self.current_report_key)
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()

    def increment_report_key(self):
        try:
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()

    def compose(self) -> ComposeResult:
        current_report = self.report_dict[self.current_report_key]
        after_width = None
        after_height = None
        after_present = False
        closest_match_present = False
        try:
            with urllib.request.urlopen(current_report
                                        ["before"]["thumbnail_url"]) as response:
                request_response = response.read()
                image1_data = io.BytesIO(request_response)

            if ("after" in current_report
                    and not (current_report["status"] == ReportStatus.SEARCH_FOUND_NOTHING)):
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
                    yield Horizontal(Image(image1_data, id="full_img"), id="album_art")
                    title = current_report["after"]["closest_match"]["title"]
                    closest_match_present = True
            else:
                yield Horizontal(Image(image1_data, id="full_img"), id="album_art")
                title = current_report["before"]["title"]

            before_width = current_report["before"]["thumbnail_width"]
            before_height = current_report["before"]["thumbnail_height"]
        except Exception as e:
            # FIXME: this should handle failure ~ BEF
            warning(f"URL Retrieval For Compose Failed: {
                    traceback.format_exc()}")
            warning(e)

        after_str = "(X,X)" if not after_width else f"({after_width}px, {after_height}px)"
        self.title = f"({before_width}px,{before_height}px) {title} {after_str}"
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
                                        "search_again", "input_scratch", "pick_and_choose"]
            case ReportStatus.DOWNLOAD_SUCCESS:
                disabled_action_list = ["accept_new",
                                        "accept_closest", "retry_download", "pick_and_choose"]
            case ReportStatus.DOWNLOAD_NO_UPDATE:
                disabled_action_list = ["accept_new", "retry_download", "pick_and_choose"]
            case ReportStatus.SEARCH_FOUND_NOTHING:
                disabled_action_list = ["accept_new",
                                        "accept_closest", "retry_download", "pick_and_choose"]
            case ReportStatus.SINGLE:
                disabled_action_list = ["accept_new", "accept_closest", "retry_download"]
            case ReportStatus.ALBUM_FOUND:
                disabled_action_list = ["accept_closest", "retry_download"]

        if (action in disabled_action_list):
            return False
        return True

    def action_accept_closest(self):
        current_report = self.report_dict[self.current_report_key]
        closest_match = current_report["after"]["closest_match"]

        if ("year" in closest_match):
            album_date = closest_match["year"]
        else:
            album_date = None

        artists = [artist["name"]
                   for artist in closest_match["artists"]]

        song_path = current_report["before"]["path"]

        new_fname = user_replace_filename(closest_match["title"], artists,
                                          song_path,
                                          current_report["after"]["ext"],
                                          closest_match["album"],
                                          current_report["after"]["duration"],
                                          closest_match["trackNumber"],
                                          closest_match["album_len"],
                                          album_date,
                                          closest_match["thumbnail_info"])

        self.playlist_handler.write_to_playlists(current_report["before"]["playlists"], None,
                                                 new_fname, self.output_filepath,
                                                 closest_match["title"],
                                                 closest_match["artists"][0]["name"],
                                                 current_report["after"]["duration"])

        self.pop_and_increment_report_key()

    def action_accept_original(self):
        current_report = self.report_dict[self.current_report_key]
        before = current_report["before"]
        if ("after" in current_report):
            path = current_report["after"]["filepath"]
        else:
            path = before["path"]

        new_fname = user_replace_filename(before["title"],
                                          [before["uploader"]],
                                          path,
                                          before["ext"],
                                          None,
                                          before["duration"],
                                          1,
                                          1,
                                          None,
                                          {"height": before["thumbnail_height"],
                                           "width": before["thumbnail_width"],
                                           "url": before["thumbnail_url"]})

        self.playlist_handler.write_to_playlists(before["playlists"], None, new_fname,
                                                 self.output_filepath, before["title"],
                                                 before["uploader"], before["duration"])

        self.pop_and_increment_report_key()

    # TODO: create new screen for this
    def action_search_again(self):
        pass
        self.playlist_handler.write_to_playlists()
        self.pop_and_increment_report_key()

    # TODO: create new screen for this
    def action_input_scratch(self):
        pass
        self.playlist_handler.write_to_playlists()
        self.pop_and_increment_report_key()

    # TODO: create new screen for this
    def action_replace_entry(self):
        pass
        self.playlist_handler.write_to_playlists()
        self.pop_and_increment_report_key()

    def action_skip_entry(self):
        self.increment_report_key()

    def action_accept_new(self):
        """ Accept newly written metadata
            @note currently metadata is written when new album is found with confidence, so this
            doesn't need to do anything"""

        current_report = self.report_dict[self.current_report_key]

        after = current_report["after"]
        self.playlist_handler.write_to_playlists(current_report["before"]["playlists"], None,
                                                 after["filename"], self.output_filepath,
                                                 after["title"], after["artists"][0],
                                                 after["duration"])
        self.pop_and_increment_report_key()

    # TODO: create new screen for this
    def action_retry_download(self):
        pass
        self.pop_and_increment_report_key()

    def action_pick_and_choose(self):
        pass
        self.pop_and_increment_report_key()

    def action_quit(self):
        with open(self.report_path, "w") as f:
            json.dump(self.report_dict, f, indent=2)
        self.exit()

    # def on_mount(self) -> None:
    #     self.title = "Test Application For CloudtoLocal TUI"
