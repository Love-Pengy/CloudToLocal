import json
import linecache
import os
import re
import shutil
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Chrome
from yt_dlp import YoutubeDL
import tracemalloc

from helpers import timer

def display_top(snapshot, key_type="lineno", limit=10):
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        )
    )
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print(
            "#%s: %s:%s: %.1f KiB"
            % (index, frame.filename, frame.lineno, stat.size / 1024)
        )
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print("    %s" % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))

class FilenameManager:

    def __init__(self):
        self.currentPlaylistName = None
        self.filenames = list()
        self.urls = list()

    def update(self, d):
        if d["info_dict"]["filename"] not in self.filenames:
            if self.currentPlaylistName is None:
                if d["status"] == "finished":
                    if d["info_dict"]["filename"] not in self.filenames:
                        self.filenames.append(d["info_dict"]["filename"])
                    if d["info_dict"]["webpage_url"] not in self.urls:
                        self.urls.append(d["info_dict"]["webpage_url"])
                    self.currentPlaylistName = d["info_dict"]["playlist_title"]

            elif self.currentPlaylistName == d["info_dict"]["playlist_title"]:
                if d["status"] == "finished":
                    if d["info_dict"]["filename"] not in self.filenames:
                        self.filenames.append(d["info_dict"]["filename"])
                    if d["info_dict"]["webpage_url"] not in self.urls:
                        self.urls.append(d["info_dict"]["webpage_url"])
            else:
                if d["status"] == "finished":
                    self.currentPlaylistName = d["info_dict"]["playlist_title"]
                    del(self.filenames)
                    del(self.urls)
                    self.filenames = list()
                    self.urls = list()
                    self.filenames.append(d["info_dict"]["filename"])
                    self.urls.append(d["info_dict"]["webpage_url"])


# invalid characters: +{;"\=?~()<>&*|$
def strParser(string):
    escapedString = re.escape(string)
    # escapedString  = re.sub(r"\+{;\"\=?~()<>&*|$", " ", string)
    return escapedString


@timer
def youtubeDownloader():
    playString = ""
    outputPath = ""

    try:
        with open("config.json", "r") as f:
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["songDir"]
            test = configDict["youtubePlaylists"]
            test = configDict["musiPlaylists"]
            del test
    except Exception as e:
        print("Json not configured for youtube correctly:")
        print(e)
        quit()

    outputPath = configDict["songDir"]
    youtubePlaylists = configDict["youtubePlaylists"]
    musiPlaylists = configDict["musiPlaylists"]

    if not os.path.exists(outputPath):
        os.makedirs(outputPath)

    tracemalloc.start()
    fNameManager = FilenameManager()
    logFile = open("log", "w")
    opts = {
        "format": "m4a/bestaudio/best",
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        "postprocessors": [
            {  # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
        "postprocessor_hooks": [fNameManager.update],
        "outtmpl_na_placeholder": "",
        "writethumbnail": "true",
        "outtmpl": f"{outputPath}/%(title)s_%(uploader)s.%(ext)s",
        # "cookiesfrombrowser": ["chromium"],
        "age_limit": 23,
        "ignoreerrors": "true",
        "restrictfilenames": "true",
        "no_overwrites": "true",
        # "quiet": "true",
        "no_warnings": "true",
        "progress": "true",
        "check_format": "true",
        # Trying not to surpass the thershold for maximum requests in an hour
        "sleep_interval_requests": 1,
        "sleep_interval": 5,
        "max_sleep_interval": 30,
        ####################################################################
    }

    # musi idea is to create a list of playlists that we can check if a file is in
    
    for i, playlist in enumerate(youtubePlaylists):
        ydl = YoutubeDL(opts)
        ydl.download(playlist)
        for i, name in enumerate(fNameManager.filenames):
            curDir = os.getcwd()
            fullDir = curDir + "/" + fNameManager.currentPlaylistName
            if not (os.path.exists(f"./{fNameManager.currentPlaylistName}")):
                os.makedirs(fullDir)
            shutil.copy(fNameManager.filenames[i], fullDir)

        if musiPlaylists is not None:
            print("Checking Musi Presence")
            for playlist in musiPlaylists:
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")

                options.page_load_stategy = "none"

                driver = Chrome(options=options)

                driver.implicitly_wait(5)

                driver.get(playlist)

                # this ensures that the webpage has time to generate everything with the js that is needed
                time.sleep(60)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                driver.quit()

                div = soup.find("div", id="playlist_content")
                div2 = soup.find("div", id="playlist_header")

                playlistName = div2.find("div", id="playlist_header_title").text
                trackList = div.find_all("a", href=True)

                checkList = list()

                for element in trackList:
                    logFile.write("ADDING " + element["href"] + "TO CHECKLIST\n")
                    if len(checkList) == 0:
                        checkList.insert(0, element["href"])
                        continue
                    checkList.append(element["href"])

                for link in checkList:
                    if not "www" in link:
                        link = link[:8] + "www." + link[8:]
                    logFile.write(f"{link}: {fNameManager.urls}\n\n")
                    if link in fNameManager.urls:
                        curDir = os.getcwd()
                        fullDir = curDir + "/" + playlistName
                        if not (os.path.exists(f"./{playlistName}")):
                            logFile.write(f"CREATING PLAYLIST DIR: {playlistName}\n")
                            os.makedirs(fullDir)
                        newPath = shutil.copy(
                            fNameManager.filenames[fNameManager.urls.index(link)],
                            fullDir,
                        )
                        logFile.write(
                            "Moved: "
                            + newPath
                            + " because of presence in musi playlist\n"
                        )
        snapshot = tracemalloc.take_snapshot()
        display_top(snapshot)
        tracemalloc.stop()
        del ydl
    logFile.close()
