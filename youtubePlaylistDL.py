from pytube import Playlist
#import tkinter as tk 
#from tkinter import ttk
from time import sleep
import os

playString = ''
outputPath = ''

if((os.path.isfile("songDir")) and (os.path.getsize("songDir") != 0)): 
    with open("songDir", "r") as f: 
        outputPath = f.readline()
        outputPath = outputPath.rstrip('\n')
else: 
    print("songDir is not properly specified")
    exit()

if((os.path.isfile("playlist")) and (os.path.getsize("playlist") != 0)): 
    with open("playlist", "r") as f: 
        playString = f.readline()
else: 
    print("playString is not properly specified")
    exit()

playlist = Playlist(playString)

for i, youtube in enumerate(playlist.videos): 
    sleep(.5)
    stream = youtube.streams.get_by_itag(140) 
    stream.download(outputPath)
    print(stream.title)
    if((i % 100) == 0): 
        sleep(20)


