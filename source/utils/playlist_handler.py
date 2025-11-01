import os
import globals
from time import sleep
from pprint import pprint
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
from selenium import webdriver
from utils.printing import info, warning


class PlaylistHandler:

    def __init__(self,  retries, urls=None, info_ret=None, request_delay=None):
        self.playlists = {}
        self.urls_populated = False
        self.request_delay = request_delay

        if (urls):
            self.add_urls(urls, retries, info_ret)

    def add_urls(self, urls, retry_cnt, info_ret=None):
        """ Creates A Dictionary Where The Keys Are Tuples
            (playlist url, playlist name) and the values are lists of song urls
        """

        # Musi
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)
        for index, url in enumerate(urls):
            if (url.startswith("https://feelthemusic.com/")):
                driver.get(url)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                driver.quit()

                url_div = soup.find("div", id="playlist_content")
                name_div = soup.find("div", id="playlist_header")

                for retry in range(0, retry_cnt-1):
                    playlist_name = name_div.find("div",
                                                  id="playlist_header_title").text
                    if (not (playlist_name == '')):
                        break
                    sleep(retry_cnt*10)
                    info(f"Failed to obtain playlist info retrying "
                         f"({retry}): {url}")
                else:
                    warning(f"FAILED TO FIND PLAYLIST {url}")
                    continue

                # NOTE: this should probably construct info for the return
                self.playlists[(url, playlist_name)] = [a['href']
                                                        for a in url_div.find_all("a", href=True)]

            # Soundcloud Long Link
            elif (url.startswith("https://soundcloud.com/")):
                ydl_opts_extract = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': globals.QUIET,
                    'verbose': globals.VERBOSE
                }

                if (self.request_delay):
                    ydl_opts_extract["sleep_interval_requests"] = self.request_delay

                with YoutubeDL(ydl_opts_extract) as ydl:
                    extraction_info = ydl.extract_info(url, download=False)
                    if (info_ret is not None):
                        info_ret.append(extraction_info)
                    if ("entries" in extraction_info):
                        self.playlists[(url, extraction_info["album"])] = [
                            entry["url"] for entry in
                            extraction_info["entries"]]
                    else:
                        warning(f"{url} Does Not Seem To Be A "
                                f"Playlist")

            elif (url.startswith("https://on.soundcloud.com/")):
                redirect = YoutubeDL({'extract_flat': True,
                                     'skip_download': True,
                                      'quiet': globals.QUIET,
                                      'verbose': globals.VERBOSE}
                                     ).extract_info(url, download=False)
                ydl_opts_extract = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': globals.QUIET,
                    'verbose': globals.VERBOSE
                }
                if (self.request_delay):
                    ydl_opts_extract["sleep_interval_requests"] = self.request_delay

                with YoutubeDL(ydl_opts_extract) as ydl:
                    extraction_info = ydl.extract_info(
                        redirect["url"], download=False)
                    if (info_ret is not None):
                        info_ret.append(extraction_info)
                    if ("entries" in extraction_info):
                        self.playlists[(url, extraction_info["album"])] = [
                            entry["url"] for entry
                            in extraction_info["entries"]]
                        self.playlists[(url, extraction_info["album"])].append(
                            redirect["original_url"])
                    else:
                        warning(f"{url} Does Not Seem To Be A "
                                f"Playlist")

            # Youtube
            elif (url.startswith("https://youtube.com/")):
                ydl_opts_extract = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': globals.QUIET,
                    'verbose': globals.VERBOSE
                }
                if (self.request_delay):
                    ydl_opts_extract["sleep_interval_requests"] = self.request_delay

                with YoutubeDL(ydl_opts_extract) as ydl:
                    extraction_info = ydl.extract_info(url, download=False)
                    if (info_ret is not None):
                        info_ret.append(extraction_info)
                    if ("entries" in extraction_info):
                        self.playlists[(url, extraction_info["title"])] = [
                            entry["url"] for entry in
                            extraction_info["entries"]]
                    else:
                        warning(f"{url} Does Not Seem To Be A "
                                f"Playlist")
            else:
                warning(f"Unexpected Domain: {url}")
        self.urls_populated = True

    def check_playlists(self, url):
        """ Returns a list of playlists that 'url' is in in
            (playlist url, playlist name) form"""

        if (not self.urls_populated):
            warning("Urls Have Not Yet Been Populated")
        return (
            [spec for spec in self.playlists if url in self.playlists[spec]])

    def list_playlists_str(self):
        """ Returns List Of Playlist Strings With No Dups """
        output = []
        for spec in self.playlists:
            if spec[1] not in output:
                output.append(spec[1])
        return (output)


    def get_playlist_tuple(self, input):
        """ Get Playlist Tuple From String Name """

        out_list = [playlist for playlist in self.playlists if playlist[1] == input]
        if (out_list is None):
            return (None)

        return (out_list[0])

    def write_to_playlists(self, playlists: dict, song_url: str, filepath: str, output_dir: str,
                           title: str, artist: str, duration: int):
        """ Write song to all playlist files it belongs to

            Args:
                playlists:      Dictionary of playlists containing url for playlist and name of
                                    playlist. Specify this if you want to manually give playlists
                song_url:       Url of song. Specify this if you want to search through matching
                                    playlists using class's context
                filepath:       Path to song
                output_dir:     Path to folder in which playlists will exist
                title:          Song Title
                album:          Album name
                duration:       Duration of song in seconds
        """
        if (filepath.startswith("#")):
            sanitized_path = "./" + os.path.basename(filepath)
        else:
            sanitized_path = os.path.basename(filepath)

        if (song_url):
            for playlist_spec in self.check_playlists(song_url):
                if (not os.path.exists(f"{output_dir}{playlist_spec[1]}.m3u")):
                    with open(f"{output_dir}{playlist_spec[1]}.m3u", "w") as f:
                        f.write("#EXTM3U\n")
                        f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                        f.write(sanitized_path + "\n")
                else:
                    with open(f"{output_dir}{playlist_spec[1]}.m3u", "a") as f:
                        f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                        f.write(sanitized_path + "\n")
        else:
            for playlist_spec in playlists:
                if (not os.path.exists(f"{output_dir}{playlist_spec[1]}.m3u")):
                    with open(f"{output_dir}{playlist_spec[1]}.m3u", "w") as f:
                        f.write("#EXTM3U\n")
                        f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                        f.write(sanitized_path + "\n")
                else:
                    with open(f"{output_dir}{playlist_spec[1]}.m3u", "a") as f:
                        f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                        f.write(sanitized_path + "\n")
