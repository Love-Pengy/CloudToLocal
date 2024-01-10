from pytube import Playlist
from yt_dlp import YoutubeDL
#import tkinter as tk 
#from tkinter import ttk
from time import sleep
import os
#import re


playString = ''
outputPath = ''

'''
not sure if this will be needed later

def strParser(string): 
    escapedString = re.escape(string)
    return(re.sub("/", ".", escapedString))
'''

if((os.path.isfile("songDir")) and (os.path.getsize("songDir") != 0)): 
    with open("songDir", "r") as f: 
        outputPath = f.readline()
        outputPath = outputPath.rstrip('\n')
else: 
    print("songDir is not properly specified")
    exit()

if((os.path.isfile("youtubePlaylist")) and (os.path.getsize("youtubePlaylist") != 0)): 
    with open("youtubePlaylist", "r") as f: 
        playString = f.readline()
else: 
    print("playString is not properly specified")
    exit()

#--output "~/Desktop/%(title)s.%(ext)s"
path = dict()
path["output"] = outputPath

opts = {
    'format': 'm4a/bestaudio/best',
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }], 
    'outtmpl_na_placeholder': '', 
    'outtmpl': './songs/%(title)s %(creator)s.%(ext)s', 
    'cookies-from-browser': 'firefox',  
    'ignoreerrors': 'true'
}

dlClass = YoutubeDL(opts)
dlClass.download(playString)
