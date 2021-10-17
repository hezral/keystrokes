# window.py
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

import gi
gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
from gi.repository import Gtk, Handy, GLib, Gdk, Granite

from datetime import date, datetime

from .key_event import MouseListener, KeyListener
from .custom_widgets import CustomDialog, Settings, ContainerRevealer, KeySquareContainer, KeyRectangleContainer, MouseContainer
from . import utils

from inspect import currentframe, getframeinfo


class KeystrokesWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'KeystrokesWindow'

    Handy.init()

    key_listener = None
    mouse_listener = None

    last_key = None

    key_press_timestamp = datetime.now()
    key_press_timestamp_old = datetime.now()
    key_press_timestamp_diff = 0
    key_press_timeout = 50
    key_press_count = 0

    word = []
    word_detect = True

    timeout_remove = False
    repeated_key = None

    key_add_delay = 500

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = self.props.application

        self.header = self.generate_headerbar()

        self.key_grid = Gtk.Grid()
        self.key_grid.props.name = "key-grid"
        self.key_grid.props.column_spacing = 20
        self.key_grid.props.expand = True
        self.key_grid.props.halign = Gtk.Align.CENTER
        self.key_grid.props.margin_top = 5
        self.key_grid.props.margin_left = self.key_grid.props.margin_right = 20

        standby_label = Gtk.Label("•••")
        standby_label.props.name = "standby"
        standby_label.props.expand = True
        standby_label.props.halign = standby_label.props.valign = Gtk.Align.CENTER

        self.stack = Gtk.Stack()
        self.stack.add_named(standby_label, "standby")
        self.stack.add_named(self.key_grid, "key-grid")

        grid = Gtk.Grid()
        grid.props.expand = True
        grid.attach(self.header, 0, 0, 1, 1)
        grid.attach(self.stack, 0, 0, 1, 1)

        self.add(grid)
        self.props.name = "main"
        self.setup_ui()
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_size_request(280, 220)
        self.connect("destroy", Gtk.main_quit)
        self.connect("button-press-event", self.show_window_controls)
        # self.connect("screen-changed", self.on_screen_changed)
        self.reposition(self.app.gio_settings.get_string("screen-position"))
        if self.app.gio_settings.get_value("sticky-mode"):
            self.stick()

        self.setup_keyboard_listener()
        self.setup_mouse_listener()
        # GLib.timeout_add(500, self.setup_keyboard_listener, None)
        # GLib.timeout_add(1000, self.setup_mouse_listener, None)

    def setup_keyboard_listener(self, *args):
        if self.key_listener is not None:
            self.key_listener.listener.stop()
            self.key_listener = None
        if self.app.gio_settings.get_value("monitor-keys"):
            self.key_listener = KeyListener(self.on_key_press, self.on_key_release)

    def setup_mouse_listener(self, *args):
        if self.mouse_listener is not None:
            self.mouse_listener.listener.stop()
            self.mouse_listener = None
        if self.app.gio_settings.get_value("monitor-scrolls") and self.app.gio_settings.get_value("monitor-clicks"):
            self.mouse_listener = MouseListener(None, self.on_mouse_click, self.on_mouse_scroll)
        elif self.app.gio_settings.get_value("monitor-scrolls") and not self.app.gio_settings.get_value("monitor-clicks"):
            self.mouse_listener = MouseListener(None, None, self.on_mouse_scroll)
        elif not self.app.gio_settings.get_value("monitor-scrolls") and self.app.gio_settings.get_value("monitor-clicks"):
            self.mouse_listener = MouseListener(None, self.on_mouse_click, None)

    def setup_ui(self, transparency_value=None):
        if transparency_value is None:
            transparency_value = float(self.app.gio_settings.get_int("display-transparency")/100)
        css = "window#main.background {background-color: rgba(0,0,0," + str(transparency_value) + ");}"
        # if transparency_value <= 0.1:
        #     print(transparency_value)
        #     css = css + "\n" + "headerbar#main button {" + "color: black;}"
        #     css = css + "\n" + "headerbar#main button {box-shadow: 0 0 0 1px rgba(0,0,0,0.75), 0 13px 16px 4px rgba(0,0,0,0), 0 3px 4px rgba(0,0,0,0.25), 0 3px 3px -3px rgba(0,0,0,0.45);}"
        #     # print(transparency_value)
        # css = css + "\n" + "window > decoration {box-shadow: 0 0 0 0px rgba(0,0,0,0), 0 0px 0px  rgba(0,0,0,0), 0 0px 0px  rgba(0,0,0,0), 0 0px 16px  rgba(0,0,0,0);}"
        # css = css + "\n" + "window > decoration-overlay {box-shadow: 0 0 0 1px rgba(0,0,0,0), 0 13px 16px 4px rgba(0,0,0,0), 0 3px 4px rgba(0,0,0,0), 0 3px 3px -3px rgba(0,0,0,0);}"
        # css = css + "\n" + "decoration {box-shadow: 0 0 0 1px rgba(0,0,0,0.75), 0 13px 16px 4px rgba(0,0,0,0), 0 3px 4px rgba(0,0,0,0.25), 0 3px 3px -3px rgba(0,0,0,0.45);}"
        # css = css + "\n" + "decoration-overlay {box-shadow: 0 -1px rgba(255,255,255,0.04) inset, 0 1px rgba(255,255,255,0.06) inset, 1px 0 rgba(255,255,255,0.014) inset, -1px 0 rgba(255,255,255,0.14) inset;}"
        # else:
        #     css = css + "\n" + "headerbar#main button {" + "color: white;}"
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(css.encode()))
        self.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def generate_headerbar(self):
        settings_button = Gtk.Button(image=Gtk.Image().new_from_icon_name("com.github.hezral-settings-symbolic", Gtk.IconSize.SMALL_TOOLBAR))
        settings_button.props.always_show_image = True
        settings_button.props.can_focus = False
        settings_button.props.margin = 2
        # settings_button.set_size_request(16, 16)
        settings_button.get_style_context().remove_class("image-button")
        settings_button.get_style_context().add_class("titlebutton")
        settings_button.connect("clicked", self.on_settings_clicked)
        self.settings_revealer = Gtk.Revealer()
        self.settings_revealer.props.transition_duration = 10
        self.settings_revealer.props.transition_type = Gtk.RevealerTransitionType.CROSSFADE
        self.settings_revealer.add(settings_button)

        header = Handy.HeaderBar()
        header.props.name = "main"
        header.props.hexpand = True
        header.props.valign = Gtk.Align.START
        header.props.halign = Gtk.Align.FILL
        header.props.spacing = 0
        header.props.has_subtitle = False
        header.props.show_close_button = False
        header.props.decoration_layout = "close:"
        header.get_style_context().add_class(Gtk.STYLE_CLASS_FLAT)
        header.pack_end(self.settings_revealer)

        return header

    def generate_settings_dialog(self):

        self.settings_grid = Settings(gtk_application=self.app)

        self.settings_dialog = CustomDialog(
            dialog_parent_widget=self,
            dialog_title="Keystrokes Settings",
            dialog_content_widget=self.settings_grid,
            action_button_label=None,
            action_button_name=None,
            action_callback=None,
            action_type=None,
            size=[500, 400],
            data=None
        )

        self.settings_dialog.header.props.show_close_button = True

    def reposition(self, position):
        screen = self.get_screen()
        screen_width = screen.width()
        screen_height = screen.height()
        monitor = screen.get_monitor_at_window(self.get_window())
        work_area = screen.get_monitor_workarea(monitor)
        work_area_x = work_area.x
        work_area_y = work_area.y
        work_area_width = work_area.width
        work_area_height = work_area.height
        window_size = self.get_size()
        # print("screen width, height: ", work_area_width, work_area_height, "x, y: ", work_area_x, work_area_y, "diff:", screen_height-work_area_height, window_size)

        self.set_position(Gtk.WindowPosition.NONE)
        if position == "north-west":
            self.set_gravity(Gdk.Gravity.NORTH_WEST)
            self.move((screen_height-work_area_height)-work_area_y, (screen_height-work_area_height))
        elif position == "north":
            self.set_gravity(Gdk.Gravity.NORTH)
            self.move((screen_width/2)-(window_size[0]/2), (screen_height-work_area_height))
        elif position == "north-east":
            self.set_gravity(Gdk.Gravity.NORTH_EAST)
            self.move(screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, (screen_height-work_area_height))
        elif position == "east":
            self.set_gravity(Gdk.Gravity.EAST)
            self.move(screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, (screen_height/2)-(window_size[1]/2))
        elif position == "south-east":
            self.set_gravity(Gdk.Gravity.SOUTH_EAST)
            self.move(screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, screen_height-window_size[1])
        elif position == "south":
            self.set_gravity(Gdk.Gravity.SOUTH)
            self.move((screen_width/2)-(window_size[0]/2), screen_height-window_size[1])
        elif position == "south-west":
            self.set_gravity(Gdk.Gravity.SOUTH_WEST)
            self.move((screen_height-work_area_height)-work_area_y, screen_height-window_size[1])
        elif position == "west":
            self.set_gravity(Gdk.Gravity.WEST)
            self.move((screen_height-work_area_height)-work_area_y, (screen_height/2)-(window_size[1]/2))
        else:
            self.set_gravity(Gdk.Gravity.CENTER)
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

    def show_window_controls(self, *args):
        if self.header.props.show_close_button:
            self.header.props.show_close_button = False
            self.settings_revealer.set_reveal_child(False)
        else:
            self.header.props.show_close_button = True
            self.settings_revealer.set_reveal_child(True)
            GLib.timeout_add(5000, self.header.set_show_close_button, False)
            GLib.timeout_add(5000, self.settings_revealer.set_reveal_child, False)

    def on_settings_clicked(self, button):
        self.generate_settings_dialog()

    def on_screen_changed(self, widget, previous_screen):
        print(previous_screen)
        self.reposition(self.app.gio_settings.get_string("screen-position"))

    def on_stack_view(self, *args):
        if self.stack.get_visible_child_name() == "key-grid" and len(self.key_grid.get_children()) == 0:
            self.stack.set_visible_child_name("standby")
        else:
            self.stack.set_visible_child_name("key-grid")
        if self.app.gio_settings.get_value("auto-position"):
            self.reposition(self.app.gio_settings.get_string("screen-position"))
        else:
            self.set_position(Gtk.WindowPosition.NONE)

    def on_event(self):
        active_window_class = utils.get_active_window_wm_class()
        if active_window_class is not None:
            if self.app.app_id in active_window_class:
                return False
            else:
                return True
        # print("triggered at line: {0}, timestamp: {1}, keystrokes_window: {2}, active_window: {3}".format(getframeinfo(currentframe()).lineno, datetime.now(), keystrokes_window, active_window, active_window_class))
        
    def on_key_press(self, key):
        if self.on_event():
            self.key_press_timestamp = datetime.now()
            key_type = "keyboard"
            try:
                key = key.char
                shape_type = "square"
            except AttributeError:
                key = key.name
                shape_type = "rectangle"

            # GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
            # GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)

            self.add_to_display(key, key_type, shape_type)

            # if shape_type == "square":
            #     GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
            #     GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
            # else:
            #     self.on_repeat_key(key_type, key, shape_type)
                
            self.last_key = key

            # self.word.append(key)
            # if self.word_detect and shape_type == "square":

            #     if len(self.word) == 0:
            #         self.key_press_timestamp_old = datetime.now()

            #     self.key_press_timestamp = datetime.now()
                
            #     self.key_press_timestamp_diff = int((self.key_press_timestamp-self.key_press_timestamp_old).total_seconds()*1000)
                
            #     print("key_press_timestamp_diff:", self.key_press_timestamp_diff)
                
            #     if self.key_press_timestamp_diff < self.key_press_timeout:
            #         self.word.append(key)
            #     else:
            #         word = ''.join(self.word)
            #         type = "square"
            #         self.word = []
                
            #     # self.key_press_timestamp_old = self.key_press_timestamp
            #     print(''.join(self.word))
            # else:
            #     self.word = []``

    def on_key_release(self, key):
        # key_type = "keyboard"
        # try:
        #     key = key.char
        #     shape_type = "square"
        # except AttributeError:
        #     key = key.name
        #     shape_type = "rectangle"
        self.key_press_timestamp_old = datetime.now()

        # if key != self.last_key:
        #     GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)

    def on_mouse_move(self, x, y):
        print('Pointer moved to {0}'.format((x, y)))

    def on_mouse_click(self, x, y, button, pressed):
        if self.on_event():
            self.key_press_timestamp = datetime.now()
            key_type = "mouse"
            try:
                key = button.name
                shape_type= "square"
            except AttributeError:
                pass
            if pressed:
                self.add_to_display(key, key_type, shape_type)
                self.last_key = key
            else:
                self.key_press_timestamp_old = datetime.now()

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.on_event():
            key_type = "mouse"
            try:
                if dy < 0:
                    key = "scrolldown"
                elif dy > 0:
                    key = "scrollup"
                elif dx < 0:
                    key = "scrollleft"
                elif dx > 0:
                    key = "scrollright"
                shape_type= "square"
                self.add_to_display(key, key_type, shape_type)
                self.last_key = key
            except AttributeError:
                pass

    def add_key(self, data):
        key, key_type, shape_type = data
        index = len(self.key_grid.get_children())

        if index == 0:
            self.on_stack_view()

        if shape_type == "square":
            if key_type == "mouse":
                self.key_grid.attach(ContainerRevealer(key, MouseContainer(key, key_type)), index, 0, 1, 1)
            else:
                self.key_grid.attach(ContainerRevealer(key, KeySquareContainer(key, key_type)), index, 0, 1, 1)

        else:
            self.key_grid.attach(ContainerRevealer(key, KeyRectangleContainer(key, key_type)), index, 0, 1, 1)

        self.key_grid.show_all()

        for child in self.key_grid.get_children():
            child.set_reveal_child(True)
        
    def remove_key(self, data):
        if data is None:
            if len(self.key_grid.get_children()) != 0:
                self.key_grid.get_children()[-1].set_reveal_child(False)
            GLib.timeout_add(self.key_add_delay, self.key_grid.remove_column, 0)
        else:
            key_grid_child = data
            key_grid_child.destroy()
            print("destroy")
        GLib.timeout_add(self.key_add_delay, self.on_stack_view, None)

    def get_last_key_grid_child(self, key):
        if len(self.key_grid.get_children()) != 0:
            last_key_grid_child = [child for child in self.key_grid.get_children() if child.props.name == key]
            if len(last_key_grid_child) == 1:
                return last_key_grid_child[0]

    def add_to_display(self, key=None, key_type=None, shape_type=None):
        monitor_repeats = self.app.gio_settings.get_value("monitor-repeatkeys")
        key_grid_children_count = len(self.key_grid.get_children())

        if monitor_repeats:
            if self.last_key is not None:
                if key == self.last_key:
                    if key_grid_children_count != 0:
                        last_key_child = self.get_last_key_grid_child(self.last_key)
                        if last_key_child is not None:
                            if last_key_child.repeat_key_counter == 0:
                                last_key_child.repeat_key_counter += 1
                                last_key_child.overlay.add_overlay(last_key_child.counter)
                            else:
                                last_key_child.repeat_key_counter += 1
                            last_key_child.counter.props.label = str(last_key_child.repeat_key_counter)
                            last_key_child.show_all()
                        else:
                            print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
                            # GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
                            GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
                    else:
                        print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
                        GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
                        self.key_press_timestamp_diff = int((self.key_press_timestamp-self.key_press_timestamp_old).total_seconds()*1000)
                        print(self.key_press_timestamp_diff)
                        if self.key_press_timestamp_diff > self.key_press_timeout:
                            GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
                else:
                    last_key_child = self.get_last_key_grid_child(self.last_key)
                    if last_key_child is not None:
                        if last_key_child.repeat_key_counter > 1:
                            print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
                            GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
                            GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
                        else:
                            print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
                            GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
                            GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
                    else:
                        print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
                        GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
                        GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
            else:
                print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
                GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
                GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)
        else:
            print("triggered at line: {3},  timestamp: {4}, key_type: {0},  key: {1},   last_key: {2}".format(key_type, key, self.last_key, getframeinfo(currentframe()).lineno, datetime.now()))
            GLib.timeout_add(self.key_add_delay, self.add_key, (key, key_type, shape_type))
            GLib.timeout_add(self.app.gio_settings.get_int("display-timeout"), self.remove_key, None)

