__kupfer_name__ = _("Hamster")
__description__ = _("Control the Hamster time tracker")
__author__ = "Jeroen Budts"
__kupfer_actions__ = ("Toggle", "StartActivity", "StartActivityWithTags", "StartActivityWithDescription",
                      "Overview", "Statistics", "Preferences",)
__kupfer_sources__ = ("HamsterSource", )

import dbus

from kupfer.objects import Action, AppLeaf, Source, Leaf, RunnableLeaf, SourceLeaf, TextLeaf
from kupfer import pretty, plugin_support, icons, uiutils
from kupfer.obj.apps import AppLeafContentMixin
from kupfer.objects import OperationError
from kupfer.weaklib import dbus_signal_connect_weakly
from kupfer import utils
import time

__kupfer_settings__ = plugin_support.PluginSettings(
    {
        "key": "toplevel_activities",
        "label": _("Include activities in top level"),
        "type": bool,
        "value": True,
    },
    {
        "key": "return_started_facts",
        "label": _("When starting an activity immediately re-open Kupfer with the new activity focused. "
                   "This will let you easily further modify the start and endtime, tags and description."),
        "type": bool,
        "value": True,
    }
)

# TODO: add to README.md (XXX: describe patch needed)
# TODO: timezones + daylight savings time correct?

HAMSTER_APPNAMES = ("hamster-indicator", "hamster-time-tracker", )

plugin_support.check_dbus_connection()


def get_hamster():
    try:
        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.gnome.Hamster', '/org/gnome/Hamster')
        return dbus.Interface(dbusObj, dbus_interface='org.gnome.Hamster')
    except dbus.exceptions.DBusException, err:
        pretty.print_debug(err)
    return None


def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    timestr = '%dmin' % minutes
    if hours > 0:
        timestr = ('%dh ' % hours) + timestr
    return timestr

def format_time(seconds):
    tm = time.gmtime(seconds)
    return time.strftime("%H:%M", tm)


def format_fact_string(activity, category=None, description=None, tags=None):
    # TODO: use whenever possible
    fact = activity
    if category:
        fact += "@" + category
    if description or tags:
        fact += ','
    if description:
        fact += description
    if tags:
        tags = ['#' + str(t) for t in tags]
        fact += ' ' + ' '.join(tags)
    return fact


def parse_time(timestr):
    parsed = time.strptime(timestr, "%H:%M")
    now = time.localtime()
    result = time.struct_time((now.tm_year, now.tm_mon, now.tm_mday, parsed.tm_hour, parsed.tm_min,
                               0, now.tm_wday, now.tm_yday, now.tm_isdst))
    return time.mktime(result) - time.timezone


class Toggle (Action):
    def __init__(self):
        Action.__init__(self, _("Open / Close"))

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, item):
        return item.get_id() in HAMSTER_APPNAMES and get_hamster() is not None

    def activate(self, leaf):
        get_hamster().Toggle()

    def get_description(self):
        return _("Open or close Hamster")

    def get_icon_name(self):
        return 'go-jump'


class HamsterCmdAction (Action):
    def __init__(self, cmd, name):
        Action.__init__(self, name)
        self.cmd = cmd

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, item):
        return item.get_id() in HAMSTER_APPNAMES and get_hamster() is not None

    def activate(self, leaf):
        try:
            args = ['hamster-time-tracker', self.cmd]
            utils.spawn_async_raise(args)
        except utils.SpawnError as exc:
            raise OperationError(exc)


class Overview (HamsterCmdAction):
    def __init__(self):
        HamsterCmdAction.__init__(self, 'overview', _("Show Overview"))

    def get_description(self):
        return _("Open the overview window of Hamster")

    def get_icon_name(self):
        return "applications-versioncontrol"


class Statistics (HamsterCmdAction):
    def __init__(self):
        HamsterCmdAction.__init__(self, 'statistics', _("Show Statistics"))

    def get_description(self):
        return _("Show the Hamster statistics window")

    def get_icon_name(self):
        return "emblem-sales"


class Preferences (HamsterCmdAction):
    def __init__(self):
        HamsterCmdAction.__init__(self, 'preferences', _("Show Preferences"))

    def get_description(self):
        return _("Show the Hamster preferences window")

    def get_icon_name(self):
        return "emblem-system"


class StartActivity (Action):
    def __init__(self):
        Action.__init__(self, _("Start activity"))

    def item_types(self):
        yield TextLeaf
        yield ActivityLeaf

    def activate(self, leaf):
        fact_id = get_hamster().AddFact(leaf.object, time.time() - time.timezone, 0, False)
        if __kupfer_settings__["return_started_facts"]:
            fact = get_hamster().GetFact(fact_id)
            return FactLeaf(fact)

    def get_description(self):
        return _("Start tracking the activity in Hamster")

    def get_icon_name(self):
        return "media-playback-start"

    def has_result(self):
        return __kupfer_settings__["return_started_facts"]


class StartActivityWithTags (Action):
    def __init__(self):
        Action.__init__(self, _("Start activity with tags"))

    def item_types(self):
        yield TextLeaf
        yield ActivityLeaf

    def activate(self, leaf, iobj):
        return self.activate_multiple([leaf], [iobj])

    def activate_multiple(self, leafs, iobjs):
        # use the first direct object, as it makes no sense to use more than one
        # direct object for this action
        leaf = leafs[0]
        tags = ['#' + str(io.object) for io in iobjs]
        fact = leaf.object + ', ' + ' '.join(tags)
        pretty.print_debug(__name__, "Adding fact: " + fact)
        fact_id = get_hamster().AddFact(fact, time.time() - time.timezone, 0, False)
        if __kupfer_settings__["return_started_facts"]:
            fact = get_hamster().GetFact(fact_id)
            return FactLeaf(fact)

    def get_description(self):
        return _("Start tracking the activity with tags in Hamster")

    def get_icon_name(self):
        return "media-playback-start"

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "tag-new")

    def requires_object(self):
        return True

    def object_types(self):
        yield TagLeaf
        yield TextLeaf

    def object_source(self, for_item):
        return TagsSource()

    def has_result(self):
        return __kupfer_settings__["return_started_facts"]


class StartActivityWithDescription (Action):
    def __init__(self):
        Action.__init__(self, _("Start activity with description"))

    def item_types(self):
        yield TextLeaf
        yield ActivityLeaf

    def activate(self, leaf, iobj):
        fact_id = get_hamster().AddFact(leaf.object + ', ' + iobj.object, time.time() - time.timezone, 0, False)
        if __kupfer_settings__["return_started_facts"]:
            fact = get_hamster().GetFact(fact_id)
            return FactLeaf(fact)

    def get_description(self):
        return _("Start tracking the activity with description in Hamster")

    def get_icon_name(self):
        return "media-playback-start"

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "txt")

    def requires_object(self):
        return True

    def object_types(self):
        yield TextLeaf

    def has_result(self):
        return __kupfer_settings__["return_started_facts"]


class FactEditAction (Action):
    '''abstract action to edit properties of a fact'''
    def item_types(self):
        yield FactLeaf

    def has_result(self):
        return True

    def requires_object(self):
        return True

    def object_types(self):
        yield TextLeaf

    def get_icon_name(self):
        return "gtk-edit"

    def update_fact(self, leaf):
        fact = format_fact_string(leaf.activity, leaf.category, leaf.description, leaf.tags)
        pretty.print_debug(__name__, "Going to update fact %d: %s" % (leaf.fact_id, fact))
        leaf.fact_id = get_hamster().UpdateFact(leaf.fact_id, fact, leaf.starttime, leaf.endtime, False)
        return leaf


class ChangeStartTime (FactEditAction):
    def __init__(self):
        Action.__init__(self, _("Change start time"))

    def get_description(self):
        return _("Change the start time (format: hh:mm) of a Hamster activty")

    def activate(self, leaf, iobj):
        leaf.starttime = parse_time(iobj.object)
        return self.update_fact(leaf)

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "media-playback-start")


class ChangeEndTime (FactEditAction):
    def __init__(self):
        Action.__init__(self, _("Change end time"))

    def get_description(self):
        return _("Change the end time (format: hh:mm) of a Hamster activty")

    def activate(self, leaf, iobj):
        leaf.endtime = parse_time(iobj.object)
        return self.update_fact(leaf)

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "media-playback-stop")


class ChangeDescription (FactEditAction):
    def __init__(self):
        Action.__init__(self, _("Change the description"))

    def get_description(self):
        return _("Change the description of a Hamster activity")

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "txt")

    def activate(self, leaf, iobj):
        leaf.description = iobj.object
        return self.update_fact(leaf)


class ChangeTags (FactEditAction):
    def __init__(self):
        Action.__init__(self, _("Change the tags"))

    def get_description(self):
        return _("Change the tags of a Hamster activity")

    def get_gicon(self):
        return icons.ComposedIconSmall(self.get_icon_name(), "tag-new")

    def activate(self, leaf, iobj):
        return self.activate_multiple([leaf], [iobj])

    def activate_multiple(self, leafs, iobjs):
        # we only care about the first selected leaf
        leaf = leafs[0]
        leaf.tags = [str(io.object) for io in iobjs]
        return self.update_fact(leaf)

    def object_types(self):
        yield TagLeaf
        yield TextLeaf

    def object_source(self, for_item):
        return TagsSource()


class Remove (Action):
    def __init__(self):
        Action.__init__(self, _("Remove"))

    def get_description(self):
        return _("Remove the Hamster activity")

    def get_icon_name(self):
        return "remove"

    def item_types(self):
        yield FactLeaf

    def activate(self, leaf):
        get_hamster().RemoveFact(leaf.fact_id)


class StopTrackingLeaf (RunnableLeaf):
    #TODO: this only makes sense when an activity is being tracked
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Stop tracking"))

    def get_description(self):
        return _("Stop tracking the current activity")

    def get_gicon(self):
        return icons.ComposedIconSmall("hamster-applet", self.get_icon_name())

    def get_icon_name(self):
        return "media-playback-stop"

    def run(self):
        get_hamster().StopTracking(time.time() - time.timezone)


class ShowHamsterInfo (RunnableLeaf):
    notification_id = 0

    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Show Hamster Info"))

    def get_description(self):
        return _("Show hamster information for today")

    def get_icon_name(self):
        return "info"

    def run(self):
        facts = get_hamster().GetTodaysFacts()
        total = 0
        current = None
        for f in facts:
            end = f[2]
            if end == 0:
                current = f
                end = time.time() - time.timezone
            duration = end - f[1]
            total += duration
        notification_body = "Total time today: %s" % format_duration(total)
        if current:
            notification_body += "\nCurrent: %s@%s (%s)" % (current[4], current[6],
                                                            format_duration(time.time() - time.timezone - current[1]))
        ShowHamsterInfo.notification_id = uiutils.show_notification('Hamster Info',
                                          notification_body, 'hamster-indicator', ShowHamsterInfo.notification_id)


class ActivityLeaf (Leaf):
    def __init__(self, activity):
        Leaf.__init__(self, activity, activity)

    def get_actions(self):
        yield StartActivity()
        yield StartActivityWithTags()
        yield StartActivityWithDescription()

    def get_icon_name(self):
        return "hamster-indicator"

    def get_description(self):
        return self.name


class TagLeaf (Leaf):
    def __init__(self, tag_name):
        Leaf.__init__(self, tag_name, tag_name)

    def get_icon_name(self):
        return "tag-new"


class FactLeaf (Leaf):
    def __init__(self, fact):
        name = fact[4]
        if fact[6]:
            name += "@" + fact[6]
        Leaf.__init__(self, fact[0], name)
        pretty.print_debug(__name__, "creating fact %d: %s" % (fact[0], name))
        self.fact_id = fact[0]
        self.activity = fact[4]
        self.category = fact[6]
        self.starttime = fact[1]
        self.endtime = fact[2]
        self.description = fact[3]
        self.tags = fact[7]

    def get_icon_name(self):
        return "hamster-indicator"

    def get_actions(self):
        yield ChangeStartTime()
        yield ChangeEndTime()
        yield ChangeDescription()
        yield ChangeTags()
        yield Remove()

    def get_description(self):
        start = format_time(self.starttime)
        end = ''
        if self.endtime:
            end = format_time(self.endtime)
        return "%s - %s" % (start, end)


class ActivitiesSource (Source):
    def __init__(self):
        Source.__init__(self, _("Hamster Activities"))
        self.activities = get_hamster().GetActivities('')

    def provides(self):
        yield ActivityLeaf

    def get_items(self):
        for act in self.activities:
            activity = str(act[0])
            if act[1]:
                activity += '@' + str(act[1])
            yield ActivityLeaf(activity)

    def get_icon_name(self):
        return "hamster-applet"

    def get_description(self):
        return _("All known activities in Hamster time tracker")

    def get_actions(self):
        return ()


class TagsSource (Source):
    def __init__(self):
        Source.__init__(self, _("Hamster Tags"))

    def provides(self):
        yield TagLeaf

    def get_items(self):
        return [TagLeaf(t[1]) for t in get_hamster().GetTags(True)]


class FactsSource (Source):
    # TODO: make sure the same fact with different start and endtimes is not
    # filtered out (=seen as duplicate), it should be available twice in that
    # case, with different start/end times
    def __init__(self):
        Source.__init__(self, _("Hamster Facts"))

    def get_description(self):
        return _("Facts for today")

    def get_icon_name(self):
        return "hamster-applet"

    def provides(self):
        yield FactLeaf

    def get_actions(self):
        return ()

    def get_items(self):
        for fact in get_hamster().GetTodaysFacts():
            leaf = FactLeaf(fact)
            yield leaf


class HamsterSource (AppLeafContentMixin, Source):
    appleaf_content_id = HAMSTER_APPNAMES

    def __init__(self):
        Source.__init__(self, _("Hamster"))

    def _facts_changed(self, *args):
        pretty.print_debug(__name__, 'facts changed')
        self.mark_for_update()

    def initialize(self):
        dbus_signal_connect_weakly(dbus.Bus(), 'FactsChanged', self._facts_changed,
                                   dbus_interface='org.gnome.Hamster')

    def provides(self):
        yield StopTrackingLeaf
        yield ShowHamsterInfo
        yield SourceLeaf
        yield ActivityLeaf

    def get_items(self):
        yield StopTrackingLeaf()
        yield ShowHamsterInfo()
        activities_source = ActivitiesSource()
        yield SourceLeaf(activities_source)
        facts_source = FactsSource()
        yield SourceLeaf(facts_source)
        if __kupfer_settings__["toplevel_activities"]:
            for leaf in activities_source.get_leaves():
                yield leaf

    def get_description(self):
        return _("Hamster time tracker")

    def get_icon_name(self):
        return "hamster-indicator"
