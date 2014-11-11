__kupfer_name__ = _("Media Players")
__kupfer_sources__ = ("MediaPlayerCommandsSource", )
__kupfer_actions__ = ("PlayPause", "Play", "Pause", "Stop", "Next",
                      "Previous", "Quit", "ShowPlaying", "Raise", "Open",
                      "Seek", "ActivatePlaylist")
__description__ = _("Control any MPRIS2 media player")
__version__ = ""
__author__ = "Jeroen Budts"

import dbus

from kupfer import pretty, plugin_support, icons, uiutils
from kupfer.objects import Source, Leaf, Action, AppLeaf
from kupfer.weaklib import dbus_signal_connect_weakly
from gio.unix import DesktopAppInfo
from gio import FileIcon, File

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
    def playlists(self):
        return dbus.Interface(self._dbus_obj, dbus_interface='org.mpris.MediaPlayer2.Playlists')

    @property
    def supports_playlists(self):
        try:
            self.get_playlists_property('PlaylistCount')
            return True
        except:
            return False

    @property
    def name(self):
        return self.get_root_property('DesktopEntry')

    @property
    def is_playing(self):
        playback_status = self.get_player_property('PlaybackStatus')
        return playback_status == 'Playing'

    def _get_property(self, target, property_name):
        properties_manager = dbus.Interface(self._dbus_obj, 'org.freedesktop.DBus.Properties')
        return properties_manager.Get(target, property_name)

    def get_player_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2.Player', property_name)

    def get_root_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2', property_name)

    def get_playlists_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2.Playlists', property_name)

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
        dbus_signal_connect_weakly(dbus.Bus(), 'PropertiesChanged', self._properties_changed,
                                   dbus_interface='org.freedesktop.DBus.Properties')

    def _signal_update(self, *args):
        if len(args) > 0 and args[0].startswith('org.mpris.MediaPlayer2.'):
            self.reindex()

    def _properties_changed(self, *args):
        if len(args) > 1 and args[0].startswith('org.mpris.MediaPlayer2.'):
            if 'PlaybackStatus' in args[1] and args[1]['PlaybackStatus'] == 'Playing':
                # a media player started playing. Set it as the active player
                # find the player and store it for later use
                self._store_playing_player()

    def _store_playing_player(self):
        for player_name in self.active_players:
            player = self.active_players[player_name]
            if player.is_playing:
                self.last_used_player = player_name

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
        self.last_used_player = ""
        self._store_playing_player()

    @property
    def players(self):
        # then return all the other players
        for player in self.active_players:
            if player != self.last_used_player:
                pretty.print_debug(__name__, "other player: " + player)
                yield player
        # if there is an active player, return that last so it will be
        # suggested
        if self.last_used_player:
            pretty.print_debug(__name__, "active player: " + self.last_used_player)
            yield self.last_used_player

    def get_player(self, name):
        return self.active_players[name]

    def has_player(self, name):
        return name in self.active_players


def format_metadata(meta):
    # TODO: check icon and download local cache (for spotify)
    album = meta.get('xesam:album', _('unknown'))
    artist = _('unknown')
    artists = meta.get('xesam:artist', [])
    length = meta.get('mpris:length', 0)
    # see http://stackoverflow.com/a/539360/306800
    length = length / 1000000  # mpris gives the length in microseconds
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
        leaf.run_on_player(self._player)

    def get_gicon(self):
        return self._player.icon

    def get_description(self):
        return self._player.description


class MediaPlayerAction (Action):
    def __init__(self, leaf):
        self.leaf = leaf
        super(MediaPlayerAction, self).__init__(leaf.name)

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, leaf):
        pretty.print_debug(__name__, "Checking %s action for %s " % (self.name, leaf.get_id()))
        return media_players_registry.has_player(leaf.get_id())

    def activate(self, leaf):
        pretty.print_debug(__name__, "activating %s action" % self.name)
        player = media_players_registry.get_player(leaf.get_id())
        self.run_action(player)

    def get_description(self):
        return self.leaf.get_description()

    def get_icon_name(self):
        return self.leaf.get_icon_name()

    def get_gicon(self):
        return self.leaf.get_gicon()

    def run_action(self, player):
        self.leaf.run_on_player(player)


class PlayPause (MediaPlayerAction):
    def __init__(self):
        super(PlayPause, self).__init__(PlayPauseLeaf())


class Play (MediaPlayerAction):
    def __init__(self):
        super(Play, self).__init__(PlayLeaf())


class Pause (MediaPlayerAction):
    def __init__(self):
        super(Pause, self).__init__(PauseLeaf())


class Stop (MediaPlayerAction):
    def __init__(self):
        super(Stop, self).__init__(StopLeaf())


class Next (MediaPlayerAction):
    def __init__(self):
        super(Next, self).__init__(NextLeaf())


class Previous (MediaPlayerAction):
    def __init__(self):
        super(Previous, self).__init__(PreviousLeaf())


class Quit (MediaPlayerAction):
    def __init__(self):
        super(Quit, self).__init__(QuitLeaf())


class ShowPlaying (MediaPlayerAction):
    def __init__(self):
        super(ShowPlaying, self).__init__(ShowPlayingLeaf())


class Raise (MediaPlayerAction):
    def __init__(self):
        super(Raise, self).__init__(RaiseLeaf())


class Seek (Action):
    def __init__(self):
        Action.__init__(self, _("Seek"))

    def get_icon_name(self):
        return "media-seek-forward"

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, leaf):
        return media_players_registry.has_player(leaf.get_id())

    def get_description(self):
        return "Seek the currently playing track"

    def requires_object(self):
        return True

    def object_types(self):
        yield SeekTimeLeaf

    def object_source(self, for_item):
        return SeekTimesSource()

    def activate(self, leaf, iobj):
        player = media_players_registry.get_player(leaf.get_id())
        player.player.Seek(iobj.object * 1000000)


class ActivatePlaylist (Action):
    def __init__(self):
        Action.__init__(self, _("Activate playlist"))

    def get_icon_name(self):
        return "audio-x-playlist"

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, leaf):
        if media_players_registry.has_player(leaf.get_id()):
            player = media_players_registry.get_player(leaf.get_id())
            return player.supports_playlists
        return False

    def get_description(self):
        return "Switch to another playlist"

    def requires_object(self):
        return True

    def object_types(self):
        yield PlaylistLeaf

    def object_source(self, for_item):
        return PlaylistSource(for_item.get_id())

    def activate(self, leaf, iobj):
        pretty.print_debug(__name__, "activating playlist")
        player = media_players_registry.get_player(leaf.get_id())
        player.playlists.ActivatePlaylist(iobj.object)


# {{{ Leafs
class MediaPlayerCommandLeaf (Leaf):
    '''a media player leaf'''

    def run_on_player(self, player):
        raise NotImplementedError('Subclasses should implement this method')

    def get_actions(self):
        return [RunningMediaPlayerTarget(player) for player in media_players_registry.players]


class PlayPauseLeaf (MediaPlayerCommandLeaf):
    '''play/pause the media player'''
    def __init__(self):
        Leaf.__init__(self, [], _("Play/Pause"))

    def get_icon_name(self):
        return "media-playback-start"

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "media-playback-pause")

    def get_description(self):
        return _("Resume/Pause playback in the media player")

    def run_on_player(self, player):
        player.player.PlayPause()


class PlayLeaf (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Play"))

    def get_icon_name(self):
        return "media-playback-start"

    def get_description(self):
        return _("Start playback in the media player")

    def run_on_player(self, player):
        player.player.Play()


class StopLeaf (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Stop"))

    def get_icon_name(self):
        return "media-playback-stop"

    def get_description(self):
        return _("Stop playback in the media player")

    def run_on_player(self, player):
        player.player.Stop()


class PauseLeaf (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Pause"))

    def get_icon_name(self):
        return "media-playback-pause"

    def get_description(self):
        return _("Pause playback in the media player")

    def run_on_player(self, player):
        player.player.Pause()


class NextLeaf (MediaPlayerCommandLeaf):
    '''skip to next track in media player'''
    def __init__(self):
        Leaf.__init__(self, [], _("Next"))

    def get_icon_name(self):
        return "media-skip-forward"

    def get_description(self):
        return _("Jump to the next track in the media player")

    def run_on_player(self, player):
        player.player.Next()


class PreviousLeaf (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Previous"))

    def get_icon_name(self):
        return "media-skip-backward"

    def get_description(self):
        return _("Jump to the previous track in the media player")

    def run_on_player(self, player):
        player.player.Previous()


class QuitLeaf (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Quit player"))

    def get_icon_name(self):
        return "application-exit"

    def get_description(self):
        return _("Quit the media player")

    def run_on_player(self, player):
        player.root.Quit()


class ShowPlayingLeaf (MediaPlayerCommandLeaf):
    notification_id = 0

    def __init__(self):
        Leaf.__init__(self, [], _("Show Playing"))

    def get_description(self):
        return _("Show information about the current track in the media player")

    def get_gicon(self):
        return icons.ComposedIcon("dialog-information", "audio-x-generic")

    def get_icon_name(self):
        return "dialog-information"

    def run_on_player(self, player):
        # TODO: more error checking (for example when no track is selected in Banshee)
        meta = player.get_player_property('Metadata')
        if len(meta) > 0:
            pretty.print_debug(__name__, meta)
            title = meta.get('xesam:title', _('unknown'))
            icon = meta.get('mpris:artUrl', 'applications-multimedia')
            ShowPlaying.notification_id \
                = uiutils.show_notification(title,
                                            format_metadata(meta).replace('&', '&amp;'),
                                            icon,
                                            ShowPlayingLeaf.notification_id)


class RaiseLeaf (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Raise player"))

    def get_description(self):
        return _("Raise the media player")

    def get_icon_name(self):
        return "go-jump"

    def run_on_player(self, player):
        player.root.Raise()


class SeekTimeLeaf (Leaf):
    '''A leaf to be selected as indirect object, providing the number of seconds to seek'''
    def __init__(self, time):
        name = "%d seconds %s" % (abs(time), ('forward' if time > 0 else 'backward'))
        Leaf.__init__(self, time, name)

    def get_icon_name(self):
        return "gnome-set-time"


class PlaylistLeaf (Leaf):
    '''A leaf to represent a playlist'''
    def __init__(self, playlist_id, playlist_name, icon):
        Leaf.__init__(self, playlist_id, playlist_name)
        self.icon = icon

    def get_gicon(self):
        return FileIcon(File(self.icon))
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
        yield RaiseLeaf()
        yield PlayPauseLeaf()
        yield PlayLeaf()
        yield PauseLeaf()
        yield StopLeaf()
        yield NextLeaf()
        yield PreviousLeaf()
        yield ShowPlayingLeaf()


class SeekTimesSource (Source):
    TIMES = (-60, -30, -10, -5, 5, 10, 30, 60)

    def __init__(self):
        Source.__init__(self, _("Seek times"))

    def provides(self):
        yield SeekTimeLeaf

    def get_items(self):
        return [SeekTimeLeaf(time) for time in SeekTimesSource.TIMES]


class PlaylistSource (Source):
    def __init__(self, player):
        Source.__init__(self, _("Playlists"))
        self.player = media_players_registry.get_player(player)

    def provides(self):
        yield PlaylistLeaf

    def should_sort_lexically(self):
        return True

    def get_items(self):
        playlists = self.player.playlists.GetPlaylists(0, 100, 'Alphabetical', False)
        return [PlaylistLeaf(p[0], p[1], p[2]) for p in playlists]

# vim: fdm=marker
