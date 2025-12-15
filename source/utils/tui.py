import io
import json
import textwrap
import traceback
import urllib.request

from utils.printing import warning
from textual.content import Content
from playlists import PlaylistHandler
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual_image.widget import Image
from textual.css.query import NoMatches
from textual.app import App, ComposeResult
from metadata import user_replace_filename
from textual.validation import Function, Number
from report import ReportStatus, get_report_status_str
from textual.containers import Horizontal, Grid, Container
from textual.widgets import Footer, Header, Pretty, Rule, Static, Button, Label, Input, Checkbox

from utils.common import (
    list_to_comma_str,
    comma_str_to_list,
    get_img_size_url,
    url_from_youtube_id
)


def format_album_info(report, state) -> dict:
    """Format report into a dict able to be pretty printed as the album info

        Arguments:
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
            output["duration"] = closest["duration"]
            output["url"] = url_from_youtube_id(closest["videoId"])

            return ({"closest_match": output})
        case _:
            warning("Invalid State For Formatting Album Info")
            return (None)


class HelpMenu(ModalScreen):

    BINDINGS = [
        ("q", "quit_menu", "Quit Menu"),
    ]

    CSS_PATH = "../css/editInputHelpMenu.tcss"

    def compose(self) -> ComposeResult:
        yield Static(
            textwrap.dedent("""
                This Is The Menu That You Will Use To Edit Metadata. Just Input Your Data Into The
                Text Boxes And Then Check Which Playlists It Should Go Into. Once Done Hit The All
                Done! Button. Below Is A Specification List For The Metadata Fields:

                Title: Title Of Song
                Artists: Comma Delimited List Of Artists
                Duration: Duration In Seconds
                Album Date: Date Of Album Release. Can Be In MMDDYYYY | YYYYMMDD | DDMMYYYY | YYYY
                Album Length: Amount Of Tracks In Album
                Track Number: Number Of Current Track
                Thumbnail Link: Link Of Thumbnail


                Press Q To Exit This Help Menu
                """), id="EditHelpStatic")

    def action_quit_menu(self):
        self.dismiss()


class EditInputMenu(ModalScreen[dict]):

    CSS_PATH = "../css/editInput.tcss"

    BINDINGS = [
        ("ctrl+h", "help_menu", "Help Menu"),
    ]

    def __init__(self, metadata: dict, metadata_type: str):

        self.metadata = metadata
        self.metadata_type = metadata_type
        self.output_metadata = self.metadata
        self.default_validator = [Function(self.is_empty, "Is Empty")]
        self.track_num_validator = self.default_validator + [Function(self.is_valid_track,
                                                                      "Is Invalid")]
        self.album_len_validator = self.default_validator + [Number(minimum=1)]
        self.image_validator = self.default_validator + [Function(self.is_valid_image,
                                                                  "Invalid URL")]

        self.yield_table = {"before": self.yield_before, "after": self.yield_after,
                            "closest": self.yield_closest}

        super().__init__()

    def action_help_menu(self):
        self.app.push_screen(HelpMenu(), None)

    def yield_before(self, metadata):

        yield Label("Title", classes="EditPageLabel")
        yield Input(placeholder="title", value=metadata["title"], type="text", id="title",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Artists", classes="EditPageLabel")
        yield Input(placeholder="artists", value=metadata["uploader"],
                    type="text", id="artists", validators=self.default_validator,
                    classes="EditPageInput")
        yield Label("Duration", classes="EditPageLabel")
        yield Input(placeholder="duration", value=str(metadata["duration"]), type="integer",
                    id="duration", validators=self.default_validator, classes="EditPageInput")

        yield Label("Album Date", classes="EditPageLabel")
        yield Input(placeholder="Album Date", type="text", id="album_date",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Album", classes="EditPageLabel")
        yield Input(placeholder="album", type="text", id="album",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Album Length", classes="EditPageLabel")
        yield Input(placeholder="Album Length", type="integer", id="album_len",
                    validators=self.album_len_validator, classes="EditPageInput")
        yield Label("Track Number", classes="EditPageLabel")
        yield Input(placeholder="Track Number", type="integer", id="track_num",
                    validators=self.track_num_validator, classes="EditPageInput")
        yield Label("Thumbnail Link", classes="EditPageLabel")
        yield Input(placeholder="Thumbnail Link", value=metadata["thumbnail_url"], type="text",
                    id="thumb_link", validators=self.image_validator, classes="EditPageInput")
        yield self.render_image(metadata["thumbnail_url"])

    def yield_after(self, metadata):
        yield Label("Title", classes="EditPageLabel")
        yield Input(placeholder="title", value=metadata["title"], type="text", id="title",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Artists", classes="EditPageLabel")
        yield Input(placeholder="artists", value=list_to_comma_str(metadata["artists"]),
                    type="text", id="artists", validators=self.default_validator,
                    classes="EditPageInput")
        yield Label("Duration", classes="EditPageLabel")
        yield Input(placeholder="duration", value=str(metadata["duration"]), type="integer",
                    id="duration", validators=self.default_validator, classes="EditPageInput")
        yield Label("Album Date", classes="EditPageLabel")
        yield Input(placeholder="Album Date", type="text", id="album_date",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Album", classes="EditPageLabel")
        yield Input(placeholder="album", value=metadata["album"], type="text", id="album",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Album Length", classes="EditPageLabel")
        yield Input(placeholder="Album Length", type="integer",
                    value=str(metadata["total_tracks"]), id="album_len",
                    validators=self.album_len_validator, classes="EditPageInput")
        yield Label("Track Number", classes="EditPageLabel")
        yield Input(placeholder="Track Number", value=str(metadata["track_num"]),
                    type="integer", id="track_num", validators=self.track_num_validator,
                    classes="EditPageInput")
        yield Label("Thumbnail Link", classes="EditPageLabel")
        yield Input(placeholder="Thumbnail Link", value=metadata["thumbnail_info"]["url"],
                    type="text", id="thumb_link", validators=self.image_validator,
                    classes="EditPageInput")
        yield self.render_image(metadata["thumbnail_info"]["url"])

    def yield_closest(self, metadata):
        yield Label("Title", classes="EditPageLabel")
        yield Input(placeholder="title", value=metadata["title"], type="text", id="title",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Artists", classes="EditPageLabel")
        yield Input(placeholder="artists", value=list_to_comma_str(metadata["artists"]),
                    type="text", id="artists", validators=self.default_validator,
                    classes="EditPageInput")
        yield Label("Duration", classes="EditPageLabel")
        yield Input(placeholder="duration", value=str(metadata["duration_seconds"]),
                    type="integer", id="duration", validators=self.default_validator,
                    classes="EditPageInput")
        yield Label("Album Date", classes="EditPageLabel")
        yield Input(placeholder="Album Date", type="text", id="album_date",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Album", classes="EditPageLabel")
        yield Input(placeholder="album", value=metadata["album"], type="text", id="album",
                    validators=self.default_validator, classes="EditPageInput")
        yield Label("Album Length", classes="EditPageLabel")
        yield Input(placeholder="Album Length", type="integer",
                    value=str(metadata["album_len"]), id="album_len",
                    validators=self.album_len_validator, classes="EditPageInput")
        yield Label("Track Number", classes="EditPageLabel")
        yield Input(placeholder="Track Number", value=str(metadata["trackNumber"]),
                    type="integer", id="track_num", validators=self.track_num_validator,
                    classes="EditPageInput")
        yield Label("Thumbnail Link", classes="EditPageLabel")
        yield Input(placeholder="Thumbnail Link", value=metadata["thumbnail_info"]["url"],
                    type="text", id="thumb_link", validators=self.image_validator,
                    classes="EditPageInput")
        yield self.render_image(metadata["thumbnail_info"]["url"])

    def compose(self) -> ComposeResult:
        meta = self.metadata
        yield from self.yield_table[self.metadata_type](meta)

        # NOTE: Currently playlists list is held in before section of report ~ BEF
        before = self.app.report_dict[self.app.current_report_key]["before"]
        for playlist in self.app.playlist_handler.list_playlists_str():
            if (playlist in [play[1] for play in before["playlists"]]):
                yield Checkbox(playlist, True, name=playlist, classes="EditPageCheckbox")
            else:
                yield Checkbox(playlist, False, name=playlist, classes="EditPageCheckbox")

        yield Button("All Done!", variant="primary", id="completion_button")
        yield Static("", disabled=True, id="EditInputErr")
        yield Footer()

    def render_image(self, url: str):
        try:
            with urllib.request.urlopen(url) as response:
                request_response = response.read()
                image_data = io.BytesIO(request_response)
                return (Image(image_data, id="EditInputUrlPreview"))
        except urllib.error.URLError:
            return (None)

    def obtain_image(self, url: str):

        try:
            with urllib.request.urlopen(url) as response:
                request_response = response.read()
                image_data = io.BytesIO(request_response)
                return (image_data)
        except urllib.error.URLError:
            return (None)

    def is_empty(self, value) -> bool:
        if (value):
            return (True)
        else:
            return (False)

    def is_valid_image(self, image: str) -> bool:

        try:
            with urllib.request.urlopen(image) as response:
                if response.status == 200:
                    type = response.headers.get("Content-Type")
                    if type and type.startswith("image"):
                        return (True)
        except (urllib.error.URLError, ValueError):
            return (False)

    def is_valid_track(self, value) -> bool:
        try:
            album_len = self.query_one("#album_len", Input)

            if (album_len and value and
                    (int(value) > 0) and
                    (int(album_len.value) >= int(value))):
                return (True)

        except ValueError:
            return (False)
        except NoMatches:
            # NOTE: Ordering matters here. Album length is loaded after track number therefore it
            #       doesn't exist the first time around. ~ BEF
            return (True)

    def validate_all(self):
        for widget in self.children:
            if hasattr(widget, "validate") and callable(widget.validate):
                widget.validate(widget.value)

    def check_input_validity(self) -> bool:

        # NOTE: Even though not needed we validate all to update borders ~ BEF
        self.validate_all()
        err_static = self.query_one("#EditInputErr", Static)
        input_widgets = [widget for widget in self.children if isinstance(widget, Input)]
        for widget in input_widgets:
            if (not widget.is_valid):
                err_static.disabled = False
                for validator in widget.validators:
                    if (validator.failure_description):
                        err_static.update(Content(f'"{widget.id}" {
                            validator.failure_description}'))
                return False
        return True

    def on_input_blurred(self, blurred_widget):

        if ((blurred_widget.input.id == "thumb_link") and
                (blurred_widget.input.is_valid)):
            dimensions = get_img_size_url(blurred_widget.value)
            self.output_metadata["thumbnail_info"] = {
                "url": blurred_widget.value,
                "width": dimensions[0],
                "height": dimensions[1]
            }

            self.query_one("#EditInputUrlPreview", Image).image = self.obtain_image(
                blurred_widget.value)

        elif (not (blurred_widget.input.id == "artists")):
            if (not blurred_widget.input.type == "integer"):
                self.output_metadata[blurred_widget.input.id] = blurred_widget.value
            else:
                self.output_metadata[blurred_widget.input.id] = (
                    None if not blurred_widget.value else int(blurred_widget.value)
                )
        else:
            self.output_metadata[blurred_widget.input.id] = comma_str_to_list(
                blurred_widget.value)

    def on_checkbox_changed(self, changed_checkbox):

        playlist = self.app.playlist_handler.get_playlist_tuple(changed_checkbox.checkbox.name)

        if "playlists" not in self.output_metadata:
            self.output_metadata["playlists"] = []

        if (changed_checkbox.value and
                (not (playlist in self.output_metadata["playlists"]))):
            self.output_metadata["playlists"].append(playlist)
        elif ((not changed_checkbox.value) and (playlist in self.output_metadata["playlists"])):
            self.output_metadata["playlists"].remove(playlist)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if (not self.check_input_validity()):
            return
        self.dismiss(self.output_metadata)


class EditSelectionMenu(ModalScreen):

    CSS_PATH = "../css/editSelection.tcss"

    BINDINGS = [
        ("q", "quit_menu", "Quit Menu"),
        ("escape", "quit_menu", "Quit Menu"),
    ]

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
            Label("Which Metadata Would You Like To Edit?", id="EditSelectionLabel"),
            Button("Original", variant="primary", id="EditSelectionButtonOrig"),
            Button("After/Closest", variant="success", id="EditSelectionButtonNew"),
            id="EditSelectionGrid"
        )

    def action_quit_menu(self):
        self.dismiss(None)

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

    BINDINGS = [
        ("n", "accept_new", "Accept New Metadata"),
        ("c", "accept_closest", "Accept Closest Match"),
        ("o", "accept_original", "Accept Original"),
        ("e", "edit_metadata", "Manually Edit Metadata"),
        # ("s", "search_again", "Search Again"),
        # ("r", "replace_entry", "Retry Download Process With New URL"),
        ("ctrl+s", "skip_entry", "Skip Entry"),
        # ("ctrl+r", "retry_download", "Retry Download Process"),
        # ("p", "pick_and_choose", "Pick Elements To Pick From Both Before And After")
    ]
    CSS_PATH = "../css/main.tcss"

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
                    after_width = current_report["after"]["closest_match"]["thumbnail_info"][
                        "width"]
                    after_height = current_report["after"]["closest_match"]["thumbnail_info"][
                        "height"]
                    after_source = "closest"
                    self.right_info = current_report["after"]["closest_match"]
                    self.right_type = "closest"

                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Horizontal(
                        Pretty(format_album_info(
                            current_report["before"], "before"), id="before_info"),
                        Container(id="spacer"),
                        Pretty(format_album_info(
                            current_report["after"], after_source), id="after_info"),
                        id="album_content"
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
        yield Rule(line_style="ascii", id="divider")

        with Container(id="album_info"):
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
        temp_metadata = before

        if ("after" in current_report):
            temp_metadata["path"] = current_report["after"]["filepath"]

        def complete_edit_of_metadata(new_metadata: dict):

            new_fname = user_replace_filename(new_metadata["title"],
                                              new_metadata["artists"],
                                              new_metadata["path"],
                                              new_metadata["ext"],
                                              new_metadata["album"],
                                              new_metadata["duration"],
                                              new_metadata["track_num"],
                                              new_metadata["album_len"],
                                              new_metadata["album_date"],
                                              new_metadata["thumbnail_info"]
                                              )

            self.playlist_handler.write_to_playlists(new_metadata["playlists"], None, new_fname,
                                                     self.output_filepath, new_metadata["title"],
                                                     new_metadata["artists"],
                                                     new_metadata["duration"])

            self.pop_and_increment_report_key()

        self.push_screen(EditInputMenu(temp_metadata, "before"), complete_edit_of_metadata)

    def action_edit_metadata(self) -> None:

        def complete_edit_of_metadata(new_metadata: dict):
            current_report = self.report_dict[self.current_report_key]

            user_replace_filename(new_metadata["title"], new_metadata["artists"],
                                  current_report["before"]["path"],
                                  current_report["before"]["ext"], new_metadata["album"],
                                  new_metadata["duration"], new_metadata["track_num"],
                                  new_metadata["album_len"], new_metadata["album_date"],
                                  new_metadata["thumbnail_info"])

            self.pop_and_increment_report_key()

        def pass_selection_menu_output(new_metadata: (dict, str)) -> None:
            if (new_metadata):
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
