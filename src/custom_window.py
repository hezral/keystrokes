#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')
from gi.repository import Gtk, Gdk, Handy
import cairo


supports_alpha = False


def screen_changed(widget, old_screen, userdata=None):
    global supports_alpha

    screen = widget.get_screen()
    visual = screen.get_rgba_visual()

    if visual is None:
        print("Your screen does not support alpha channels!")
        visual = screen.get_system_visual()
        supports_alpha = False
    else:
        print("Your screen supports alpha channels!")
        supports_alpha = True

    widget.set_visual(visual)


def expose_draw(widget, event, userdata=None):
    global supports_alpha

    cr = Gdk.cairo_create(widget.get_window())

    if supports_alpha:
        print("setting transparent window")
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5) 
    else:
        print("setting opaque window")
        cr.set_source_rgb(1.0, 1.0, 1.0)

    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.paint()

    return False

def draw(drawing_area, cairo_context):
    # print(locals())
    cairo_context.set_source_rgba(0.0, 0.0, 0.0, 0.5) 
    cairo_context.set_operator(cairo.OPERATOR_SOURCE)
    cairo_context.paint()

def clicked(window, event, userdata=None):
    # toggle window manager frames
    window.set_decorated(not window.get_decorated())


if __name__ == "__main__":
    Handy.init()
    window = Handy.Window()
    # window.set_position(Gtk.WindowPosition.CENTER)
    window.set_default_size(400, 400)
    window.set_title("Alpha Demo")
    window.connect("delete-event", Gtk.main_quit)

    window.set_app_paintable(True)

    # window.connect("screen-changed", screen_changed)

    window.set_decorated(True)
    # window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    # window.connect("button-press-event", clicked)

    # fixed_container = Gtk.Fixed()
    # button = Gtk.Button.new_with_label("button1")
    # button.set_size_request(100, 100)
    # fixed_container.add(button)

    header = Handy.HeaderBar()
    header.props.name = "main"
    header.props.hexpand = True
    header.props.spacing = 0
    header.props.has_subtitle = False
    header.props.show_close_button = False
    header.props.decoration_layout = "close:"

    drawing_area = Gtk.DrawingArea()
    drawing_area.connect("draw", draw)

    inner_grid = Gtk.Grid()
    inner_grid.props.expand = True
    inner_grid.props.halign = inner_grid.props.valign = Gtk.Align.FILL
    inner_grid.props.margin = 2
    inner_grid.add(drawing_area)

    grid = Gtk.Grid()
    grid.props.expand = True
    grid.attach(header, 0, 0, 1, 1)
    grid.attach(inner_grid, 0, 1, 1, 1)

    # inner_grid.connect("draw", expose_draw)
    # window.connect("draw", expose_draw)
    window.add(grid)

    # window.get_style_context().add_class(Gtk.STYLE_CLASS_FLAT)
    # window.get_style_context().add_class("rounded")
    # screen_changed(window, None, None)

    window.show_all()
    Gtk.main()