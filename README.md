# CloudToLocal

+ Automated online backup tool for local backups with Youtube, Soundcloud, and Musi

## Usage
+ In order to configure behavior of this tool create a config.json file in the root of the project directory 

+ The current configuration options are as follows: 
    + songDir
        - directory to hold the downloaded songs
    - soundcloudPlaylists 
        - list of links for soundcloud playlists to download
    - youtubePlaylists
        - list of youtube playlists to download
    - musiPlaylists
        - list of musi playlists to use for mapping
    - soundcloudSongMapping
        - list of lists that represent which youtube playlist to put a specified soudcloud playlist withing

## Example
```json
[{
    "songDir": "songs", 
    "soundcloudPlaylists": [
        "https://soundcloud.com/username/foo" 
    ], 
"youtubePlaylists": [
        "https://youtube.com/playlist?list=id1", 
        "https://youtube.com/playlist?list=id2", 
        "https://youtube.com/playlist?list=id3"
    ], 
    "musiPlaylists": [
        "https://feelthemusi.com/playlist/id1", 
        "https://feelthemusi.com/playlist/id2", 
        "https://feelthemusi.com/playlist/id3", 
        "https://feelthemusi.com/playlist/id4" 
    ],
    "soundcloudSongMapping": [
        {
        "My Cool SoundCloud Playlist": ["My Cool Youtube Playlist"]  
        }
    ], 
}]
```


