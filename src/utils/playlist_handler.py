import os
from time import sleep
from pprint import pprint
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
from selenium import webdriver
import utils.printing as printing


class PlaylistHandler:

    def __init__(self, urls, retries):
        self.playlists = {}
        self.add_urls(urls, retries)

    def add_urls(self, urls, retry_cnt):
        """ Creates A Dictionary Where The Keys Are Tuples
            (playlist url, playlist name) and the values are lists of song urls
        """

        # Musi
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)
        for url in urls:
            if (url.startswith("https://feethemusic.com/")):
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
                    printing.pinfo(f"Failed to obtain playlist info retrying "
                                   f"({retry}): {url}")
                else:
                    printing.pwarning(f"FAILED TO FIND PLAYLIST {url}")
                    continue

                self.playlists[(url, playlist_name)] = [a['href']
                                                        for a in url_div.find_all("a", href=True)]

            # Soundcloud
            elif (url.startswith("https://soundcloud.com/")):
                ydl_opts_extract = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': (not printing.VERBOSE)
                }
                with YoutubeDL(ydl_opts_extract) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if ("entries" in info):
                        self.playlists[(url, info["album"])] = [
                            entry["url"] for entry in info["entries"]]
                    else:
                        printing.pwarning(f"{url} Does Not Seem To Be A "
                                          f"Playlist")

            # Youtube
            elif (url.startswith("https://youtube.com/")):
                ydl_opts_extract = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': (not printing.VERBOSE)
                }
                with YoutubeDL(ydl_opts_extract) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if ("entries" in info):
                        self.playlists[(url, info["title"])] = [
                            entry["url"] for entry in info["entries"]]
                    else:
                        printing.pwarning(f"{url} Does Not Seem To Be A "
                                          f"Playlist")
            else:
                printing.pwarning(f"Unexpected Domain: {url}")

    def check_playlists(self, url):
        """ Returns a list of playlists that 'url' is in in
            (playlist url, playlist name) form"""

        return (
            [spec for spec in self.playlists if url in self.playlists[spec]])

    def write_to_playlists(self, url, duration, artist, title, track_num, album,
                           filepath, output_dir):
        """ Write song to all playlist files it belongs to

            Args:
                url (str): playlist url
                duration (int): duration of song in seconds
                artist (str): artist of song
                title (str): title of song
                track_num (int): number of track within album
                album (str): name of album
                filepath (str): path to song
        """
        for playlist_spec in self.check_playlists(url):

            if (not os.path.exists(f"{output_dir}{playlist_spec[1]}.playlist")):
                with open(f"{output_dir}{playlist_spec[1]}.playlist", "w") as f:
                    f.write("#EXTM3U\n")
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    f.write(f"{artist}_{album}_{track_num}:02d_{title}\n")
            else:
                with open(f"{output_dir}{playlist_spec[1]}.playlist", "a") as f:
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    f.write(f"{artist}_{album}_{track_num:02d}_{title}\n")
