# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import gi
gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Handy, GLib, Gdk

from datetime import date, datetime
from time import sleep

from .custom_widgets import CustomDialog, Settings, ContainerRevealer, KeySquareContainer, KeyRectangleContainer, MouseContainer
from . import utils

from uuid import uuid4

from inspect import currentframe, getframeinfo

class KeystrokesWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'KeystrokesWindow'

    Handy.init()

    key_listener = None
    mouse_listener = None

    active_app = None

    last_key = None
    last_key_id = None
    repeat_key_counter = 0

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
    key_remove_delay = 250

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = self.props.application

        self.header = self.generate_headerbar()

        self.key_grid = Gtk.Grid()
        self.key_grid.props.name = "key-grid"
        self.key_grid.props.column_spacing = 15
        self.key_grid.props.expand = True
        self.key_grid.props.halign = Gtk.Align.FILL
        self.key_grid.props.valign = Gtk.Align.FILL
        self.key_grid.props.margin_top = 10
        self.key_grid.props.margin_bottom = 0
        self.key_grid.props.margin_left = self.key_grid.props.margin_right = 15

        self.key_info_grid = Gtk.Grid()
        self.key_info_grid.props.name = "key-info-grid"
        self.key_info_grid.props.margin = 10
        self.key_info_grid.props.margin_top = 0
        self.key_info_grid.props.column_spacing = 5
        self.key_info_grid.props.expand = True
        self.key_info_grid.props.halign = Gtk.Align.END
        self.key_info_grid.props.valign = Gtk.Align.END

        movement_label = Gtk.Label("0,0")
        movement_label.props.name = "movement"
        movement_label.props.expand = True
        movement_label.props.justify = Gtk.Justification.LEFT
        movement_label.props.halign = Gtk.Align.START
        movement_label.set_size_request(95, -1)
        self.movement_revealer = Gtk.Revealer()
        self.movement_revealer.add(movement_label)
        self.key_info_grid.attach(self.movement_revealer, 0, 0, 1, 1)
        
        key_press_image = Gtk.Image().new_from_icon_name(icon_name="key-press", size=Gtk.IconSize.DND)
        key_press_image.props.expand = True
        self.key_press_revealer = Gtk.Revealer()
        self.key_press_revealer.add(key_press_image)
        self.key_info_grid.attach(self.key_press_revealer, 1, 0, 1, 1)

        key_release_image = Gtk.Image().new_from_icon_name(icon_name="key-release", size=Gtk.IconSize.DND)
        key_release_image.props.expand = True
        self.key_release_revealer = Gtk.Revealer()
        self.key_release_revealer.add(key_release_image)
        self.key_info_grid.attach(self.key_release_revealer, 1, 0, 1, 1)

        self.active_app_image = Gtk.Image()
        self.active_app_image.props.expand = True
        self.key_info_grid.attach(self.active_app_image, 2, 0, 1, 1)

        self.key_display_grid = Gtk.Grid()
        self.key_display_grid.props.expand = True
        self.key_display_grid.props.halign = Gtk.Align.FILL
        self.key_display_grid.props.valign = Gtk.Align.FILL
        self.key_display_grid.attach(self.key_grid, 0, 0, 1, 1)
        self.key_display_grid.attach(self.key_info_grid, 0, 1, 1, 1)
        
        standby_label = Gtk.Label("•••")
        standby_label.props.name = "standby"
        standby_label.props.expand = True
        standby_label.props.halign = standby_label.props.valign = Gtk.Align.CENTER
        self.standby_revealer = Gtk.Revealer()
        self.standby_revealer.add(standby_label)
        self.standby_revealer.set_reveal_child(True)

        grid = Gtk.Grid()
        grid.props.expand = True
        grid.attach(self.header, 0, 0, 1, 1)
        grid.attach(self.key_display_grid, 0, 0, 1, 1)
        grid.attach(self.standby_revealer, 0, 0, 1, 1)

        window_handle = Handy.WindowHandle()
        window_handle.add(grid)

        self.add(window_handle)
        self.props.name = "main"
        self.setup_ui()
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_size_request(280, 230)
        self.connect("button-press-event", self.show_window_controls)
        self.reposition(self.app.gio_settings.get_string("screen-position"))
        if self.app.window_manager is not None:
            self.app.window_manager._run(callback=self.on_active_window_changed)

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

        if self.app.gio_settings.get_value("sticky-mode"):
            self.stick()

    def generate_headerbar(self):
        settings_button = Gtk.Button(image=Gtk.Image().new_from_icon_name("settings-symbolic", Gtk.IconSize.SMALL_TOOLBAR))
        settings_button.props.always_show_image = True
        settings_button.props.can_focus = False
        settings_button.props.margin = 2
        # settings_button.set_size_request(16, 16)
        settings_button.get_style_context().remove_class("image-button")
        settings_button.get_style_context().add_class("titlebutton")
        settings_button.connect("clicked", self.on_settings_clicked)
        self.settings_revealer = Gtk.Revealer()
        self.settings_revealer.props.transition_duration = 250
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

    def generate_settings_dialog(self, *args):

        self.settings_grid = Settings(gtk_application=self.app)

        self.settings_dialog = CustomDialog(
            dialog_parent_widget=self,
            dialog_title="Keystrokes Settings",
            dialog_content_widget=self.settings_grid,
            action_button_label=None,
            action_button_name=None,
            action_callback=None,
            action_type=None,
            size=[400, 300],
            data=None
        )

        self.settings_dialog.header.props.show_close_button = True

    def reposition(self, position):
        gravity = self.get_gravity()
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
        x = None
        y = None

        # if position not in gravity.value_name:
        a, b, c, d = 0, 1, 1, 2
        # self.key_info_grid.props.halign = Gtk.Align.END
        gravity = Gdk.Gravity.SOUTH_EAST
        x, y = screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, screen_height-window_size[1]
        align = Gtk.Align.END

        for i in range(4):
            self.key_info_grid.remove_column(0)

        self.set_position(Gtk.WindowPosition.NONE)
        
        if position == "NORTH_WEST":
            gravity = Gdk.Gravity.NORTH_WEST
            x, y = (screen_height-work_area_height)-work_area_y, (screen_height-work_area_height)
            a, b, c, d = 2, 1, 1, 0
            align = Gtk.Align.START
        elif position == "NORTH":
            gravity = Gdk.Gravity.NORTH
            x, y = (screen_width/2)-(window_size[0]/2), (screen_height-work_area_height)
            align = Gtk.Align.CENTER
        elif position == "NORTH_EAST":
            gravity = Gdk.Gravity.NORTH_EAST
            x, y = screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, (screen_height-work_area_height)
            align = Gtk.Align.END
        elif position == "EAST":
            gravity = Gdk.Gravity.EAST
            x, y = screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, (screen_height/2)-(window_size[1]/2)
            align = Gtk.Align.END
        elif position == "SOUTH_EAST":
            gravity = Gdk.Gravity.SOUTH_EAST
            x, y = screen_width-window_size[0]-(screen_height-work_area_height)+work_area_y, screen_height-window_size[1]
            align = Gtk.Align.END
        elif position == "SOUTH":
            gravity = Gdk.Gravity.SOUTH
            x, y = (screen_width/2)-(window_size[0]/2), screen_height-window_size[1]
            align = Gtk.Align.CENTER
        elif position == "SOUTH_WEST":
            gravity = Gdk.Gravity.SOUTH_WEST
            x, y = (screen_height-work_area_height)-work_area_y, screen_height-window_size[1]
            a, b, c, d = 2, 1, 1, 0
            align = Gtk.Align.START
        elif position == "WEST":
            gravity = Gdk.Gravity.WEST
            x, y = (screen_height-work_area_height)-work_area_y, (screen_height/2)-(window_size[1]/2)
            a, b, c, d = 2, 1, 1, 0
            align = Gtk.Align.START
        else:
            gravity = Gdk.Gravity.CENTER
            self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            align = Gtk.Align.CENTER

        if x and y:
            self.app.gio_settings.set_int("pos-x", x)
            self.app.gio_settings.set_int("pos-y", y)

        self.set_gravity(gravity)
        self.move(self.app.gio_settings.get_int("pos-x"), self.app.gio_settings.get_int("pos-y"))
        self.key_info_grid.props.halign = align
        self.key_info_grid.attach(self.movement_revealer, a, 0, 1, 1)
        self.key_info_grid.attach(self.key_press_revealer, b, 0, 1, 1)
        self.key_info_grid.attach(self.key_release_revealer, c, 0, 1, 1)
        self.key_info_grid.attach(self.active_app_image, d, 0, 1, 1)

    def show_window_controls(self, *args):
        self.header.props.show_close_button = True
        self.settings_revealer.set_reveal_child(True)
        GLib.timeout_add(5000, self.header.set_show_close_button, False)
        GLib.timeout_add(5000, self.settings_revealer.set_reveal_child, False)

    def on_settings_clicked(self, button):
        self.generate_settings_dialog()

    def on_screen_changed(self, widget, previous_screen):
        print(previous_screen)
        self.reposition(self.app.gio_settings.get_string("screen-position"))

    def on_key_removed(self, *args):
        if self.app.gio_settings.get_value("auto-position"):
            self.reposition(self.app.gio_settings.get_string("screen-position"))
        # else:
        #     self.set_position(Gtk.WindowPosition.NONE)
        
    def on_event(self):
        if self.app.app_id.split(".")[-1].lower() in self.active_app.lower():
            return False
        else:
            return True

    def on_active_window_changed(self, window_id):
        app_data = self.app.utils.get_app_by_window_id(window_id)
        if len(app_data) != 0:
            self.active_app = app_data[0]
            self.active_app_image.set_from_icon_name(icon_name=app_data[1], size=Gtk.IconSize.DND)
            self.active_app_image.set_pixel_size(32)
        
    def on_key_event(self, key, event):
        if self.on_event():
            self.key_press_timestamp = datetime.now()
            key_type = "keyboard"
            try:
                key = key.char
                shape_type = "square"
            except AttributeError:
                key = key.name
                shape_type = "rectangle"

            if key == self.last_key:
                self.repeat_key_counter += 1

            self.add_to_display(key, key_type, shape_type, event)

            self.last_key = key
    
    def on_key_press(self, key):
        if self.app.gio_settings.get_value("monitor-key-press"):
            self.on_key_event(key, "key-press")
            self.key_press_revealer.set_reveal_child(True)
            self.key_release_revealer.set_reveal_child(False)

    def on_key_release(self, key):
        if self.app.gio_settings.get_value("monitor-key-release"):
            self.on_key_event(key, "key-release")
            self.key_release_revealer.set_reveal_child(True)
            self.key_press_revealer.set_reveal_child(False)

    def on_mouse_move(self, x, y):
        def update_movement(data):
            x, y = data
            self.movement_revealer.get_child().props.label = "x: {0}, y: {1}".format(x, y)
            self.movement_revealer.set_reveal_child(True)

        if self.app.gio_settings.get_value("monitor-movements"):
            GLib.idle_add(update_movement, (x, y))
        else:
            self.movement_revealer.set_reveal_child(False)

    def on_mouse_click(self, x, y, button, pressed):
        if self.app.gio_settings.get_value("monitor-clicks"):
            if self.on_event():
                self.key_press_timestamp = datetime.now()
                key_type = "mouse"
                try:
                    key = button.name
                    shape_type= "square"
                except AttributeError:
                    pass
                if pressed:
                    self.add_to_display(key, key_type, shape_type, "mouse-click")
                    self.last_key = key
                else:
                    self.key_press_timestamp_old = datetime.now()

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.app.gio_settings.get_value("monitor-scrolls"):
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
                    self.add_to_display(key, key_type, shape_type, "mouse-scroll")
                    self.last_key = key
                except AttributeError:
                    pass

    def add_key(self, data):
        key, key_type, shape_type, id = data
        index = len(self.key_grid.get_children())
    
        if index == 0:
            self.on_key_removed()

        if shape_type == "square":
            if key_type == "mouse":
                self.key_grid.attach(ContainerRevealer(key, MouseContainer(key, key_type), id), index, 0, 1, 1)
            else:
                self.key_grid.attach(ContainerRevealer(key, KeySquareContainer(key, key_type), id), index, 0, 1, 1)
        else:
            self.key_grid.attach(ContainerRevealer(key, KeyRectangleContainer(key, key_type), id), index, 0, 1, 1)

        self.key_grid.show_all()

        for child in self.key_grid.get_children():
            if isinstance(child, Gtk.Revealer):
                child.set_reveal_child(True)

    def remove_key(self, data):
        if data is None:
            if len(self.key_grid.get_children()) != 0:
                self.key_grid.get_children()[-1].set_reveal_child(False)
            # GLib.timeout_add(self.key_remove_delay, self.key_grid.remove_column, 0)
            # sleep(0.1)
            self.key_grid.remove_column(0)
        else:
            key_grid_child = data
            key_grid_child.destroy()
        
        # GLib.timeout_add(self.key_remove_delay, self.on_key_removed, None)
        print("{0}, triggered at line: {1}, data: {2}, child_count: {3}".format(datetime.now(), getframeinfo(currentframe()).lineno, "remove_key", len(self.key_grid.get_children())))

    def get_last_key_grid_child(self, key):
        if len(self.key_grid.get_children()) != 0:
            last_key_grid_child = [child for child in self.key_grid.get_children() if child.props.name == key]
            if len(last_key_grid_child) == 1:
                return last_key_grid_child[0]
    
    def add_to_display(self, key=None, key_type=None, shape_type=None, event=None):

        id = uuid4().hex
        self.last_key_id = id

        @utils.run_async
        def queue(*args):
            self.standby_revealer.set_reveal_child(False)
            # sleep(0.25)
            GLib.idle_add(self.add_key, (key, key_type, shape_type, id))
            
            if self.app.gio_settings.get_value("monitor-repeatkeys"):
                if self.repeat_key_counter != 0:
                    ...
            else:
                sleep(self.app.gio_settings.get_int("display-timeout")/1000)

                key_widget = [child for child in self.key_grid.get_children() if (hasattr(child, 'id') and child.id == id)]
                if key_widget:
                    try:
                        sleep(0.25)
                        key_widget[0].set_reveal_child(False)
                        sleep(0.25)
                        GLib.idle_add(key_widget[0].self_remove, None)
                        sleep(0.25)
                        GLib.idle_add(self.on_key_removed, None)
                    except:
                        import traceback
                        print(traceback.format_exc())
                        pass
                if len(self.key_grid.get_children()) == 0:
                    self.standby_revealer.set_reveal_child(True)
                self.key_release_revealer.set_reveal_child(False)
                self.key_press_revealer.set_reveal_child(False)

        queue()

