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

def main(args):

    for playlist in args.playlists:
        # Get Metadata Of Vids For Extraction Of URL On Failure
        ydl_opts_extract = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'quiet': (not args.verbose) 
        }

        with YoutubeDL(ydl_opts_extract) as ydl:
            playlist = ydl.extract_info(playlist, download=False)

        for index, entry in enumerate(playlist['entries']):
            # TODO: Make Parser To Attempt To Get The Real Name
            title = entry.get('title')
            url = entry.get('url')
                 
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                }],
                'quiet': (not args.verbose),
                'noplaylist': True,
                'paths': {"home":args.outdir},
                'outtmpl': "%(title)s.%(ext)s",
                # TODO: Specify in docs that this is the expected place for 
                # archive 
                'download_archive': args.outdir+"/archive"
            }
 
            if not url:
                warning(f"[{index+1}] Skipping: No URL found for '{title}'")
                continue

            print(f"\n[{index+1}/{len(playlist['entries'])}]"
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

    success("Download Completed")

# TODO: put note in docs that age restricted videos will not work
if __name__ == "__main__": 
    parser = configargparse.ArgParser(
            description="Automated Youtube and Soundcloud Downloader", 
            config_file_parser_class=configargparse.YAMLConfigFileParser
    )
    
    # TODO: Reorder this to make sense in help page
    parser.add_argument("--retry_amt", "-r", default=10, 
                        help="Amount Of Times To Retry Non-Fatal Download"
                        " Errors")

    parser.add_argument("--verbose", "-v", default=0, 
                        help="Enable Verbose Output")

    parser.add_argument("--config", "-c", type=str, 
                        is_config_file=True, default="ctlConfig.yaml",
                        help="Configuration File Path")
    
    parser.add_argument("--playlists", "-p", type=str, 
                        nargs="+", 
                        help="List of Playlists To Download"
                             "  Can Be Either Youtube or Soundcloud")
    
    # TODO: make it so you can't specify fail on warning and unavail file
    parser.add_argument("--fail_on_warning", "-w", type=int, 
                        default=0, help="Exit Program On Failure")
    
    # TODO: Recommend wayback machine for archive somewhere in docs
    parser.add_argument("--unavail_file", "-u", type=str, 
                        default="unavailable_videos", 
                        help="List Of Video URLS Unavailable For Download")

    parser.add_argument("--outdir", "-o", type=str, 
                        required=True, help="Directory To Output Files To")

    args = parser.parse_args()
    VERBOSE = args.verbose 
    FAIL_ON_WARNING = args.fail_on_warning 
    
    main(args)
