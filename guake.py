__kupfer_name__ = _("Guake")
__kupfer_actions__ = ("RunInCurrentTab", "RunInNewTab",)
__description__ = _("Execute commands in Guake")
__version__ = ""
__author__ = "Jeroen Budts"

import dbus
from kupfer import plugin_support, pretty, icons
from kupfer.objects import Action, TextLeaf, FileLeaf
from kupfer.obj.fileactions import is_good_executable
from gio.unix import DesktopAppInfo
from gio import FileIcon, File

plugin_support.check_dbus_connection()


def get_guake():
    try:
        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.guake.RemoteControl', '/org/guake/RemoteControl')
        return dbus.Interface(dbusObj, dbus_interface='org.guake.RemoteControl')
    except dbus.exceptions.DBusException, err:
        pretty.print_debug(err)
    return None


class RunInCurrentTab (Action):
    def __init__(self):
        Action.__init__(self, _("Run in current Guake tab"))

    def get_description(self):
        return _("Run the command in the currently active Guake tab")

    def get_gicon(self):
        # TODO: this is probably not how it should be done...
        return FileIcon(File('/usr/share/pixmaps/guake/guake.svg'))
        # return DesktopAppInfo('guake.desktop').get_icon()

    def activate(self, leaf):
        get_guake().execute_command(leaf.object)

    def item_types(self):
        yield FileLeaf
        yield TextLeaf

    def valid_for_item(self, item):
        if isinstance(item, FileLeaf):
            return not item.is_dir() and item.is_valid() and is_good_executable(item)
        return True


class RunInNewTab (Action):
    def __init__(self):
        Action.__init__(self, _("Run in new Guake tab"))

    def get_description(self):
        return _("Run the command in a new Guake tab")

    # def get_gicon(self):
        # TODO: this is probably not how it should be done...
        # guake_icon = FileIcon(File('/usr/share/pixmaps/guake/guake.svg'))
        # guake_icon = DesktopAppInfo('guake.desktop').get_icon()
        # return icons.ComposedIconSmall(guake_icon, "add")
    
    def get_icon_name(self):
        return "add"

    def activate(self, leaf):
        get_guake().add_tab('~')
        get_guake().execute_command(leaf.object)

    def item_types(self):
        yield FileLeaf
        yield TextLeaf

    def valid_for_item(self, item):
        if isinstance(item, FileLeaf):
            return not item.is_dir() and item.is_valid() and is_good_executable(item)
        return True
