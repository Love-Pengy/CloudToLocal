from yt_dlp import YoutubeDL
import json
import os
import shutil
import re 
from helpers import timer
from selenium import webdriver
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup 
import time
import platform

class FilenameManager:
    def __init__(self): 
        self.currentPlaylistName = None
        self.filenames = list()
        self.urls = list()

    def update(self, d): 
        if(self.currentPlaylistName is None): 
            if(d['status'] == 'finished'): 
                self.currentPlaylistName = d['info_dict']['playlist_title']
                self.filenames.append(d['filename'])
                self.urls.append(d['info_dict']['webpage_url'])

        elif(self.currentPlaylistName == d['info_dict']['playlist_title']): 
            if(d['status'] == 'finished'): 
                self.filenames.append(d['filename'])
                self.urls.append(d['info_dict']['webpage_url'])
                #print(dir(d))
                #print(d["info_dict"]["webpage_url"])
        else: 
            if(d['status'] == 'finished'): 
                self.currentPlaylistName = d['info_dict']['playlist_title']
                self.filenames = list()
                self.filenames.append(d['filename'])
                self.urls.append(d['info_dict']['webpage_url'])
                




# invalid characters: +{;"\=?~()<>&*|$
def strParser(string): 
    escapedString = re.escape(string)
    # escapedString  = re.sub(r"\+{;\"\=?~()<>&*|$", " ", string)
    return(escapedString)

@timer
def youtubeDownloader(): 
    playString = ''
    outputPath = ''

    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["songDir"]
            test = configDict["youtubePlaylists"]     
            test = configDict["musiPlaylists"]
            del(test)
    except Exception as e: 
        print("Json not configured for youtube correctly:")
        print(e)
        quit()


    outputPath = configDict["songDir"]
    youtubePlaylists = configDict["youtubePlaylists"]
    musiPlaylists = configDict["musiPlaylists"]
    sysPlatform = platform.system()
       



    if(not os.path.exists(outputPath)): 
        os.makedirs(outputPath)


            
    fNameManager = FilenameManager()
        

    opts = {
        'format': 'm4a/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }], 
        'progress_hooks': [fNameManager.update], 
        'outtmpl_na_placeholder': '', 
        'outtmpl': f'{outputPath}/%(title)s_%(uploader)s.%(ext)s', 
        'cookies-from-browser': 'chrome',  
        'ignoreerrors': 'true', 
        'restrictfilenames': 'true'
    }

    ydl = YoutubeDL(opts)
    
    #musi idea is to create a list of playlists that we can check if a file is in  
    
    for i, playlist in enumerate(youtubePlaylists): 
        ydl.download(playlist)
        for i,name in enumerate(fNameManager.filenames): 
            curDir = os.getcwd()
            fullDir = curDir + "/" + fNameManager.currentPlaylistName
            if(not (os.path.exists(f"./{fNameManager.currentPlaylistName}"))): 
                os.makedirs(fullDir)
            shutil.copy(fNameManager.filenames[i], fullDir)



    opts = {
        'format': 'm4a/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }], 
        'outtmpl_na_placeholder': '', 
        'outtmpl': f'{outputPath}/%(title)s_%(uploader)s.%(ext)s', 
        'cookies-from-browser': 'chrome',  
        'ignoreerrors': 'true', 
        'restrictfilenames': 'true'
    }
        
    if(musiPlaylists is not None): 
        for playlist in musiPlaylists: 
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")

            options.page_load_stategy = "none"

            driver = Chrome(options=options)

            driver.implicitly_wait(5)

            driver.get(playlist)

            # this ensures that the webpage has time to generate everything with the js that is needed
            time.sleep(60)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()


            div = soup.find('div', id="playlist_content")
            div2 = soup.find('div', id="playlist_header")

            playlistName = div2.find_all('div', id="playlist_header_title")
            trackList = div.find_all('a', href=True)

            checkList = list()

            for element in trackList: 
                checkList.append(element['href'])

            for link in checkList: 
                print(f"WE ARE CHECKING BETWEEN: {link=} and {fNameManager.urls}")
                if(link in fNameManager.urls): 
                    curDir = os.getcwd()
                    fullDir = curDir + "/" + playlistName
                    if(not (os.path.exists(f"./{playlistName}"))): 
                        os.makedirs(fullDir)
                    newPath = shutil.copy(fNameManager.filenames[fNameManager.urls.index(link)], fullDir)
                    print("Moved: ", newPath, " because of presence in musi playlist")

