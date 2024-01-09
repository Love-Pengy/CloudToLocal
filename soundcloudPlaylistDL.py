from sclib import SoundcloudAPI, Track, Playlist
from time import sleep
import os
import re

def strParser(string): 
    escapedString = re.escape(string)
    return(re.sub("/", ".", escapedString))
 

playString = ''
outputPath = ''

if((os.path.isfile("songDir")) and (os.path.getsize("songDir") != 0)): 
    with open("songDir", "r") as f: 
        outputPath = f.readline()
        outputPath = outputPath.rstrip('\n')
else: 
    print("soundcloud songDir is not properly specified")
    exit()

if((os.path.isfile("soundcloudPlaylist")) and (os.path.getsize("soundcloudPlaylist") != 0)): 
    with open("soundcloudPlaylist", "r") as f: 
        playString = f.readline()
        playString = playString.rstrip('\n')
else: 
    print("soundcloud playlist is not properly specified")
    exit()

api = SoundcloudAPI()

playlist = api.resolve(playString)

assert type(playlist) is Playlist

for i, song in enumerate(playlist): 
    sleep(.5)
    filename = f'{outputPath}/{strParser(song.artist)} - {strParser(song.title)}.mp3'
    with open(filename, 'wb+') as f:
        song.write_mp3_to(f)
        print(f"wrote {filename}")
    if((i % 100) == 0): 
        sleep(20)


