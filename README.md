# CloudToLocal

<!--toc:start-->
- [CloudToLocal](#cloudtolocal)
  - [Installation](#installation)
      - [Local](#local)
      - [Docker](#docker)
  - [Local Usage](#local-usage)
  - [Configuration](#configuration)
<!--toc:end-->

Automated online backup tool for local backups with YouTube, Soundcloud, and Musi

## Installation 
 
#### Local
> `pip install .`
Install dependencies with setup.py

> [!TIP]
> An external Javascript dependency is now required for yt-dlp to operate properly for Youtube. You
> can find more about this change [here](https://github.com/yt-dlp/yt-dlp/issues/15012)

> [!IMPORTANT]
> It is crucial that you keep the dependencies up to date. If download failures start
> to occur it is most likely that yt-dlp needs an update. If you find that this
> is the case submit an issue and or update the yt-dlp package

#### Docker

1. build the image `podman compose build`
2. run image `podman compose up`


## Local Usage

```
usage: ctl-dl.py [-h] [--config CONFIG] [--playlists PLAYLISTS [PLAYLISTS ...]] --outdir OUTDIR [--retry_amt RETRY_AMT] [--start_tui] [--fail_on_warning]
                 [--verbose] [--quiet] [--download_sleep DOWNLOAD_SLEEP] [--request_sleep REQUEST_SLEEP] [--fresh]

Automated Youtube and Soundcloud Downloader

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Configuration File Path
  --playlists PLAYLISTS [PLAYLISTS ...], -i PLAYLISTS [PLAYLISTS ...]
                        List of Playlists To Download Can Be Either Youtube or Soundcloud
  --outdir OUTDIR, -o OUTDIR
                        Directory To Output Unverified Songs To
  --retry_amt RETRY_AMT, -retry RETRY_AMT
                        Amount Of Times To Retry Non-Fatal Download Errors
  --start_tui, -t       Start Tui To Edit Metadata
  --fail_on_warning, -w
                        Exit Program On Failure
  --verbose, -v         Enable Verbose Output
  --quiet, -q           Suppress Everything But Warnings and Errors
  --download_sleep DOWNLOAD_SLEEP, -ds DOWNLOAD_SLEEP
                        Maximum Amount Of Seconds To Sleep Before A Download
  --request_sleep REQUEST_SLEEP, -rs REQUEST_SLEEP
                        Amount Of Seconds To Sleep Between Requests
  --fresh, -f           Delete Directory Before Downloading (Mainly For Testing)

Args that start with '--' can also be set in a config file (specified via --config). The config file uses YAML syntax and must represent a YAML 'mapping'
(for details, see http://learn.getgrav.org/advanced/yaml). In general, command-line values override config file values which override defaults.
```


## Configuration

Change `example_conf.yaml` to match what you want. All Settings are there and documented

> [!IMPORTANT]
> When using the docker image you must create your output directory **before** running the image.
> this is to prevent docker from creating the directory for you which will create it as root.
