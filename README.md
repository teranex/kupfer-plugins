# kupfer-plugins

## Hotot
This plugin let's you tweet directly from Kupfer using the running Hotot instance. It also
let's you easily show, hide and quit the running Hotot instance.

![Hotot screenshot](https://raw.github.com/teranex/kupfer-plugins/master/doc/screenshots/hotot-1.png "Sending a tweet")

## Media players
This plugin can be used to command any mpris2-enabled media player. Tested with Banshee,
VLC, Spotify, Gmusicbrowser and a few others. It let's you perform commands actions such
as Play/Pause, Stop, skip to the next or previous track, show information about the
currently playing track, seek forward and backward and so on.
For this to work the medi player should implement Mpris2 and it should be enabled. For
example in Banshee you should enable the 'MPRIS D-Bus interface'-extension.

![Media Players screenshot](https://raw.github.com/teranex/kupfer-plugins/master/doc/screenshots/media_players-1.png "play/pause selected for Banshee player")

## Hamster
Hamster is a time tracker. This plugin lets you start, stop and edit tasks directly from
Kupfer.

### Starting Activities
To start an activty which you already tracked in the past, simply start typing, and the
plugin will bring up all the matches. Activities are in the form of `activity@category`,
as is usual in Hamster. Once you have found the correct activity you can start tracking it
with the 'Start Tracking' action. It is also possible to start tracking a new activiy,
which is not yet known in Hamster, by simply typing the text ('activity@category', or
simply 'activity' if you don't want to use a category). To make this easier, you can enter
text mode in Kupfer by typing a dot (.).
When starting an activity, you can also use the 'Start Activity with description' action.
This will show the third pane in Kupfer and will let you type a text which will be used as
the action. (Again, you can enter text-mode by first typing a .).
It is also possible to use the 'Start Activity with tags' action. This will also open the
third pane, which will present you with all the known tags in Hamster. You can select
multiple tags by using the 'comma trick': select a tag, type a comma (,), select another
tag, type a comma again, and so on. It is also possible to create new tags with text mode
(followed by the comma trick for multiple tags).
After starting an activity, Kupfer will immediately open again with the new activity
preselected, to let you do additional edits. This can be disabled in the options of the
plugin.

![Hamster screenshot](https://raw.github.com/teranex/kupfer-plugins/master/doc/screenshots/hamster-1.png "Starting an activity with tags")

### Editing Activities
The plugin lets you edit activities. To do this, first search for the 'Hamster
Facts'-catalog. (Note: for the moment only activities of the current day are accessible).
Then select the activity you want to edit. You can edit the following:
  * Start time: you can enter a new start time in the third pane. The format must be H:MM
  or HH:MM
  * End time: change the end time for the task. The format must be H:MM or HH:MM
  * Description: enter a new description in the third pane. (Use . to open text-mode)
  * Tags: enter new tags. You can use the comma trick and text-mode to create new and
  select multiple tags. Note: all previous tags are removed.
  * Remove: remove the activity. (this can not be undone!)

![Hamster screenshot](https://raw.github.com/teranex/kupfer-plugins/master/doc/screenshots/hamster-2.png "Editing the end time")

### Notes
    * Note: a patch is needed in Kupfer! The patch can be found in comment 19 in this
    issue report: https://bugs.launchpad.net/ubuntu/+source/kupfer/+bug/1038434 Without
    this patch, Kupfer will crash with a Segmentation Fault.
    * Please test that all times are correct. I'm not yet 100% sure that timezones and DST
    are handled correctly.
    * Make a backup of your Hamster database. I'm not responsible if things explode :)


<!---
vim:textwidth=90:wrap:
-->
