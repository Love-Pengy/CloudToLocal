from soundcloudPlaylistDL import soundcloudDownloader
from youtubePlaylistDL import youtubeDownloader
import json
from playlistCreation import youtubePlaylistCreator
from playlistCreation import musiPlaylistCreator
from playlistCreation import soundcloudPlaylistCreator

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



    print("soundCloud downloader starting")
    soundcloudDownloader()

    if(scMaps is not None): 
        print("Playlist Creator Moving")
        soundcloudPlaylistCreator()

    '''
    print("youtube downdloader starting")
    youtubeDownloader()

    if(youtubePlaylists is not None): 
        youtubePlaylistCreator()

    if(musiPlaylists is not None): 
        musiPlaylistCreator()
    '''


