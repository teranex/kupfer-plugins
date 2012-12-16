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
from kupfer import utils, icons, pretty

class Mpris2RunnableLeaf (RunnableLeaf):
    def get_player(self):
        bus = dbus.SessionBus()
        target = None
        dbusObj = bus.get_object('org.freedesktop.DBus', '/')
        for name in dbusObj.ListNames(dbus_interface='org.freedesktop.DBus'):
            if name.startswith('org.mpris.MediaPlayer2.'):
                target = name
                break
        targetObject = bus.get_object(target, '/org/mpris/MediaPlayer2')
        player = dbus.Interface(targetObject, dbus_interface='org.mpris.MediaPlayer2.Player')
        return player

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
    def provides(self):
        yield RunnableLeaf
    def get_description(self):
        return __description__
    def get_icon_name(self):
        return "media-playback-start"
