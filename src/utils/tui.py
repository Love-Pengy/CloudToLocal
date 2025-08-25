import json
from ytmusicapi import YTMusic
from utils.common import get_img_size_url, sanitize_string
from utils.file_operations import user_replace_filename


def correct_missing(report_path):
    """Interactive Function To Fix Albums And Songs That Could Not Be
        Automatically Found With A High Level Of Certainty

        Args:
            report_path (str): Path To Report JSON File
        """

    ytmusic = YTMusic()
    with open(report_path, "r") as f:
        missing_albums = json.load(f)

    for song_path in list(missing_albums):
        spec = missing_albums[song_path]
        print(f"OG Path: {song_path}\n"
              f"OG Title: {spec["found_title"]}, OG Artist: {
                  spec["found_artist"]}\n"
              f"Matched Title: {spec["closest_match"]["title"]}, "
              f"Matched Artist: {[artist["name"]
                                  for artist in
                                  spec["closest_match"]["artists"]]}\n"
              f"Matched Album: {spec["closest_match"]["album"]}\n")
        f"Provider: {spec["provider"]}"
        user_input = None
        while (not (user_input == '1') and
               not (user_input == '2') and
               not (user_input == '3') and
               not (user_input == '4') and
               not (user_input == 'q')):
            user_input = input(
                "1: Accept Closest Match 2: Accept Original (No Album) "
                "3: Search Again 4: Input From Scratch q: Save And Exit ")

        match user_input:
            case '1':
                closest_match = spec["closest_match"]
                artists = [artist["name"]
                           for artist in closest_match["artists"]]

                if ("year" in closest_match):
                    album_date = closest_match["year"]
                else:
                    album_date = None

                if (closest_match["thumbnails"] is not None):
                    thumbnail = closest_match["thumbnails"][len(
                        closest_match["thumbnails"]-1)]
                else:
                    thumbnail = None

                user_replace_filename(closest_match["title"], artists,
                                      song_path, spec["ext"],
                                      closest_match["album"],
                                      spec["url"], spec["duration"],
                                      closest_match["trackNumber"],
                                      closest_match["album_len"],
                                      album_date,
                                      thumbnail)
                missing_albums.pop(song_path)

            case '2':
                user_replace_filename(spec["found_title"],
                                      [spec["found_artist"]],
                                      song_path,
                                      spec["ext"],
                                      "", spec["url"],
                                      spec["duration"],
                                      1, 1, None, user_url)
                missing_albums.pop(song_path)

            case '3':
                while (1):
                    print(f"Old FilePath: {song_path}\n"
                          f"Old Title: {spec["closest_match"]["title"]}\n"
                          f"Old Artist: {spec["closest_match"]["title"]}")

                    user_title = input("New Title: ")
                    user_artist = input("New Artist: ")
                    search = ytmusic.search(
                        user_artist + " " + user_title, filter="songs", limit=1)
                    if (search):
                        album = ytmusic.get_album(
                            search[0]["album"]["id"])["tracks"]

                        # See if track is in the album we found
                        album_name = [
                            track for track in album
                            if track["title"].lower() == user_title.lower()
                        ]
                        if (album_name):
                            track_num = album_name[0]["trackNumber"]

                            if (("thumbnails" in album_name[0])
                                    and (album_name[0]["thumbnails"]
                                         is not None)):
                                thumbs = album_name[0]["thumbnails"]
                            else:
                                thumbs = search[0]["thumbnails"]

                            artists = [sanitize_string(artist["name"])
                                       for artist in search[0]["artists"]]

                            if (("year" in search[0])
                               and (search[0]["year"] is not None)):
                                year = search[0]["year"]
                            else:
                                year = None

                            print(f"Found: \nTitle: {search[0]["title"]}\n"
                                  f"Artists: {artists}\n"
                                  f"Track Num: {track_num}\n"
                                  f"Album Len: {len(album)}\n"
                                  f"Year: {year}\n"
                                  f"Thumbnail: {thumbs[len(thumbs)-1]}")

                            user_input = ""
                            while ((not user_input.lower() == 'y') and
                                   (not user_input.lower() == 'n')):
                                user_input = input(
                                    "Does The Above Seem Correct? (Y/N) ")

                            if (user_input.lower() == 'y'):
                                image_size = get_img_size_url(
                                    thumbs[len(thumbs-1)]["url"])

                                url = f"http://youtu.be/{
                                    search[0]["videoId"]}"
                                user_replace_filename(search[0]["title"],
                                                      artists,
                                                      song_path,
                                                      spec["ext"],
                                                      album_name[0]["album"],
                                                      url,
                                                      spec["duration"],
                                                      track_num,
                                                      len(album),
                                                      year,
                                                      {"height": image_size[1],
                                                       "width": image_size[0],
                                                       "url": thumbs[len(thumbs)-1]["url"]})
                                missing_albums.pop(song_path)
                                break
                        else:
                            print("Album Not Found")
                    else:
                        print("Song Not Found")
            case '4':
                while (1):
                    print(f"Old FilePath: {song_path}\n"
                          f"Old Title: {spec["closest_match"]["title"]}\n"
                          f"Old Artist: {spec["closest_match"]["title"]}")
                    user_title = input("New Title: ")
                    user_artists = [input for input in input(
                        "New Artists (seperated by ,): ").split(',')]
                    user_album = input(
                        "New Album (Leave Blank For None): ")
                    user_url = input("New Song Url: ")
                    user_duration = int(input("New Duration (seconds): "))
                    user_track_num = int(input("New Track Number: "))
                    user_total_tracks = int(
                        input("Total Tracks In Album: "))
                    user_album_date = input("Album Year: ")
                    user_thumbnail_url = input("Thumbnail Url: ")

                    confirmation = input(f"Title: {user_title}\n"
                                         f"Artist: {user_artists}\n"
                                         f"Album: {user_album}\n"
                                         f"Url: {user_url}\n"
                                         f"Duration: {user_duration}\n"
                                         f"Track Num: {user_track_num}\n"
                                         f"Total Tracks: {
                        user_total_tracks}\n"
                        f"Album Year: {user_album_date}\n"
                        "Does Everything Above Look Right? (Y/N) ")

                    if (confirmation.lower() == 'y'):
                        image_size = get_img_size_url(user_thumbnail_url)

                        user_replace_filename(user_title,
                                              user_artists,
                                              song_path,
                                              spec["ext"],
                                              user_album,
                                              user_url,
                                              user_duration,
                                              user_track_num,
                                              user_total_tracks,
                                              user_album_date,
                                              {"height": image_size[1],
                                               "width": image_size[0],
                                               "url": user_thumbnail_url}
                                              )
                        missing_albums.pop(song_path)
                        break
            case 'q':
                break
    with open(report_path, "w") as f:
        json.dump(missing_albums, f, indent=2)

# Idea here is to do the following: 
#   1. clear the screen
#   2. write status in the top middle
#   3. display original embed information to the left
#   4. display changed embed information to the right
#   5. display options at the bottom

# What this requires: a more specific reporting system. I need the original information as well 
#   as the new information
def render_comparison():
    pass

