# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import sys
import os
import gi

gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
from gi.repository import Gtk, Gdk, Gio, Granite, GLib

from .window import KeystrokesWindow
from .keystrokes_backend import MouseListener, KeyListener
from . import utils

from datetime import datetime

class Application(Gtk.Application):

    app_id = "com.github.hezral.keystrokes"
    granite_settings = Granite.Settings.get_default()
    gtk_settings = Gtk.Settings.get_default()
    gio_settings = Gio.Settings(schema_id=app_id)
    utils = utils

    main_window = None
    key_listener = None
    mouse_listener = None

    def __init__(self):
        super().__init__(application_id=self.app_id,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        prefers_color_scheme = self.granite_settings.get_prefers_color_scheme()
        self.gtk_settings.set_property("gtk-application-prefer-dark-theme", prefers_color_scheme)
        self.granite_settings.connect("notify::prefers-color-scheme", self.on_prefers_color_scheme)

        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_path(os.path.join(os.path.dirname(__file__), "data", "application.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if "io.elementary.stylesheet" not in self.gtk_settings.props.gtk_theme_name:
            self.gtk_settings.set_property("gtk-theme-name", "io.elementary.stylesheet.blueberry")

        # prepend custom path for icon theme
        self.icon_theme = Gtk.IconTheme.get_default()
        self.icon_theme.prepend_search_path("/run/host/usr/share/pixmaps")
        self.icon_theme.prepend_search_path("/run/host/usr/share/icons")
        self.icon_theme.prepend_search_path("/var/lib/flatpak/exports/share/icons")
        self.icon_theme.prepend_search_path(os.path.join(GLib.get_home_dir(), ".local/share/flatpak/exports/share/icons"))
        self.icon_theme.prepend_search_path(os.path.join(os.path.dirname(__file__), "data", "icons"))

    def do_activate(self):
        if not self.main_window:
            self.main_window = KeystrokesWindow(application=self)
        self.main_window.present()

        GLib.timeout_add(500, self.setup_keyboard_listener, None)
        GLib.timeout_add(750, self.setup_mouse_listener, None)

    def on_prefers_color_scheme(self, *args):
        prefers_color_scheme = self.granite_settings.get_prefers_color_scheme()
        self.gtk_settings.set_property("gtk-application-prefer-dark-theme", prefers_color_scheme)

    def setup_keyboard_listener(self, *args):
        if self.key_listener is not None:
            self.key_listener.listener.stop()
            self.key_listener = None
            print(datetime.now(), "key listener stopped")

        self.key_listener = KeyListener(self.main_window.on_key_press, self.main_window.on_key_release)

    def setup_mouse_listener(self, *args):
        if self.mouse_listener is not None:
            self.mouse_listener.listener.stop()
            self.mouse_listener = None
            print(datetime.now(), "mouse listener stopped")

        self.mouse_listener = MouseListener(self.main_window.on_mouse_move, self.main_window.on_mouse_click, self.main_window.on_mouse_scroll)


def main(version):
    app = Application()
    return app.run(sys.argv)
