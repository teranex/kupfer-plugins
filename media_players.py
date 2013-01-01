__kupfer_name__ = _("Media Players")
__kupfer_sources__ = ("MediaPlayerCommandsSource", )
# __kupfer_actions__ = ("Play", )
__description__ = _("Control any MPRIS2 media player")
__version__ = "0.1"
__author__ = "Jeroen Budts <jeroen@budts.be>"

import dbus

from kupfer import pretty, plugin_support, icons, uiutils
from kupfer.objects import Source, Leaf, Action
from kupfer.obj.base import ActionGenerator
from kupfer.weaklib import dbus_signal_connect_weakly
from gio.unix import DesktopAppInfo

plugin_support.check_dbus_connection()

# {{{ supporting classes and functions
class MediaPlayer (object):
    def __init__(self, dbus_obj):
        self._dbus_obj = dbus_obj
        entry = self.get_root_property('DesktopEntry')
        # TODO: handle case of absent DesktopEntry (DesktopEntry is optional according to MPRIS2)
        self.desktop_app_info = DesktopAppInfo(entry + '.desktop')

    @property
    def root(self):
        return dbus.Interface(self._dbus_obj, dbus_interface='org.mpris.MediaPlayer2')

    @property
    def player(self):
        return dbus.Interface(self._dbus_obj, dbus_interface='org.mpris.MediaPlayer2.Player')

    @property
    def name(self):
        return self.get_root_property('DesktopEntry')

    def _get_property(self, target, property_name):
        properties_manager = dbus.Interface(self._dbus_obj, 'org.freedesktop.DBus.Properties')
        return properties_manager.Get(target, property_name)

    def get_player_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2.Player', property_name)

    def get_root_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2', property_name)

    @property
    def icon(self):
        return self.desktop_app_info.get_icon()

    @property
    def description(self):
        return self.desktop_app_info.get_description()


class MediaPlayersRegistry (object):
    def __init__(self):
        self.reindex()
        self._setup_monitor()

    def _setup_monitor(self):
        dbus_signal_connect_weakly(dbus.Bus(), 'NameOwnerChanged', self._signal_update,
                                   dbus_interface='org.freedesktop.DBus')

    def _signal_update(self, *args):
        if (len(args) > 0 and args[0].startswith('org.mpris.MediaPlayer2.')):
            self.reindex()

    def reindex(self):
        self.active_players = {}

        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.freedesktop.DBus', '/')
        for name in dbusObj.ListNames(dbus_interface='org.freedesktop.DBus'):
            if name.startswith('org.mpris.MediaPlayer2.'):
                pretty.print_debug(__name__, "discovered player: " + name)
                dbus_obj = bus.get_object(name, '/org/mpris/MediaPlayer2')
                player = MediaPlayer(dbus_obj)
                self.active_players[player.name] = player
                pretty.print_debug(__name__, "registered player: %s (%s)" % (player.name, player))

    @property
    def players(self):
        for player in self.active_players:
            yield player

    def get_player(self, name):
        return self.active_players[name]


def format_metadata(meta):
    # TODO: check icon and download local cache (for spotify)
    album = meta.get('xesam:album', _('unknown'))
    artist = _('unknown')
    artists = meta.get('xesam:artist', [])
    length = meta.get('mpris:length', 0)
    # see http://stackoverflow.com/a/539360/306800
    length = length / 1000000 # mpris gives the length in microseconds
    hours, remainder = divmod(length, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration = '%d:%02d:%02d' % (hours, minutes, seconds)
    if len(artist) > 0:
        artist = artists[0]
    track_nr = meta.get('xesam:trackNumber', _('unknown'))
    return """by <i>{0}</i>
from <i>{1}</i>
track: {2} - duration: {3}""".format(artist, album, track_nr, duration)
# }}}


media_players_registry = MediaPlayersRegistry()


class RunningMediaPlayerTarget (Action):
    def __init__(self, player):
        self._player = media_players_registry.get_player(player)
        Action.__init__(self, player)


    def activate(self, leaf):
        pretty.print_debug(__name__, "activating for " + self._player.name)
        leaf.do_command(self._player)

    def get_gicon(self):
        return self._player.icon

    def get_description(self):
        return self._player.description


# {{{ Leafs
class MediaPlayerCommandLeaf (Leaf):
    '''a media player leaf'''

    def do_command(self, player):
        raise NotImplementedError('Subclasses should implement this method')

    def get_actions(self):
        return [RunningMediaPlayerTarget(player) for player in media_players_registry.players]


class PlayPause (MediaPlayerCommandLeaf):
    '''play/pause the media player'''
    def __init__(self):
        Leaf.__init__(self, [], _("Play/Pause"))

    def get_icon_name(self):
        return "media-playback-start"

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "media-playback-pause")

    def get_description(self):
        return _("Resume/Pause playback in the media player")

    def do_command(self, player):
        player.player.PlayPause()


class Play (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Play"))

    def get_icon_name(self):
        return "media-playback-start"

    def get_description(self):
        return _("Start playback in the media player")

    def do_command(self, player):
        player.player.Play()


class Stop (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Stop"))

    def get_icon_name(self):
        return "media-playback-stop"

    def get_description(self):
        return _("Stop playback in the media player")

    def do_command(self, player):
        player.player.Stop()


class Pause (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Pause"))

    def get_icon_name(self):
        return "media-playback-pause"

    def get_description(self):
        return _("Pause playback in the media player")

    def do_command(self, player):
        player.player.Pause()


class Next (MediaPlayerCommandLeaf):
    '''skip to next track in media player'''
    def __init__(self):
        Leaf.__init__(self, [], _("Next"))

    def get_icon_name(self):
        return "media-skip-forward"

    def get_description(self):
        return _("Jump to the next track in the media player")

    def do_command(self, player):
        player.player.Next()


class Previous (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Previous"))

    def get_icon_name(self):
        return "media-skip-backward"

    def get_description(self):
        return _("Jump to the previous track in the media player")

    def do_command(self, player):
        player.player.Previous()


class Quit (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Quit"))

    def get_icon_name(self):
        return "application-exit"

    def get_description(self):
        return _("Quit the media player")

    def do_command(self, player):
        player.root.Quit()


class ShowPlaying (MediaPlayerCommandLeaf):
    notification_id = 0

    def __init__(self):
        Leaf.__init__(self, [], _("Show Playing"))

    def get_description(self):
        return _("Show information about the current track in the media player")

    def get_gicon(self):
        return icons.ComposedIcon("dialog-information", "audio-x-generic")

    def get_icon_name(self):
        return "dialog-information"

    def do_command(self, player):
        # TODO: more error checking (for example when no track is selected in Banshee)
        meta = player.get_player_property('Metadata')
        if (len(meta) > 0):
            pretty.print_debug(__name__, meta)
            title = meta.get('xesam:title', _('unknown'))
            icon = meta.get('mpris:artUrl', 'applications-multimedia')
            ShowPlaying.notification_id = uiutils.show_notification(title,
                                                                    format_metadata(meta).replace('&', '&amp;'),
                                                                    icon,
                                                                    ShowPlaying.notification_id)


class Raise (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Raise player"))

    def get_description(self):
        return _("Raise the media player")

    def get_icon_name(self):
        return "go-jump"

    def do_command(self, player):
        player.root.Raise()
# }}}


class MediaPlayerCommandsSource (Source):
    '''returns a list of all the commands available for running media players'''
    def __init__(self):
        Source.__init__(self, _("Media player commands"))

    def get_description(self):
        return _("Commands that can be executed on a media player, such as play, pause, next.")

    def get_icon_name(self):
        return "applications-multimedia"

    def provides(self):
        yield MediaPlayerCommandLeaf

    def get_items(self):
        yield Raise()
        yield PlayPause()
        yield Play()
        yield Pause()
        yield Stop()
        yield Next()
        yield Previous()
        yield ShowPlaying()
        yield Quit()

# vim: fdm=marker
