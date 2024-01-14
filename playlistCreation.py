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
    print("Json not configured for musiPlaylists correctly:")
    print(e)
    quit()

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
        if(info.get('creator') is None): 
            filePath = f'{outputPath}/{(info.get('title'))} + " .m4a"'   
            if(os.path.exists(filePath)): 
                newPath = shutil.copy(filePath, f'{playlistName}/{(info.get('title'))} + " .m4a"')
        else: 
            filePath = f'{outputPath}/{(info.get('title'))} + " " + {(info.get('creator'))} + ".m4a"'   
            if(os.path.exists(filePath)):
                newPath = shutil.copy(filePath, f'{playlistName}/{(info.get('title'))} + " " + {info.get('creator')} + " .m4a"')                
            


