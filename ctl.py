#!/usr/bin/env python3
import configargparse
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from time import sleep

VERBOSE = False
FAIL_ON_WARNING = False

def info(*args, **kwargs):
    if(VERBOSE):
        print(*args, **kwargs)

def warning(*args, **kwargs): 
    print("\033[93m")
    print("⚠️", end = "")
    print(*args, **kwargs)
    print("\033[0m")
    if(FAIL_ON_WARNING): 
        exit()

def success(*args, **kwargs):
    print("\033[92m")
    print("✅", end = "")
    print(*args, **kwargs)
    print("\033[0m")

def error(*args, **kwargs):
    print("\033[91m")
    print("❌", end = "")
    print(*args, **kwargs)
    print("\033[0m")
    exit()


class CloudToLocal: 
    def __init__(self, args): 
        self.dl_playlists = args.playlists
        self.output_dir = args.outdir
        self.unavail_file = args.unavail_file
        self.retries = args.retry_amt
        self.playlists_info = [] 
        self.replace_fname = args.replace_filenames

        ydl_opts_extract = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'quiet': (not args.verbose) 
        }
        
        for playlist in self.dl_playlists: 
            with YoutubeDL(ydl_opts_extract) as ydl: 
                self.playlists_info.append(
                    ydl.extract_info(playlist, download=False)) 
    
    def download(self): 
        for info in self.playlists_info: 
            for index, entry in enumerate(info['entries']):
                url = entry['url']
                if not url:
                    warning(f"[{index+1}] Skipping: No URL found for '{title}'")
                    continue

                if(entry["ie_key"] == "Youtube"): 
                    title = entry['title']
                    uploader = entry["uploader"]
                else: 
                    # NOTE: Soundcloud's API Gives References To Song Instead Of 
                    #       Song Information For Top Level Entry So We Must Query 
                    #       Further
                    sc_info = YoutubeDL({'simulate': True, 
                                         'quiet': True,}
                                       ).extract_info(url)
                    if('artist' in sc_info): 
                        uploader = sc_info['artist']
                    else: 
                        uploader = sc_info['uploader']

                    title = sc_info['title']

                ydl_opts_download = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                    }],
                    'quiet': (not args.verbose),
                    'noplaylist': True,
                    'paths': {"home":args.outdir},
                    'outtmpl': "%(title)s.%(ext)s",
                    'download_archive': args.outdir+"/archive"
                }
                print(f"\n[{index+1}/{len(info['entries'])}]"
                      f" Attempting: {title}")

                for retry in range(0, args.retry_amt-1):
                    try:
                        with YoutubeDL(ydl_opts_download) as ydl:
                            ydl.download([url])
                        break
                    except DownloadError as e:
                        info(f"Failed to download Retrying'{title} ({url})': {e}")
                        sleep(retry*10)
                        if(not retry):
                            with open(args.unavail_file, "a") as f: 
                                f.write(url)
                    except Exception as e:
                        error(f"Unexpected error for '{title}': {e}")
                        exit()
                        
                # TODO: implement filename replacement
                # if(args.replace_filenames): 
                #     self.parse_filenames(filename, uploader)


        success("Download Completed")
        

    # TODO: put this as part of the download process
    def parse_filenames(self, filename, uploader): 
        for file in os.listdir(self.output_dir): 
            result = get_artist_title(file)
            if(result): 
                artist = result[0]
                title = result[1]
                #TODO: Change Filename To Comply With ext m3u will also need album info here 
                search = ytmusic.search(artist + " " + title, filter = "songs", limit = 1)
                        # print(f"{search[0]["artists"]=} {search[0]["title"]=}\n" 
                        #       f" {artist=} {title=}")      
            else: 
                if(self.replace_fname == 'full'): 
                # TODO: implemetn replacement with uploader name
                    pass

def main(args):
    ctl = CloudToLocal(args)
    print("STARTING DOWNLOAD")
    ctl.download()

if __name__ == "__main__": 
    parser = configargparse.ArgParser(
            description="Automated Youtube and Soundcloud Downloader", 
            config_file_parser_class=configargparse.YAMLConfigFileParser
    )
    
    parser.add_argument("--replace_filenames", "-r", default = 'off', 
                        nargs='?', choices=['nofallback', 'full', 'off']) 

    parser.add_argument("--config", "-c", type=str, 
                        is_config_file=True, default="ctlConfig.yaml",
                        help="Configuration File Path")
    
    parser.add_argument("--playlists", "-i", type=str, 
                        nargs="+", 
                        help="List of Playlists To Download"
                             "  Can Be Either Youtube or Soundcloud")

    parser.add_argument("--outdir", "-o", type=str, 
                        required=True, help="Directory To Output Files To")
    
    parser.add_argument("--unavail_file", "-u", type=str, 
                        default="unavailable_videos", 
                        help="List Of Video URLS Unavailable For Download")

    parser.add_argument("--retry_amt", "-retry", default=10, 
                        help="Amount Of Times To Retry Non-Fatal Download"
                        " Errors")

    parser.add_argument("--fail_on_warning", "-w", type=int, 
                        default=0, help="Exit Program On Failure")

    parser.add_argument("--verbose", "-v", default=0, 
                        help="Enable Verbose Output")

    args = parser.parse_args()
    VERBOSE = args.verbose 
    FAIL_ON_WARNING = args.fail_on_warning 
    
    main(args)
