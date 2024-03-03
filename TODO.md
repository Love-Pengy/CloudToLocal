# Efficiency 
+ need to get rid of redundant config element checks
+ the playlist categorization and downloads need to be combined so that the following can be done: 
    + reduce amount of time needed because only one youtube and soundcloud dl operation needs to be done
    + song directory can be deleted automatically afterwards
+ make the songdir be based off of the current working dir or make it automatic
+ add timer dataclass to quantify runtime
+ Switches to toggle between linux and windows would also be nice
+ redundant code that can be optmized with vars after fetching info 

# Bug fixes
+ ~~need to fix the youtube playlist system it is not categorizing properly~~
+ getting a bug on line 158 of youtubePlaylistDL.py that FilenameManager has no attribute urls


# In Progress
+ working on moving the playlists creators over into the downloaders
    + Soundcloud ~~ Done But needs to be refactored and tested with mutliple playlists
    + musi  
    + youtube ~~ done but needs to be tested extensively 
