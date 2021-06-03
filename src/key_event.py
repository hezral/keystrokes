# key_event.py
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

from pynput import keyboard, mouse

class KeyListener():
    def __init__(self, on_press_callback, on_release_callback, *args, **kwargs):
        
        self.keyboard = keyboard

        self.listener = keyboard.Listener(
            on_press=on_press_callback,
            on_release=on_release_callback)
        self.listener.start()


class MouseListener():
    def __init__(self, on_move_callback, on_click_callback, on_scroll_callback, *args, **kwargs):

        self.mouse = mouse
        
        self.listener = self.mouse.Listener(
            on_move=on_move_callback,
            on_click=on_click_callback,
            on_scroll=on_scroll_callback)
        self.listener.start()



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