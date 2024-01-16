import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
import os 
import shutil
import json




def musiPlaylistCreator(): 
    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["songDir"]
    except Exception as e: 
        print("Json not configured for playlist creation  correctly (songDir):")
        print(e)
        quit()

    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["musiPlaylists"]

    except Exception as e: 
        print("No Musi Playlists Specified In Config")
        print(e)
        return 

    outputPath = configDict["songDir"]
    playlists = configDict["musiPlaylists"]

    for playlist in playlists: 

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        options.page_load_stategy = "none"

        driver = Chrome(options=options)

        driver.implicitly_wait(5)

        driver.get(playlist)
        time.sleep(20)

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
            info = YoutubeDL({}).extract_info(link, download=False)
            if(info.get('uploader') is None): 
                filePath = f'{outputPath}/{info.get("title")}_.m4a'
            else: 
                filePath = f'{outputPath}/{(info.get("title"))}_{(info.get("uploader"))}.m4a'   
                if(os.path.exists(filePath)):
                    newPath = shutil.copy(filePath, f'{playlistName}/{(info.get("title"))}_{info.get("creator")}.m4a')                
                

def youtubePlaylistCreator(): 

    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["songDir"]
    except Exception as e: 
        print("Json not configured for playlist creation  correctly (songDir):")
        print(e)
        quit()
    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["youtubePlaylists"]
    except Exception as e: 
        print("Json not configured for youtube Playlists correctly:")
        print(e)
        return      
    
    playlists = configDict["youtubePlaylists"]
    songDir = configDict["songDir"]

    #"outtmpl": '~/Projects/CloudToLocal/songs/%(uploader)s_%(title)s.%(ext)s',  # this is where you can edit how you'd like the filenames to be formatted
    ydl_opts = {
        "ignoreerrors": "True"
    } 

    for playlistURL in playlists: 
        with YoutubeDL(ydl_opts) as ydl:
            playlist = ydl.extract_info(playlistURL, download=False)
            playlistName = playlist['playlist']
            if('entries' in playlist): 
                videos = playlist['entries']
                for i, item in enumerate(videos): 
                    if(item is not None): 
                        info = ydl.extract_info(item['webpage_url'], download=False)
                        print(info['title'], info['uploader'], info['ext'])
                        if(info.get('uploader') is None): 
                            fPath = f"{songDir}/{info['title']}_.{info['ext']}"
                            if(os.path.isfile(fPath)): 
                                newPath = shutil.copy(fPath, f'{playlistName}/{(info.get("title"))}_{info.get("creator")}.m4a')                
                        else: 
                            fPath = f"{songDir}/{info['title']} {info['uploader']}.{info['ext']}"
                            if(os.path.isfile(fPath)): 
                                newPath = shutil.copy(fPath, f'{playlistName}/{(info.get("title"))}_{info.get("creator")}.m4a')                





