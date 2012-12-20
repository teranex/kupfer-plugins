"""
A plugin to control any MPRIS2 player.

Initially based on the Spotify plugin
(https://github.com/stephenrjohnson/Kupfer-Spotify) and Python MPRIS-2 Remote
(https://bitbucket.org/whitelynx/pymprisr/overview)
"""

__kupfer_name__ = _("MPRIS2")
__kupfer_sources__ = ("Mpris2Source", )
__description__ = _("Control the active MPRIS2 player")
__version__ = "0.1"
__author__ = "Jeroen Budts <jeroen@budts.be>"

import dbus

from kupfer.objects import RunnableLeaf, Source
from kupfer.obj.apps import AppLeafContentMixin
from kupfer import utils, icons, pretty, uiutils

class Mpris2RunnableLeaf (RunnableLeaf):
    def get_target_object(self):
        bus = dbus.SessionBus()
        target = None
        dbusObj = bus.get_object('org.freedesktop.DBus', '/')
        for name in dbusObj.ListNames(dbus_interface='org.freedesktop.DBus'):
            if name.startswith('org.mpris.MediaPlayer2.'):
                target = name
                break
        return bus.get_object(target, '/org/mpris/MediaPlayer2')

    def get_rootobject(self):
        return dbus.Interface(self.get_target_object(), dbus_interface='org.mpris.MediaPlayer2')

    def get_player(self):
        return dbus.Interface(self.get_target_object(), dbus_interface='org.mpris.MediaPlayer2.Player')

    def get_property(self, property_name):
        properties_manager = dbus.Interface(self.get_target_object(), 'org.freedesktop.DBus.Properties')
        return properties_manager.Get('org.mpris.MediaPlayer2.Player', property_name)


class PlayPause (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Play/Pause"))
    def run(self):
        self.get_player().PlayPause()
    def get_description(self):
        return _("Resume/Pause playback in MPRIS2 Player")
    def get_icon_name(self):
        return "media-playback-start"

class Play (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Play"))
    def run(self):
        self.get_player().Play()
    def get_description(self):
        return _("Start playback in MPRIS2 Player")
    def get_icon_name(self):
        return "media-playback-start"

class Stop (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Stop"))
    def run(self):
        self.get_player().Stop()
    def get_description(self):
        return _("Stop playback in MPRIS2 Player")
    def get_icon_name(self):
        return "media-playback-stop"

class Pause (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Pause"))
    def run(self):
        self.get_player().Pause()
    def get_description(self):
        return _("Pause playback in MPRIS2 Player")
    def get_icon_name(self):
        return "media-playback-pause"

class Next (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Next"))
    def run(self):
        self.get_player().Next()
    def get_description(self):
        return _("Jump to next track in MPRIS2 Player")
    def get_icon_name(self):
        return "media-skip-forward"

class Previous (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Previous"))
    def run(self):
        self.get_player().Previous()
    def get_description(self):
        return _("Jump to previous track in MPRIS2 Player")
    def get_icon_name(self):
        return "media-skip-backward"

class Quit (Mpris2RunnableLeaf):
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Quit"))
    def run(self):
        self.get_rootobject().Quit()
    def get_description(self):
        return _("Quit the MPRIS2 Player")
    def get_gicon(self):
        return icons.ComposedIconSmall("applications-multimedia", self.get_icon_name())
    def get_icon_name(self):
        return "application-exit"

class ShowPlaying (Mpris2RunnableLeaf):
    '''
    notification_id will be used to store the id of the notification displaying the track information
    this way we can replace the notification if the user runs this leaf a few times
    '''
    notification_id = 0

    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Show Playing"))
    def run(self):
        meta = self.get_property('Metadata')
        pretty.print_debug(__name__, meta)
        title = meta.get('xesam:title', 'unknown')
        icon = meta.get('mpris:artUrl', 'applications-multimedia')
        ShowPlaying.notification_id = uiutils.show_notification(title, self.format_metadata(meta), icon, ShowPlaying.notification_id)
    def get_description(self):
        return _("Show information about the current track in MPRIS2 Player")
    def get_icon_name(self):
        return "applications-multimedia"

    @staticmethod
    def format_metadata(meta):
        album = meta.get('xesam:album', 'unknown')
        artist = 'unknown'
        artists = meta.get('xesam:artist', [])
        length = meta.get('mpris:length', 0)
        # see http://stackoverflow.com/a/539360/306800
        length = length / 1000000 # mpris gives the length in microseconds
        hours, remainder = divmod(length, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration = '%d:%02d:%02d' % (hours, minutes, seconds)
        if len(artist) > 0:
            artist = artists[0]
        track_nr = meta.get('xesam:trackNumber', 'unknown')
        return """by <i>{0}</i>
from <i>{1}</i>
track: {2} - duration: {3}""".format(artist, album, track_nr, duration)

class Mpris2Source (AppLeafContentMixin, Source):
    appleaf_content_id = 'mpris2'
    def __init__(self):
        Source.__init__(self, _("MPRIS2"))
    def get_items(self):
        yield PlayPause()
        yield Next()
        yield Previous()
        yield Play()
        yield Stop()
        yield Pause()
        yield Quit()
        yield ShowPlaying()
    def provides(self):
        yield RunnableLeaf
    def get_description(self):
        return __description__
    def get_icon_name(self):
        return "applications-multimedia"
