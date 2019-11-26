from threading import Thread

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

import os


class Splash:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_title("Launching Astrogator initalized!")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        path = os.path.join('images', 'splash.png')
        box = Gtk.VBox()
        image_area = Gtk.Box()
        box.add(image_area)
        image = Gtk.Image()
        image.set_from_file(path)
        image_area.add(image)
        image_area.show_all()
        self.window.add(box)
        print('Splash mostrado')
        self.window.show_all()

    def destroy(self):
        self.window.destroy()


if __name__ == "__main__":
    splashScreen = Splash()
    Gtk.main()