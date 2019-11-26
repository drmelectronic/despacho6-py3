import gi

import Widgets

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository import GObject




if __name__ == '__main__':
    def nueva_ventana(*args):
        print('nueva_ventana')

    def flota(*args):
        print('flota')

    w = Gtk.Window()
    entry = Gtk.Entry()
    entry.set_text('HOLA')
    w.add(entry)
    w.show_all()
    entry.select_region(2, 3)

    Gtk.main()