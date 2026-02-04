###
#  @file    tui.py
#  @author  Brandon Elias Frazier
#  @date    Dec 18, 2025
#
#  @brief   TUI For Ctldl
#
#  @copyright (c) 2025 Brandon Elias Frazier
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#
#
#################################################################################

import io
import json
import time
import textwrap
import urllib.request
from datetime import datetime
from dataclasses import asdict
from pathlib import PurePath, Path

import globals
import downloader
from textual import work
from utils.ctl_logging import tui_log
from playlists import PlaylistHandler
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual_image.widget import Image
from textual.css.query import NoMatches
from textual.app import App, ComposeResult
from textual.worker import get_current_worker
from textual.validation import Function, Number
from report import ReportStatus, get_report_status_str
from music_brainz import musicbrainz_construct_user_agent
from textual.containers import Horizontal, Grid, Container, VerticalScroll
from metadata import replace_metadata, MetadataCtx, LyricHandler, fill_report_metadata

from utils.common import (
    get_img_size_url,
    list_to_comma_str,
    comma_str_to_list,
)

from textual.widgets import (
    Footer, Header, Pretty,
    Rule, Static, Button,
    Label, Input, Checkbox,
    Select, Collapsible
)

MAX_THUMBNAIL_RETRIES = 5
DEFAULT_IMAGE_SIZE = (1200, 1200)
THUMBNAIL_SIZE_PRIO_LIST = ["1200", "500", "250"]
FAILURE_IMAGE_PATH = Path(globals.PROJECT_ROOT_DIR, "source/assets/failure_white.png")


def initialize_image(in_id: str) -> Image:
    output_image = Image(id=in_id)
    output_image.loading = True
    output_image._image_width, output_image._image_height = DEFAULT_IMAGE_SIZE
    return (output_image)


@work(thread=True)
async def obtain_image_from_url(screen, url: str, in_image_id: str):
    tui_log(f"WORKER STARTED WITH ID: {in_image_id}")
    worker = get_current_worker()

    if (not url):
        screen.app.call_from_thread(tui_log, "Url not provided")
        if (not worker.is_cancelled):
            image_widget = screen.query_one(f"#{in_image_id}", Image)
            image_widget.loading = False
            image_widget.image = FAILURE_IMAGE_PATH
        return

    for i in range(0, MAX_THUMBNAIL_RETRIES):
        if (worker.is_cancelled):
            return

        retrieved_bytes = None
        try:
            with urllib.request.urlopen(url) as response:
                request_response = response.read()
                retrieved_bytes = io.BytesIO(request_response)
                break
        except Exception:
            screen.app.call_from_thread(tui_log, f"{i}: Image obtain failed...retrying")
            delay = time.time() + i**2
            while ((time.time() < delay) and (not worker.is_cancelled)):
                pass

            continue

    if (not worker.is_cancelled):
        image_widget = screen.query_one(f"#{in_image_id}", Image)
        image_widget.loading = False
        image_widget.image = retrieved_bytes or FAILURE_IMAGE_PATH


def input_widget_change_first_element(widget, value):
    if (not widget or not value):
        return
    split_list = value.split(',')
    if (1 == len(split_list)):
        widget.value = value + ', '
    else:
        split_list[0] = value
        output = ', '.join(split_list)
        widget.value = output


class NewUrlInputMenu(ModalScreen):

    BINDINGS = [("q", "quit_menu", "Quit Menu")]

    CSS_PATH = "css/urlinputmenu.tcss"

    def __init__(self):
        self.url_validator = [Function(self.validate_url, "Is not a valid Url")]

    def check_input_validity(self) -> bool:

        input_widget = self.query_one("#NewUrlInput", Input)
        input_widget.validate(input_widget.value)
        self.validate_all(input_widget)
        if (not input_widget.is_valid):
            for validator in input_widget.validators:
                if (validator.failure_description):
                    self.notify(f'"{input_widget.id}" field {validator.failure_description}',
                                severity="error")
            return False
        return True

    def compose(self) -> ComposeResult:
        yield Static("Input Url You would like to download.", id="NewUrlInputStatic")
        yield Input(id="NewUrlInput", validators=self.url_validator)
        yield Button("All Done!", variant="primary", id="completion_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if (not self.check_input_validity()):
            return
        tui_log("Exiting input menu")
        url = self.query_one("#NewUrlInput", Input).value
        self.dismiss(url)

    def validate_url(self, url: str):
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return True
        except Exception:
            return False
        return False

    def action_quit_menu(self):
        tui_log("Exiting url input menu")
        self.dismiss()


class HelpMenu(ModalScreen):

    BINDINGS = [("q", "quit_menu", "Quit Menu")]

    CSS_PATH = "css/editInputHelpMenu.tcss"

    def compose(self) -> ComposeResult:
        yield Static(
            textwrap.dedent("""
                This Is The Menu That You Will Use To Edit Metadata. Just Input Your Data Into The
                Text Boxes And Then Check Which Playlists It Should Go Into. Once Done Hit The All
                Done! Button. Below Is A Specification List For The Metadata Fields:

                Title: Title Of Song
                Artists: Comma Delimited List Of Artists
                Duration: Duration In Seconds
                Album Date: Date Of Album Release. Must be in the form YYYY-MM-DD
                Album Length: Amount Of Tracks In Album
                Track Number: Number Of Current Track
                Thumbnail Link: Link Of Thumbnail


                Press q To Exit This Help Menu
                """), id="EditHelpStatic")

    def action_quit_menu(self):
        tui_log("Quit menu dismissing")
        self.dismiss()


class EditInputMenu(ModalScreen[MetadataCtx]):

    MAX_GENRE_AMT = 3
    DATE_FORMAT = "%Y-%m-%d"
    CSS_PATH = "css/editInput.tcss"
    BINDINGS = [("ctrl+h", "help_menu", "Help Menu")]
    GENRES = json.load(open(globals.GENRE_PATH, 'r'))

    def __init__(self, metadata: dict | MetadataCtx, type: str, outdir: str):

        # Override for if metadata is being passed in again for a retry
        if type == "meta":
            self.metadata = asdict(metadata)
            self.output = metadata
            self.output.path = self.metadata["path"]
        else:
            self.metadata = metadata[type]
            self.output = MetadataCtx()
            self.output.path = PurePath(outdir,
                                        self.app.report_dict[
                                            self.app.current_report_key]["pre"]["short_path"])

        self.default_validator = [Function(self.validator_is_empty, "Is Empty")]
        self.album_len_validator = self.default_validator + [Number(minimum=1)]
        self.image_validator = self.default_validator + [Function(self.validator_is_valid_image,
                                                                  "Invalid URL")]
        self.date_validator = self.default_validator + [Function(self.validator_is_valid_date,
                                                                 "Invalid Date Format")]
        self.track_num_validator = self.default_validator + [
            Function(self.validator_is_valid_track, "Is Invalid")
        ]

        super().__init__()
        tui_log(f"Edit input menu metadata: {self.metadata}")

    @work
    async def action_help_menu(self):
        tui_log("Help menu called")
        await self.app.push_screen(HelpMenu(), wait_for_dismiss=True)

    def convert_for_input(self, value):
        if (value):
            return str(value)
        else:
            return None

    def compose(self) -> ComposeResult:

        tui_log("Compose Started")

        pre = self.app.report_dict[self.app.current_report_key]["pre"]

        with VerticalScroll(id="InputMenuScrollContainer", can_focus=True):
            yield Label("Title", classes="EditPageLabel")
            yield Input(placeholder="Name of Song", value=self.metadata["title"],
                        type="text", id="title", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Artist", classes="EditPageLabel")
            yield Input(placeholder="Main Artist", value=self.metadata.get("artist", None),
                        type="text", id="artist", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Artists", classes="EditPageLabel")
            yield Input(placeholder="Comma Delimited List Of All Artists Involved **Including** "
                        "The Main Artist",
                        value=list_to_comma_str(self.metadata.get("artists", None)),
                        type="text", id="artists", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Duration", classes="EditPageLabel")
            yield Input(placeholder="Duration Of Song In Seconds",
                        value=self.convert_for_input(pre.get("duration", None)), type="integer",
                        id="duration", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Album Date", classes="EditPageLabel")
            yield Input(placeholder="YYYY-MM-DD", type="text", id="album_date",
                        validators=self.date_validator, classes="EditPageInput")

            yield Label("Album", classes="EditPageLabel")
            yield Input(placeholder="Album Name Or Song Name If Single",
                        value=self.metadata.get("album", None), type="text", id="album",
                        validators=self.default_validator, classes="EditPageInput")

            yield Label("Album Length", classes="EditPageLabel")
            yield Input(placeholder="Amount Of Tracks In Album", type="integer",
                        value=self.convert_for_input(self.metadata.get("total_tracks", None)),
                        id="album_len", validators=self.album_len_validator,
                        classes="EditPageInput")

            yield Label("Track Number", classes="EditPageLabel")
            yield Input(placeholder="This Song's Track Number Within Album",
                        value=self.convert_for_input(self.metadata.get("track_num", None)),
                        type="integer", id="track_num", validators=self.track_num_validator,
                        classes="EditPageInput")

            yield Label("Genres", classes="EditPageLabel")
            genre_list = self.metadata.get("genres", [])
            for i in range(0, len(genre_list)):
                if (genre_list[i]):
                    select_value = genre_list[i]
                else:
                    select_value = Select.BLANK

                yield Select(((line, line) for line in self.GENRES), value=select_value,
                             classes="EditPageListItem", prompt=f"Genre {i+1}")

            remainder = self.MAX_GENRE_AMT - len(genre_list)
            for i in range(0, remainder):
                yield Select(((line, line) for line in self.GENRES), value=Select.BLANK,
                             classes="EditPageListItem", prompt=f"Genre {i+1}")

            yield Label("Thumbnail Link", classes="EditPageLabel")
            yield Input(placeholder="Link To Thumbnail",
                        value=self.metadata.get("thumbnail_url", None), type="text",
                        id="thumb_link", validators=self.image_validator, classes="EditPageInput")

            preview_image = initialize_image("EditInputUrlPreview")
            yield preview_image

            for playlist in self.app.playlist_handler.list_playlists_str():
                if (playlist in [play[1] for play in pre["playlists"]]):
                    yield Checkbox(playlist, True, name=playlist, classes="EditPageCheckbox")
                else:
                    yield Checkbox(playlist, False, name=playlist, classes="EditPageCheckbox")

            with Collapsible(title="Lyrics", collapsed=True, id="lyrics_collapsible"):
                yield Static(self.metadata.get("lyrics", None) or "")

        yield Button("All Done!", variant="primary", id="completion_button")
        yield Footer()
        obtain_image_from_url(self,
                              self.metadata.get("thumbnail_url", None),
                              "EditInputUrlPreview")
        tui_log("Compose completed")

    def validator_is_empty(self, value) -> bool:
        if (value):
            return (True)
        else:
            return (False)

    def validator_is_valid_image(self, image_url: str) -> bool:

        try:
            with urllib.request.urlopen(image_url) as response:
                if response.status == 200:
                    type = response.headers.get("Content-Type")
                    if type and type.startswith("image"):
                        return True
        except Exception:
            return False

    def validator_is_valid_track(self, value) -> bool:
        try:
            album_len = self.query_one("#album_len", Input)

            if (album_len and value and
                    (int(value) > 0) and
                    (int(album_len.value) >= int(value))):
                return True

        except ValueError:
            return False
        except NoMatches:
            # Ordering matters here. Album length is loaded after track number therefore it
            # doesn't exist the first time around. ~ BEF
            return True

    def validator_is_valid_date(self, value) -> bool:
        output = False
        try:
            output = bool(datetime.strptime(value, self.DATE_FORMAT))
        except ValueError:
            pass

        return output

    def validate_all(self, container):
        tui_log("Validating all children")
        for widget in container.children:
            if hasattr(widget, "validate") and callable(widget.validate):
                tui_log(widget.validate(widget.value))

    def check_input_validity(self) -> bool:

        # NOTE: Even though not needed we validate all to update borders ~ BEF
        container = self.query_one("#InputMenuScrollContainer", VerticalScroll)
        self.validate_all(container)
        input_widgets = [widget for widget in container.children if isinstance(widget, Input)]
        for widget in input_widgets:
            if (not widget.is_valid):
                for validator in widget.validators:
                    if (validator.failure_description):
                        self.notify(f'"{widget.id}" field {validator.failure_description}',
                                    severity="error")
                return False
        return True

    def on_select_changed(self, event: Select.Changed) -> None:
        for select in self.query("Select"):
            if (not (Select.BLANK == select.value)):
                self.output.genres.append(select.value)

    # Enforce Artist value is the beginning of Artists
    def on_input_changed(self, changed):
        if changed.input.id == "artist":

            artists = self.query_one("#artists", Input)
            if (artists.value == ""):
                artists.value = changed.value + ', '
            else:
                split_list = artists.value.split(',')
                if (not (split_list[0] == changed.input.value)):
                    if (1 == len(split_list)):
                        artists.value = changed.value + ', '
                    else:
                        split_list[0] = changed.input.value
                        split_list = map(str.lstrip, split_list)
                        output = ', '.join(split_list)
                        artists.value = output

        elif changed.input.id == "artists":
            artist = self.query_one("#artist", Input)
            split_list = changed.value.split(',')
            if (not split_list[0] == artist.value):
                split_list[0] = artist.value
                split_list = map(str.lstrip, split_list)
                output = ', '.join(split_list)
                changed.input.value = output
                if (changed.input.cursor_position < len(artist.value + ', ')):
                    changed.input.cursor_position = len(artist.value + ', ')

    def on_input_blurred(self, blurred_widget):

        if (blurred_widget.input.id == "thumb_link"):
            preview_image = self.query_one("#EditInputUrlPreview", Image)
            if (blurred_widget.input.is_valid):
                dimensions = get_img_size_url(blurred_widget.value)
                self.output.thumbnail_url = blurred_widget.value
                self.output.thumbnail_width = dimensions[0]
                self.output.thumbnail_height = dimensions[1]

                preview_image.loading = True
                obtain_image_from_url(self,
                                      blurred_widget.value,
                                      "EditInputUrlPreview")
            else:
                preview_image.image = FAILURE_IMAGE_PATH

        elif (not (blurred_widget.input.id == "artists")):
            if (not blurred_widget.input.type == "integer"):
                setattr(self.output, blurred_widget.input.id, blurred_widget.value)
            else:
                setattr(self.output, blurred_widget.input.id,
                        None if not blurred_widget.value else int(blurred_widget.value))
        else:
            setattr(self.output, blurred_widget.input.id, comma_str_to_list(blurred_widget.value))

    def on_checkbox_changed(self, changed_checkbox):

        playlist = self.app.playlist_handler.get_playlist_tuple(changed_checkbox.checkbox.name)

        if (changed_checkbox.value and
                (not (playlist in self.output.playlists))):
            tui_log(f"Adding playlist: {playlist}")
            self.output.playlists.append(playlist)
        elif ((not changed_checkbox.value) and (playlist in self.output.playlists)):
            tui_log(f"Removing playlist: {playlist}")
            self.output.playlists.remove(playlist)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if (not self.check_input_validity()):
            return
        tui_log("Exiting input menu")
        self.dismiss(self.output)

    def on_mount(self) -> None:
        container = self.query_one("#InputMenuScrollContainer", VerticalScroll)
        self.validate_all(container)


class EditSelectionMenu(ModalScreen):

    CSS_PATH = "css/editSelection.tcss"

    BINDINGS = [
        ("q", "quit_menu", "Quit Menu"),
        ("escape", "quit_menu", "Quit Menu"),
    ]

    def __init__(self):
        """ Initialize Edit Metadata Screen """
        self.meta_type_chosen = None
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Which Metadata Would You Like To Edit?", id="EditSelectionLabel"),
            Button("Pre", variant="primary", id="EditSelectionButtonPre"),
            Button("Post", variant="success", id="EditSelectionButtonPost"),
            id="EditSelectionGrid"
        )

    def action_quit_menu(self):
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed):
        if (event.button.id == "EditSelectionButtonPre"):
            self.meta_type_chosen = "pre"
        else:
            self.meta_type_chosen = "post"

        self.dismiss(self.meta_type_chosen)


class ctl_tui(App):

    REQUIRED_POST_SEARCH_KEYS = ["title", "artist", "artists", "track_num", "total_tracks",
                                 "release_date", "thumbnail_url", "thumbnail_width",
                                 "thumbnail_height"]
    BINDINGS = [
        ("n", "accept_new", "Accept New Metadata"),
        ("o", "accept_original", "Accept Original"),
        ("e", "edit_metadata", "Edit Metadata"),
        # ("r", "replace_entry", "Retry Download Process With New URL"),
        ("ctrl+s", "skip_entry", "Skip Entry"),
        ("ctrl+r", "retry_download", "Retry Download Process"),
    ]
    CSS_PATH = "css/main.tcss"

    # Refresh Footer/Bindings and recompose on change
    current_report_key = reactive(None, recompose=True, bindings=True)

    def __init__(self, arguments, **kwargs):
        super().__init__(**kwargs)

        self.theme = "textual-dark"
        self.outdir = arguments.host_outdir
        self.report_path = self.outdir+"ctl_report"

        self.playlists_info = []
        self.playlist_handler = PlaylistHandler(arguments.retry_amt,
                                                arguments.playlists,
                                                self.playlists_info,
                                                arguments.request_sleep)
        self.lyric_handler = LyricHandler(arguments.genius_api_key, verbosity=False)

        with open(self.report_path, "r") as fptr:
            self.report_dict = json.load(fptr)

        self.current_report_key_iter = iter(list(self.report_dict))
        self.current_report_key = next(self.current_report_key_iter)
        self.user_agent = musicbrainz_construct_user_agent(arguments.email)

        self.downloader = downloader.DownloadManager({
            "playlists_info": self.playlists_info,
            "output_dir": arguments.host_outdir,
            "download_sleep": arguments.download_sleep,
            "request_sleep": arguments.request_sleep,
            "retry_amt": arguments.retry_amt,
            "playlist_handler": self.playlist_handler,
        })

    def pop_and_increment_report_key(self):
        self.report_dict.pop(self.current_report_key)
        self.increment_report_key()

    def increment_report_key(self):
        try:
            # Cancel thumbnail workers
            self.workers.cancel_all()
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            tui_log("All songs in report exhausted")
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()

    def _get_current_report(self) -> dict:
        return (self.report_dict[self.current_report_key])

    def compose(self) -> ComposeResult:

        title = None
        pre_height = None
        post_width = None
        post_height = None
        current_report = self._get_current_report()

        if (ReportStatus.DOWNLOAD_FAILURE == current_report["status"]):
            title = "Download Failed"
            yield Horizontal(Image(FAILURE_IMAGE_PATH, id="full_img"), id="album_art")
            info_content = [
                Static(get_report_status_str(
                    current_report["status"]), id="status"),
            ]
        else:
            pre_width = current_report["pre"].get("thumbnail_width", None)
            pre_height = current_report["pre"].get("thumbnail_height", None)

            if (current_report["status"] in [ReportStatus.SINGLE, ReportStatus.ALBUM_FOUND]):

                pre_image = initialize_image("pre_image")
                post_image = initialize_image("post_image")

                yield Horizontal(pre_image, post_image, id="album_art")

                title = current_report["post"]["title"]
                post_width = current_report["post"]["thumbnail_width"]
                post_height = current_report["post"]["thumbnail_height"]

                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Horizontal(
                        Pretty(current_report["pre"], id="pre_info"),
                        Container(id="spacer"),
                        Pretty(current_report["post"], id="post_info"),
                        id="album_content"
                    )
                ]

                obtain_image_from_url(self, current_report["pre"]["thumbnail_url"], "pre_image")
                obtain_image_from_url(self, current_report["post"]["thumbnail_url"], "post_image")

            elif (current_report["status"] == ReportStatus.METADATA_NOT_FOUND):
                pre_image = initialize_image("full_img")
                yield Horizontal(pre_image, id="album_art")

                title = current_report["pre"]["title"]
                post_width = None
                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Pretty(current_report["pre"], id="pre_info")
                ]

                obtain_image_from_url(self, current_report["pre"]["thumbnail_url"], "full_img")
            else:
                # On DOWNLOAD_FAILURE && DOWNLOAD_SUCCESS setup user to just retry the download.
                #   Something went wrong or was cancelled midway if we are in these statuses.
                pre_width = None
                post_width = None
                title = current_report["pre"]["title"]

                pre_image = initialize_image("full_img")
                yield Horizontal(pre_image, id="album_art")

                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Pretty(current_report["pre"], id="pre_info")
                ]

                obtain_image_from_url(self, None, "full_img")

        post_dimension_str = "(X,X)" if not post_width else f"({post_width}px, {post_height}px)"
        pre_dimension_str = "(X,X)" if not pre_width else f"({pre_width}px, {pre_height}px)"
        self.title = f"{pre_dimension_str} {title} {post_dimension_str}"

        yield Header()
        yield Rule(line_style="ascii", id="divider")
        with Container(id="album_info"):
            for content in info_content:
                yield content
        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:

        disabled_action_list = ["command_palette"]
        match (self._get_current_report()["status"]):
            case ReportStatus.DOWNLOAD_FAILURE:
                disabled_action_list += ["accept_new", "accept_original", "edit_metadata"]
            case ReportStatus.DOWNLOAD_SUCCESS:
                disabled_action_list += ["accept_new"]
            case ReportStatus.METADATA_NOT_FOUND:
                disabled_action_list += ["accept_new"]
            case ReportStatus.SINGLE:
                disabled_action_list += []
            case ReportStatus.ALBUM_FOUND:
                disabled_action_list += []

        if (action in disabled_action_list):
            return False
        return True

    @work
    async def action_accept_original(self):

        ok = False
        meta = None
        while not ok:
            if not meta:
                meta = await self.push_screen_wait(EditInputMenu(self._get_current_report(),
                                                                 "pre", self.outdir))
            else:
                meta = await self.push_screen_wait(EditInputMenu(meta, "meta", self.outdir))

            ok = replace_metadata(meta, self.lyric_handler)

            if (ok):
                self.playlist_handler.write_to_playlists(meta, self.outdir, None)
                self.pop_and_increment_report_key()
            else:
                self.notify("Failed to replace metadata... Returning to metadata screen",
                            severity="error")

    @work
    async def action_edit_metadata(self) -> None:

        if ("post" not in self._get_current_report()):
            selected_type = "pre"
        else:
            selected_type = await self.push_screen(EditSelectionMenu(),
                                                   wait_for_dismiss=True)
        if (not selected_type):
            return

        meta = await self.push_screen_wait(EditInputMenu(self._get_current_report(),
                                                         selected_type, self.outdir))

        ok = False
        while not ok:

            ok = replace_metadata(meta, self.lyric_handler)

            if (ok):
                self.playlist_handler.write_to_playlists(meta, self.outdir, None)
                self.pop_and_increment_report_key()
            else:
                self.notify("Failed to replace metadata... Returning to metadata screen",
                            severity="error")
                meta = await self.push_screen_wait(EditInputMenu(meta, "meta", self.outdir))

    def action_replace_entry(self):

        url = await self.push_screen_wait(NewUrlInputMenu())
        if (not url):
            return

        self.notify("Attempting to download. This can take a while....")
        tui_log("Retrying download")
        download_info = self.downloader.download_from_url(url)

        if (not download_info):
            # failure case
            tui_log("Download info is None")
            pass

        tui_log("Filling metadata")
        download_meta = fill_report_metadata(self.user_agent,
                                             self.lyric_handler,
                                             download_info=download_info)
        tui_log("Done Filling metadata")

        user_input_meta = await self.push_screen_wait(EditInputMenu(download_meta,
                                                                    "meta", self.outdir))

        ok = False
        while not ok:

            ok = replace_metadata(user_input_meta, self.lyric_handler)

            if (ok):
                self.playlist_handler.write_to_playlists(user_input_meta, self.outdir, None)
                self.pop_and_increment_report_key()
            else:
                self.notify("Failed to replace metadata... Returning to metadata screen",
                            severity="error")
                user_input_meta = await self.push_screen_wait(EditInputMenu(user_input_meta,
                                                                            "meta",
                                                                            self.outdir))
        self.pop_and_increment_report_key()

    def action_skip_entry(self):
        self.increment_report_key()

    @work
    async def action_accept_new(self):
        """ Accept newly written metadata
            @note currently metadata is written when new album is found with confidence, so this
            doesn't need to do anything"""

        current_report = self._get_current_report()

        if (not all(
                ((key in current_report["post"]) and current_report["post"][key] is not None)
                for key in self.REQUIRED_POST_SEARCH_KEYS)):
            meta = await self.push_screen_wait(EditInputMenu(current_report, "post", self.outdir))

        else:

            pre = current_report["pre"]
            post = current_report["post"]
            meta = MetadataCtx(title=post["title"],
                               artist=post["artist"],
                               artists=post["artists"],
                               path=PurePath(self.outdir, pre["short_path"]),
                               album=post["album"],
                               duration=pre["duration"],
                               track_num=post["track_num"],
                               album_len=post["total_tracks"],
                               album_date=post["release_date"],
                               thumbnail_url=post["thumbnail_url"],
                               thumbnail_width=post["thumbnail_width"],
                               thumbnail_height=post["thumbnail_height"],
                               playlists=pre["playlists"]
                               )

        ok = False
        while not ok:
            ok = replace_metadata(meta, self.lyric_handler)

            self.playlist_handler.write_to_playlists(meta, self.outdir, None)

            if (ok):
                self.pop_and_increment_report_key()
            else:
                self.notify("Failed to replace metadata... Returning to metadata screen",
                            severity="error")
                await self.push_screen_wait(EditInputMenu(meta, "meta", self.outdir))

    @work
    async def action_retry_download(self):

        self.notify("Attempting to retry download. This can take a while....")
        tui_log("Retrying download")
        current_report = self._get_current_report()
        download_info = self.downloader.download_from_url(current_report["pre"].get("url", None))

        if (not download_info):
            # failure case
            tui_log("Download info is None")
            pass

        tui_log("Filling metadata")
        download_meta = fill_report_metadata(self.user_agent,
                                             self.lyric_handler,
                                             download_info=download_info)
        tui_log("Done Filling metadata")

        user_input_meta = await self.push_screen_wait(EditInputMenu(download_meta,
                                                                    "meta", self.outdir))

        ok = False
        while not ok:

            ok = replace_metadata(user_input_meta, self.lyric_handler)

            if (ok):
                self.playlist_handler.write_to_playlists(user_input_meta, self.outdir, None)
                self.pop_and_increment_report_key()
            else:
                self.notify("Failed to replace metadata... Returning to metadata screen",
                            severity="error")
                user_input_meta = await self.push_screen_wait(EditInputMenu(user_input_meta,
                                                                            "meta",
                                                                            self.outdir))
        self.pop_and_increment_report_key()

    def action_quit(self):
        tui_log("Exiting TUI")
        with open(self.report_path, "w") as f:
            json.dump(self.report_dict, f, indent=2)
        self.exit()
