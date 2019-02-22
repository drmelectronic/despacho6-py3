#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "daniel"
__date__ = "$06-mar-2012 16:06:23$"

import gtk
import Modulos
import Widgets
import datetime
import os
import gobject
if os.name != 'nt':
    import sh

class Ventana(gtk.Window):

    __gsignals__ = {'cerrar': (gobject.SIGNAL_RUN_LAST,
        gobject.TYPE_NONE, ()),
            'login': (gobject.SIGNAL_RUN_LAST,
        gobject.TYPE_NONE, ()),
            'salidas': (gobject.SIGNAL_RUN_LAST,
        gobject.TYPE_NONE, ())
        }

    def __init__(self, principal, titulo, toolbar, twist, status_bar, version, ticketera):
        self.version = version
        super(Ventana, self).__init__()
        pixbuf = gtk.gdk.pixbuf_new_from_file("images/fondo-salida.jpg")
        pixmap, mask = pixbuf.render_pixmap_and_mask()
        width, height = pixmap.get_size()
        del pixbuf
        self.twist = twist
        self.status_bar = status_bar
        self.logueado = False
        self.set_app_paintable(gtk.TRUE)
        self.realize()
        self.window.set_back_pixmap(pixmap, gtk.FALSE)
        self.principal = principal
        self.http = principal.http
        self.http.connect('update', self.actualizar)
        self.sonido = self.http.sonido
        self.connect('destroy', self.cerrar)
        #Maquetación
        self.set_border_width(2)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        main_vbox = gtk.VBox(False, 0)
        path = os.path.join('images', 'icono.png')
        icon = gtk.gdk.pixbuf_new_from_file(path)
        self.set_icon_list(icon)
        #main_vbox.pack_start(toolbar, False, False, 0)

        self.add(main_vbox)
        hbox_main = gtk.HBox(False, 2)
        main_vbox.pack_start(hbox_main, True, True, 0)
            #VBox 1
        vbox1 = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox1, False, False, 0)
        #vbox1.pack_start(toolbar, False, False, 0)
        frame_selector = Widgets.Frame()
        vbox1.pack_start(frame_selector, False, False, 0)
        self.toolbar = toolbar
        self.selector = Modulos.Selector(self, toolbar)
        self.toolbar.add_button('Monitoreo de Flota (Ctrl + F)', 'flota.png', self.flota)
        self.toolbar.add_button('Liquidaciones (Ctrl + L)', 'dinero.png', self.liquidar)
        self.toolbar.add_button('Mantenimiento (Ctrl + M)', 'mantenimiento.png', self.mantenimiento)
        self.toolbar.add_button('Grifo (Ctrl + G)', 'grifo.png', self.grifo)
        self.toolbar.add_button('Buscar Boleto (Ctrl + B)', 'buscar.png', self.buscar)
        self.toolbar.add_button('Sistema Web (Ctrl + T)', 'chrome.png', self.chrome_web)

        self.selector.vertical()
        frame_selector.add(self.selector)
        self.enruta = Modulos.EnRuta(self)
        vbox1.pack_start(self.enruta, True, True, 0)
            #VBox 2
        vbox2 = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox2, True, True, 0)
                #Notebook
        self.notebook = Widgets.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.datos_unidad = Modulos.Datos(self)
        vbox2.pack_start(self.datos_unidad.frame_padron, False, False, 0)
        vpaned = gtk.VPaned()
        vbox2.pack_start(vpaned, True, True, 0)
        vpaned.pack1(self.notebook, True, True)
        label_datos = gtk.Label('Datos')
        self.notebook.insert_page(self.datos_unidad, label_datos)
        label_llegadas = gtk.Label('Voladas')
        self.notebook.insert_page(self.datos_unidad.llegadas, label_llegadas)
        label_boletos = gtk.Label('Boletos')
        self.notebook.insert_page(self.datos_unidad.boletaje, label_boletos)
        label_boletos = gtk.Label('Inspectoría')
        self.notebook.insert_page(self.datos_unidad.inspectoria, label_boletos)
        self.notebook.set_homogeneous_tabs(True)
        self.notebook.child_set_property(self.datos_unidad, 'tab-expand', True)
                #Vueltas
        vbox_pack2 = gtk.VBox(False, 0)
        vbox_pack2.pack_start(self.datos_unidad.vueltas, False, False, 0)
        vbox_pack2.pack_start(self.datos_unidad.cortes, False, False, 0)
        vpaned.pack2(vbox_pack2, False, False)
        frame_llamada = Widgets.Frame()
        vbox2.pack_start(frame_llamada, False, False, 0)
        self.llamada = Modulos.Llamada()
        frame_llamada.add(self.llamada)
        self.llamada.pack_end(self.datos_unidad.vueltas.entry_total, False, False, 0)
            #VBox3
        vbox3 = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox3, False, False, 0)
        frame_reloj = Widgets.Frame()
        vbox3.pack_start(frame_reloj, False, False, 0)
        self.reloj = Modulos.Reloj(self.http)
        frame_reloj.add(self.reloj)
                #Notebook2
        self.notebook2 = Widgets.Notebook()
        self.notebook2.set_tab_pos(gtk.POS_TOP)
        vbox3.pack_start(self.notebook2, True, True, 0)
        self.disponibles = Modulos.Disponibles(self.http)
        self.notebook2.insert_page(self.disponibles, self.disponibles.label)
        self.excluidos = Modulos.Excluidos(self.http)
        self.notebook2.insert_page(self.excluidos, self.excluidos.label)
        self.notebook2.set_homogeneous_tabs(True)
        self.notebook2.child_set_property(self.disponibles, 'tab-expand', True)
                #Opciones
        hbox_opciones = gtk.HBox(True, 0)
        vbox3.pack_start(hbox_opciones, False, False, 0)
        self.check_llamar = gtk.CheckButton('Llamar auto')
        hbox_opciones.pack_start(self.check_llamar)
        self.check_sonido_gps = gtk.CheckButton('Sonido GPS')
        hbox_opciones.pack_start(self.check_sonido_gps)
        self.check_imprimir = gtk.CheckButton('Imprimir')
        hbox_opciones.pack_start(self.check_imprimir)
                #Botones
        frame_botones = Widgets.Frame()
        vbox3.pack_start(frame_botones, False, False, 0)
        hbox_botones = gtk.HBox(False, 0)
        frame_botones.add(hbox_botones)
        self.but_despachar = Widgets.Button('despachar.png',
            'Despachar')
        hbox_botones.pack_start(self.but_despachar)
        self.but_excluir = Widgets.Button('excluir.png',
            'Excluir')
        hbox_botones.pack_start(self.but_excluir)
        self.but_llamar = Widgets.Button('llamar.png',
            'Llamar')
        hbox_botones.pack_start(self.but_llamar)
        self.conexiones()
        self.dia = self.ruta = self.lado = 0
        self.check_llamar.set_active(True)
        self.check_imprimir.set_active(True)
        eb = gtk.EventBox()
        main_vbox.pack_end(eb, False, False, 0)
        hbox = gtk.HBox(False, 5)
        eb.add(hbox)
        eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#0188d1'))
        hbox.pack_start(twist, False, False, 0)
        hbox.pack_start(status_bar, False, False, 0)
        hbox.pack_end(ticketera, False, False, 0)
        self.notebook.realize()
        self.disponibles.selector = self.selector
        self.excluidos.selector = self.selector
        self.enruta.selector = self.selector
        self.datos_unidad.selector = self.selector
        self.datos_unidad.boletaje.selector = self.selector
        self.datos_unidad.llegadas.selector = self.selector
        self.datos_unidad.vueltas.selector = self.selector
        self.datos_unidad.inspectoria.selector = self.selector
        self.datos_unidad.entry_padron.grab_focus()
        self.llamado = 0
        self.show_all()
        self.datos_unidad.cortes.hide_all()
        #self.datos_unidad.vueltas.hide_all()

    def conexiones(self):
        self.selector.connect('cambio-selector', self.actualizar)
        self.datos_unidad.connect('confirmar', self.confirmar)
        self.datos_unidad.llegadas.connect('cambiar-a-boletos', self.cambiar_a_boletos)
        self.enruta.connect('salida-seleccionada', self.leer_salida)
        self.enruta.connect('alerta-siguiente', self.alerta_siguiente)
        self.enruta.connect('editar-llegadas', self.cambiar_a_llegadas)
        self.disponibles.connect('salida-seleccionada', self.leer_salida)
        self.disponibles.treeview.connect('row-activated', self.despachar)
        self.disponibles.connect('key-release-event', self.disponibles_key)
        self.excluidos.connect('salida-seleccionada', self.leer_salida)
        self.excluidos.connect('desexcluir', self.desexcluir)
        self.datos_unidad.connect(
            'actualizar', self.confirmar)
        self.datos_unidad.vueltas.connect(
            'salida-seleccionada', self.leer_salida)
        self.datos_unidad.vueltas.connect(
            'editar-llegadas', self.cambiar_a_llegadas)
        self.datos_unidad.vueltas.connect(
            'ver-boletos', self.cambiar_a_boletos)
        self.datos_unidad.vueltas.connect(
            'excluir-vuelta', self.excluir_vuelta)
        self.enruta.connect('excluir-vuelta', self.excluir_vuelta)
        self.enruta.connect('ver-boletos', self.cambiar_a_boletos)
        self.enruta.connect('llamar', self.llamar_salida)
        self.but_despachar.connect('clicked', self.despachar)
        self.but_excluir.connect('clicked', self.excluir_but)
        self.but_llamar.connect('clicked', self.llamar)
        self.datos_unidad.frecuencia.connect('frecuencia-auto',
            self.frecuencia_auto)
        self.datos_unidad.frecuencia.connect('frecuencia-manual',
            self.frecuencia_manual)
        self.connect('key-release-event', self.on_key_release)
        self.datos_unidad.connect('hora-revisada', self.frecuencia_reloj)
        self.datos_unidad.connect('cambiar-a-llegadas',
            self.cambiar_a_llegadas)
        self.llamada.connect('llamar', self.llamar_custom)
        self.llamada.connect('stop', self.sonido_stop)
        if os.name == 'nt':
            self.reloj.www.connect('mostrar', self.focus_entry)
            self.datos_unidad.www.connect('mostrar', self.focus_entry)

    def buscar(self, *args):
        Modulos.BuscarBoleto(self.http, self.ruta)

    def chrome_web(self, *args):
        self.http.webbrowser('/')

    def liquidar(self, *args):
        Modulos.Liquidaciones(self.http, self.ruta, self.lado)

    def flota(self, *args):
        Modulos.Reporte(self.http, self.dia, self.ruta, self.lado)

    def grifo(self, *args):
        Modulos.Grifo(self.http, self.ruta, self.lado)

    def mantenimiento(self, *args):
        Modulos.Mantenimiento(self.http, self.ruta, self.lado, self.dia)

    def disponibles_key(self, widget, event):
        k = event.keyval
        if k == 65535:  # Delete
            self.but_excluir.clicked()

    def focus_entry(self, *args):
        self.get_window().focus()

    def login(self, sessionid):
        self.reloj.correr = False
        self.selector.login()
        self.datos_unidad.update_selector()
        self.datos_unidad.login(sessionid)
        self.logueado = True
        self.actualizar()

    def twist_recibido(self, params):
        color = int(params[0])
        padron = int(params[1])
        mensaje = params[2]
        self.datos_unidad.insertar_chat(color, padron, mensaje)
        params = params[4:]
        if len(params) > 3:
            self.twist_recibido(params)

    def actualizar(self, *args):
        self.focus_entry()
        if self.logueado:
            self.dia, self.ruta, self.lado = self.selector.get_datos()
            self.datos_unidad.hora.set_date(self.dia)
            nombre_ruta = self.selector.ruta.get_item()
            self.sonido_folder = self.llamada.set_ruta(nombre_ruta[2])
            self.datos_unidad.update_selector()
            self.disponibles.update_selector()
            self.enruta.update_selector()
            self.excluidos.update_selector()
            self.datos_unidad.vueltas.update_selector()
            self.datos_unidad.llegadas.update_selector()
            self.datos_unidad.boletaje.update_selector()
            self.datos_unidad.inspectoria.update_selector()
            datos = {'dia': str(self.dia),
                'ruta_id': self.ruta,
                'lado': self.lado}
            tablas = self.http.load('actualizar-tablas', datos)
            if os.name == 'nt':
                version = 'Sistema de Despacho TCONTUR v%s' % self.version
            else:
                version = 'Sistema de Despacho TCONTUR PRO v%s' % self.version
            if tablas:
                titulo = 'RUTA: %s Lado: %s del %s - %s' % (self.selector.ruta.get_text(),
                    self.selector.lado.get_text(),
                    self.selector.fecha.get_text(),
                    version)
                self.set_title(titulo)
                self.confirmar(self, tablas)

    def confirmar(self, modulo, tablas):
        if self.logueado and tablas:
            self.disponibles.actualizar(tablas['disponibles'])
            self.excluidos.actualizar(tablas['excluidos'])
            self.enruta.actualizar(tablas['enruta'])
            self.datos_unidad.set_siguiente(tablas['inicio'],
                tablas['frecuencia'], tablas['manual'])
            self.reloj.set_limite(tablas['enruta'],
                tablas['disponibles'], tablas['frecuencia'])
            if self.datos_unidad.entry_padron.get_text() != '':
                self.llamar(False)

    def frecuencia_reloj(self, *args):
        frecuencia = self.datos_unidad.frecuencia.get_int()
        self.reloj.cambiar_frecuencia(frecuencia)

    def alerta_siguiente(self, widget, sig):
        try:
            padron = int(self.enruta.model[sig][1])
        except:
            try:
                padron = int(self.disponibles.model[0][1])
            except:
                pass
            else:
                if self.check_llamar.get_active():
                    self.sonido.preparar(padron, self.sonido_folder)
        else:
            if self.check_llamar.get_active():
                self.sonido.preparar(padron, self.sonido_folder)

    def despachar(self, *args):
        salida, padron = self.disponibles.get_primera_salida()
        if salida:
            dialogo1 = Widgets.Alerta_SINO('Despachar',
                'info.png',
                'Confirme que está seguro de despachar.', False)
            respuesta = dialogo1.iniciar()
            dialogo1.cerrar()
            if respuesta:
                if self.datos_unidad.button_stock.ok and padron == self.datos_unidad.entry_padron.get_int():
                    self.datos_unidad.stock_clicked()
                    if self.datos_unidad.button_stock.ok:
                        mensaje = 'La unidad no tiene boletos suficientes.\n'
                        mensaje += '¿Desea despacharla de todas maneras?.'
                        dialogo2 = Widgets.Alerta_SINO('Falta Stock',
                            'info.png',
                '<span foreground="#FF0000" weight="bold">%s</span>' % mensaje,
                False)
                        respuesta = dialogo2.iniciar()
                        dialogo2.cerrar()
                if respuesta:
                    datos = {
                    'salida_id': salida,
                    'dia': str(self.dia),
                    'ruta_id': self.ruta,
                    'lado': self.lado,
                    'imprimir': self.check_imprimir.get_active(),
                    'padron': self.datos_unidad.entry_padron.get_int()
                        }
                    tablas = self.http.load('despachar', datos)
                    actualizar_unidad = True
                    if tablas:
                        if isinstance(tablas, list):
                            dialog = Modulos.Stock(padron, self.selector, self.http, tablas)
                            respuesta = dialog.iniciar()
                            dialog.cerrar()
                            if not respuesta:
                                if self.http.datos['boleto-obligatorio']:
                                    Widgets.Alerta('Falta Stock', 'error.png',
                                        'No puede despachar la unidad, asígnele stock.')
                                    return
                            actualizar_unidad = False
                            datos = {
                            'salida_id': salida,
                            'dia': str(self.dia),
                            'ruta_id': self.ruta,
                            'lado': self.lado,
                            'imprimir': self.check_imprimir.get_active(),
                            'padron': padron
                                }
                            tablas = self.http.load('despachar', datos)
                        if self.check_llamar.get_active():
                            try:
                                padron = int(self.disponibles.model[1][1])
                            except:
                                pass
                            else:
                                self.sonido.preparar(padron, self.sonido_folder)
                                self.llamado = padron
                        self.confirmar(self, tablas['tablas'])
                        if actualizar_unidad:
                            if tablas['tablas']:
                                self.datos_unidad.escribir(None, tablas['unidad'])

    def leer_salida(self, widget, padron, salida):
        print padron, salida, self.dia, self.datos_unidad.padron, self.datos_unidad.salida, self.datos_unidad.padron_dia
        if padron == 0 or padron == self.datos_unidad.padron:  # mismo padron
            #if salida != self.datos_unidad.salida:
                self.datos_unidad.salida = salida
                self.datos_unidad.escribir_datos_salida()
        else:  # otro padron
            if padron != self.datos_unidad.padron or self.dia != self.datos_unidad.padron_dia:
                self.datos_unidad.unidad_salida(padron, salida)

    def frecuencia_auto(self, widget):
        datos = {
            'dia': self.dia,
            'ruta_id': self.ruta,
            'lado': self.lado}
        tablas = self.http.load('frecuencia-auto', datos)
        self.confirmar(self, tablas)

    def frecuencia_manual(self, widget, frec):
        datos = {
            'dia': self.dia,
            'ruta_id': self.ruta,
            'lado': self.lado,
            'frecuencia': frec}
        tablas = self.http.load('frecuencia-manual', datos)
        self.confirmar(self, tablas)

    def frecuencia_cambiada(self, *args):
        hora, orden = self.config.obj_salida.siguiente()
        frecuencia = self.datos_unidad.frecuencia.get_int()
        if frecuencia == 0:
            self.datos_unidad.padron_activate()
            return
        hora += datetime.timedelta(seconds=frecuencia * 60)
        if self.datos_unidad.hora.get_sensitive():
            self.datos_unidad.hora.set_time(hora)

    def cambiar_a_datos(self, *args):
        self.notebook.set_current_page(0)
        self.datos_unidad.entry_padron.grab_focus()

    def cambiar_a_llegadas(self, *args):
        self.notebook.set_current_page(1)
        self.datos_unidad.llegadas.treeview.grab_focus()
        self.datos_unidad.llegadas.set_cursor()

    def cambiar_a_boletos(self, *args):
        self.notebook.set_current_page(2)
        self.datos_unidad.boletaje.treeview.grab_focus()
        self.datos_unidad.boletaje.set_cursor()

    def cambiar_a_inspectoria(self, *args):
        self.notebook.set_current_page(3)
        self.datos_unidad.inspectoria.treeview.grab_focus()

    def excluir_but(self, *args):
        try:
            path, column = self.disponibles.treeview.get_cursor()
            salida = self.disponibles.model[path][10]
            padron = self.disponibles.model[path][1]
        except:
            return
        else:
            llamar = self.check_llamar.get_active()
            if int(path[0]) == 0 and llamar:
                self.sonido.ultimo(padron, self.sonido_folder)
            self.excluir(salida)

    def excluir_vuelta(self, widget, salida):
        self.excluir(salida)

    def excluir(self, salida):
        dialogo = Widgets.Alerta_Texto('Motivo de Exclusión', self.http.datos['exclusiones'])
        string = dialogo.iniciar()
        if string:
            datos = {'salida_id': salida,
                'motivo': string,
                'dia': self.dia,
                'ruta_id': self.ruta,
                'lado': self.lado,
                'padron': self.datos_unidad.entry_padron.get_int()
                }
            tablas = self.http.load('excluir', datos)
            if tablas:
                self.confirmar(self, tablas['tablas'])
                self.datos_unidad.escribir(None, tablas['unidad'])
        dialogo.cerrar()

    def anular(self, salida):
        dialogo = Widgets.Alerta_Texto('Motivo de Exclusión', self.http.datos['exclusiones'])
        string = dialogo.iniciar()
        if string:
            datos = {'salida_id': salida,
                'motivo': string,
                'dia': self.dia,
                'ruta_id': self.ruta,
                'lado': self.lado,
                'padron': self.datos_unidad.entry_padron.get_int()
                }
            tablas = self.http.load('anular', datos)
            if tablas:
                self.confirmar(self, tablas['tablas'])
                self.datos_unidad.escribir(None, tablas['unidad'])
        dialogo.cerrar()

    def llamar(self, obligatorio=False):
        if obligatorio:
            try:
                padron = self.disponibles.model[0][1]
            except:
                return
            self.sonido.ubicar(padron, self.sonido_folder)
        else:
            try:
                padron = self.disponibles.model[0][1]
            except:
                padron = 0
            llamar = self.check_llamar.get_active()
            if llamar and self.llamado != padron:
                if padron != 0:
                    self.sonido.ubicar(padron, self.sonido_folder)
                self.llamado = padron

    def llamar_salida(self, modulo, padron, obligatorio):
        if obligatorio:
            self.sonido.salir(padron, self.sonido_folder)
        elif self.check_llamar.get_active():
            self.sonido.salir(padron, self.sonido_folder)

    def llamar_custom(self, modulo, personal, lugar):
        padron = self.llamada.entry_padron.get_int()
        if padron != 0:
            self.sonido.custom(padron, personal, lugar, self.sonido_folder)

    def sonido_stop(self, *args):
        self.sonido.stop()

    def cola_espera(self, *args):
        self.http.webbrowser('pantalla')

    def programacion(self, *args):
        Modulos.ProgramacionFlota(self)

    def desexcluir(self, widget, padron):
        if self.datos_unidad.but_confirmar.get_sensitive():
            self.datos_unidad.but_confirmar.clicked()
        else:
            Widgets.Alerta('Error', 'error_dialogo.png',
                'La unidad tiene restricciones')
            self.notebook.set_current_page(0)
            self.datos_unidad.entry_padron.grab_focus()

    def on_key_release(self, widget, event):
        k = event.keyval
        if k == 65307:  # Escape
            self.datos_unidad.entry_codigo.grab_focus()
        elif k == 65470:  # F1
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + F1
                mensaje = """Escape = Seleccionar Padron
F1 = Pestaña Datos
F2 = Pestaña Llegadas
F3 = Pestaña Boletos
F4 = Pestaña Inspectoria
F5 = Actualizar Tablas
F6 = Cambiar navegador interno
F7 = Cambiar Hora
F8 = Cambiar Orden
F9 = Reordenar cola
F10 = Reducir +1
F11 = Voladas a Cero
F12 = Registrar Tarjeta
Delete = Excluir de Disponibles
Ctrl + Eliminar = Excluir de EN RUTA
Ctrl + Enter = Confirmar
Ctrl + N = Nueva Ventana
Ctrl + M = Monitoreo
Ctrl + L = Liquidacion
Ctrl + G = Grifo
Ctrl + C = Caja Central
Ctrl + B = Buscar Boleto
Ctrl + R = Mantenimiento
Ctrl + E = Cola de Espera"""
                dialogo = Widgets.Alerta('Teclas Rápidas',
                    'info.png', mensaje)
            else:
                self.cambiar_a_datos()
        elif k == 65471:  # F2 Cambiar Hora
            self.cambiar_a_llegadas()
        elif k == 65472:  # F3
            self.cambiar_a_boletos()
        elif k == 65473:  # F4
            self.cambiar_a_inspectoria()
        elif k == 65474:  # F5 Actualizar
            self.actualizar()
        elif k == 65475:  # F6
            self.datos_unidad.www.switch(self.http.server)
        elif k == 65476:  # F7
            try:
                hora = self.disponibles.model[0][2]
            except:
                return
            dialogo = Widgets.Alerta_Dia_Hora('Cambiar Hora',
                'cambiar_hora.png',
                'Indique la hora de inicio de la cola.\
                \nEl programa actualizará las frecuencias y\
                \nlas horas de salida según la programación.')
            dialogo.hora.set_time(hora)
            dialogo.fecha.set_date(self.dia)
            hora = dialogo.iniciar()
            if hora:
                datos = {
                    'hora': dialogo.hora.get_time(),
                    'dia': dialogo.fecha.get_date(),
                    'ruta_id': self.ruta,
                    'lado': self.lado,
                }
                data = self.http.load('cambiar-hora', datos)
                if data:
                    self.disponibles.actualizar(data)
            dialogo.cerrar()
        elif k == 65477:  # F8 Cambiar Orden
            try:
                path, column = self.disponibles.treeview.get_cursor()
                path = int(path[0])
                salida = self.disponibles.model[path][10]
                padron = self.disponibles.model[path][1]
            except:
                return
            dialogo = Widgets.Alerta_Numero('Cambiar Orden',
                'cambiar_volada.png',
                'Indique el número de orden.\
                \nEl programa lo ubicará y cambiará la cantidad\
                \nde voladas arregladas.')
            numero = dialogo.iniciar()
            if numero:
                datos = {
                    'salida_id': salida,
                    'numero': numero,
                    'ruta_id': self.ruta,
                    'lado': self.lado,
                    'dia': self.dia,
                    'padron': padron
                }
                data = self.http.load('cambiar-volada', datos)
                if data:
                    self.disponibles.actualizar(data)
            dialogo.cerrar()
        elif k == 65478:  # F9 Reordenar cola
            Modulos.Reordenar(self.disponibles)
        elif k == 65479:  # F10 Reducir +1
            try:
                path, column = self.disponibles.treeview.get_cursor()
                path = int(path[0])
                salida = self.disponibles.model[path][10]
                orden = self.disponibles.model[path][0]
            except:
                return
            dialogo = Widgets.Alerta_SINO('Reducir al Mínimo',
                'reducir_voladas_minimo.png',
                '¿Está seguro de reducir las voladas arregladas\
                \npara la cola desde la fila seleccionada hacia abajo?', False)
            respuesta = dialogo.iniciar()
            if respuesta:
                datos = {
                    'ruta_id': self.ruta,
                    'lado': self.lado,
                    'dia': self.dia,
                    'orden': orden
                }
                data = self.http.load('reducir-total', datos)
                if data:
                    self.disponibles.actualizar(data)
            dialogo.cerrar()
        elif k == 65480:  # F11 Voladas a Cero
            try:
                path, column = self.disponibles.treeview.get_cursor()
                path = int(path[0])
                salida = self.disponibles.model[path][10]
                orden = self.disponibles.model[path][0]
            except:
                return
            dialogo = Widgets.Alerta_SINO('Bloquear con Ceros',
                'reducir_voladas_ceros.png',
                '¿Está seguro de bloquear toda la cola, desde\
                \nla file seleccionada hacia arriba?', False)
            respuesta = dialogo.iniciar()
            if respuesta:
                datos = {
                    'ruta_id': self.ruta,
                    'lado': self.lado,
                    'dia': self.dia,
                    'orden': orden
                }
                data = self.http.load('reducir-ceros', datos)
                if data:
                    self.disponibles.actualizar(data)
            dialogo.cerrar()
        elif k == 65481:  # F12 Registrar Tarjeta
            self.datos_unidad.llegadas.registrar()
        elif k == 65535:  # Delete
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + Eliminar
                try:
                    path = len(self.datos_unidad.vueltas.model) - 1
                    salida = self.datos_unidad.vueltas.model[path][12]['id']
                except:
                    raise
                    return
                mensaje = '¿Está seguro de cancelar la última salida\n'
                mensaje += 'de la <b>Unidad %s</b>?' % self.datos_unidad.padron
                mensaje += '\nLa unidad se pasará a la cola de exclusión\n'
                mensaje += 'si no ha salido aún, de lo contrario se\n'
                mensaje += 'considerará como Fin de Ruta.'
                dialogo = Widgets.Alerta_SINO('Cuidado',
                    'eliminar_tarjeta.png', mensaje, False)
                respuesta = dialogo.iniciar()
                if respuesta:
                    self.anular(salida)
                dialogo.cerrar()
        elif k == 65293 or k == 65421:  # return = 65293, intro= 65421
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + return
                if self.datos_unidad.but_confirmar.get_sensitive():
                    self.datos_unidad.but_confirmar.clicked()
        elif k == 110:  # Ctrl + N
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + N
                self.emit('salidas')
        elif k == 102:  # Ctrl + F
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + F
                self.flota()
        elif k == 103:  # Ctrl + G
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + G
                self.grifo()
        elif k == 98:  # Ctrl + B
            if event.state & gtk.gdk.CONTROL_MASK:
                self.buscar()
        elif k == 113:                             # Control + Q
            if event.state & gtk.gdk.CONTROL_MASK:
                self.backups()
        elif k == 109:  # Ctrl + M
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + M
                self.mantenimiento()
        elif k == 112:  # Ctrl + P
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + M
                self.programacion()
        elif k == 108:  # Ctrl + L
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + L
                self.liquidar()
        elif k == 99:  # Ctrl + C
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + C
                self.caja_central()
        elif k == 101:  # Ctrl + E
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + C
                self.cola_espera()
        elif k == 116:  # Ctrl + T
            if event.state & gtk.gdk.CONTROL_MASK:  # Control + T
                self.chrome_web()
        else:
            if event.state & gtk.gdk.CONTROL_MASK:  # Control ++
                print k

    def backups(self):
        data = self.http.load('backups', {'dato': 1})
        if data:
            dialogo = Widgets.Alerta_Combo('Lista de Backup', 'backup.png', 'Escoja el backup que desea descargar:', data, liststore=(str, str))
            url = dialogo.iniciar()
            if url:
                print 'Backup'
                print url
                sh.wget(url)
                1/0
                sh.unzip()
        print data

    def cerrar(self, *args):
        self.emit('cerrar')
