# utils.py
#
# Copyright 2021 adi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

def run_async(func):
    '''
    https://github.com/learningequality/ka-lite-gtk/blob/341813092ec7a6665cfbfb890aa293602fb0e92f/kalite_gtk/mainwindow.py
    http://code.activestate.com/recipes/576683-simple-threading-decorator/
    run_async(func): 
    function decorator, intended to make "func" run in a separate thread (asynchronously).
    Returns the created Thread object
    Example:
        @run_async
        def task1():
            do_something
        @run_async
        def task2():
            do_something_too
    '''
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        # Never return anything, idle_add will think it should re-run the
        # function because it's a non-False value.
        return None

    return async_func

def get_all_apps(app=None):
    ''' Function to get all apps installed on system using desktop files in standard locations for flatpak, snap, native '''
    import gi, os, re
    from gi.repository import Gio, GLib

    all_apps = {}
    app_name = None
    app_icon = None
    startup_wm_class = None
    no_display = None
    duplicate_app = 0

    flatpak_system_app_dirs = "/run/host/usr/share/applications"
    native_system_app_dirs = "/usr/share/applications"
    native_system_app_alt_dirs = "/usr/local/share/applications"
    native_system_flatpak_app_dirs = "/var/lib/flatpak/exports/share/applications"
    native_snap_app_dirs = "/var/lib/snapd/desktop"
    native_user_flatpak_app_dirs = os.path.join(GLib.get_home_dir(), ".local/share/flatpak/exports/share/applications")
    native_user_app_dirs = os.path.join(GLib.get_home_dir(), ".local/share/applications")
    desktop_file_dirs = [native_system_app_dirs, native_system_app_alt_dirs, flatpak_system_app_dirs, native_system_flatpak_app_dirs, native_snap_app_dirs, native_user_flatpak_app_dirs, native_user_app_dirs]

    for dir in desktop_file_dirs:
        if os.path.exists(dir):
            d = Gio.file_new_for_path(dir)
            files = d.enumerate_children("standard::*", 0)
            for desktop_file in files:
                if ".desktop" in desktop_file.get_name():

                    desktop_file_path = ""

                    if "application/x-desktop" in desktop_file.get_content_type():
                        desktop_file_path = os.path.join(dir, desktop_file.get_name())

                    if "inode/symlink" in desktop_file.get_content_type():
                        if ".local/share/flatpak/exports/share/applications" in dir:
                            desktop_file_path = os.path.join(GLib.get_home_dir(), ".local/share/flatpak", os.path.realpath(desktop_file.get_symlink_target()).replace("/home/", ""))

                    if desktop_file_path != "":
                        with open(desktop_file_path) as file:
                            lines = file.readlines()
                        contents = ''.join(lines)

                        app_name = re.search("Name=(?P<name>.+)*", contents)
                        app_icon = re.search("Icon=(?P<name>.+)*", contents)
                        startup_wm_class = re.search("StartupWMClass=(?P<name>.+)*", contents)
                        no_display = re.search("NoDisplay=(?P<name>.+)*", contents)

                        if app_name != None:
                            app_name = app_name.group(1)
                        else:
                            app_name = "unknown"
                        
                        if app_icon != None:
                            app_icon = app_icon.group(1)
                        else:
                            app_icon = "application-default-icon"

                        if startup_wm_class != None:
                            startup_wm_class = startup_wm_class.group(1)

                        if no_display != None:
                            no_display = no_display.group(1)
                            if 'true' in no_display:
                                no_display = True
                            else:
                                no_display = False

                        if app_name != None and app_icon != None:
                            if no_display is None or no_display is False:
                                if app_name in all_apps:
                                    duplicate_app += 1
                                    app_name = app_name + "#{0}".format(str(duplicate_app))
                                    all_apps[app_name] = [app_icon, startup_wm_class, no_display, desktop_file_path]
                                else:
                                    all_apps[app_name] = [app_icon, startup_wm_class, no_display, desktop_file_path]

    if app != None:
        return all_apps[app]
    else:
        # print("total apps:", len(all_apps))
        # for app in sorted(all_apps.keys()):
        #     if "code" in app.lower():
        #         print(app, all_apps[app])
        return all_apps

def get_active_appinfo_xlib():
    source_app = None
    source_icon = None
    all_apps = get_all_apps()

    import os
    import Xlib
    import Xlib.display

    display = Xlib.display.Display()
    root = display.screen().root

    NET_CLIENT_LIST = display.intern_atom('_NET_CLIENT_LIST')
    NET_DESKTOP_NAMES = display.intern_atom('_NET_DESKTOP_NAMES')
    NET_ACTIVE_WINDOW = display.intern_atom('_NET_ACTIVE_WINDOW')
    GTK_APPLICATION_ID = display.intern_atom('_GTK_APPLICATION_ID')
    WM_NAME = display.intern_atom('WM_NAME')
    WM_CLASS = display.intern_atom('WM_CLASS')
    BAMF_DESKTOP_FILE = display.intern_atom('_BAMF_DESKTOP_FILE')

    try:
        window_id = root.get_full_property(NET_ACTIVE_WINDOW, Xlib.X.AnyPropertyType).value[0]
        window = display.create_resource_object('window', window_id)
        
        for key in sorted(all_apps.keys()):

            app_name = key.split("#")[0].lower()
            app_icon = all_apps[key][0].lower()
            if all_apps[key][1] is not None:
                startup_wm_class = all_apps[key][1].lower()
            else:
                startup_wm_class = None
            desktop_file_path = all_apps[key][3].lower()

            if window.get_full_property(BAMF_DESKTOP_FILE, 0):
                bamf_desktop_file = window.get_full_property(BAMF_DESKTOP_FILE, 0).value.replace(b'\x00',b' ').decode("utf-8").lower()
                # print("utils.py: os.path.basename(bamf_desktop_file) == os.path.basename(desktop_file_path): {0}, xlib: {1}, all_apps: {2}".format(os.path.basename(bamf_desktop_file) == os.path.basename(desktop_file_path), os.path.basename(bamf_desktop_file), os.path.basename(desktop_file_path)))
                if os.path.basename(bamf_desktop_file) == os.path.basename(desktop_file_path):
                    if "#" in key:
                        source_app = key.split("#")[0]
                    else:
                        source_app = key
                    source_icon = all_apps[key][0]
                    break_point = "bamf_desktop_file"
                    break

            elif window.get_full_property(GTK_APPLICATION_ID, 0):
                gtk_application_id = window.get_full_property(GTK_APPLICATION_ID, 0).value.replace(b'\x00',b' ').decode("utf-8").lower()
                # print("utils.py: gtk_application_id == app_icon", gtk_application_id == app_icon, gtk_application_id, app_icon)
                if gtk_application_id == app_icon:
                    if "#" in key:
                        source_app = key.split("#")[0]
                    else:
                        source_app = key
                    source_icon = all_apps[key][0]
                    break_point = "gtk_application_id"
                    break

            elif window.get_full_property(WM_CLASS, 0):
                wm_class = window.get_full_property(WM_CLASS, 0).value.replace(b'\x00',b',').decode("utf-8")
                wm_class_keys = wm_class.split(",")
                for wm_class_key in wm_class_keys:
                    if wm_class_key != '':
                        # if wm_class_key.lower() == app_name or wm_class_key.lower() == startup_wm_class or wm_class_key.lower() in app_icon:
                        if wm_class_key.lower() in app_icon:
                            # print("utils.py: key: {0}, all_apps[key]: {1}".format(key, all_apps[key]))
                            # print("utils.py: wm_class_key.lower() == app_name: {0}, wm_class_key: {1}, app_name: {2}".format(wm_class_key.lower() == app_name, wm_class_key, app_name))
                            # print("utils.py: wm_class_key.lower() == startup_wm_class: {0}, wm_class_key: {1}, startup_wm_class: {2}".format(wm_class_key.lower() == startup_wm_class, wm_class_key, startup_wm_class))
                            # print("utils.py: wm_class_key.lower() in app_icon: {0}, wm_class_key: {1}, app_icon: {2}".format(wm_class_key.lower() in app_icon, wm_class_key, app_icon))
                            # print("\n")
                            if "#" in key:
                                source_app = key.split("#")[0]
                            else:
                                source_app = key
                            source_icon = all_apps[key][0]
                            break_point = "wm_class_key, {0}".format(all_apps[key])
                            break
                        elif "-" in wm_class_key:
                            # print("utils.py: wm_class_key.split("-")", wm_class_key.split("-"))
                            for wm_class_subkey in wm_class_key.split("-"):
                                if wm_class_subkey.lower() == app_name or wm_class_subkey.lower() == startup_wm_class or wm_class_subkey.lower() in app_icon:
                                    # print("utils.py: wm_class_subkey", wm_class_subkey)
                                    # print("utils.py: key, all_apps[key]", key, all_apps[key])
                                    # print("utils.py: wm_class_subkey.lower() == app_name", wm_class_subkey.lower() == app_name, wm_class_subkey)
                                    # print("utils.py: wm_class_subkey.lower() == startup_wm_class", wm_class_subkey.lower() == startup_wm_class, wm_class_subkey)
                                    # print("utils.py: wm_class_subkey.lower() in app_icon", wm_class_subkey.lower() in app_icon, wm_class_subkey)
                                    if "#" in key:
                                        source_app = key.split("#")[0]
                                    else:
                                        source_app = key
                                    source_icon = all_apps[key][0]
                                    break_point = "wm_class_subkey, {0}".format(all_apps[key])
                                    break

            elif window.get_full_property(WM_NAME, 0):
                wm_name = window.get_full_property(WM_NAME, 0).value.decode("utf-8").lower()
                if " - " in wm_name:
                    wm_name = wm_name.split(" - ")[-1]
                if startup_wm_class != None:
                    if wm_name == app_name or wm_name == startup_wm_class or wm_name in app_icon:
                        # print("utils.py: key, all_apps[key]", key, all_apps[key])
                        # print("utils.py: wm_name == app_name", wm_name == app_name, wm_name)
                        # print("utils.py: wm_name == startup_wm_class", wm_name == startup_wm_class, wm_name)
                        # print("utils.py: wm_name in app_icon", wm_name in app_icon, wm_name)
                        if "#" in key:
                            source_app = key.split("#")[0]
                        else:
                            source_app = key
                        source_icon = all_apps[key][0]
                        break_point = "wm_name, {0}".format(all_apps[key])
                        break
            
        if source_app is None and source_icon is None:
            workspace = root.get_full_property(NET_DESKTOP_NAMES, Xlib.X.AnyPropertyType).value.replace(b'\x00',b'').decode("utf-8")
            source_app = workspace + ": unknown app" # if no active window, fallback to workspace name
            source_icon = "application-default-icon"

    except Xlib.error.XError: #simplify dealing with BadWindow
        source_app = None
        source_icon = None

    return source_app, source_icon

def get_active_window_wm_class():
    ''' Function to get active window wm class'''
    import Xlib
    import Xlib.display

    display = Xlib.display.Display()
    root = display.screen().root

    NET_ACTIVE_WINDOW = display.intern_atom('_NET_ACTIVE_WINDOW')
    WM_CLASS = display.intern_atom('WM_CLASS')

    root.change_attributes(event_mask=Xlib.X.FocusChangeMask)
    try:
        window_id = root.get_full_property(NET_ACTIVE_WINDOW, Xlib.X.AnyPropertyType).value[0]
        window = display.create_resource_object('window', window_id)
        try:
            return window.get_full_property(WM_CLASS, 0).value.replace(b'\x00',b' ').decode("utf-8").lower()
        except:
            return None
    except Xlib.error.XError: #simplify dealing with BadWindow
        return None