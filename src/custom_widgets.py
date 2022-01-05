# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from Xlib.protocol import event
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
from gi.repository import GObject, Gtk, Granite, Gdk, Pango, Gio, GLib

class CustomDialog(Gtk.Window):
    def __init__(self, dialog_parent_widget, dialog_title, dialog_content_widget, action_button_label, action_button_name, action_callback, action_type, size=None, data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parent_window = dialog_parent_widget.get_toplevel()

        def on_close_window():
            self.destroy()

        def close_dialog(button):
            on_close_window()

        def on_key_press(self, eventkey):
            if eventkey.keyval == 65307: #63307 is esc key
                on_close_window()

        self.header = Gtk.HeaderBar()
        self.header.props.show_close_button = False
        self.header.props.title = dialog_title
        self.header.get_style_context().add_class("default-decoration")
        self.header.get_style_context().add_class(Gtk.STYLE_CLASS_FLAT)

        grid = Gtk.Grid()
        grid.props.expand = True
        grid.props.margin_top = 0
        grid.props.margin_bottom = grid.props.margin_left = grid.props.margin_right = 15
        grid.props.row_spacing = 10
        grid.props.column_spacing = 10
        grid.attach(dialog_content_widget, 0, 0, 2, 1)

        if action_type is not None:
            dialog_parent_widget.ok_button = Gtk.Button(label=action_button_label)
            dialog_parent_widget.ok_button.props.name = action_button_name
            dialog_parent_widget.ok_button.props.expand = False
            dialog_parent_widget.ok_button.props.halign = Gtk.Align.END
            dialog_parent_widget.ok_button.set_size_request(65,25)
            if action_type == "destructive":
                dialog_parent_widget.ok_button.get_style_context().add_class("destructive-action")
            else:
                dialog_parent_widget.ok_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

            dialog_parent_widget.cancel_button = Gtk.Button(label="Cancel")
            dialog_parent_widget.cancel_button.props.hexpand = True
            dialog_parent_widget.cancel_button.props.halign = Gtk.Align.END
            dialog_parent_widget.cancel_button.set_size_request(65,25)

            dialog_parent_widget.ok_button.connect("clicked", action_callback, (data, dialog_parent_widget.cancel_button))
            dialog_parent_widget.cancel_button.connect("clicked", close_dialog)

            grid.attach(dialog_parent_widget.cancel_button, 0, 1, 1, 1)
            grid.attach(dialog_parent_widget.ok_button, 1, 1, 1, 1)

        if size is not None:
            self.set_size_request(size[0],size[1])
        else:
            self.set_size_request(150,100)

        self.get_style_context().add_class("rounded")
        self.get_style_context().add_class("custom-decoration")
        self.get_style_context().add_class("custom-decoration-overlay")
        self.set_titlebar(self.header)
        self.props.transient_for = parent_window
        # self.props.modal = True
        self.props.resizable = False
        self.props.window_position = Gtk.WindowPosition.CENTER_ON_PARENT
        self.add(grid)
        self.show_all()
        self.connect("destroy", close_dialog)
        self.connect("key-press-event", on_key_press)


class ContainerRevealer(Gtk.Revealer):
    def __init__(self, keyname, widget, id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.props.name = keyname
        self.props.transition_duration = 500
        self.props.transition_type = Gtk.RevealerTransitionType.CROSSFADE

        self.repeat_key_counter = 0
        self.id = id

        self.counter = Gtk.Label(self.repeat_key_counter)
        self.counter.props.name = "repeat-counter"
        self.counter.props.expand = False
        self.counter.props.margin_top = 20
        self.counter.props.halign = Gtk.Align.START
        self.counter.props.valign = Gtk.Align.START
        self.counter.get_style_context().add_class(Granite.STYLE_CLASS_CARD)

        self.overlay = Gtk.Overlay()
        self.overlay.add(widget)
        self.add(self.overlay)

    def self_remove(self, *args):
        self.destroy()


class KeySquareContainer(Gtk.Grid):
    def __init__(self, keyname, key_type, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.props.name = "key-container"
        self.props.hexpand = True
        # self.props.margin = 5
        self.props.halign = self.props.valign = Gtk.Align.CENTER
        self.set_size_request(64, 64)

        keymap = Gdk.Keymap().get_for_display(Gdk.Display.get_default())
        if keymap.get_caps_lock_state():
            keyname = keyname.upper()
        self.label = Gtk.Label(keyname)
        self.label.props.name = "single-key"
        self.label.props.expand = True
        self.label.props.halign = self.label.props.valign = Gtk.Align.CENTER
        self.attach(self.label, 0, 0, 1, 1)


class KeyRectangleContainer(Gtk.Grid):

    symbols = {
        "cmd": "⌘",
        "alt": "⌥",
        "alt_r": "⌥",
        "shift": "⇧",
        "shift_r": "⇧",
        "ctrl": "⌃",
        "ctrl_r": "⌃",
        "enter": "↵",
        "backspace": "⌫",
        "delete": "⌦",
        "caps_lock": "⇪",
        "tab": "↹",
        "left": "◁",
        "right": "▷",
        "up": "△",
        "down": "▽ ",
        "page_up": "△",
        "page_down": "▽ ",
        "space": "⎵",
        "esc": "⎋",
        "break": "⎊",
        "pause": "⎉",
        "scroll_lock": "⇳",
        "print_screen": "⎙",
    }

    def __init__(self, keyname, key_type, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if keyname[0] == "f" and isinstance(int(keyname[1]),int):
            keyname = keyname.upper()

        self.props.name = "key-container"
        # self.props.margin = 5
        self.props.hexpand = True
        self.props.halign = self.props.valign = Gtk.Align.CENTER
        self.set_size_request(96, 64)

        self.label = Gtk.Label(keyname.replace("_"," "))
        self.label.props.name = "mod-key"
        self.label.props.expand = True
        self.label.props.margin_bottom = 10
        self.label.props.margin_left = 15
        self.label.props.margin_right = 15
        self.label.props.valign = Gtk.Align.END

        if keyname in ["shift_r", "alt_r", "enter", "backspace", "delete"]:
            self.label.props.halign = Gtk.Align.END
        else:
            self.label.props.halign = Gtk.Align.START

        if "caps" in keyname or "num" in keyname or "scroll" in keyname:
            self.generate_capsnumlock_symbol(keyname)

        if keyname in self.symbols.keys():
            self.generate_symbol(keyname)

        if keyname == "cmd":
            self.label.props.label = ""
            self.set_size_request(64, 64)

        self.attach(self.label, 0, 0, 1, 1)

    def generate_capsnumlock_symbol(self, keyname):
        on_state = Gtk.Label("°")
        on_state.props.name = "on-state"
        on_state.props.expand = True
        on_state.props.margin_left = 12
        on_state.props.margin_top = 0
        on_state .props.halign = on_state.props.valign = Gtk.Align.START

        default_state = Gtk.Label("°")
        default_state.props.name = "default-state"
        default_state.props.expand = True
        default_state.props.margin_left = 12
        default_state.props.margin_top = 0
        default_state.props.halign = default_state.props.valign = Gtk.Align.START

        keymap = Gdk.Keymap().get_for_display(Gdk.Display.get_default())
        
        self.attach(default_state, 0, 0, 1, 1)
        
        if "caps" in keyname:
            state = keymap.get_caps_lock_state()
        if "num" in keyname:
            state = keymap.get_num_lock_state()
        if "scroll" in keyname:
            state = keymap.get_scroll_lock_state()
        
        if state:
            self.attach(on_state, 0, 0, 1, 1)

    def generate_symbol(self, keyname):

        symbol = Gtk.Label(self.symbols[keyname])
        symbol.props.expand = True

        if keyname == "cmd":
            symbol.props.name = "symbol-large"
            symbol.props.valign = Gtk.Align.CENTER
            symbol.props.halign = Gtk.Align.CENTER
        else:
            symbol.props.name = "symbol"
            symbol.props.margin_right = 8
            symbol.props.margin_top = 4
            symbol.props.halign = Gtk.Align.END
            symbol.props.valign = Gtk.Align.START

        self.attach(symbol, 0, 0, 1, 1)


class MouseContainer(Gtk.Grid):
    def __init__(self, keyname, key_type, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.props.name = "mouse-container"
        self.props.hexpand = True
        # self.props.margin = 5
        self.props.halign = self.props.valign = Gtk.Align.CENTER
        self.set_size_request(50, 80)

        if key_type == "mouse":
            if keyname == "left":
                self.key_image = Gtk.Image().new_from_icon_name("mouse-left-symbolic", Gtk.IconSize.DND)
            elif keyname == "right":
                self.key_image = Gtk.Image().new_from_icon_name("mouse-right-symbolic", Gtk.IconSize.DND)
            elif keyname == "scrollup":
                self.key_image = Gtk.Image().new_from_icon_name("mouse-scrollup-symbolic", Gtk.IconSize.DND)
            elif keyname == "scrolldown":
                self.key_image = Gtk.Image().new_from_icon_name("mouse-scrolldown-symbolic", Gtk.IconSize.DND)
            elif keyname == "scrollleft":
                self.key_image = Gtk.Image().new_from_icon_name("mouse-scrollleft-symbolic", Gtk.IconSize.DND)
            elif keyname == "scrollright":
                self.key_image = Gtk.Image().new_from_icon_name("mouse-scrollright-symbolic", Gtk.IconSize.DND)
            self.key_image.set_pixel_size(56)
            self.key_image.props.name = "single-key"
            self.key_image.props.expand = True
            self.key_image.props.halign = self.key_image.props.valign = Gtk.Align.CENTER
            self.attach(self.key_image, 0, 0, 1, 1)


class SettingsGroup(Gtk.Grid):
    def __init__(self, group_label=None, subsettings_list=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        grid = Gtk.Grid()
        grid.props.margin = 8
        grid.props.hexpand = True
        grid.props.row_spacing = 8
        grid.props.column_spacing = 10

        i = 0
        for subsetting in subsettings_list:
            grid.attach(subsetting, 0, i, 1, 1)
            i += 1

        frame = Gtk.Frame()
        frame.props.name = "settings-group-frame"
        frame.props.hexpand = True
        frame.add(grid)
        self.attach(frame, 0, 1, 1, 1)

        if group_label is not None:
            label = Gtk.Label(group_label)
            label.props.name = "settings-group-label"
            label.props.halign = Gtk.Align.START
            label.props.margin_left = 4
            self.attach(label, 0, 0, 1, 1)

        self.props.name = "settings-group"
        self.props.halign = Gtk.Align.FILL
        self.props.hexpand = True
        self.props.row_spacing = 4
        self.props.can_focus = False


class SubSettings(Gtk.Grid):
    def __init__(self, type=None, name=None, label=None, sublabel=None, separator=True, params=None, utils=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.type = type

        # box---
        box = Gtk.VBox()
        box.props.spacing = 2
        box.props.hexpand = True

        # label---
        if label is not None:
            self.label_text = Gtk.Label(label)
            self.label_text.props.halign = Gtk.Align.START
            box.add(self.label_text)
        
        # sublabel---
        if sublabel is not None:
            self.sublabel_text = Gtk.Label(sublabel)
            self.sublabel_text.props.halign = Gtk.Align.START
            self.sublabel_text.props.wrap_mode = Pango.WrapMode.WORD
            self.sublabel_text.props.max_width_chars = 30
            self.sublabel_text.props.justify = Gtk.Justification.LEFT
            #self.sublabel_text.props.wrap = True
            self.sublabel_text.get_style_context().add_class("settings-sub-label")
            box.add(self.sublabel_text)

        if type == "switch":
            self.switch = Gtk.Switch()
            self.switch.props.name = name
            self.switch.props.halign = Gtk.Align.END
            self.switch.props.valign = Gtk.Align.CENTER
            self.switch.props.hexpand = False
            self.attach(self.switch, 1, 0, 1, 2)

        if type == "spinbutton":
            self.spinbutton = Gtk.SpinButton().new_with_range(min=params[0], max=params[1], step=params[2])
            self.spinbutton.props.name = name
            self.attach(self.spinbutton, 1, 0, 1, 2)

        if type == "button":
            if len(params) == 1:
                self.button = Gtk.Button(label=params[0])
            else:
                self.button = Gtk.Button(label=params[0], image=params[1])
            self.button.props.name = name
            self.button.props.hexpand = False
            self.button.props.always_show_image = True
            self.button.set_size_request(90, -1)
            if len(params) >1:
                label = [child for child in self.button.get_children()[0].get_child() if isinstance(child, Gtk.Label)][0]
                label.props.valign = Gtk.Align.CENTER
            self.attach(self.button, 1, 0, 1, 2)

        if type == "checkbutton":
            self.checkbutton = Gtk.CheckButton().new_with_label(params[0])
            self.checkbutton.props.name = name
            self.attach(self.checkbutton, 0, 0, 1, 2)

        if type == "comboboxtext":
            self.combobox = Gtk.ComboBoxText()
            self.combobox.props.name = name
            self.combobox.props.popup_fixed_width = False
            for param in params:
                self.combobox.append(id=param, text=param)
            self.attach(self.combobox, 1, 0, 1, 2)

        if type == "radiobutton":
            self.radiobutton1 = Gtk.RadioButton().new_with_label(group=None, label=params[0])
            self.radiobutton2 = Gtk.RadioButton().new_with_label(group=None, label=params[1])
            self.radiobutton3 = Gtk.RadioButton().new_with_label(group=None, label="Off")
            self.radiobutton2.join_group(self.radiobutton1)
            self.radiobutton3.join_group(self.radiobutton1)
            self.attach(self.radiobutton1, 1, 0, 1, 2)
            self.attach(self.radiobutton2, 2, 0, 1, 2)
            self.attach(self.radiobutton3, 3, 0, 1, 2)

        # separator ---
        if separator:
            row_separator = Gtk.Separator()
            row_separator.props.hexpand = True
            row_separator.props.valign = Gtk.Align.CENTER
            if type == None:
                self.attach(row_separator, 0, 0, 1, 1)
            else:
                self.attach(row_separator, 0, 2, 2, 1)
        
        # SubSettings construct---
        self.props.name = name
        self.props.hexpand = True
        if type == None:
            self.attach(box, 0, 0, 1, 1)
        else:
            self.props.row_spacing = 8
            self.props.column_spacing = 10
            self.attach(box, 0, 0, 1, 2)


class Settings(Gtk.Grid):

    NORTH_WEST = 1 #the reference point is at the top left corner
    NORTH = 2 #the reference point is in the middle of the top edge
    NORTH_EAST = 3 #the reference point is at the top right corner
    WEST = 4 #the reference point is at the middle of the left edge
    CENTER = 5 #the reference point is at the center of the window
    EAST = 6 #the reference point is at the middle of the right edge
    SOUTH_WEST = 7 #the reference point is at the lower left corner
    SOUTH = 8 #the reference point is at the middle of the lower edge
    SOUTH_EAST = 9 #the reference point is at the lower right corner
    STATIC = 10 #the reference point is at the top left corner of the window itself, ignoring window manager decorations

    def __init__(self, gtk_application, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = gtk_application

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.props.row_spacing = 8

        self.screen_icon = Gtk.Grid()
        self.screen_icon.props.expand = True
        self.screen_icon.props.margin = 8
        self.screen_icon.props.halign = self.screen_icon.props.valign = Gtk.Align.CENTER
        self.screen_icon.props.height_request = 140
        self.screen_icon.props.width_request = 200
        self.screen_icon.get_style_context().add_class("screen-display")

        northwest = Gtk.EventBox()
        northwest.props.name = str(self.NORTH_WEST)
        north = Gtk.EventBox()
        north.props.name = str(self.NORTH)
        northeast = Gtk.EventBox()
        northeast.props.name = str(self.NORTH_EAST)
        east = Gtk.EventBox()
        east.props.name = str(self.EAST)
        southeast = Gtk.EventBox()
        southeast.props.name = str(self.SOUTH_EAST)
        south = Gtk.EventBox()
        south.props.name = str(self.SOUTH)
        southwest = Gtk.EventBox()
        southwest.props.name = str(self.SOUTH_WEST)
        west = Gtk.EventBox()
        west.props.name = str(self.WEST)
        center = Gtk.EventBox()
        center.props.name = str(self.CENTER)

        for position_eventbox in [northwest, north, northeast, east, southeast, south, southwest, west, center]:
            position_eventbox.props.expand = True
            position_eventbox.props.above_child = True
            position_eventbox.props.halign = position_eventbox.props.valign = Gtk.Align.FILL
            position_eventbox.connect("enter-notify-event", self.on_screen_position_hover)
            position_eventbox.connect("leave-notify-event", self.on_screen_position_hover)
            position_eventbox.connect("button_press-event", self.on_screen_position_clicked)
            button = Gtk.Button(label="•••")
            button.props.expand = True
            button.props.halign = button.props.valign = Gtk.Align.CENTER
            button.get_style_context().add_class("position-default")
            position_eventbox.add(button)
            if self.app.gio_settings.get_int("screen-position") == int(position_eventbox.props.name):
                button.get_style_context().add_class("position-selected")

        self.screen_icon.attach(northwest, 0, 0, 1, 1)
        self.screen_icon.attach(north, 1, 0, 1, 1)
        self.screen_icon.attach(northeast, 2, 0, 1, 1)
        self.screen_icon.attach(west, 0, 1, 1, 1)
        self.screen_icon.attach(center, 1, 1, 1, 1)
        self.screen_icon.attach(east, 2, 1, 1, 1)
        self.screen_icon.attach(southwest, 0, 2, 1, 1)
        self.screen_icon.attach(south, 1, 2, 1, 1)
        self.screen_icon.attach(southeast, 2, 2, 1, 1)

        position_label = SubSettings(type=None, name="position-label", label="Screen position", sublabel=None, separator=False, params=None)

        monitor_label = SubSettings(type=None, name="monitor-label", label="Event monitoring", sublabel=None, separator=False, params=None)
        
        monitor_movements = SubSettings(type="checkbutton", name="monitor-movements", label=None, sublabel=None, separator=False, params=("Movements",))
        self.app.gio_settings.bind("monitor-movements", monitor_movements.checkbutton, "active", Gio.SettingsBindFlags.DEFAULT)

        monitor_scrolls = SubSettings(type="checkbutton", name="monitor-scrolls", label=None, sublabel=None, separator=False, params=("Scrolls",))
        self.app.gio_settings.bind("monitor-scrolls", monitor_scrolls.checkbutton, "active", Gio.SettingsBindFlags.DEFAULT)

        monitor_clicks = SubSettings(type="checkbutton", name="monitor-clicks", label=None, sublabel=None, separator=False, params=("Clicks",))
        self.app.gio_settings.bind("monitor-clicks", monitor_clicks.checkbutton, "active", Gio.SettingsBindFlags.DEFAULT)

        monitor_key_press = SubSettings(type="checkbutton", name="monitor-key-press", label=None, sublabel=None, separator=False, params=("Key Press",))
        self.app.gio_settings.bind("monitor-key-press", monitor_key_press.checkbutton, "active", Gio.SettingsBindFlags.DEFAULT)

        monitor_key_release = SubSettings(type="checkbutton", name="monitor-key-release", label=None, sublabel=None, separator=False, params=("Key Release",))
        self.app.gio_settings.bind("monitor-key-release", monitor_key_release.checkbutton, "active", Gio.SettingsBindFlags.DEFAULT)

        monitor_repeatkeys = SubSettings(type="checkbutton", name="monitor-repeatkeys", label=None, sublabel=None, separator=False, params=("Repeats",))
        monitor_repeatkeys.props.has_tooltip = True
        monitor_repeatkeys.props.tooltip_text = "Experimental, may cause app freezes/crashes"
        self.app.gio_settings.bind("monitor-repeatkeys", monitor_repeatkeys.checkbutton, "active", Gio.SettingsBindFlags.DEFAULT)

        monitor_separator = SubSettings(type=None, name="dummy-setting", label=None, sublabel=None, separator=True, params=None)

        monitor_grid = Gtk.Grid()
        monitor_grid.props.hexpand = True
        monitor_grid.props.halign = Gtk.Align.START
        monitor_grid.props.column_spacing = 10
        monitor_grid.props.row_spacing = 8
        monitor_grid.attach(monitor_movements, 0, 0, 1, 1)
        monitor_grid.attach(monitor_scrolls, 1, 0, 1, 1)
        monitor_grid.attach(monitor_clicks, 2, 0, 1, 1)
        monitor_grid.attach(monitor_key_press, 0, 1, 1, 1)
        monitor_grid.attach(monitor_key_release, 1, 1, 1, 1)
        # monitor_grid.attach(monitor_repeatkeys, 4, 0, 1, 1)

        sticky_mode = SubSettings(type="switch", name="sticky-mode", label="Sticky mode", sublabel="Display on all workspaces",separator=True)
        sticky_mode.switch.connect_after("notify::active", self.on_switch_activated)
        self.app.gio_settings.bind("sticky-mode", sticky_mode.switch, "active", Gio.SettingsBindFlags.DEFAULT)

        display_timeout = SubSettings(type="spinbutton", name="display-timeout", label="Display timeout (ms)", sublabel="How long until key dissapears", separator=True, params=(1000,15000,250))
        self.app.gio_settings.bind("display-timeout", display_timeout.spinbutton, "value", Gio.SettingsBindFlags.DEFAULT)
        
        display_transparency = SubSettings(type="spinbutton", name="display-transparency", label="Display transparency", sublabel="Customize window transparency", separator=True, params=(0,100,1))
        display_transparency.spinbutton.connect("value-changed", self.on_spinbutton_activated)
        self.app.gio_settings.bind("display-transparency", display_transparency.spinbutton, "value", Gio.SettingsBindFlags.DEFAULT)

        display_transparency_slider = Gtk.Scale().new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        display_transparency_slider.props.draw_value = False
        
        auto_position = SubSettings(type="switch", name="auto-position", label="Auto position", sublabel="Revert window position", separator=True)
        self.app.gio_settings.bind("auto-position", auto_position.switch, "active", Gio.SettingsBindFlags.DEFAULT)
        auto_position.switch.bind_property("active", self.screen_icon, "sensitive", GObject.BindingFlags.DEFAULT)
        if not auto_position.switch.props.active:
            self.screen_icon.props.sensitive = False

        display_behaviour_settings = SettingsGroup(None, (monitor_label, monitor_grid, monitor_separator, sticky_mode, display_timeout, display_transparency, auto_position, position_label, self.screen_icon))
        self.add(display_behaviour_settings)

    def on_screen_position_clicked(self, eventbox, eventbutton):
        for child in self.screen_icon.get_children():
            child.get_child().get_style_context().remove_class("position-selected")
        eventbox.get_child().get_style_context().add_class("position-selected")
        self.app.gio_settings.set_int("screen-position", int(eventbox.props.name))
        self.app.main_window.reposition()

    def on_screen_position_hover(self, eventbox, eventcrossing):
        if eventcrossing.type.value_name == "GDK_ENTER_NOTIFY":
            eventbox.get_child().get_style_context().add_class("position-hover")
        else:
            eventbox.get_child().get_style_context().remove_class("position-hover")
    
    def on_switch_activated(self, switch, gparam):
        name = switch.get_name()
        
        if self.is_visible():
            if name == "sticky-mode":
                if switch.get_active():
                    self.app.main_window.stick()
                else:
                    self.app.main_window.unstick()

            if name == "monitor-scrolls":
                self.app.main_window.setup_mouse_listener()

            if name == "monitor-clicks":
               self.app.main_window.setup_mouse_listener()

            if name == "monitor-key-press" or name == "monitor-key-release":
                self.app.main_window.setup_keyboard_listener()

    def on_spinbutton_activated(self, spinbutton):        
        name = spinbutton.get_name()

        if self.is_visible():
            if name == "display-transparency":
                transparency_value = float(spinbutton.props.value/100)
                self.app.main_window.setup_ui(transparency_value)
