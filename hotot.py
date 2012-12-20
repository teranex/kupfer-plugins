"""
A plugin to control Hotot
"""

__kupfer_name__ = _("Hotot")
# __kupfer_sources__ = ("HototSource", )
__kupfer_actions__ = ("SendUpdate",)
__description__ = _("Control Hotot")
__version__ = "0.1"
__author__ = "Jeroen Budts <jeroen@budts.be>"

import dbus

from kupfer.objects import Action, TextLeaf
from kupfer import pretty

# class HototSource (AppLeafContentMixin, Source):
#     appleaf_content_id = "hotot"
#     def __init__(self):
#         Source.__init__(self, _("Hotot"))
#     def get_items(self):
#         []
#     def provides(self):
#         []
#     def get_description(self):
#         return __description__
#     def get_icon_name(self):
#         return 'hotot'

class SendUpdate (Action):
    def __init__(self):
        Action.__init__(self, _("Send Update"))

    def wants_context(self):
        return True

    def activate(self, leaf, ctx):
        pretty.print_debug(__name__, leaf.object)

        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.hotot.service', '/org/hotot/service')
        obj = dbus.Interface(dbusObj, dbus_interface='org.hotot.service')
        obj.update_status(leaf.object)

    def item_types(self):
        yield TextLeaf

    def get_description(self):
        return _("Send an update to Twitter with Hotot")

    def get_icon_name(self):
        return 'hotot'
