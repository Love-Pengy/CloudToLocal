<!--toc:start-->
- [Efficiency](#efficiency)
- [Bug fixes](#bug-fixes)
- [In Progress](#in-progress)
- [ACTUAL TODO](#actual-todo)
<!--toc:end-->

# Cloud To Local

## Efficiency

+ need to get rid of redundant config element checks
+ the playlist categorization and downloads need to be combined so that the following can be done:
  + reduce amount of time needed because only one youtube and soundcloud dl operation needs to be done
  + song directory can be deleted automatically afterwards
+ make the songdir be based off of the current working dir or make it automatic
+ add timer dataclass to quantify runtime
+ Switches to toggle between linux and windows would also be nice
+ redundant code that can be optmized with vars after fetching info

## Bug fixes

+ ~~need to fix the youtube playlist system it is not categorizing properly~~
~~+ getting a bug on line 158 of youtubePlaylistDL.py that FilenameManager has no attribute urls~
+ need to make a windows and linux mode because the windows file system fucking sucks 

## In Progress

+ working on moving the playlists creators over into the downloaders
  + Soundcloud ~~ Done But needs to be refactored and tested with mutliple playlists
  + youtube ~~ done but needs to be tested extensively~~
  + musi  Needs to be tested

## ACTUAL TODO

+ dump a log of files that were unable to be downloaded
+ take the images and embed them within the songs
+ allow specification of how much quality you want
+ add length mapping (for sets)
+ allow specification of file type
