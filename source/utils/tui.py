import io
import json
import traceback
import urllib.request
from time import strptime
from datetime import timedelta

from utils.printing import warning
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.app import App, ComposeResult
from textual_image.widget import Image
from utils.playlist_handler import PlaylistHandler
from globals import get_report_status_str, ReportStatus
from utils.file_operations import user_replace_filename
from textual.containers import Horizontal, Vertical, Grid
from utils.common import list_to_comma_str, comma_str_to_list
from textual.widgets import Footer, Header, Pretty, Rule, Static, Button, Label, Input


def format_album_info(report, state) -> dict:
    """Format report into a dict able to be pretty printed as the album info

        Args:
            report (dict): before or after dictionary
            state (str): specifies whether report is before or after
    """

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

            # quick and extremely dirty
            if (not type(closest["duration"]) is int):
                try:
                    ptime = strptime(closest["duration"], "%H:%M:%S")
                except ValueError:
                    ptime = strptime(closest["duration"], "%M:%S")
                finally:
                    output["duration"] = int(timedelta(hours=ptime.tm_hour, minutes=ptime.tm_min,
                                                       seconds=ptime.tm_sec).total_seconds())
            else:
                output["duration"] = closest["duration"]

            return ({"closest_match": output})
        case _:
            warning("Invalid State For Formatting Album Info")
            return (None)


class EditInputMenu(ModalScreen[dict]):
    def __init__(self, metadata: dict, metadata_type: str):

        self.metadata = metadata
        self.metadata_type = metadata_type
        self.output_metadata = self.metadata

        super().__init__()

    def compose(self) -> ComposeResult:
        meta = self.metadata
        match (self.metadata_type):
            case ("before"):
                yield Input(placeholder="title", value=meta["title"], type="text", id="title")
                yield Input(placeholder="artists", value=meta["uploader"],
                            type="text", id="artists")
                yield Input(placeholder="duration", value=str(meta["duration"]), type="integer",
                            id="duration")
                yield Input(placeholder="album", type="text", id="album")
            case ("after"):
                yield Input(placeholder="title", value=meta["title"], type="text", id="title")
                yield Input(placeholder="artists", value=list_to_comma_str(meta["artists"]),
                            type="text", id="artists")
                yield Input(placeholder="duration", value=str(meta["duration"]), type="integer",
                            id="duration")
                yield Input(placeholder="album", value=meta["album"], type="text", id="album")
            case ("closest"):
                yield Input(placeholder="title", value=meta["title"], type="text", id="title")
                yield Input(placeholder="artists", value=list_to_comma_str(meta["artists"]),
                            type="text", id="artists")
                yield Input(placeholder="duration", value=str(meta["duration_seconds"]),
                            type="integer", id="duration")
                yield Input(placeholder="album", value=meta["album"], type="text", id="album")
            case _:
                raise TypeError(f"Invalid metadata type: {self.metadata_type}")
        yield Button("All Done!", variant="primary", id="completion_button")

    def on_input_blurred(self, blurred_widget):

        if (not (blurred_widget.input.id == "artists")):
            self.output_metadata[blurred_widget.input.id] = blurred_widget.value
        else:
            self.output_metadata[blurred_widget.input.id] = comma_str_to_list(
                blurred_widget.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(self.output_metadata)


class EditSelectionMenu(ModalScreen):
    BINDINGS = []

    # Possible metadata types
    METADATA_TYPE_OPTIONS = ["before", "closest", "after", None]

    def __init__(self, metadata1: dict, meta_type1: str, metadata2: dict = None,
                 meta_type2: str = None):
        """ Initialize Edit Metadata Screen """

        if ((metadata1 not in self.METADATA_TYPE_OPTIONS)
                or (metadata2 and (meta_type2.lower() not in self.METADATA_TYPE_OPTIONS))):
            self.dismiss(None)

        self.meta1 = metadata1
        self.meta2 = metadata2
        self.meta_type1 = meta_type1.lower()
        self.meta_type2 = meta_type2.lower()

        self.meta_chosen = self.meta1 if not self.meta2 else None
        self.meta_type_chosen = self.meta_type1.lower() if not self.meta2 else None

        if (not self.meta2):
            self.meta_chosen = metadata1
            self.meta_type_chosen = meta_type1.lower()
            if (self.meta_type1 not in self.METADATA_TYPE_OPTIONS):
                self.dismiss(None)
            else:
                self.exit_menu()

        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Which Metadata Would You Like To Edit?"),
            Button("Original", variant="primary", id="original_meta_edit"),
            Button("New/Closest", variant="primary", id="new_meta_edit")
        )

    def exit_menu(self):

        self.dismiss((self.meta_chosen, self.meta_type_chosen))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if (event.button.id == "original_meta_edit"):
            if (self.meta_type1 == "before"):
                self.meta_chosen = self.meta1
            else:
                self.meta_chosen = self.meta2
            self.meta_type_chosen = "before"
        else:
            if (self.meta_type1 in ["after", "closest"]):
                self.meta = self.meta1
                self.meta_type_chosen = self.meta_type1
            else:
                self.meta_chosen = self.meta2
                self.meta_type_chosen = self.meta_type2

        self.exit_menu()


class ctl_tui(App):

    # TODO: should make this a menu or something
    BINDINGS = [
        ("n", "accept_new", "Accept New Metadata"),
        ("c", "accept_closest", "Accept Closest Match"),
        # NOTE: this is a little silly, should have user input album.
        ("o", "accept_original", "Accept Original (No Album)"),
        ("e", "edit_metadata", "Manually Edit Metadata"),
        # ("s", "search_again", "Search Again"),
        # ("i", "input_scratch", "Input From Scratch"),
        # ("r", "replace_entry", "Retry Download Process With New URL"),
        ("ctrl+s", "skip_entry", "Skip Entry"),
        # ("ctrl+r", "retry_download", "Retry Download Process"),
        # ("p", "pick_and_choose", "Pick Elements To Pick From Both Before And After")
    ]
    CSS_PATH = "../ctl-dl.tcss"

    # Refresh Footer/Bindings and recompose on change
    current_report_key = reactive(None, recompose=True, bindings=True)

    def __init__(self, arguments, **kwargs):
        super().__init__(**kwargs)

        self.output_filepath = arguments.outdir
        if (not (self.output_filepath[len(self.output_filepath)-1] == '/')):
            self.output_filepath += '/'

        self.report_path = self.output_filepath+"ctl_report"
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
        self.right_info = self.right_type = None

    def pop_and_increment_report_key(self):
        try:
            self.report_dict.pop(self.current_report_key)
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()
        self.right_info = None
        self.right_type = None

    def increment_report_key(self):
        try:
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()
        self.right_info = None
        self.right_type = None

    def compose(self) -> ComposeResult:
        current_report = self.report_dict[self.current_report_key]
        after_width = None
        after_height = None
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
                    after_source = "after"
                    self.right_info = current_report["after"]
                    self.right_type = "after"
                else:
                    with urllib.request.urlopen(current_report["after"]["closest_match"]
                                                ["thumbnail_info"]["url"]) as response:
                        request_response = response.read()
                        image2_data = io.BytesIO(request_response)

                    yield Horizontal(
                        Image(image1_data, id="img1"),
                        Image(image2_data, id="img2"), id="album_art"
                    )
                    title = current_report["after"]["closest_match"]["title"]
                    after_width = current_report["after"]["closest_match"]["thumbnail_info"]
                    ["width"]
                    after_height = current_report["after"]["closest_match"]["thumbnail_info"]
                    ["height"]
                    after_source = "closest"
                    self.right_info = current_report["after"]["closest_match"]
                    self.right_type = "closest"

                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Horizontal(
                        Pretty(format_album_info(
                            current_report["before"], "before"), id="before_info"),
                        Pretty(format_album_info(
                            current_report["after"], after_source), id="after_info"),
                        id="album_info"
                    )
                ]

            else:
                yield Horizontal(Image(image1_data, id="full_img"), id="album_art")
                title = current_report["before"]["title"]
                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Pretty(format_album_info(
                        current_report["before"], "before"), id="before_info")
                ]

            before_width = current_report["before"]["thumbnail_width"]
            before_height = current_report["before"]["thumbnail_height"]
        except Exception as e:
            warning(f"URL Retrieval For Compose Failed. Skipping Entry: {
                    traceback.format_exc()}")
            warning(e)
            self.action_skip_entry()
            return

        after_str = "(X,X)" if not after_width else f"({after_width}px, {after_height}px)"
        self.title = f"({before_width}px,{before_height}px) {title} {after_str}"
        yield Header()
        yield Rule(line_style="ascii")

        with Vertical(id="album_info"):
            for content in info_content:
                yield content

        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:

        disabled_action_list = ["command_palette"]
        match (self.report_dict[self.current_report_key]["status"]):
            case ReportStatus.DOWNLOAD_FAILURE:
                disabled_action_list += ["accept_new", "accept_closest", "accept_original",
                                         "search_again", "input_scratch", "pick_and_choose"]
            case ReportStatus.DOWNLOAD_SUCCESS:
                disabled_action_list += ["accept_new",
                                         "accept_closest", "retry_download", "pick_and_choose"]
            case ReportStatus.DOWNLOAD_NO_UPDATE:
                disabled_action_list += ["accept_new", "retry_download", "pick_and_choose"]
            case ReportStatus.SEARCH_FOUND_NOTHING:
                disabled_action_list += ["accept_new",
                                         "accept_closest", "retry_download", "pick_and_choose"]
            case ReportStatus.SINGLE:
                disabled_action_list += ["accept_new", "accept_closest", "retry_download"]
            case ReportStatus.ALBUM_FOUND:
                disabled_action_list += ["accept_closest", "retry_download"]

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

    def action_edit_metadata(self) -> None:

        def complete_edit_of_metadata(new_metadata: dict):
            current_report = self.report_dict[self.current_report_key]

            # FIXME: set track number to 1 for testing
            user_replace_filename(new_metadata["title"], new_metadata["artists"],
                                  current_report["before"]["path"],
                                  current_report["before"]["ext"], new_metadata["album"],
                                  new_metadata["duration"], 1, None, None)

            self.pop_and_increment_report_key()

        def pass_selection_menu_output(new_metadata: (dict, str)) -> None:
            self.push_screen(EditInputMenu(new_metadata[0], new_metadata[1]),
                             complete_edit_of_metadata)

        self.push_screen(EditSelectionMenu(self.report_dict[self.current_report_key]["before"],
                                           "before", self.right_info, self.right_type),
                         pass_selection_menu_output)

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

        user_replace_filename(after["title"],
                              after["artists"],
                              after["filepath"],
                              after["ext"],
                              after["album"],
                              after["duration"],
                              after["track_num"],
                              after["total_tracks"],
                              after["year"],
                              after["thumbnail_info"])

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
