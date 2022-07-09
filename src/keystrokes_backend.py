# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from pynput import keyboard, mouse

from time import sleep

import threading

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(asctime)s, %(funcName)s:%(lineno)d: %(message)s")


class KeyListener():
    def __init__(self, on_press_callback, on_release_callback, *args, **kwargs):
        
        self.keyboard = keyboard

        self.listener = keyboard.Listener(
            on_press=on_press_callback,
            on_release=on_release_callback
        )
        self.listener.start()

        logging.info("key listener started")


class MouseListener():

    stop_thread = False
    id_thread = None
    callback = None

    def __init__(self, on_move_callback, on_click_callback, on_scroll_callback, *args, **kwargs):

        self.mouse = mouse
        
        self.listener = self.mouse.Listener(
            on_move=on_move_callback,
            on_click=on_click_callback,
            on_scroll=on_scroll_callback)
        self.listener.start()

        logging.info("mouse listener started")

    
#     def _run(self, callback=None):

#         self.callback = callback

#         def init_monitor():
#             while True:  # next_event() sleeps until we get an event
#                 logging.info("movements monitoring")
#                 sleep(5)
#                 if self.stop_thread:
#                     break

#         self.thread = threading.Thread(target=init_monitor)
#         self.thread.daemon = True
#         self.thread.start()
#         logging.info("movements monitor started")

#     def _stop(self):
#         logging.info("movements monitor stopped")
#         self.stop_thread = True

# class MouseController():

#     def __init__(self, *args, **kwargs):

#         self.mouse = mouse
        
#         self.controller = self.mouse.Controller()

#         logging.info("mouse controller started")
