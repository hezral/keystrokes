
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

import time
from datetime import datetime

from pynput import mouse

SHAKE_DIST = 250
SHAKE_SLICE_TIMEOUT = 75 # ms
SHAKE_TIMEOUT = 500 # ms
EVENT_TIMEOUT = 50 # ms
SHOWING_TIMEOUT = 2500 #ms
NEEDED_SHAKE_COUNT = 4
SENSITIVITY_HIGH = 2
SENSITIVITY_MEDIUM = 4
SENSITIVITY_LOW = 7


class MouseListener():
    def __init__(self, widget, *args, **kwargs):
        
        self.label = widget

        self.init_listener()

    def init_listener(self, data=None):
        self.showing_timestamp = datetime.now()
        self.shake_slice_timestamp = datetime.now()
        self.shake_timeout_timestamp = datetime.now()
        self.showing_timestamp_diff = 0
        self.shake_slice_timestamp_diff = 0
        self.shake_timeout_timestamp_diff = 0
        
        self.now_x = 0
        self.old_x = 0
        self.min_x = 0
        self.max_x = 0
        self.has_min = 0
        self.has_max = 0
        self.shake_count = 0
        
        self.showing = False
        
        self.update_label(True)

        self.listener = mouse.Listener(
            on_move=self.on_move,
            on_click=None,
            on_scroll=None)
        self.listener.start()

        print("init")
    
    def on_move(self, x, y):
        self.detect_mouse_movement(x)
        self.update_mouse()
        
        time.sleep(EVENT_TIMEOUT/1000)

    def update_label(self, clear):
        if not clear:
            state = "is_shaking:{0}, shake_count:{1}, showing:{2}".format(self.isShaking, self.shake_count, self.showing)
            details1 = "now_x:{0}, old_x:{1}".format(self.now_x, self.old_x)
            details2 = "min_x:{0}, max_x:{1}".format(self.min_x, self.max_x)
            details3 = "has_min:{0}, has_max:{1}".format(self.has_min, self.has_max)
            details4 = "showing_timestamp:{0}".format(self.showing_timestamp)
            details5 = "shake_timeout_timestamp:{0}".format(self.shake_timeout_timestamp)
            details6 = "shake_timeout_timestamp_diff:{0}".format(self.shake_timeout_timestamp_diff)
            details7 = "shake_slice_timestamp:{0}".format(self.shake_slice_timestamp)
            details8 = "shake_slice_timestamp_diff:{0}".format(self.shake_slice_timestamp_diff)
            details9 = "self.shake_timeout_timestamp_diff >= SHAKE_TIMEOUT:{0}".format(self.shake_timeout_timestamp_diff >= SHAKE_TIMEOUT)
            details10 = "self.shake_slice_timestamp_diff >= SHAKE_SLICE_TIMEOUT:{0}".format(self.shake_slice_timestamp_diff >= SHAKE_SLICE_TIMEOUT)
            details11 = "self.max_x-self.min_x > SHAKE_DIST:{0}".format(self.max_x-self.min_x > SHAKE_DIST)
            update = "{0}\n\n{1}\n\n{2}\n\n{3}\n\n{4}\n\n{5}\n\n{6}\n\n{7}\n\n{8}\n\n{9}\n\n{10}\n\n{11}\n".format(state, details1, details2, details3, details4, details5, details6, details7, details8, details9, details10, details11)
            update = state
        else:
            update = "-"
        GLib.idle_add(self.label.set_text, update)

    def detect_mouse_movement(self, x):
        self.now_x = x

        if self.now_x < self.old_x:
            if self.has_min == 0:
                self.has_min = 1
                self.min_x = self.now_x
            else:
                self.min_x = min(self.min_x, self.now_x)

        elif self.now_x > self.old_x:
            if self.has_max == 0:
                self.has_max = 1
                self.max_x = self.now_x
            else:
                self.max_x = max(self.max_x, self.now_x)

        self.old_x = self.now_x

    def is_shaking(self):
        self.isShaking = False

        self.shake_slice_timestamp_diff = int((datetime.now()-self.shake_slice_timestamp).total_seconds()*1000)
        if self.shake_slice_timestamp_diff >= SHAKE_SLICE_TIMEOUT:
            self.shake_slice_timestamp = datetime.now()

            if self.has_min == 1:
                if self.has_max == 1:
                    if self.max_x-self.min_x > SHAKE_DIST:
                        self.shake_count += 1
                        self.shake_timeout_timestamp = datetime.now()
            
            if self.shake_count >= NEEDED_SHAKE_COUNT:
                self.showing_timestamp = datetime.now()
                self.shake_count = 0
                self.isShaking = True
                self.has_min = 0
                self.has_max = 0
                self.min_x = 0
                self.max_x = 0

        return self.isShaking

    def hide_big_mouse_on_timeout(self):
        self.showing_timestamp_diff = int((datetime.now()-self.showing_timestamp).total_seconds()*1000)
        if self.showing_timestamp_diff >= SHOWING_TIMEOUT:
            self.hide_big()
            self.shake_count = 0

    def update_mouse(self):
        if self.showing is True:
            print("showing")
            self.hide_big_mouse_on_timeout()
        else:
            if self.is_shaking():
                self.show_big()
                # self.move_big_mouse()
        
            self.shake_timeout_timestamp_diff = int((datetime.now()-self.shake_timeout_timestamp).total_seconds()*1000)
            if self.shake_timeout_timestamp_diff >= SHAKE_TIMEOUT:
                self.shake_timeout_timestamp = datetime.now()
                self.shake_count = 0

    def show_big(self):
        if self.showing is False:
            self.showing = True
            # self.listener = mouse.Listener(
            #     on_move=self.on_move,
            #     on_click=None,
            #     on_scroll=None,
            #     suppress=True)
            # do something to show window
            self.update_label(False)
            self.listener.stop()
            GLib.timeout_add(SHOWING_TIMEOUT, self.init_listener, None)
            print("show_big")

    def hide_big(self):
        if self.showing is True:
            self.showing = False
            # self.listener = mouse.Listener(
            #     on_move=self.on_move,
            #     on_click=None,
            #     on_scroll=None,
            #     suppress=False)
            # do something to hide window
            self.init_listener()
            print("hide_big")

    def is_enabled(self):
        return True

    def need_ctrl(self):
        return True

    def is_ctrl_pressed(self):
        return True


class PyApp(Gtk.Window):
    def __init__(self):
        super().__init__()

        self.set_title("Mouse coordinates 0.1")
        self.connect("destroy", self.quit)

        label = Gtk.Label()

        self.mouse_listener = MouseListener(label)

        fixed = Gtk.Fixed()
        fixed.props.halign = fixed.props.valign = Gtk.Align.CENTER
        fixed.put(label, 10, 10)

        self.set_size_request(400, 400)
        self.add(fixed)
        self.show_all()

    def quit(self, widget):
        self.mouse_listener.listener.stop()
        Gtk.main_quit()


if __name__ == '__main__':
    app = PyApp()
    Gtk.main()