from sclib import SoundcloudAPI, Track, Playlist
from time import sleep
import os
import re
import json
import shutil
from helpers import timer
import platform

def strParser(string): 
    escapedString = re.escape(string)
    return(re.sub("/", ".", escapedString))

@timer
def soundcloudDownloader(): 

    playString = ''
    outputPath = ''

    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
        configDict = jsonList[0]
        test = configDict["songDir"]
        test = configDict["soundcloudPlaylists"]
        test = configDict["soundcloudSongMapping"]
        del(test)
    except Exception as e: 
        print("Json not configured for youtube correctly:")
        print(e)
        quit()
    
    outputPath = configDict["songDir"]
    playlists = configDict["soundcloudPlaylists"]
    mappings = configDict["soundcloudSongMapping"]
    sysPlatform = platform.system()

    if(not os.path.exists(outputPath)): 
        os.makedirs(outputPath)

    for i, mapping in enumerate(mappings): 
        for mapKey in mapping.keys(): 
            for playlist in playlists: 
                for playString in playlists: 
                    api = SoundcloudAPI()
                    playlist = api.resolve(playString)

                    assert type(playlist) is Playlist
                    
                    for i, song in enumerate(playlist): 
                        sleep(.5)
                        if(sysPlatform == 'Windows'):
                            filename = f'{outputPath}\{strParser(song.artist, sysPlatform)} - {strParser(song.title, sysPlatform)}.mp3'    
                        else:
                            filename = f'{outputPath}\{strParser(song.artist, sysPlatform)} - {strParser(song.title, sysPlatform)}.mp3'

                        with open(filename, 'wb+') as f:
                            song.write_mp3_to(f)
                            print(f"{filename} downloaded")
                        if(playlist.title == mapKey): 
                            filename = f'{outputPath}/{strParser(song.artist)} - {strParser(song.title)}.mp3'
                            if(os.path.exists(filename)):  
                                for playlistList in mapping: 
                                    for playlistName in mapping[playlistList]: 
                                        if(os.path.exists(f'./{playlistName}')): 
                                            coppiedPath = shutil.copy(filename, f'{playlistName}/{strParser(song.artist)} - {strParser(song.title)}.mp3')
                                            print(f"{coppiedPath} moved")
                                        else: 
                                            curDir = os.getcwd()
                                            fullDir = curDir + "/" + playlistName
                                            os.makedirs(fullDir)
                                            if(os.path.exists(f'./{playlistName}')): 
                                                coppiedPath = shutil.copy(filename, f'{playlistName}/{strParser(song.artist)} - {strParser(song.title)}.mp3')
                                                print(f"{coppiedPath} moved")
                        if(((i % 100) == 0) and (i != 0)): 
                            sleep(20)


