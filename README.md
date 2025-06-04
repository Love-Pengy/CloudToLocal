# CloudToLocal

Automated online backup tool for local backups with Youtube, Soundcloud, and Musi

## Installation 
 
Install Deps With setup.py 
> `pip install .` 

> [!IMPORTANT] 
> It is crucial that you keep the deps up to date. If download failures start
> to occur it is most likely that yt-dlp needs an update. If you find that this 
> is the case submit an issue and or update the yt-dlp package

## Usage
    
In order to use this program you must either specify everything via arguments 
or through a configuration file. 

Because this is intended to be an automation, it is highly recommended that you
use a file.

Below is a list of all the current options

```
usage: ctl-dl.py [-h] [--replace_filenames REPLACE_FILENAMES]
                 [--config CONFIG]
                 [--playlists PLAYLISTS [PLAYLISTS ...]] --outdir
                 OUTDIR [--unavail_file UNAVAIL_FILE]
                 [--retry_amt RETRY_AMT]
                 [--fail_on_warning FAIL_ON_WARNING]
                 [--verbose VERBOSE] [--not_found NOT_FOUND]
                 [--missing_albums MISSING_ALBUMS]

Automated Youtube and Soundcloud Downloader

options:
  -h, --help            show this help message and exit
  --replace_filenames REPLACE_FILENAMES, -r REPLACE_FILENAMES
                        Attempt To Replace Filename With Official
                        YTMusic Name and embed metadata
  --config CONFIG, -c CONFIG
                        Configuration File Path
  --playlists PLAYLISTS [PLAYLISTS ...], -i PLAYLISTS [PLAYLISTS ...]
                        List of Playlists To Download Can Be Either
                        Youtube or Soundcloud
  --outdir OUTDIR, -o OUTDIR
                        Directory To Output Files To
  --unavail_file UNAVAIL_FILE, -u UNAVAIL_FILE
                        List Of Video URLS Unavailable For Download
  --retry_amt RETRY_AMT, -retry RETRY_AMT
                        Amount Of Times To Retry Non-Fatal Download
                        Errors
  --fail_on_warning FAIL_ON_WARNING, -w FAIL_ON_WARNING
                        Exit Program On Failure
  --verbose VERBOSE, -v VERBOSE
                        Enable Verbose Output
  --not_found NOT_FOUND, -nf NOT_FOUND
                        File Path To Output Songs That Failed The
                        YTMusic Search
  --missing_albums MISSING_ALBUMS, -ma MISSING_ALBUMS
                        File Path To Output Songs That Failed To Verify
                        The Album`
```

## Tips

When using the `unavail_file` option it will give you the urls of the videos
that failed. For these songs you can not get the relevent information through
youtube's site. I recommned using the [Wayback Machine](https://web.archive.org/)
in order to obtain the information you need to replace that song.

There is currently no option to pass cookies to this script. Therefore, age 
restricted videos will not work.




