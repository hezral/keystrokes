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