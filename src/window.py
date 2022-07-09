# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from typing import final
import gi
gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Handy, GLib, Gdk

from datetime import date, datetime
from time import sleep

from .custom_widgets import *
from . import utils

from uuid import uuid4
import threading

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(asctime)s, %(funcName)s:%(lineno)d: %(message)s")

class KeystrokesWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'KeystrokesWindow'

    Handy.init()

    key_listener = None
    mouse_listener = None

    display_cleaner_thread = None
    stop_display_cleaner_thread = False

    last_key = None
    last_key_id = None
    last_active_app = None

    active_app = None

    key_ids = {}

    repeat_key_counter = 0

    key_press_timestamp = datetime.now()
    key_press_timestamp_old = datetime.now()
    key_press_timestamp_diff = 0
    key_press_timeout = 50
    key_press_count = 0

    timeout_id = 0
    repeated_key = None

    app_startup = True

    key_displays_grid_idx = 0

    mouse_distance = 0

    before_xy = None
    current_xy = None
    mouse_moving = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = self.props.application

        self.header = self.generate_headerbar()
        self.standby_revealer = self.generate_standby_revealer()
        self.movement_revealer = self.generate_movement_revealer()

        self.key_displays_grid = Gtk.Grid()
        
        self.grid = Gtk.Grid()
        self.grid.props.expand = True
        self.grid.attach(self.key_displays_grid, 0, 0, 1, 1)
        self.grid.attach(self.standby_revealer, 0, 0, 1, 1)
        self.grid.attach(self.movement_revealer, 0, 0, 1, 1)

        overlay = Gtk.Overlay()
        overlay.add(self.grid)
        overlay.add_overlay(self.header)

        window_handle = Handy.WindowHandle()
        window_handle.add(overlay)

        self.add(window_handle)
        self.props.name = "main"
        self.setup_ui()
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_size_request(200, 180)
        self.reposition()
        if self.app.window_manager is not None:
            self.app.window_manager._run(callback=self.on_active_window_changed)
        
        # screen = self.get_screen()
        # display = screen.get_display()
        # display.connect("monitor-added", self.on_n_monitor_changed, "monitor-added")
        # display.connect("monitor-removed", self.on_n_monitor_changed, "monitor-removed")
        # n_monitors = display.get_n_monitors()
        ...

    def setup_ui(self, transparency_value=None):
        if transparency_value is None:
            transparency_value = float(self.app.gio_settings.get_int("display-transparency")/100)
        css = "window#main.background {background-color: rgba(0,0,0," + str(transparency_value) + ");}"
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(css.encode()))
        self.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if self.app.gio_settings.get_value("sticky-mode"):
            self.stick()

        self.connect("button-press-event", self.show_window_controls)
        # self.connect("screen-changed", self.on_screen_changed)
        self.connect("configure-event", self.on_configure_event)

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

    def generate_standby_revealer(self):
        standby_label = Gtk.Label("•••")
        standby_label.props.name = "standby"
        standby_label.props.expand = True
        standby_label.props.halign = standby_label.props.valign = Gtk.Align.CENTER
        standby_revealer = Gtk.Revealer()
        standby_revealer.add(standby_label)
        standby_revealer.set_reveal_child(True)
        return standby_revealer

    def generate_movement_revealer(self):
        label = "x: 0\ny: 0"
        self.movement_label = Gtk.Label()
        self.movement_label.props.name = "movement"
        self.movement_label.props.expand = True
        self.movement_label.props.margin_top = 24
        self.movement_label.props.justify = Gtk.Justification.LEFT
        self.movement_label.props.halign = Gtk.Align.CENTER
        self.movement_label.props.valign = Gtk.Align.CENTER
        self.movement_label.set_label(label)
        movements_image = Gtk.Image().new_from_icon_name(icon_name="movements6", size=Gtk.IconSize.DIALOG)
        movements_image.props.expand = True
        movements_image.props.margin_bottom = 24
        movements_image.props.valign = Gtk.Align.START
        movements_grid = Gtk.Grid()
        movements_grid.props.expand = True
        movements_grid.attach(movements_image, 0, 0, 1, 1)
        movements_grid.attach(self.movement_label, 0, 0, 1, 1)
        movement_revealer = Gtk.Revealer()
        movement_revealer.props.name = "movement-revealer"
        movement_revealer.props.expand = True
        movement_revealer.props.halign = Gtk.Align.CENTER
        movement_revealer.props.valign = Gtk.Align.CENTER
        movement_revealer.props.margin_top = 10
        movement_revealer.props.margin_bottom = 10
        movement_revealer.props.margin_left = 15
        movement_revealer.props.margin_right = 15
        movement_revealer.add(movements_grid)
        return movement_revealer

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

    def reposition(self, *args):

        # defaults
        a, b, c, d = 0, 1, 1, 2
        align = Gtk.Align.END

        # clear key_info_grid
        # for i in range(4):
        #     self.key_info_grid.remove_column(0)

        if self.app.gio_settings.get_value("auto-position"):

            gravity = Gdk.Gravity(self.app.gio_settings.get_int("screen-position"))

            window_width, window_height = self.get_size()
            root_x, root_y = self.get_position()
            
            screen = self.get_screen()
            screen_width = screen.width()
            screen_height = screen.height()
            # logging.info("screen:{0}".format((screen_width, screen_height)))

            display = screen.get_display()
            n_monitors = display.get_n_monitors()
            # logging.info("n_monitors:{0}".format(n_monitors))

            monitor = screen.get_monitor_at_window(self.get_window())
            # logging.info("get_monitor_at_window:{0}".format(monitor))
            
            monitor_geometry = screen.get_monitor_geometry(monitor)
            # logging.info("get_monitor_at_window:{0}".format((monitor_geometry.x, monitor_geometry.y, monitor_geometry.width, monitor_geometry.height)))

            work_area = screen.get_monitor_workarea(monitor)
            # logging.info("work_area:{0}".format((work_area.x, work_area.y, work_area.width, work_area.height)))

            offset_x = monitor_geometry.height - work_area.height
            offset_y = (screen_height-work_area.height)-work_area.y
            # logging.info("offset:{0}".format((offset_x, offset_y)))

            monitor = screen.get_primary_monitor()
            # logging.info("get_primary_monitor:{0}".format(monitor))

            monitor_geometry = screen.get_monitor_geometry(monitor)
            # logging.info("get_monitor_at_window:{0}".format((monitor_geometry.x, monitor_geometry.y, monitor_geometry.width, monitor_geometry.height)))

            work_area = screen.get_monitor_workarea(monitor)
            # logging.info("work_area:{0}".format((work_area.x, work_area.y, work_area.width, work_area.height)))

            offset_y = monitor_geometry.height - work_area.height
            offset_x = (screen_height-work_area.height)-work_area.y
            # logging.info("offset:{0}".format((offset_x, offset_y)))

            safe_area_width = screen_width - (screen_height - work_area.height - work_area.y) * 2
            # logging.info("safe_area:{}, window_width:{}".format(safe_area_width,window_width))

            # defaults
            # x, y = screen_width-window_width-(screen_height-work_area.height)+work_area.y, screen_height-window_height

            self.set_position(Gtk.WindowPosition.NONE)

            if gravity.value_name == "GDK_GRAVITY_NORTH_WEST":
                x, y = (screen_height-work_area.height)-work_area.y, (screen_height-work_area.height)
                a, b, c, d = 2, 1, 1, 0
                align = Gtk.Align.START
            elif gravity.value_name =="GDK_GRAVITY_NORTH":
                x, y = (screen_width/2)-(window_width/2), (screen_height-work_area.height)
                align = Gtk.Align.CENTER
            elif gravity.value_name == "GDK_GRAVITY_NORTH_EAST":
                x, y = screen_width-window_width-(screen_height-work_area.height)+work_area.y, (screen_height-work_area.height)
                align = Gtk.Align.END
            elif gravity.value_name == "GDK_GRAVITY_EAST":
                x, y = screen_width-window_width-(screen_height-work_area.height)+work_area.y, (screen_height/2)-(window_height/2)
                align = Gtk.Align.END
            elif gravity.value_name == "GDK_GRAVITY_SOUTH_EAST":
                x, y = screen_width-window_width-(screen_height-work_area.height)+work_area.y, screen_height-window_height
                align = Gtk.Align.END
            elif gravity.value_name == "GDK_GRAVITY_SOUTH":
                x, y = (screen_width/2)-(window_width/2), screen_height-window_height
                align = Gtk.Align.CENTER
            elif gravity.value_name == "GDK_GRAVITY_SOUTH_WEST":
                x, y = (screen_height-work_area.height)-work_area.y, screen_height-window_height
                a, b, c, d = 2, 1, 1, 0
                align = Gtk.Align.START
            elif gravity.value_name == "GDK_GRAVITY_WEST":
                x, y = (screen_height-work_area.height)-work_area.y, (screen_height/2)-(window_height/2)
                a, b, c, d = 2, 1, 1, 0
                align = Gtk.Align.START
            elif gravity.value_name == "GDK_GRAVITY_CENTER":
                x, y = (screen_width/2)-(window_width/2), (screen_height/2)-(window_height/2)
                align = Gtk.Align.CENTER
            else:
                pass

            x, y = int(x), int(y)
            # logging.info("move:{0}".format((x,y)))
            self.move(x, y)
            # gdk_window.move(x, y)

        else:
            if self.app.gio_settings.get_string("current-position") in ["upper-left", "lower-left"] :
                a, b, c, d = 2, 1, 1, 0
                align = Gtk.Align.START
                gravity = Gdk.Gravity.NORTH_WEST
            elif self.app.gio_settings.get_string("current-position") in ["upper-right", "lower-right"] :
                a, b, c, d = 0, 1, 1, 2
                align = Gtk.Align.END
                gravity = Gdk.Gravity.NORTH_EAST

        self.set_gravity(gravity)
        # self.key_info_grid.props.halign = align
        # self.key_info_grid.attach(self.movement_revealer, a, 0, 1, 1)
        # self.key_info_grid.attach(self.key_press_revealer, b, 0, 1, 1)
        # self.key_info_grid.attach(self.key_release_revealer, c, 0, 1, 1)
        # self.key_info_grid.attach(self.active_app_image, d, 0, 1, 1)
        ...

    def show_window_controls(self, *args):
        self.header.props.show_close_button = True
        self.settings_revealer.set_reveal_child(True)
        GLib.timeout_add(5000, self.header.set_show_close_button, False)
        GLib.timeout_add(5000, self.settings_revealer.set_reveal_child, False)

    def on_n_monitor_changed(self, display, monitor, event_type):
        logging.info((event_type, monitor))

    def on_configure_event(self, widget, event):
        position = ""

        root_x, root_y = self.get_position()

        screen = self.get_screen()

        display = screen.get_display()
        n_monitors = display.get_n_monitors()

        monitor = screen.get_monitor_at_window(self.get_window())
        monitor = screen.get_primary_monitor()

        monitor_geometry = screen.get_monitor_geometry(monitor)

        work_area = screen.get_monitor_workarea(monitor)

        if root_x >= 0 and root_x <= monitor_geometry.width/2 and root_y >= 0 and root_y <= monitor_geometry.height/2:
            position = "upper-left"
        elif root_x >= monitor_geometry.width/2 and root_y >= 0 and root_y <= monitor_geometry.height/2:
            position = "upper-right"
        elif root_x >= 0 and root_x <= monitor_geometry.width/2 and root_y >= monitor_geometry.height/2:
            position = "lower-left"
        elif root_x >= monitor_geometry.width/2 and root_y >= monitor_geometry.height/2:
            position = "lower-right"

        if position not in self.app.gio_settings.get_string("current-position"):
            self.app.gio_settings.set_string("current-position", position)
            self.reposition()
            ...

    def on_active_window_changed(self, window_id):

        @utils.run_async
        def queue_key_display_remove(key_display, *args):
            while len(key_display.key_grid.get_children()) != 0:
                sleep(0.25)
            else:
                GLib.idle_add(key_display.self_remove, None)

        app_data = self.app.utils.get_app_by_window_id(window_id)

        if app_data is not None and len(app_data) != 0:
            self.active_app = app_data[0]

            # app startup
            if not self.app_startup and self.active_app != "Keystrokes":

                key_displays = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active'))]

                # logging.info("len(key_displays):{0}".format(len(key_displays)))

                if len(key_displays) == 0:
                    key_display_grid = KeyDisplayContainer(self.active_app, True)
                    key_display_grid.active_app_image.set_from_icon_name(icon_name=app_data[1], size=Gtk.IconSize.DND)
                    key_display_grid.active_app_image.set_pixel_size(48)
                    self.key_displays_grid.attach(key_display_grid, 0, self.key_displays_grid_idx, 1, 1)
                    self.key_displays_grid.show_all()
                    self.key_displays_grid_idx += 1
                
                else:
                    active_key_display = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active') and child.active is True)]
                    if len(active_key_display) != 0:
                        active_key_display = active_key_display[0]

                        if self.active_app != active_key_display.props.name:
                            
                            active_key_display.active = False
                            queue_key_display_remove(active_key_display)

                            key_display_grid = KeyDisplayContainer(self.active_app, True)
                            key_display_grid.active_app_image.set_from_icon_name(icon_name=app_data[1], size=Gtk.IconSize.DND)
                            key_display_grid.active_app_image.set_pixel_size(48)
                            self.key_displays_grid.attach(key_display_grid, 0, self.key_displays_grid_idx, 1, 1)
                            self.key_displays_grid.show_all()
                            self.key_displays_grid_idx += 1

        self.app_startup = False

    def on_settings_clicked(self, button):
        self.generate_settings_dialog()

    def on_screen_changed(self, widget, previous_screen):
        logging.info(previous_screen)
        self.reposition()
        ...
      
    def on_event(self):
        GLib.idle_add(self.reposition, None)
        if self.app.app_id.split(".")[-1].lower() in self.active_app.lower():
            return False
        else:
            return True
        
    def on_key_event(self, key, event):
        if self.on_event():
            self.key_press_timestamp = datetime.now()
            key_type = "keyboard"

            try:
                _key = key.char
                shape_type = "square"
                is_modifier = False
            except AttributeError:
                _key = key.name
                shape_type = "rectangle"
                is_modifier = True
            else:
            # print(Gdk.keyval_name(key.vk))
                if key.vk:
                    if key.vk == 65032: #temporary workaround for issue https://github.com/moses-palmer/pynput/issues/215
                        _key = "shift"
                        shape_type = "rectangle"
                        is_modifier = True
            finally:
                key = _key

            # if key == self.last_key:
            #     self.repeat_key_counter += 1

            data = {(key, key_type, shape_type, event, self.active_app)}
            self.queue_to_display(data)

            # self.last_key = key
            ...
    
    def on_key_press(self, key):
        if self.app.gio_settings.get_value("monitor-key-press"):
            self.on_key_event(key, "pressed")

    def on_key_release(self, key):
        if self.app.gio_settings.get_value("monitor-key-release"):
            self.on_key_event(key, "released")

    def on_mouse_move(self, x=0, y=0):

        @utils.run_async
        def queue_movement_revealer_remove():
            while self.mouse_moving:
                if self.before_xy == self.current_xy:
                    sleep(1)
                    self.mouse_moving = False
                    self.movement_revealer.set_reveal_child(False)
                    sleep(0.25)
                    key_display = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active') and child.active is True)]
                    if len(key_display) == 0 or len(key_display[0].key_grid.get_children()) == 0:
                        self.standby_revealer.set_reveal_child(True)

                    self.grid.remove(self.movement_revealer)
                    
                    break
                self.before_xy = self.current_xy
        
        def update_movement(data):
            self.before_xy = self.current_xy
            self.current_xy = data
            self.new_x, self.new_y = data
            self.movement_label.props.label = "x: {0}\ny: {1}".format(self.new_x, self.new_y)
            
        if self.app.gio_settings.get_value("monitor-movements"):

            key_display = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active') and child.active is True and child.key_grid_revealer.is_visible())]

            if len(key_display) == 0:
                self.movement_revealer.set_reveal_child(True)
                self.standby_revealer.set_reveal_child(False)
            else:
                self.movement_revealer.set_reveal_child(False)

            GLib.idle_add(update_movement, (x, y))

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
                    data = {(key, key_type, shape_type, "clicked", self.active_app)}
                    self.queue_to_display(data)

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
                    
                    data = {(key, key_type, shape_type, "scroll", self.active_app)}
                    self.queue_to_display(data)
                except AttributeError:
                    pass

    def add_key(self, data):

        key_display, key, key_type, shape_type, id, event, active_app = data

        if shape_type == "square":
            if key_type == "mouse":
                widget = MouseContainer(key, key_type, event)
            else:
                widget = KeySquareContainer(key, key_type, event)
        else:
            widget = KeyRectangleContainer(key, key_type, event)
        
        key_display.key_grid.add(ContainerRevealer(key, widget, id, event, active_app))
        key_display.key_grid.show_all()

        for child in key_display.key_grid.get_children():
            if isinstance(child, Gtk.Revealer):
                child.set_reveal_child(True)
        
        self.key_ids[id] = widget.get_parent().get_parent()

        self.last_key = key
        self.last_key_id = id
        self.last_active_app = active_app

    def queue_to_display(self, data):
        '''
        data = {(key, key_type, shape_type, event, self.active_app)}
        receive parameters as set to make the values immutable

        then convert it back into list and individual variables
        key, key_type, shape_type, event, active_app = list(data)[0]
        '''
        
        key, key_type, shape_type, event, active_app = list(data)[0]

        @utils.run_async
        def add(key_display, id, *args):

            self.standby_revealer.set_reveal_child(False)
            self.movement_revealer.set_reveal_child(False)
            sleep(0.25)
            key_display.active_app_revealer.set_reveal_child(True)
            key_display.key_grid_revealer.set_visible(True)
            sleep(0.25)
            key_display.key_grid_revealer.set_reveal_child(True)
            
            if self.app.gio_settings.get_value("monitor-repeatkeys") and key == self.last_key and active_app == self.last_active_app:
                self.key_ids[self.last_key_id].repeat_key = True
                self.key_ids[self.last_key_id].counter_revealer.set_reveal_child(True)
                self.key_ids[self.last_key_id].repeat_key_counter += 1
                self.key_ids[self.last_key_id].counter.set_text(str(self.key_ids[self.last_key_id].repeat_key_counter))

            elif self.app.gio_settings.get_value("monitor-repeatkeys") and key != self.last_key or not self.app.gio_settings.get_value("monitor-repeatkeys"):
                GLib.idle_add(self.add_key, (key_display, key, key_type, shape_type, id, event, active_app))

            if self.display_cleaner_thread is None:
                self.run_display_cleaner()

        @utils.run_async
        def released(*args):
            sleep(0.5)
            for key_id in self.key_ids.keys():
                if event + key + active_app + self.key_ids[key_id].event + self.key_ids[key_id].name + self.key_ids[key_id].active_app == "released" + key + active_app + "pressed" + key + active_app:
                    self.key_ids[key_id].overlay.get_child().get_style_context().add_class("animate-released")
                    break
        
        # press
        # release
        # press + release
        # press + repeat
        # release + repeat
        # press + release + repeat

        id = uuid4().hex
        
        if (event == "pressed" and self.app.gio_settings.get_value("monitor-key-press")) or (event == "clicked" and self.app.gio_settings.get_value("monitor-clicks")) or (event == "scroll" and self.app.gio_settings.get_value("monitor-scrolls")):
            add(self.get_key_display(active_app), id)
            
        elif event == "released" and self.app.gio_settings.get_value("monitor-key-release"):
            released()

    def get_key_display(self, active_app):
        try:
            key_display = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active_app') and child.active_app == active_app)]
            if len(key_display) != 0:
                return key_display[0]
        except:
            key_display = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active') and child.active is True)]
            if len(key_display) != 0:
                return key_display[0]

    def run_display_cleaner(self):

        timeout = datetime.now()
        # timeout = 0
        
        def init_manager():
            while True:
                logging.info("loop")
                sleep(self.app.gio_settings.get_int("display-timeout")/1000)

                if len(self.key_ids) != 0:

                    first_value = list(self.key_ids.keys())[0]
                    first_key_container = self.key_ids[first_value]
                    
                    try:
                        second_value = list(self.key_ids.keys())[1]
                        second_key_container = self.key_ids[second_value]
                        if first_key_container.repeat_key and not second_key_container.repeat_key:
                            first_key_container.repeat_key = False
                            logging.info("stopped repeating")
                    except:
                        second_value = None

                    # logging.info("first:{}, second:{}, repeat:{}".format(first_value,second_value))

                    if not first_key_container.repeat_key:
                        logging.info("not repeating")
                        sleep(0.125)
                        first_key_container.set_reveal_child(False)
                        sleep(0.125)
                        GLib.idle_add(first_key_container.self_remove, None)
                        try:
                            del self.key_ids[first_value]
                        except:
                            pass
                        finally:
                            self.last_key = None
                            self.last_key_id = None

                        # sleep(0.25)

                        if len(self.key_ids) == 0:
                            logging.info("key_ids zero")
                            sleep(0.25)
                            key_display = [child for child in self.key_displays_grid.get_children() if (isinstance(child, Gtk.Grid) and hasattr(child, 'active') and child.active is True)]
                            if len(key_display) != 0:
                                key_display = key_display[0]

                                if len(key_display.key_grid.get_children()) == 0:
                                    key_display.key_grid_revealer.set_reveal_child(False)
                                    sleep(0.25)
                                    key_display.active_app_revealer.set_reveal_child(False)
                                    sleep(0.25)
                                    key_display.key_grid_revealer.set_visible(False)
                                    sleep(0.25)
                                    self.standby_revealer.set_reveal_child(True)
                                    GLib.idle_add(self.reposition, None)

                            self.stop_display_cleaner()
                            break

                    elif (datetime.now() - timeout).seconds > (self.app.gio_settings.get_int("repeat-timeout")/1000):
                        logging.info("timeout")
                        first_key_container.repeat_key = False

        self.display_cleaner_thread = threading.Thread(target=init_manager)
        self.display_cleaner_thread.daemon = True
        self.display_cleaner_thread.start()

    def stop_display_cleaner(self):
        self.stop_display_cleaner_thread = True
        self.display_cleaner_thread = None
        self.stop_display_cleaner_thread = False
        logging.info("stopped")

    def get_safe_area(self):
        window_width, window_height = self.get_size()
        root_x, root_y = self.get_position()

        screen = self.get_screen()
        screen_width = screen.width()
        screen_height = screen.height()
        # logging.info("screen:{0}".format((screen_width, screen_height)))

        display = screen.get_display()
        n_monitors = display.get_n_monitors()
        # logging.info("n_monitors:{0}".format(n_monitors))

        monitor = screen.get_monitor_at_window(self.get_window())
        # logging.info("get_monitor_at_window:{0}".format(monitor))

        monitor_geometry = screen.get_monitor_geometry(monitor)
        # logging.info("get_monitor_at_window:{0}".format((monitor_geometry.x, monitor_geometry.y, monitor_geometry.width, monitor_geometry.height)))

        work_area = screen.get_monitor_workarea(monitor)
        # logging.info("work_area:{0}".format((work_area.x, work_area.y, work_area.width, work_area.height)))

        offset_x = monitor_geometry.height - work_area.height
        offset_y = (screen_height-work_area.height)-work_area.y
        # logging.info("offset:{0}".format((offset_x, offset_y)))

        monitor = screen.get_primary_monitor()
        # logging.info("get_primary_monitor:{0}".format(monitor))

        monitor_geometry = screen.get_monitor_geometry(monitor)
        # logging.info("get_monitor_at_window:{0}".format((monitor_geometry.x, monitor_geometry.y, monitor_geometry.width, monitor_geometry.height)))

        work_area = screen.get_monitor_workarea(monitor)
        # logging.info("work_area:{0}".format((work_area.x, work_area.y, work_area.width, work_area.height)))

        offset_y = monitor_geometry.height - work_area.height
        offset_x = (screen_height-work_area.height)-work_area.y
        # logging.info("offset:{0}".format((offset_x, offset_y)))

        safe_area_width = screen_width - (screen_height - work_area.height - work_area.y) * 2
        # logging.info("safe_area:{}, window_width:{}".format(safe_area_width,window_width))

        return safe_area_width, window_width