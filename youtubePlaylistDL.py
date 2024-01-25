#from pytube import Playlist
from yt_dlp import YoutubeDL
#from time import sleep
#import os
import json
import os
import shutil
import re 

class FilenameManager:
    def __init__(self): 
        self.currentPlaylistName = None
        self.filenames = list()

    def updateFilenames(self, d): 
        if(self.currentPlaylistName is None): 
            if(d['status'] == 'finished'): 
                self.currentPlaylistName = d['info_dict']['playlist_title']
                self.filenames.append(d['filename'])

        elif(self.currentPlaylistName == d['info_dict']['playlist_title']): 
            if(d['status'] == 'finished'): 
                self.filenames.append(d['filename'])
        else: 
            if(d['status'] == 'finished'): 
                self.currentPlaylistName = d['info_dict']['playlist_title']
                self.filenames = list()
                self.filenames.append(d['filename'])


'''
class FilenameCollector(YoutubeDL.post_processor.common.PostPocessor): 
    def __init__(self): 
        super(FilenameCollector, self).__init__(None)
        self.filenames = []
    
    def run(self, information): 
        self.filenames.append(information['filepath'])
        return [], information
'''


# invalid characters: +{;"\=?~()<>&*|$
def strParser(string): 
    escapedString = re.escape(string)
    # escapedString  = re.sub(r"\+{;\"\=?~()<>&*|$", " ", string)
    return(escapedString)

def youtubeDownloader(): 
    playString = ''
    outputPath = ''

    try: 
        with open("config.json", "r") as f:     
            jsonList = json.load(f)
            configDict = jsonList[0]
            test = configDict["songDir"]
            test = configDict["youtubePlaylists"]     
            test = configDict["musiPlaylists"]
            del(test)
    except Exception as e: 
        print("Json not configured for youtube correctly:")
        print(e)
        quit()


    outputPath = configDict["songDir"]
    youtubePlaylists = configDict["youtubePlaylists"]
        
    if(not os.path.exists(outputPath)): 
        os.makedirs(outputPath)


    
    fNameManager = FilenameManager()
        
    opts = {
        'format': 'm4a/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }], 
        'progress_hooks': [fNameManager.updateFilenames], 
        'outtmpl_na_placeholder': '', 
        'outtmpl': f'{outputPath}/%(title)s_%(uploader)s.%(ext)s', 
        'cookies-from-browser': 'chrome',  
        'ignoreerrors': 'true', 
        'restrictfilenames': 'true'
    }

    # filename_collector = FilenameCollector()
    ydl = YoutubeDL(opts)
    #ydl.add_post_processor(filename_collector)
    


    #playlist names include the entire file path
    for i, playlist in enumerate(youtubePlaylists): 
        ydl.download(playlist)
        for i,name in enumerate(fNameManager.filenames): 
            print("TEST:", name)
            curDir = os.getcwd()
            fullDir = curDir + "/" + fNameManager.currentPlaylistName
            if(not (os.path.exists(f"./{fNameManager.currentPlaylistName}"))): 
                os.makedirs(fullDir)
            print("TEST2:", fullDir)
            shutil.copy(fNameManager.filenames[i], fullDir)
            
       # with YoutubeDL(opts) as ydl: 
            #print(playlistNames)
    print("TEST:", fNameManager.filenames)
'''
    for playlist in youtubePlaylists: 
            playlistNames = ydl.download(playlist)
            playlistInfo = ydl.extract_info(playlist, download=False)
            playlistName = playlistInfo['title']
            #playlist = playlistInfo
            if('entries' in playlistInfo): 
                videos = playlistInfo['entries']
                if(not (os.path.exists(f"./{playlistName}"))): 
                    curDir = os.getcwd()
                    fullDir = curDir + "/" + playlistName
                    os.makedirs(fullDir)
                for i, item in enumerate(videos): 
                    if(item is not None): 
                        videoInfo = ydl.extract_info(item['webpage_url'], download=False)
                        if(videoInfo['uploader'] is None): 
                            filePath = f'{strParser(outputPath)}/{strParser(videoInfo["title"])}_.{videoInfo["ext"]}'
                            print(filePath)
                            if(os.path.isfile(filePath)): 
                                shutil.copy(filePath, f"{playlistName}/{strParser(videoInfo['title'])}_.m4a")                
                                print(f'{strParser(videoInfo["title"])}_.{strParser(videoInfo["ext"])}')
                        else: 
                            filePath = f'{outputPath}/{strParser(videoInfo["title"])}_{strParser(videoInfo["uploader"])}.{videoInfo["ext"]}'
                            print(filePath)
                            if(os.path.isfile(filePath)): 
                                shutil.copy(filePath, f'{playlistName}/{strParser(videoInfo["title"])}_{strParser(videoInfo["uploader"])}.{videoInfo["ext"]}')
                                print(f'{strParser(videoInfo["title"])}_{strParser(videoInfo["uploader"])}.{videoInfo["ext"]}')

'''


'''
    for i, item in enumerate(videos): 
        videoInfo = ydl.extract_info(item['webpage_url'], download=False)
        if(videoInfo['uploader'] is None): 
            filePath = f"{outputPath}/{videoInfo['title']}_.{videoInfo['ext']}"
            if(os.path.exists(f"./{playlistName}")): 
                if(os.path.isfile(filePath)): 
                    shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_.m4a")
                    print(f"{videoInfo['title']}_{videoInfo['ext']} MOVED")
            else: 
                curDir = os.getcwd()
                fullDir = curDir + "/" + playlistName
                os.makeDirs(fullDir)
                filePath = f"{outputPath}/{videoInfo['title']}_.{videoInfo['ext']}"
                if(os.path.isfile(filePath)): 
                    shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_.m4a")                
                    print(f"{videoInfo['title']}_{videoInfo['ext']} MOVED")
        else: 
            filePath = f"{outputPath}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}"
            if(os.path.exists(f"./{playlistName}")): 
                if(os.path.isfile(filePath)): 
                    shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}")
                    print(f"{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']} MOVED")
            else: 
                curDir = os.getcwd()
                fullDir = curDir + "/" + playlistName
                os.makeDirs(fullDir)
                filePath = f"{outputPath}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}"
                if(os.path.isfile(filePath)): 
                    shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}")                
                    print(f"{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']} MOVED") 

    for playlist in youtubePlaylists: 
        with YoutubeDL(opts) as ydl: 
            playlistInfo = ydl.extract_info(playlist, download=True)
            playlistName = playlistInfo['title']
            #playlist = playlistInfo
            if('entries' in playlist): 
                print("HAS ENTRIES")
                videos = playlist['entries']
                for i, item in enumerate(videos): 
                    videoInfo = ydl.extract_info(item['webpage_url'], download=False)
                    if(videoInfo['uploader'] is None): 
                        filePath = f"{outputPath}/{videoInfo['title']}_.{videoInfo['ext']}"
                        if(os.path.exists(f"./{playlistName}")): 
                            if(os.path.isfile(filePath)): 
                                shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_.m4a")
                                print(f"{videoInfo['title']}_{videoInfo['ext']} MOVED")
                        else: 
                            curDir = os.getcwd()
                            fullDir = curDir + "/" + playlistName
                            os.makeDirs(fullDir)
                            filePath = f"{outputPath}/{videoInfo['title']}_.{videoInfo['ext']}"
                            if(os.path.isfile(filePath)): 
                                shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_.m4a")                
                                print(f"{videoInfo['title']}_{videoInfo['ext']} MOVED")
                    else: 
                        filePath = f"{outputPath}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}"
                        if(os.path.exists(f"./{playlistName}")): 
                            if(os.path.isfile(filePath)): 
                                shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}")
                                print(f"{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']} MOVED")
                        else: 
                            curDir = os.getcwd()
                            fullDir = curDir + "/" + playlistName
                            os.makeDirs(fullDir)
                            filePath = f"{outputPath}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}"
                            if(os.path.isfile(filePath)): 
                                shutil.copy(filePath, f"{playlistName}/{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']}")                
                                print(f"{videoInfo['title']}_{videoInfo['uploader']}.{videoInfo['ext']} MOVED") 
'''



