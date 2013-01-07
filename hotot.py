"""
A plugin to control Hotot
"""

__kupfer_name__ = _("Hotot")
__kupfer_actions__ = ("SendUpdate", "Show", "Quit", )
__description__ = _("Control Hotot")
__version__ = "1.0"
__author__ = "Jeroen Budts <jeroen@budts.be>"

import dbus

from kupfer.objects import Action, TextLeaf, AppLeaf
from kupfer import pretty, plugin_support, launch

plugin_support.check_dbus_connection()

def get_hotot():
    try:
        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.hotot.service', '/org/hotot/service')
        return dbus.Interface(dbusObj, dbus_interface='org.hotot.service')
    except dbus.exceptions.DBusException, err:
        pretty.print_debug(err)
    return None


class SendUpdate (Action):
    ''' Create a Tweet with Hotot '''
    def __init__(self):
        Action.__init__(self, _("Send Update"))

    def activate(self, leaf):
        pretty.print_debug(__name__, leaf.object)
        text = leaf.object.replace('"', '\\"')
        pretty.print_debug(__name__, "SendUpdate: "+text)
        get_hotot().update_status(text)

    def item_types(self):
        yield TextLeaf

    def get_description(self):
        return _("Send an update to Twitter with Hotot")

    def get_icon_name(self):
        return 'hotot'

    def valid_for_item(self, item):
        return get_hotot() != None


class HototAction (Action):
    def __init__(self, action, func):
        self.action = action
        self.func = func
        Action.__init__(self, _(action))

    def get_description(self):
        return _(self.action + ' the running Hotot instance')

    def activate(self, leaf):
        self.func()

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, item):
        return item.get_id() == 'hotot' and get_hotot() != None


class Show (HototAction):
    def __init__(self):
        HototAction.__init__(self, 'Show', lambda: get_hotot().show())

    def get_icon_name(self):
        return "go-jump"

    def valid_for_item(self, item):
        return super(Show, self).valid_for_item(item) \
               and not launch.application_is_running('hotot')


class Quit (HototAction):
    def __init__(self):
        HototAction.__init__(self, 'Quit', lambda: get_hotot().quit())

    def get_icon_name(self):
        return "application-exit"
