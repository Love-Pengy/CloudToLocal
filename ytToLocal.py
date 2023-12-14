from pytube import Playlist
#import tkinter as tk 
#from tkinter import ttk
from time import sleep


playlist = Playlist('https://youtube.com/playlist?list=PLN0r2zeXfMwBKK9973al4wKwSTSBG5GnO&si=b15a0AxLTPCi8V2M')

for i, youtube in enumerate(playlist.videos): 
    print(f"{youtube.video_id=}, {youtube.check_availability()=}, {i=}")
    sleep(.5)
    if((i % 100) == 0): 
        sleep(10)

