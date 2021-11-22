# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from pynput import keyboard, mouse
from datetime import datetime

class KeyListener():
    def __init__(self, on_press_callback, on_release_callback, *args, **kwargs):
        
        self.keyboard = keyboard

        self.listener = keyboard.Listener(
            on_press=on_press_callback,
            on_release=on_release_callback)
        self.listener.start()

        print(datetime.now(), "key listener started")


class MouseListener():
    def __init__(self, on_move_callback, on_click_callback, on_scroll_callback, *args, **kwargs):

        self.mouse = mouse
        
        self.listener = self.mouse.Listener(
            on_move=on_move_callback,
            on_click=on_click_callback,
            on_scroll=on_scroll_callback)
        self.listener.start()

        print(datetime.now(), "mouse listener started")


# import signal
# import gi
# gi.require_version('Gtk', '3.0')
# from gi.repository import Gtk, GLib
# GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, Gtk.main_quit) 

# Gtk.main()


# from Xlib.display import Display
# from Xlib import X, XK
# import signal, sys

# import gi
# from gi.repository import Gdk

# def main():
#     display = Display()
#     root = display.screen().root

#     root.change_attributes(event_mask = X.KeyPressMask|X.KeyReleaseMask)
#     root.grab_keyboard(False, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)

#     signal.signal(signal.SIGINT, lambda a,b:sys.exit(1))
#     # signal.alarm(4)
    

#     while True:
#         event = root.display.next_event()
#         if event.type in [X.KeyPress]:
#             keycode = event.detail
#             keysym = display.keycode_to_keysym(keycode, 0)
#             char = XK.keysym_to_string(keysym)
#             display.allow_events(X.ReplayKeyboard, X.CurrentTime)
#             keyval_name = Gdk.keyval_name(keysym)
#             print(keycode, keysym, char, keyval_name)

# if __name__ == '__main__':
#     main()