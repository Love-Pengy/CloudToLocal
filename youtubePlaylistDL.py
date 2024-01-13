#from pytube import Playlist
from yt_dlp import YoutubeDL
#from time import sleep
#import os
import json


def youtubeDownloader(): 
    playString = ''
    outputPath = ''


    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
        configDict = jsonList[0]
        test = configDict["songDir"]
        test = configDict["youtubeURL"]     
    except Exception as e: 
        print("Json not configured for youtube correctly:")
        print(e)
        quit()


    outputPath = configDict["songDir"]
    playString = configDict["youtubeURL"]

    opts = {
        'format': 'm4a/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }], 
        'outtmpl_na_placeholder': '', 
        'outtmpl': f'{outputPath}/%(title)s %(creator)s.%(ext)s', 
        'cookies-from-browser': 'firefox',  
        'ignoreerrors': 'true'
    }

    dlClass = YoutubeDL(opts)
    dlClass.download(playString)
