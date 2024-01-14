from sclib import SoundcloudAPI, Track, Playlist
from time import sleep
import os
import re
import json
 
def strParser(string): 
    escapedString = re.escape(string)
    return(re.sub("/", ".", escapedString))

def soundcloudDownloader(): 
    playString = ''
    outputPath = ''

    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
        configDict = jsonList[0]
        test = configDict["songDir"]
        test = configDict["soundcloudURL"]
        del(test)
    except Exception as e: 
        print("Json not configured for youtube correctly:")
        print(e)
        quit()




    
    outputPath = configDict["songDir"]
    playlists = configDict["soundcloudURL"]


    for playString in playlists: 

        api = SoundcloudAPI()
        playlist = api.resolve(playString)

        assert type(playlist) is Playlist

        for i, song in enumerate(playlist): 
            sleep(.5)
            filename = f'{outputPath}/{strParser(song.artist)} - {strParser(song.title)}.mp3'
            with open(filename, 'wb+') as f:
                song.write_mp3_to(f)
            if((i % 100) == 0): 
                sleep(20)


