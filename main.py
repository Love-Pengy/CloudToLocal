from soundcloudPlaylistDL import soundcloudDownloader
from youtubePlaylistDL import youtubeDownloader
import json
from time import time

#this needs to be on the function defs
def timer(function): 
    def functionality(): 
        startTime = time()         
        function()
        finalTime = time()
        return((finalTime - startTime)/60)

if __name__ == "__main__": 
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
            youtubePlaylists = configDict["youtubePlaylists"]
    except Exception as e: 
        print("Json not configured for youtube playlists correctly:")
        print(e)

    try: 
        with open("config.json", "r") as f: 
            jsonList = json.load(f)
            configDict = jsonList[0] 
            musiPlaylists = configDict["musiPlaylists"]
    except Exception as e: 
        print("Json not configured for musi playlists correctly:")
        print(e)

    try: 
        with open("config.json", "r") as f: 
            jsonList = json.load(f)
            configDict = jsonList[0]
            scMaps = configDict["soundcloudSongMapping"]

    except Exception as e: 
        print("Sound cloud maps not imported correctly")
        print(e)



    '''
    print("soundCloud downloader starting")
    soundcloudDownloader()
    '''

    print("youtube downdloader starting")
    youtubeDownloader()

    '''
    if(musiPlaylists is not None): 
        musiPlaylistCreator()



    "https://youtube.com/playlist?list=PLN0r2zeXfMwAI4xwHW2zobG5lPVWa37G-&si=69xreI0pt3qN6oE_", 
    "https://youtube.com/playlist?list=PLN0r2zeXfMwBKK9973al4wKwSTSBG5GnO&si=4wf-VoQSSANnO_hy" 

    '''


