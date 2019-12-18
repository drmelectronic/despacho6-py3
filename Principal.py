#! /usr/bin/python
# -*- encoding: utf-8 -*-

import gtk
import Salidas
import Widgets
import gobject
import os
import DataLocal
import models
from Http import Http

from uuid import getnode

if __name__ == '__main__':
    gobject.threads_init()


class Aplicacion:

    def __init__(self):
        self.grupo = gtk.WindowGroup()
        self.ventanas = []
        self.http = Http()
        self.http.set_ventanas(self.ventanas)
        self.ventana = self.nueva_ventana()

    def nueva_ventana(self, *args):
        ventana = Salidas.Ventana()
        self.grupo.add_window(ventana)
        ventana.present()
        self.ventanas.append(ventana)
        ventana.connect('cerrar', self.cerrar)
        ventana.connect('nueva-ventana', self.nueva_ventana)
        ventana.login()
        ventana.grab_focus()
        return ventana

    def ticketera(self, widgets, event):
        dialogo = Widgets.Configuracion(self.http)
        self.http.dataLocal.limpiar_data()
        dialogo.cerrar()

    def cerrar(self, ventana):
        print('ventanas', len(self.ventanas))
        self.ventanas.remove(ventana)
        del ventana
        print('ventanas', len(self.ventanas))
        if len(self.ventanas) == 0:
            print('cerrar ventana')
            self.http.reloj.cerrar()
            self.http.sonido.cerrar()
            gtk.main_quit()


class Login(gtk.Window):

    tokens = []

    def __init__(self):
        super(Login, self).__init__()
        self.user = None
        self.pw = None
        self.http = Http()
        self.set_title('Inicie Sesión:')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)

        self.set_decorated(False)
        # self.set_resizable(False)
        pixbuf = gtk.gdk.pixbuf_new_from_file("images/splash.png")
        pixmap, mask = pixbuf.render_pixmap_and_mask()
        width, height = pixmap.get_size()
        self.set_default_size(width, height)
        del pixbuf
        self.set_app_paintable(gtk.TRUE)
        self.realize()
        self.window.set_back_pixmap(pixmap, gtk.FALSE)


        hbox = gtk.HBox(False, 0)
        self.add(hbox)

        vbox_main = gtk.VBox(False, 0)
        hbox.pack_end(vbox_main, False, True, 0)

        vbox = gtk.VBox(False, 54)
        vbox_main.pack_end(vbox, False, True, 48)  # margen inferior

        hbox = gtk.HBox(True, 0)
        vbox.pack_end(hbox, False, False, 0)

        action_area = gtk.HBox(False, 0)
        hbox.pack_end(action_area, False, True, 30)

        self.but_salir = gtk.EventBox()
        imagen = gtk.Image()
        imagen.set_from_file('images/salir.png')
        self.but_salir.add(imagen)
        action_area.pack_end(self.but_salir, False, False, 0)
        self.but_salir.connect('button_press_event', self.salir)

        self.but_login = gtk.EventBox()
        imagen = gtk.Image()
        imagen.set_from_file('images/login.png')
        self.but_login.add(imagen)
        action_area.pack_end(self.but_login, False, False, 0)
        self.but_login.connect('button_press_event', self.comprobar)

        self.clave = Widgets.PlaceholderEntry()
        self.clave.placeholder = 'Clave Personal'
        self.clave.visible = False

        hbox = gtk.HBox(False, 0)
        vbox.pack_end(hbox, True, False, 0)
        hbox.pack_end(self.clave, True, False, 76)

        self.password = Widgets.PlaceholderEntry()
        self.password.placeholder = 'Password Perfil'
        self.password.visible = False

        hbox = gtk.HBox(False, 0)
        vbox.pack_end(hbox, True, False, 0)
        hbox.pack_start(self.password, True, False, 0)
        self.password.connect('activate', lambda w: self.set_focus(self.clave))

        self.username = Widgets.PlaceholderEntry()
        self.username.placeholder = 'Username'

        hbox = gtk.HBox(False, 0)
        vbox.pack_end(hbox, True, False, 0)
        hbox.pack_start(self.username, True, False, 0)
        self.username.connect('activate', lambda w: self.set_focus(self.password))

        self.clave.connect('activate', self.comprobar)


        self.combo = Widgets.ComboBox()
        self.combo.set_lista(self.http.dataLocal.get_empresas())

        hbox = gtk.HBox(False, 0)
        vbox_main.pack_end(hbox, True, False, 0)
        hbox.pack_end(self.combo, True, False, 0)

        self.set_focus(self.username)
        self.mac = str(getnode())
        self.secret_key = 'S3CRE1K3Y'
        self.show_all()
        self.get_credentials()
        self.username._focus_out_event(None, None)
        self.password._focus_out_event(None, None)
        self.clave._focus_out_event(None, None)

    def get_credentials(self):
        if self.http.dataLocal.username:
            self.username.set_text(self.http.dataLocal.username)
        if self.http.dataLocal.password:
            self.password.set_text(self.http.dataLocal.password)
        print('empresa', self.http.dataLocal.empresa)
        if self.http.dataLocal.empresa:
            self.combo.hide()
            self.combo.set_id(self.http.dataLocal.empresa)

    def comprobar(self, *args):
        self.clave._focus_out_event(None, None)
        self.emp = self.combo.get_id()
        self.user = self.username.get_text()
        self.pw = self.password.get_text()
        self.cl = self.clave.get_text()
        login = self.http.login(self.emp, self.user, self.pw, self.cl)
        if login:
            self.http.set_usuario(models.MyUsuario(login))
            Aplicacion()
            self.cerrar()

    def autologin(self):
        self.username.set_text('daniel')
        self.password.set_text('clavetest')
        self.clave.set_text('0000')
        self.comprobar()

    def cerrar(self, *args):
        self.destroy()

    def salir(self, *args):
        self.destroy()
        gtk.main_quit()

if __name__ == '__main__':
    # s = Splash()

    d = DataLocal.DataLocal()
    d.load_main()
    d.load_config()
    http = Http()
    http.construir()
    d.http = http
    http.dataLocal = d
    dialog = Login()
    # dialog.autologin()
    try:
        gtk.main()
    except:
        print('Ctrl + C')
        try:
            http.reloj.cerrar()
        except:
            pass
        try:
            http.sonido.cerrar()
        except:
            pass
    else:
        print('EXIT GTK')
    # try:
    #     gtk.main()
    # except BaseException:
    #     s.a.http.reloj.cerrar()
        # gtk.main_quit()
    if os.name == 'nt':
        os.system('taskkill /im TCONTUR6.exe /f')