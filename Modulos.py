#! /usr/bin/python
# -*- encoding: utf-8 -*-
import Widgets
import Impresion
import gtk
import gobject
import glob
import os
import threading
import time
import datetime
import random
import socket
from operator import itemgetter
import Chrome
from decimal import Decimal, ROUND_UP, ROUND_DOWN
import pango
import json

class Selector(gtk.HBox):
    __gsignals__ = {'desactivar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
     'activar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
     'cambio-selector': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

    def __init__(self, parent, toolbar):
        super(Selector, self).__init__(False, 2)
        self.http = parent.http
        self.dia_ = self.ruta_ = self.lado_ = None
        self.fecha = Widgets.Fecha()
        self.fecha.set_size_request(90, 30)
        hbox = gtk.HBox(False, 2)
        self.pack_start(toolbar, False, False, 0)
        self.pack_start(hbox, True, True, 0)
        hbox.pack_start(self.fecha, True, True, 0)
        hbox = gtk.HBox(False, 2)
        self.pack_start(hbox, True, True, 0)
        self.ruta = Widgets.ComboBox((str, int, int))
        hbox.pack_start(self.ruta, True, True, 0)
        self.lado = Widgets.ComboBox()
        hbox.pack_start(self.lado, True, True, 0)
        but_actualizar = Widgets.Button('actualizar.png', size=16, tooltip='Actualizar')
        hbox.pack_start(but_actualizar, False, False, 0)
        but_actualizar.connect('clicked', parent.actualizar)
        self.lado.connect('changed', self.comparar)
        self.ruta.connect('changed', self.comparar)
        self.fecha.connect('changed', self.comparar)
        self.dia = self.fecha.get_date()
        self.lado.set_lista((('A', 0), ('B', 1)))
        lista = self.http.datos['rutas']
        self.ruta.set_lista(lista)
        if self.http.datos['despacho'] is False:
            lado = 1
        else:
            lado = 0
        self.lado.set_id(lado)

    def comparar(self, *args):
        lado = self.lado.get_id()
        dia = self.fecha.get_date()
        ruta = self.ruta.get_id()
        if self.http.datos['despacho'] == lado or self.dia != dia:
            self.emit('desactivar')
        else:
            self.emit('activar')
        if self.lado_ != lado or self.dia_ != dia or self.ruta_ != ruta:
            self.lado_ = lado
            self.dia_ = dia
            self.ruta_ = ruta
            self.emit('cambio-selector')

    def login(self):
        lista = self.http.datos['rutas']
        self.ruta.set_lista(lista)
        if self.http.datos['despacho'] is False:
            lado = 1
        else:
            lado = 0
        self.lado.set_id(lado)

    def get_datos(self):
        return (self.dia_, self.ruta_, self.lado_)

    def vertical(self):
        self.set_orientation(gtk.ORIENTATION_VERTICAL)


class Disponibles(gtk.ScrolledWindow):
    __gsignals__ = {'salida-seleccionada': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING))}

    def __init__(self, http):
        super(Disponibles, self).__init__()
        self.label = gtk.Label()
        self.w = self.get_parent_window()
        self.selector = self.dia = self.ruta = self.lado = None
        self.label.set_markup('<b>DISPONIBLES (0)</b>')
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            self.set_size_request(200, 500)
        else:
            self.set_size_request(320, 500)
        self.model = gtk.ListStore(int, int, str, int, int, int, str, str, str, str, str)
        columnas = ['N\xc2\xba',
         'P',
         'H.SAL',
         'F',
         'VR',
         'VA',
         'H.ING',
         'TI']
        self.http = http
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_enable_search(False)
        self.treeview.connect('cursor-changed', self.fila_seleccionada)
        amarillo = gtk.gdk.color_parse('#FFFFAA')
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, text=i, foreground=8)
            if i == 0:
                cell_text.set_property('weight', 500)
                cell_text.set_property('foreground', '#328aa4')
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.set_reorderable(False)
        self.add(self.treeview)

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def get_primera_salida(self):
        try:
            salida = self.model[0][10]
            padron = self.model[0][1]
            return (salida, padron)
        except:
            return (False, False)

    def fila_seleccionada(self, *args):
        path, column = self.treeview.get_cursor()
        path = int(path[0])
        salida = self.model[path][10]
        padron = self.model[path][1]
        print padron, salida
        self.emit('salida-seleccionada', padron, salida)

    def actualizar(self, lista):
        self.model.clear()
        for fila in lista:
            self.model.append(fila)

        self.label.set_markup('<b>DISPONIBLES (%d)</b>' % len(lista))


class Reordenar(gtk.Dialog):

    def __init__(self, disponibles):
        super(Reordenar, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title('Reordenar Cola')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        self.ruta = disponibles.ruta
        self.lado = disponibles.lado
        self.treeview = Disponibles(disponibles.http)
        hbox.pack_start(self.treeview, False, False, 0)
        vbox = gtk.VBox(False, 0)
        hbox.pack_start(vbox, False, False, 0)
        self.but_arriba = Widgets.Button('arriba.png', tooltip='Subir')
        vbox.pack_start(self.but_arriba, False, False, 0)
        self.but_abajo = Widgets.Button('abajo.png', tooltip='Bajar')
        vbox.pack_start(self.but_abajo, False, False, 0)
        self.but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.add_action_widget(self.but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('aceptar.png', '_Aceptar')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.but_arriba.connect('clicked', self.arriba)
        self.but_abajo.connect('clicked', self.abajo)
        self.set_focus(self.but_salir)
        self.disponibles = disponibles
        for d in disponibles.model:
            self.treeview.model.append(d)

        self.iniciar()

    def arriba(self, *args):
        try:
            path, column = self.treeview.treeview.get_cursor()
            path = int(path[0])
            orden = self.treeview.model[path][0]
        except:
            return

        if orden < 3:
            return
        self.treeview.model[path][0] = orden - 1
        self.treeview.model[path - 1][0] = orden
        uno = self.treeview.model.get_iter(path)
        otro = self.treeview.model.get_iter(path - 1)
        self.treeview.model.swap(uno, otro)

    def abajo(self, *args):
        try:
            path, column = self.treeview.treeview.get_cursor()
            path = int(path[0])
            orden = self.treeview.model[path][0]
        except:
            return

        if orden == len(self.treeview.model) or orden == 1:
            return
        self.treeview.model[path][0] = orden + 1
        self.treeview.model[path + 1][0] = orden
        uno = self.treeview.model.get_iter(path)
        otro = self.treeview.model.get_iter(path + 1)
        self.treeview.model.swap(uno, otro)

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            ids = []
            ordenes = []
            padrones = []
            for l in self.treeview.model:
                ids.append(l[10])
                ordenes.append(l[0])
                padrones.append(l[1])

            datos = {'salida_ids': json.dumps(ids),
             'padrones': json.dumps(padrones),
             'ordenes': json.dumps(ordenes),
             'ruta_id': self.ruta,
             'lado': self.lado}
            data = self.disponibles.http.load('reordenar-cola', datos)
            if data:
                self.disponibles.actualizar(data)
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class EnRuta(Widgets.Frame):
    __gsignals__ = {'salida-seleccionada': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING)),
     'editar-llegadas': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
     'excluir-vuelta': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
     'ver-boletos': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
     'llamar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int, bool)),
     'alerta-siguiente': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,))}

    def __init__(self, padre):
        super(EnRuta, self).__init__()
        self.label = gtk.Label()
        self.w = self.get_parent_window()
        self.selector = self.dia = self.ruta = self.lado = None
        self.label.set_markup('<b>EN RUTA (0)</b>')
        self.set_label_widget(self.label)
        vbox = gtk.VBox(False, 2)
        self.add(vbox)
        self.sw = gtk.ScrolledWindow()
        self.indice = 0
        self.horas = []
        self.set_property('label-xalign', 0.2)
        vbox.pack_start(self.sw, True, True, 2)
        self.sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            self.sw.set_size_request(150, 300)
        else:
            self.sw.set_size_request(180, 300)
        self.model = gtk.ListStore(int, int, str, int, str, str)
        columnas = ['Nº', 'P', 'H.SAL', 'F']
        self.padre = padre
        self.http = padre.http
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.connect('row-activated', self.editar_llegada)
        self.treeview.connect('cursor-changed', self.fila_seleccionada)
        self.treeview.connect('button-press-event', self.button_press_event)
        self.treeview.connect('size-allocate', self.treeview_changed)
        self.treeview.set_enable_search(False)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            if i == 0:
                tvcolumn.set_attributes(cell_text, text=i)
                cell_text.set_property('weight', 600)
                cell_text.set_property('foreground', '#328aa4')
            else:
                tvcolumn.set_attributes(cell_text, text=i, foreground=4)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.set_reorderable(False)
        self.treeview.set_enable_tree_lines(True)
        self.treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)
        self.sw.add(self.treeview)
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False, False, 2)
        self.imprimir = Widgets.Button('imprimir.png', 'Imprimir')
        hbox.pack_start(self.imprimir, True, True, 0)
        self.llamar = Widgets.Button('llamar.png', tooltip='Ya es su hora de salida')
        hbox.pack_start(self.llamar, True, True, 0)
        self.imprimir.connect('clicked', self.imprimir_clicked)
        self.llamar.connect('clicked', self.llamar_clicked)
        self.http.reloj.connect('tic-tac', self.buscar)
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Anular Impresión')
        item2 = gtk.MenuItem('Se Regresó')
        item3 = gtk.MenuItem('Eliminar Salida')
        item1.connect('activate', self.anular)
        item2.connect('activate', self.regreso)
        item3.connect('activate', self.eliminar)
        self.menu.append(item1)
        self.menu.append(item2)
        self.menu.append(item3)
        self.treeview.connect('button-release-event', self.on_release_button)

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True

    def anular(self, *args):
        path, column = self.treeview.get_cursor()
        path = int(path[0])
        salida = self.model[path][5]
        padron = self.model[path][1]
        pregunta = Widgets.Alerta_Texto(
            'Motivo de ANULACION DE IMPRESION',
            ('Error de Digitacion', 'Falta de Combustible', 'Conductor', 'Mantenimiento')
        )
        motivo = pregunta.iniciar()
        pregunta.cerrar()
        if motivo:
            datos = {'salida_id': salida,
                     'motivo': motivo,
                     'dia': self.dia,
                     'ruta_id': self.ruta,
                     'lado': self.lado,
                     'padron': padron
                     }
            tablas = self.http.load('anular-salida', datos)
            if tablas:
                self.padre.confirmar(self, tablas['tablas'])
                self.padre.datos_unidad.escribir(None, tablas['unidad'])

    def regreso(self, *args):
        path, column = self.treeview.get_cursor()
        path = int(path[0])
        salida = self.model[path][5]
        padron = self.model[path][1]
        pregunta = Widgets.Alerta_Texto(
            'Motivo de REGRESO DE UNIDAD',
            ('Error de Digitacion', 'Falta de Combustible', 'Conductor', 'Mantenimiento', 'Siniestro')
        )
        motivo = pregunta.iniciar()
        pregunta.cerrar()
        if motivo:
            datos = {'salida_id': salida,
                     'motivo': motivo,
                     'dia': self.dia,
                     'ruta_id': self.ruta,
                     'lado': self.lado,
                     'padron': padron
                     }
            tablas = self.http.load('regreso-salida', datos)
            if tablas:
                self.padre.confirmar(self, tablas['tablas'])
                self.padre.datos_unidad.escribir(None, tablas['unidad'])

    def eliminar(self, *args):
        path, column = self.treeview.get_cursor()
        path = int(path[0])
        salida = self.model[path][5]
        padron = self.model[path][1]
        pregunta = Widgets.Alerta_Texto(
            'Motivo de ELIMINAR SALIDA',
            ('Error de Digitacion',)
        )
        motivo = pregunta.iniciar()
        pregunta.cerrar()
        if motivo:
            datos = {'salida_id': salida,
                     'motivo': motivo,
                     'dia': self.dia,
                     'ruta_id': self.ruta,
                     'lado': self.lado,
                     'padron': padron
                     }
            tablas = self.http.load('eliminar-salida', datos)
            if tablas:
                self.padre.confirmar(self, tablas['tablas'])
                self.padre.datos_unidad.escribir(None, tablas['unidad'])

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def editar_llegada(self, *args):
        self.emit('editar-llegadas')

    def fila_seleccionada(self, *args):
        path, column = self.treeview.get_cursor()
        path = int(path[0])
        salida = self.model[path][5]
        padron = self.model[path][1]
        self.emit('salida-seleccionada', padron, salida)

    def buscar(self, *args):
        if self.indice is None:
            return
        l = len(self.model)
        if self.indice != l:
            t = datetime.datetime.now().replace(microsecond=0)
            hora = self.horas[self.indice]
            if t == hora:
                self.indice += 1
                sig = self.llamar_clicked(None, False)
                self.emit('alerta-siguiente', sig)

    def actualizar(self, lista):
        t = datetime.datetime.now()
        self.model.clear()
        self.horas = []
        self.indice = None
        buscar = True
        guardar = self.dia == datetime.date.today()
        i = 0
        for fila in lista:
            if guardar:
                h, m = fila[2].split(':')
                hora = datetime.datetime(self.dia.year, self.dia.month, self.dia.day, int(h), int(m))
                self.horas.append(hora)
                if buscar:
                    self.indice = i
                if hora > t:
                    buscar = False
            self.model.append(fila)
            i += 1

        if buscar:
            self.indice = i
        self.label.set_markup('<b>EN RUTA (%d)</b>' % len(lista))

    def button_press_event(self, treeview, event):
        if event.button == 3:
            self.emit('ver-boletos')

    def imprimir_clicked(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            if path is None:
                Widgets.Alerta('Error', 'falta_escoger.png', 'Escoja una salida para imprimir.')
                return
            path = int(path[0])
            salida = self.model[path][5]
        except:
            return

        datos = {'salida_id': salida,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'dia': self.dia}
        self.http.load('imprimir-tarjeta', datos)

    def llamar_clicked(self, widget, obligatorio = True):
        try:
            path = self.indice - 1
            hora = self.horas[path]
            padron = self.model[path][1]
            self.emit('llamar', padron, obligatorio)
            return path + 1
        except:
            return None

    def treeview_changed(self, widget, event, data = None):
        adj = self.sw.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)


class Excluidos(gtk.ScrolledWindow):
    __gsignals__ = {'salida-seleccionada': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING)),
     'desexcluir': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,))}

    def __init__(self, http):
        super(Excluidos, self).__init__()
        self.label = gtk.Label()
        self.label.set_markup('<b>EXCLUIDOS (0)</b>')
        self.selector = self.dia = self.ruta = self.lado = None
        self.display = gtk.gdk.display_get_default()
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            self.set_size_request(200, 200)
        else:
            self.set_size_request(320, 200)
        self.model = gtk.ListStore(int, int, str, str, int, str)
        columnas = ['N\xc2\xba',
         'P',
         'H.SAL',
         'H. CREACION']
        self.http = http
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.connect('row-activated', self.desexcluir)
        self.treeview.connect('cursor-changed', self.fila_seleccionada)
        self.treeview.connect('motion-notify-event', self.popup)
        self.treeview.connect('leave-notify-event', self.popup)
        self.treeview.set_enable_search(False)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, text=i)
            if i == 0:
                cell_text.set_property('weight', 500)
                cell_text.set_property('foreground', '#328aa4')
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.add(self.treeview)
        self.pop = gtk.Window(gtk.WINDOW_POPUP)
        self.eb = gtk.EventBox()
        self.label_pop = gtk.Label()
        self.pop.add(self.eb)
        self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#F5F6CE'))
        self.eb.add(self.label_pop)

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def popup(self, widget, e):
        try:
            path, col, x, y = widget.get_path_at_pos(int(e.x), int(e.y))
            it = widget.get_model().get_iter(path)
            value = 'HORAS DE EXCLUSION:\n' + widget.get_model().get_value(it, 5)
            self.pop.show_all()
            a, x, y, b = self.display.get_pointer()
            self.pop.move(x + 10, y + 10)
            self.label_pop.set_markup(str(value))
        except:
            self.pop.hide_all()

    def desexcluir(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            padron = self.model[path][1]
        except:
            return

        self.emit('desexcluir', padron)

    def fila_seleccionada(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            salida = self.model[path][4]
            padron = self.model[path][1]
        except:
            return

        self.emit('salida-seleccionada', padron, salida)

    def actualizar(self, lista):
        self.model.clear()
        for fila in lista:
            self.model.append(fila)
        self.label.set_markup('<b>EXCLUIDOS (%d)</b>' % len(lista))


class Vueltas(Widgets.Frame):
    __gsignals__ = {'salida-seleccionada': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_STRING)),
     'editar-llegadas': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
     'excluir-vuelta': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,)),
     'ver-boletos': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

    def __init__(self, http):
        super(Vueltas, self).__init__()
        self.sw = gtk.ScrolledWindow()
        self.w = self.get_parent_window()
        self.selector = self.dia = self.ruta = self.lado = None
        self.add(self.sw)
        self.sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            self.sw.set_size_request(300, 140)
        else:
            self.sw.set_size_request(460, 170)
        self.set_property('shadow-type', gtk.SHADOW_NONE)
        self.model = gtk.ListStore(str, str, str, str, str, str, str, str, str, str, str, str, gobject.TYPE_PYOBJECT)
        columnas = ['N\xc2\xba',
         'L',
         'RUTA',
         'H.SAL',
         'H.FIN',
         'F',
         'VOL',
         'ESTADO',
         'PROD',
         'DIA']
        self.http = http
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.connect('row-activated', self.editar_llegadas)
        self.treeview.connect('cursor-changed', self.fila_seleccionada)
        self.treeview.connect('button-press-event', self.button_press_event)
        self.treeview.connect('size-allocate', self.treeview_changed)
        self.treeview.set_enable_search(False)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, text=i, foreground=10)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.sw.add(self.treeview)
        self.unidad = {}
        self.entry_total = Widgets.Entry()
        self.entry_total.set_size_request(100, 25)
        self.entry_total.set_text('S/. 0.00')

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def guardar_salida(self, data):
        salida = data['id']
        for i, fila in enumerate(self.model):
            if fila[11] == salida:
                self.model[i][12] = data

    def actualizar(self, lista):
        self.model.clear()
        total = Decimal('0.00')
        for fila in lista:
            self.model.append(fila)
            total += Decimal(fila[8])

        self.entry_total.set_text('S/. ' + str(total))

    def editar_llegadas(self, *args):
        self.emit('editar-llegadas')

    def fila_seleccionada(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            salida = self.model[path][11]
        except:
            return

        self.emit('salida-seleccionada', 0, salida)

    def button_press_event(self, treeview, event):
        if event.button == 3:
            self.emit('ver-boletos')

    def treeview_changed(self, widget, event, data = None):
        adj = self.sw.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)


class Datos(gtk.VBox):
    __gsignals__ = {
        'vueltas': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'confirmar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'hora-revisada': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'cambiar-a-llegadas': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'actualizar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self, salidas):
        super(Datos, self).__init__()
        self.padron = 0
        self.salida = 0
        self._media_vuelta = False
        self._vuelta_completa = False
        self.combustible = ''
        self.http = salidas.http
        self.ventana = salidas
        self.w = self.get_parent_window()
        self.siguiente = None
        self.hora_minimo = datetime.datetime.now()
        self.selector = self.dia = self.ruta = self.lado = None
        vbox_main = gtk.VBox(False, 5)
        self.pack_start(vbox_main, True, True, 0)
        self.frame_padron = Widgets.Frame()
        hbox_padron = gtk.HBox(False, 5)
        self.frame_padron.add(hbox_padron)
        label_padron = gtk.Label('Padr\xc3\xb3n:')
        hbox_padron.pack_start(label_padron, False, False, 5)
        self.button_padron = Widgets.ButtonDoble('no_castigado.png', 'castigado.png', '+H.Sal')
        hbox_padron.pack_start(self.button_padron, False, False, 0)
        self.entry_codigo = Widgets.Texto(7)
        hbox_padron.pack_start(self.entry_codigo, False, False, 0)
        self.entry_codigo.connect('activate', self.codigo_activate)
        self.entry_completion = gtk.EntryCompletion()
        self.entry_codigo.set_completion(self.entry_completion)
        self.completion_liststore = gtk.ListStore(str)
        self.entry_completion.set_model(self.completion_liststore)
        self.entry_padron = Widgets.Numero(4)
        hbox_padron.pack_start(self.entry_padron, False, False, 0)
        self.entry_padron.set_sensitive(False)
        self.entry_padron.connect('activate', self.padron_activate)

        self.entry_padron.connect('key-release-event', self.padron_release)
        self.but_celular = Widgets.Button('celular.png', size=16, tooltip='Llamar')
        hbox_padron.pack_start(self.but_celular, False, False, 0)
        self.but_celular.connect('clicked', self.llamar_celular)
        label_hora = gtk.Label('H. Salida:')
        hbox_padron.pack_start(label_hora, False, False, 0)
        self.hora = Widgets.Hora()
        hbox_padron.pack_start(self.hora, False, False, 0)
        self.but_relojes = Widgets.Button('relojes.png', size=16, tooltip='Registrar vuelta completa')
        hbox_padron.pack_start(self.but_relojes, False, False, 0)
        label_frecuencia = gtk.Label('Frec. Auto')
        hbox_padron.pack_start(label_frecuencia, False, False, 0)
        self.frecuencia = Frecuencia(label_frecuencia)
        hbox_padron.pack_start(self.frecuencia, False, False, 0)
        tabla = gtk.Table(5, 4, False)
        vbox_main.pack_start(tabla, False, False, 0)
        etiquetas = ('Unidad', 'Propietario', 'Conductor', 'Cobrador')
        for i, etiqueta in enumerate(etiquetas):
            label = gtk.Label(etiqueta)
            label.set_alignment(0, 0.5)
            if os.name == 'nt':
                label.set_size_request(55, 25)
            else:
                label.set_size_request(80, 25)
            tabla.attach(label, 0, 2, i, i + 1, gtk.FILL, gtk.FILL, 2, 2)

        self.button_placa = Widgets.ButtonDobleUnidad(self.http, self, tooltip='Estado de Unidad')
        self.button_placa.set_size_request(25, 25)
        self.button_propietario = Widgets.ButtonDoble('no_castigado.png', 'castigado.png', 'Sin Poliza', tooltip='Estado de Propietario')
        self.button_propietario.set_size_request(25, 25)
        self.button_conductor = Widgets.ButtonDoblePersonal(self.http, self, tooltip='Datos de Conductor')
        self.button_conductor.motivo = 'Conductor'
        self.button_conductor.set_size_request(25, 25)
        self.button_cobrador = Widgets.ButtonDoblePersonal(self.http, self, tooltip='Datos de Cobrador')
        self.button_cobrador.motivo = 'Cobrador'
        self.button_cobrador.set_size_request(25, 25)
        self.button_stock = Widgets.ButtonDoble('no_castigado.png', 'castigado.png', '')
        self.botones = (self.button_padron,
         self.button_placa,
         self.button_propietario,
         self.button_conductor,
         self.button_cobrador)
        self.botones_b = (self.button_padron,
         self.button_placa,
         self.button_propietario,
         self.button_conductor,
         self.button_cobrador)
        tabla.attach(self.button_placa, 2, 3, 0, 1, gtk.FILL, gtk.FILL)
        tabla.attach(self.button_propietario, 2, 3, 1, 2, gtk.FILL, gtk.FILL)
        tabla.attach(self.button_conductor, 2, 3, 2, 3, gtk.FILL, gtk.FILL)
        tabla.attach(self.button_cobrador, 2, 3, 3, 4, gtk.FILL, gtk.FILL)
        self.label_placa = gtk.Label('-')
        self.label_propietario = gtk.Label('-')
        self.combo_conductor = Widgets.ComboBox((str,
         str,
         int,
         gobject.TYPE_PYOBJECT))
        self.combo_conductor.column = 2
        self.combo_cobrador = Widgets.ComboBox((str,
         str,
         int,
         gobject.TYPE_PYOBJECT))
        self.combo_cobrador.column = 2
        if os.name == 'nt':
            self.label_placa.set_size_request(180, 25)
            self.combo_conductor.set_size_request(180, 25)
            self.combo_cobrador.set_size_request(180, 25)
        else:
            self.label_placa.set_size_request(250, 25)
            self.combo_conductor.set_size_request(250, 25)
            self.combo_cobrador.set_size_request(250, 25)
        tabla.attach(self.label_placa, 3, 4, 0, 1, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        tabla.attach(self.label_propietario, 3, 4, 1, 2, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(self.combo_conductor, True, True, 0)
        self.but_conductor_cobrador = Widgets.Button('abajo.png', size=16, tooltip='Ubicar como cobrador')
        self.but_conductor_cobrador.connect('clicked', self.downgrade_conductor)
        hbox.pack_start(self.but_conductor_cobrador, False, False, 0)
        tabla.attach(hbox, 3, 4, 2, 3, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        tabla.attach(self.combo_cobrador, 3, 4, 3, 4, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        imagen = 'buscar_personal.png'
        self.button_bloquear = Widgets.ButtonDobleBloquear('no_bloqueado.png', 'bloqueado.png', tooltip='Bloquear/Desbloquear')
        self.guardar_personal_but = Widgets.Button('guardar.png', size=16, tooltip='Guardar cambios de personal')
        self.buscar_conductor = Widgets.Button(imagen, size=16, tooltip='Escoger Conductor')
        self.buscar_cobrador = Widgets.Button(imagen, size=16, tooltip='Escoger Cobrador')
        tabla.attach(self.button_bloquear, 4, 5, 0, 1, gtk.SHRINK, gtk.SHRINK)
        tabla.attach(self.guardar_personal_but, 4, 5, 1, 2, gtk.SHRINK, gtk.SHRINK)
        tabla.attach(self.buscar_conductor, 4, 5, 2, 3, gtk.SHRINK, gtk.SHRINK)
        tabla.attach(self.buscar_cobrador, 4, 5, 3, 4, gtk.SHRINK, gtk.SHRINK)
        hbox_accion = gtk.HBox(False, 0)
        vbox_main.pack_start(hbox_accion, False, False, 0)
        self.but_reserva = Widgets.Button(None, '<span foreground="#FF0000" weight="bold">R</span>', tooltip='Reservas y Suministros')
        hbox_accion.pack_start(self.but_reserva, False, False, 0)
        but_actualizar = Widgets.Button('actualizar.png', '', 16, tooltip='Actualizar Datos de la Unidad')
        hbox_accion.pack_start(but_actualizar, False, False, 0)
        but_actualizar.connect('clicked', self.padron_activate)
        self.but_pagar = Widgets.Button('caja.png', '', tooltip='Cobrar a la unidad')
        hbox_accion.pack_start(self.but_pagar, False, False, 0)
        self.but_fondo = Widgets.Button('fondo.png', '', tooltip='Cobrar Fondos')
        hbox_accion.pack_start(self.but_fondo, False, False, 0)
        self.but_reporte = Widgets.Button('reporte.png', '', tooltip='Reporte de Caja')
        hbox_accion.pack_start(self.but_reporte, False, False, 0)
        self.but_stock_rojo = Widgets.Button('stock_rojo.png', '', tooltip='Suministrar Boletos (Obligatorio)')
        hbox_accion.pack_start(self.but_stock_rojo, False, False, 0)
        self.but_stock_verde = Widgets.Button('stock_verde.png', '', tooltip='Suministrar Boletos (Opcional)')
        hbox_accion.pack_start(self.but_stock_verde, False, False, 0)
        self.info = gtk.Label()
        hbox_accion.pack_start(self.info, False, False, 0)
        self.but_confirmar = Widgets.Button('confirmar.png', '_Confirmar')
        hbox_accion.pack_end(self.but_confirmar, False, False, 0)
        url = 'http://%s/despacho/ingresar/?sessionid=%s' % (self.http.dominio, salidas.principal.sessionid)
        hpaned = gtk.HPaned()
        vbox_main.pack_start(hpaned, True, True, 0)
        if os.name == 'nt':
            self.www = Chrome.Browser(url, 150, 100)
        else:
            self.www = Chrome.IFrame(url, 150, 100)
        hpaned.pack1(self.www, True, True)
        self.sw_chat = gtk.ScrolledWindow()
        hpaned.pack2(self.sw_chat, False, False)
        self.sw_chat.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw_chat.set_size_request(100, 100)
        self.model_chat = gtk.ListStore(int, str, str)
        self.chat = Widgets.TreeView(self.model_chat)
        self.sw_chat.add(self.chat)
        columnas = ['PAD', 'EVENTO']
        self.chat.set_enable_search(False)
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            column.set_flags(gtk.CAN_FOCUS)
            cell = gtk.CellRendererText()
            cell.set_property('editable', False)
            column.pack_start(cell, True)
            column.set_attributes(cell, text=i, foreground=2)
            self.chat.append_column(column)
            column.encabezado()

        self.chat.connect('row-activated', self.evento_seleccionado)
        self.activado = True
        self.padron_dia = None
        self.llegadas = Llegadas(self.http, self)
        self.boletaje = Boletos(self.http, self)
        self.vueltas = Vueltas(self.http)
        self.inspectoria = Inspectoria(self.http)
        self.cortes = Cortes(self.http)
        self.conectar()

    def codigo_activate(self, *args):
        codigo = self.entry_codigo.get_text()
        if codigo == '':
            self.padron_activate()
            return
        elif codigo.isdigit():
            self.entry_padron.set_text(codigo)
            self.padron_activate()
        else:
            data = {
                'tipo': 'unidad',
                'codigo': self.entry_codigo.get_text()
            }
            opciones = self.http.load('buscar-codigo', data)
            if len(opciones) == 1:
                self.entry_padron.set_text(str(opciones[0]['padron']))
                self.entry_codigo.set_text(str(opciones[0]['placa']))
                self.padron_activate()
            elif len(opciones) == 0:
                self.entry_padron.set_text('')
            else:
                self.menu_codigo = gtk.Menu()
                for o in opciones:
                    item = gtk.MenuItem('%s (%s)' % (o['padron'], o['placa']))
                    self.menu_codigo.append(item)
                    item.connect('activate', self.set_padron, str(o['padron']))
                    self.menu_codigo.popup(None, None, None, event.button, event.time)
                    self.menu.show_all()

    def set_padron(self, widget, padron):
        self.entry_padron.set_text(padron)
        self.padron_activate()

    def downgrade_conductor(self, *args):
        js = self.combo_conductor.get_item()
        nombre = 'CONDUCTOR: %s' % js[0]
        self.combo_cobrador.add_item([nombre, js[1], js[2]])

    def insertar_chat(self, tipo, padron, mensaje):
        mensaje += ' ' + datetime.datetime.now().strftime('%H:%M:%S')
        if tipo == 0:
            self.model_chat.append((padron, mensaje, '#0B0'))
        elif tipo == 1:
            self.model_chat.append((padron, mensaje, '#0B0'))
            if self.ventana.check_sonido_gps.get_active():
                self.http.sonido.normal()
        elif tipo == 2:
            self.model_chat.append((padron, mensaje, '#00B'))
            if self.ventana.check_sonido_gps.get_active():
                self.http.sonido.importante()
        else:
            self.model_chat.append((padron, mensaje, '#B00'))
            if self.ventana.check_sonido_gps.get_active():
                self.http.sonido.emergencia()
        adj = self.sw_chat.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)

    def llamar_celular(self, *args):
        txt = self.entry_padron.get()
        Trackers(self.http, self.dia, self.ruta, self.lado, txt)

    def evento_seleccionado(self, *args):
        try:
            path, column = self.chat.get_cursor()
            path = int(path[0])
            padron = self.model_chat[path][0]
        except:
            return

        self.www.execute_script('update(%d);' % padron)

    def bloquear(self, *args):
        datos = {'padron': self.padron,
         'dia': str(self.dia),
         'ruta_id': self.ruta,
         'lado': self.lado}
        bloqueos = self.http.load('bloqueos-unidad', datos)
        antes = len(bloqueos) > 0
        dialogo = Widgets.DesbloquearUnidad(self, bloqueos, datos)
        respuesta = dialogo.iniciar()
        despues = dialogo.bloqueado
        dialogo.cerrar()
        if antes != despues:
            self.padron_activate()

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()
        print 'actualizar dia', self.dia
        self.hora.set_date(self.dia)
        self.www.execute_script("setTimeout('set_ruta(%d)', 5000);" % self.ruta)

    def login(self, sessionid):
        url = 'http://%s/despacho/ingresar/?sessionid=%s&ruta=%d' % (self.http.appengine, sessionid, self.ruta)
        self.www.open(url)
        self.www.url = url
        self.logueado = True

    def conectar(self):
        self.llegadas.connect('actualizar', self.escribir)
        self.boletaje.connect('actualizar', self.escribir)
        self.inspectoria.connect('actualizar', self.escribir)
        self.button_bloquear.connect('clicked', self.bloquear)
        self.buscar_conductor.connect('clicked', self.cambiar_personal, 'Conductor')
        self.buscar_cobrador.connect('clicked', self.cambiar_personal, 'Cobrador')
        self.combo_conductor.connect('changed', self.personal_cambio, 'Conductor')
        self.combo_cobrador.connect('changed', self.personal_cambio, 'Cobrador')
        self.guardar_personal_but.connect('clicked', self.guardar_personal)
        self.frecuencia.connect('ok', self.frecuencia_cambiada)
        self.hora.connect('cambio', self.cambiar_hora)
        self.but_stock_rojo.connect('clicked', self.stock_clicked)
        self.but_stock_verde.connect('clicked', self.stock_clicked)
        self.hora.connect('enter', self.hora_activate)
        self.but_reserva.connect('clicked', self.anular_reserva)
        self.but_confirmar.connect('clicked', self.confirmar_clicked)
        self.but_relojes.connect('clicked', self.vuelta_completa)
        self.but_pagar.connect('clicked', self.pagar)
        self.but_fondo.connect('clicked', self.fondo)
        self.but_reporte.connect('clicked', self.reporte)
        self.js_count = 0
        self.logueado = False

    def desactivar(self):
        self.activado = False
        self.frecuencia.set_sensitive(False)
        self.hora.set_sensitive(False)
        self.but_confirmar.set_sensitive(False)

    def activar(self):
        self.activado = True
        self.frecuencia.set_sensitive(True)
        self.hora.set_sensitive(True)

    def hora_activate(self, *args):
        if self.but_confirmar.get_sensitive():
            self.confirmar_clicked()

    def confirmar_clicked(self, *args):
        padron = int(self.entry_padron.get_text())
        conductor = self.combo_conductor.get_id()
        cobrador = self.combo_cobrador.get_id()
        hora = self.hora.get_time()
        print hora
        try:
            frecuencia = self.frecuencia.get_int()
        except ValueError:
            Widgets.Alerta('Error', 'error_numero.png', 'El campo FRECUENCIA est\xc3\xa1 vac\xc3\xado.')
            return
        automatica = self.frecuencia.frec
        datos = {'padron': padron,
         'dia': self.dia,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'hora': str(self.hora.get_time()),
         'frecuencia': frecuencia,
         'automatica': automatica,
         'conductor_id': conductor,
         'cobrador_id': cobrador,
         'empresa_id': self.http.empresa,
         'atrasada': 0}
        hora = datetime.datetime.strptime(str(self.dia) + ' ' + str(self.hora.get_time()), '%Y-%m-%d %H:%M:%S')
        print 'atrasada?', hora, self.ultima_hora - datetime.timedelta(0, self.frec * 60)
        if hora < self.ultima_hora - datetime.timedelta(0, self.frec * 60):
            dialogo = Widgets.Alerta_SINO('Cuidado Hora Menor', 'cuidado_hora.png', 'Est\xc3\xa1 digitando una hora menor a la de la cola.\n' + '\xc2\xbfDesea continuar de todas maneras?')
            if not dialogo.iniciar():
                dialogo.cerrar()
                return
            datos['atrasada'] = 1
            dialogo.cerrar()
        tablas = self.http.load('confirmar', datos)
        if tablas:
            self.emit('confirmar', tablas['tablas'])
            self.escribir(None, tablas['unidad'])

    def reporte(self, *args):
        dialogo = MiCaja(self.http, self)

    def pagar(self, *args):
        dialogo = Factura(self, True)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()

    def fondo(self, *args):
        cond = self.combo_conductor.get_item()
        cobr = self.combo_cobrador.get_item()
        padron = self.entry_padron.get_text()
        dialogo = Fondo(self, cond, cobr, padron)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()

    def padron_release(self, *args):
        txt = self.entry_padron.get_text()
        if txt == '':
            color = '#FFCCCC'
        try:
            self.padron = int(txt)
        except:
            color = '#FFCCCC'
        else:
            padron = int(txt)
            if padron == self.padron:
                color = '#FFFFFF'
            else:
                color = '#FFCCCC'

        self.entry_padron.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

    def padron_activate(self, *args):
        self._vuelta_completa = False
        self._media_vuelta = False
        for boton in self.botones:
            boton.set(True)
        txt = self.entry_padron.get_text()
        if txt == '':
            return
        try:
            self.padron = int(txt)
        except:
            print txt
            Widgets.Alerta('Error', 'error_numero.png', 'Escriba un n\xc3\xbamero de padron. S\xc3\xb3lo n\xc3\xbameros.')
            self.entry_padron.set_text('')
            self.padron = None
            self.activado = False
            return
        self.entry_padron.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.www.execute_script('update(%d);' % self.padron)
        self.js_count = 0
        datos = {
            'padron': self.padron,
            'dia': str(self.dia),
            'ruta_id': self.ruta,
            'lado': self.lado
        }
        self.datos = self.http.load('solo-unidad', datos)
        self.padron_dia = self.dia
        self.salida = None
        self.escribir_datos_unidad()
        if self.datos['salida_tablas'] is not None:
            self.vueltas.guardar_salida(self.datos['salida_tablas'])
        self.escribir_datos_salida()
        self.hora.set_sensitive(True)
        self.but_relojes.set_sensitive(False)
        if 'estado' in self.datos:
            if self.datos['estado'] == 'R':
                self._media_vuelta = True
                if self.datos['lado'] == self.lado:
                    self.hora.set_sensitive(False)
                    self.but_relojes.set_sensitive(True)
                    self.but_relojes.grab_focus()
                    if self.http.datos['despacho'] is None:
                        self._vuelta_completa = True
                else:
                    self.emit('cambiar-a-llegadas')

    def vuelta_completa(self, *args):
        self._vuelta_completa = True
        self.emit('cambiar-a-llegadas')

    def unidad_salida(self, padron, salida):
        for boton in self.botones:
            boton.set(True)

        self.entry_padron.set_text(str(padron))
        self.padron = padron
        self.salida = salida
        self.www.execute_script('update(%d);' % self.padron)
        self.js_count = 0
        datos = {'salida_id': salida,
         'padron': padron,
         'dia': str(self.dia),
         'ruta_id': self.ruta,
         'lado': self.lado}
        data = self.http.load('unidad-salida', datos)
        if data:
            self.padron_dia = self.dia
            self.datos = data['unidad']
            self.entry_codigo.set_text(data['unidad']['placa'])
            self.escribir_datos_unidad()
            self.salida = data['salida']['id']
            self.vueltas.guardar_salida(data['salida'])
            self.escribir_datos_salida()

    def escribir(self, widget, data):
        if data:
            self.datos = data
            self.escribir_datos_unidad()
            self.salida = self.datos['salida']
            self.escribir_datos_salida()

    def revisar_disponible(self):
        confirmable = True
        texto = ''
        if self.lado:
            botones = self.botones_b
        else:
            botones = self.botones
        for boton in botones:
            if boton.ok:
                confirmable = False
                texto += ' ' + boton.motivo

        if len(texto) > 25:
            texto = texto[:25] + '...'
        self.info.set_text(texto)
        self.but_confirmar.set_sensitive(confirmable)

    def escribir_datos_unidad(self):
        self.combo_conductor.set_lista(self.datos['conductores'])
        self.combo_cobrador.set_lista(self.datos['cobradores'])
        self.entry_codigo.set_text(self.datos['placa'])
        print self.datos['unidad_check']
        self.button_placa.set(self.datos['unidad_check'][0], self.datos['id'])
        self.label_placa.set_markup(self.datos['modelo'])
        self.button_propietario.set(False, '')
        self.label_propietario.set_markup(self.datos['propietario'])
        self.hora_minimo = datetime.datetime.strptime(self.datos['hora_check'], '%Y-%m-%d %H:%M:%S')
        self.revisar_hora()
        self.vueltas.actualizar(self.datos['salidas'])
        self.salida = self.datos['salida']
        self.hora.grab_focus()
        self.bloqueado = self.datos['bloqueado']
        self.button_bloquear.set(self.bloqueado)
        if self.datos['faltan']:
            self.but_stock_rojo.show_all()
            self.but_stock_verde.hide_all()
            self.button_stock.set(True)
        elif self.datos['faltan'] is None:
            self.but_stock_rojo.hide_all()
            self.but_stock_verde.show_all()
            self.button_stock.set(False)
        else:
            self.but_stock_rojo.hide_all()
            self.but_stock_verde.hide_all()
            self.button_stock.set(False)
            self.revisar_disponible()
            return
        self.revisar_disponible()
        vacio = {'tabla': [],
         'padron': self.padron,
         'id': self.salida,
         'dia': '--/--/----',
         'hora': '--:--'}
        self.llegadas.actualizar(vacio)
        self.boletaje.actualizar(vacio)
        self.inspectoria.actualizar(vacio)
        conductor = None
        cobrador = None

    def escribir_datos_salida(self):
        if self.salida is None:
            return
        no_esta = True
        fila = None
        for i, row in enumerate(self.vueltas.model):
            if int(row[11]) == self.salida:
                no_esta = False
                fila = i
                break

        if no_esta:
            datos = {'salida_id': self.salida,
             'dia': self.dia,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'padron': self.padron}
            data = self.http.load('datos-salida', datos)
            if data:
                self.vueltas.guardar_salida(data)
            salida = data
        else:
            salida = self.vueltas.model[fila][12]
            if salida is None:
                datos = {'salida_id': self.salida,
                 'dia': self.dia,
                 'ruta_id': self.ruta,
                 'lado': self.lado,
                 'padron': self.padron}
                data = self.http.load('datos-salida', datos)
                if data:
                    self.vueltas.guardar_salida(data)
                salida = data
        if salida:
            self.vueltas.guardar_salida(salida)
            self.llegadas.actualizar(salida['tablas']['llegadas'])
            self.boletaje.actualizar(salida['tablas']['boletaje'])
            self.inspectoria.actualizar(salida['tablas']['inspectorias'])
            self.combo_conductor.add_item(salida['conductor'])
            self.combo_cobrador.add_item(salida['cobrador'])

    def cambiar_personal(self, widget, tipo):
        datos = {'tipo': tipo,
         'empresa_id': self.http.empresa}
        if tipo == 'Conductor':
            lista = self.http.conductores
            if lista == []:
                lista = self.http.load('personal', datos)
                if lista:
                    self.http.conductores = lista
        else:
            lista = self.http.cobradores
            if lista == []:
                lista = self.http.load('personal', datos)
                if lista:
                    self.http.cobradores = lista
        if lista:
            dialogo = Personal(tipo, lista, self.http)
            js = dialogo.iniciar()
            dialogo.cerrar()
            if js:
                if tipo == 'Conductor':
                    self.combo_conductor.add_item(js)
                    self.button_conductor.set(js[3], js[2])
                elif tipo == 'Cobrador':
                    self.combo_cobrador.add_item(js)
                    self.button_cobrador.set(js[3], js[2])

    def personal_cambio(self, widget, tipo):
        if tipo == 'Conductor':
            conductor = self.combo_conductor.get_item()
            if conductor:
                self.button_conductor.set(conductor[3], conductor[2])
        elif tipo == 'Cobrador':
            cobrador = self.combo_cobrador.get_item()
            if cobrador:
                self.button_cobrador.set(cobrador[3], cobrador[2])
        self.revisar_disponible()

    def guardar_personal(self, widget):
        datos = {'conductor_id': self.combo_conductor.get_item()[2],
         'cobrador_id': self.combo_cobrador.get_item()[2],
         'salida_id': self.salida,
         'lado': self.lado,
         'ruta_id': self.ruta,
         'dia': self.dia,
         'padron': self.padron}
        data = self.http.load('cambiar-personal', datos)
        if data:
            self.escribir(None, data)

    def actualizar(self):
        self.padron_activate()

    def cambiar_hora(self, *args):
        hora = self.hora.get_datetime()
        frecuencia = hora - self.ultima_hora
        self.frecuencia.set_text(str(int(frecuencia.total_seconds() / 60) + self.frec))
        self.revisar_hora()

    def stock_clicked(self, widget=None):
        datos = {'ruta_id': self.ruta,
         'padron': self.padron}
        boletos = self.http.load('boletos-faltan', datos)
        if boletos:
            dialog = Stock(self.padron, self.selector, self.http, boletos)
            if dialog.iniciar():
                self.escribir(None, dialog.respuesta)
            dialog.cerrar()

    def frecuencia_cambiada(self, *args):
        frecuencia = self.frecuencia.get_int()
        hora = self.ultima_hora
        hora += datetime.timedelta(seconds=(frecuencia - self.frec) * 60)
        self.hora.set_datetime(hora)
        self.revisar_hora()

    def revisar_hora(self):
        hora = self.hora.get_datetime()
        if hora < self.hora_minimo:
            self.button_padron.set(True, '+H.Sal %s' % self.hora_minimo)
        else:
            self.button_padron.set(False)
        self.revisar_disponible()
        self.emit('hora-revisada')

    def set_siguiente(self, hora, frec, manual):
        self.ultima_hora = datetime.datetime.strptime(hora, '%Y-%m-%d %H:%M:%S')
        self.frec = int(frec)
        self.frecuencia.set_frec(self.frec, manual)
        self.hora.set_datetime(self.ultima_hora)
        self.revisar_hora()

    def anular_reserva(self, *args):
        datos = {'ruta_id': self.ruta,
         'padron': self.padron}
        reservas = self.http.load('reserva-stock', datos)
        if reservas:
            dialog = ReservaStock(self.padron, self.selector, self.http, reservas)
            if dialog.iniciar():
                self.escribir(None, dialog.respuesta)
            dialog.cerrar()


class Llegadas(gtk.VBox):
    __gsignals__ = {'actualizar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
     'cambiar-a-boletos': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

    def __init__(self, http, padre):
        super(Llegadas, self).__init__()
        self.http = http
        self.padre = padre
        self.w = self.get_parent_window()
        hbox_label = gtk.HBox(True, 0)
        self.pack_start(hbox_label, False, False, 0)
        self.label_padron = gtk.Label('No hay salida')
        self.label_hora = gtk.Label('--:--')
        self.label_dia = gtk.Label('--/--/--')
        hbox_label.pack_start(self.label_padron, False, False, 0)
        hbox_label.pack_start(self.label_hora, False, False, 0)
        hbox_label.pack_start(self.label_dia, False, False, 0)
        sw = gtk.ScrolledWindow()
        self.pack_start(sw, True, True, 0)
        sw.set_size_request(200, 100)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.model = gtk.ListStore(int, str, str, str, str, str, str, str)
        columnas = ('N\xc2\xba', 'PUNTO', 'H.ORIG', 'H.CALC', 'H.REAL', 'VOL.')
        self.treeview = Widgets.TreeView(self.model)
        sw.add(self.treeview)
        self.treeview.set_enable_search(False)
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            if i == 5:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado)
                cell.set_property('editable', True)
                column.set_flags(gtk.CAN_FOCUS)
                self.column = column
                self.cell = cell
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', False)
            column.pack_start(cell, True)
            column.set_attributes(cell, text=i)
            self.treeview.append_column(column)
            column.encabezado()

        hbox_botones = gtk.HBox(False, 0)
        self.pack_start(hbox_botones, False, False, 0)
        but_actualizar = Widgets.Button('actualizar.png', '', 16, tooltip='Actualizar las Voladas')
        hbox_botones.pack_start(but_actualizar, False, False, 0)
        but_actualizar.connect('clicked', self.actualizar_datos)
        self.but_registrar = Widgets.Button('reporte.png', 'Registrar Tarjeta')
        hbox_botones.pack_start(self.but_registrar, False, False, 0)
        self.but_registrar.connect('clicked', self.registrar)
        self.but_guardar = Widgets.Button('guardar.png', 'Guardar')
        hbox_botones.pack_end(self.but_guardar, False, False, 0)
        self.but_guardar.connect('clicked', self.guardar)
        self.treeview.connect('button-release-event', self.editar)
        self._media_vuelta = False

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def registrar(self, *args):
        dialogo = Relojes(self)
        if dialogo.iniciar():
            self.emit('cambiar-a-boletos')
        dialogo.cerrar()

    def set_cursor(self):
        self.treeview.set_cursor(0, self.column, True)

    def actualizar_datos(self, *args):
        if self.padron is None:
            return
        if self.salida is None:
            return
        datos = {'salida_id': self.salida,
         'padron': self.padron,
         'ruta_id': self.ruta,
         'lado': self.lado}
        data = self.http.load('tabla-llegadas', datos)
        if data:
            self.actualizar(data)

    def actualizar(self, diccionario):
        lista = diccionario['tabla']
        self.model.clear()
        for fila in lista:
            self.model.append(fila)

        self.escribir(diccionario['padron'], diccionario['id'], diccionario['hora'], diccionario['dia'])
        if diccionario['id'] is None:
            self.but_guardar.set_sensitive(False)
        else:
            self.but_guardar.set_sensitive(True)

    def escribir(self, padron = None, salida = None, hora = None, dia = None):
        self.salida = salida
        if padron is None:
            self.label_padron.set_text('No hay salida')
            self.padron = None
        else:
            self.label_padron.set_text('Padr\xc3\xb3n %s' % padron)
            self.padron = padron
        if hora is None:
            self.label_hora.set_text('--:--')
        else:
            self.label_hora.set_text(str(hora))
        if dia is None:
            self.label_dia.set_text('--/--/--')
        else:
            self.label_dia.set_text(str(dia))

    def editado(self, widget, path, new_text):
        if new_text == '':
            new_text = '0'
        try:
            int(new_text)
        except:
            if new_text.upper() == 'NM':
                new_text = 'NM'
                self.model[path][5] = 'NM'
            elif new_text.upper() == 'FM':
                self.model[path][5] = 'FM'
                self.but_guardar.grab_focus()
                return
        else:
            self.model[path][5] = new_text
        finally:
            if path + 1 == len(self.model):
                self.but_guardar.grab_focus()
            else:
                self.treeview.set_cursor(path + 1, self.column, True)

    def editar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def guardar(self, widget):
        voladas = []
        llegadas = []
        for i, fila in enumerate(self.model):
            voladas.append(fila[5])

        datos = {'salida_id': self.salida,
         'voladas': json.dumps(voladas),
         'actualizar': True,
         'dia': self.dia,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron}
        data = self.http.load('guardar-llegadas', datos)
        if data:
            self.emit('actualizar', data)
            if self.padre._media_vuelta:
                self.padre._media_vuelta = False
                self.emit('cambiar-a-boletos')
            if self.padre._vuelta_completa:
                self.padre._media_vuelta = True
            self.padre.hora.set_sensitive(True)


class Cortes(gtk.VBox):
    __gsignals__ = {'terminado': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,))}

    def __init__(self, http):
        super(Cortes, self).__init__()
        self.http = http
        self.w = self.get_parent_window()
        hbox_label = gtk.HBox(True, 0)
        self.rojo = '#EB9EA3'
        self.verde = '#B0EB9E'
        self.amarillo = '#F5F6CE'
        self.selector = None
        self.pack_start(hbox_label, False, False, 0)
        self.label_salida = gtk.Label('No hay corte')
        self.label_inicio = gtk.Label('-')
        self.label_fin = gtk.Label('-')
        hbox_label.pack_start(self.label_salida, False, False, 0)
        hbox_label.pack_start(self.label_inicio, False, False, 0)
        hbox_label.pack_start(self.label_fin, False, False, 0)
        sw = gtk.ScrolledWindow()
        self.pack_start(sw, True, True, 0)
        sw.set_size_request(200, 100)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.model = gtk.ListStore(int)
        self.treeview = Widgets.TreeView(self.model)
        sw.add(self.treeview)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        hbox_botones = gtk.HBox(False, 0)
        but_actualizar = Widgets.Button('guardar.png', '', 16)
        hbox_botones.pack_start(but_actualizar, False, False, 0)
        self.but_reporte = Widgets.Button('reporte.png')
        hbox_botones.pack_start(self.but_reporte, False, False, 0)

    def configurar(self, tablas):
        columnas = ['N\xc2\xba', 'CONTROL']
        liststore = [int, str]
        for b in tablas['boletos']['tabla']:
            columnas.append(b[1])
            liststore.append(str)

        cols = self.treeview.get_columns()
        self.model = gtk.ListStore(*liststore)
        for c in cols:
            self.treeview.remove_column(c)

        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.set_model(self.model)
        self.controles = []
        for c in tablas['llegadas']['tabla']:
            self.controles = c.append(c[1])

    def actualizar(self, salida):
        data = {'salida_id': salida}
        cortes = self.http.load('cortes', data)
        boletos = []
        for c in cortes:
            pass

    def comprobar(self, widget):
        cortes = []
        for i, d in enumerate(self.ids):
            corte = int(self.cortes[i].get_text())
            cortes.append(corte)

        datos = {'id': self.ids,
         'boleto_id': self.boleto_id,
         'corte': json.dumps(cortes),
         'inspectoria_id': self.inspectoria}
        self.respuesta = self.http.load('guardar-corte', datos)
        if self.respuesta:
            self.but_ok.clicked()

    def escribir_tabla(self, *args):
        ruta = self.ruta.get_id()
        lado = self.lado.get_id()
        data = self.data[lado]
        self.columnas = data['columnas']
        lista = data['liststore']
        self.geocercas = data['geocercas']
        self.salidas = data['salidas']
        self.widths = data['widths']
        self.cabeceras = data['cabeceras']
        liststore = []
        for l in lista:
            liststore.append(eval(l))

        self.tabla = data['tabla']
        self.model = gtk.ListStore(*liststore)
        cols = self.treeview.get_columns()
        for c in cols:
            self.treeview.remove_column(c)

        for i, columna in enumerate(self.columnas):
            cell_text = gtk.CellRendererText()
            if isinstance(columna, list):
                tvcolumn = Widgets.TreeViewColumn(columna[0])
            else:
                tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            tvcolumn.set_clickable(True)
            tvcolumn.connect('clicked', self.centrar, i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.set_model(self.model)
        i = self.tipo.get_id()
        for fila in self.tabla:
            self.model.append(fila)

        self.cambiar_contenido()
        self.mostrar_controles()
        self.www.execute_script('set_ruta_lado(%d, %d);' % (ruta, lado))
        self.treeview_changed()

    def cerrar(self, *args):
        self.destroy()


class Boletos(gtk.VBox):
    __gsignals__ = {'actualizar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
     'grifo': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

    def __init__(self, http, padre):
        super(Boletos, self).__init__()
        self.http = http
        self.padre = padre
        self.w = self.get_parent_window()
        hbox_label = gtk.HBox(True, 0)
        self.rojo = '#EB9EA3'
        self.verde = '#B0EB9E'
        self.amarillo = '#F5F6CE'
        self.selector = None
        self.pack_start(hbox_label, False, False, 0)
        self.label_padron = gtk.Label('No hay salida')
        self.label_hora = gtk.Label('--:--')
        self.label_dia = gtk.Label('--/--/--')
        hbox_label.pack_start(self.label_padron, False, False, 0)
        hbox_label.pack_start(self.label_hora, False, False, 0)
        hbox_label.pack_start(self.label_dia, False, False, 0)
        sw = gtk.ScrolledWindow()
        self.pack_start(sw, True, True, 0)
        sw.set_size_request(200, 100)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.model = gtk.ListStore(str, str, str, str, str, str, str, str, str, int, str, str, bool, str, int, int, int)
        columnas = ('N\xc2\xba', 'BOLETO', 'TAR', 'SERIE', 'N.I', 'CANT', 'N.F')
        self.treeview = Widgets.TreeView(self.model)
        sw.add(self.treeview)
        self.treeview.set_enable_search(False)
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            if i == 6:
                cell = Widgets.CellBoleto()
                column.pack_start(cell, True)
                column.set_attributes(cell, text=i, background=11)
                cell.connect('editado', self.editado)
                cell.connect('inicio', self.rellenar)
                cell.set_property('editable', True)
                column.set_flags(gtk.CAN_FOCUS)
                column.set_min_width(60)
                self.column = column
                self.cell = cell
            else:
                cell = gtk.CellRendererText()
                column.pack_start(cell, True)
                cell.set_property('editable', False)
                column.set_attributes(cell, text=i)
            self.treeview.append_column(column)
            column.encabezado()
        hbox_botones = gtk.HBox(False, 0)
        but_reserva = Widgets.Button(None, '<span foreground="#FF0000" weight="bold">R</span>', tooltip='Reservas y Suministros')
        hbox_botones.pack_start(but_reserva, False, False, 0)
        but_reserva.connect('clicked', self.anular_reserva)
        but_actualizar = Widgets.Button('actualizar.png', size=16, tooltip='Actualizar')
        hbox_botones.pack_start(but_actualizar, False, False, 0)
        but_actualizar.connect('clicked', self.actualizar_datos)
        self.but_reporte = Widgets.Button('reporte.png', tooltip='Boletaje por Salida')
        hbox_botones.pack_start(self.but_reporte, False, False, 0)
        self.but_reporte.connect('clicked', self.reporte)
        self.but_pagar = Widgets.Button('caja.png', tooltip='Reporte de Gastos del Día')
        hbox_botones.pack_start(self.but_pagar, False, False, 0)
        self.but_pagar.connect('clicked', self.pagar)
        self.but_deudas = Widgets.Button('credito.png', tooltip='Deudas')
        hbox_botones.pack_start(self.but_deudas, False, False, 0)
        self.but_deudas.connect('clicked', self.deudas)
        self.but_liquidar = Widgets.Button('liquidar.png', tooltip='Nueva Liquidación')
        hbox_botones.pack_start(self.but_liquidar, False, False, 0)
        self.but_liquidar.connect('clicked', self.liquidar)
        self.but_transbordo = Widgets.Button('transbordo.png', tooltip='Transbordo')
        hbox_botones.pack_start(self.but_transbordo, False, False, 0)
        self.but_transbordo.connect('clicked', self.transbordo)
        self.but_ticket_reporte = Widgets.Button('imprimir.png', tooltip='Ticket de Suministros')
        hbox_botones.pack_start(self.but_ticket_reporte, False, False, 0)
        self.but_ticket_reporte.connect('clicked', self.ticket_reporte)
        self.but_corte = Widgets.Button('corte.png')
        self.but_corte.connect('clicked', self.corte)
        self.but_guardar = Widgets.Button('guardar.png', 'Guardar')
        hbox_botones.pack_end(self.but_guardar, False, False, 0)
        self.but_guardar.connect('clicked', self.guardar)
        self.but_borrar = Widgets.Button('cancelar.png', 'Borrar')
        hbox_botones.pack_end(self.but_borrar, False, False, 0)
        self.but_borrar.connect('clicked', self.borrar)
        self.salida = 0
        self.padron = 0
        self.backup = False
        self.pack_start(hbox_botones, False, False, 0)
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Corregir')
        item2 = gtk.MenuItem('Anular')
        item3 = gtk.MenuItem('Eliminar Anulado')
        item1.connect('activate', self.corregir)
        item2.connect('activate', self.anular)
        item3.connect('activate', self.eliminar)
        self.menu.append(item1)
        self.menu.append(item2)
        self.menu.append(item3)
        self.treeview.connect('button-release-event', self.on_release_button)

    def anular_reserva(self, *args):
        datos = {'ruta_id': self.ruta,
         'padron': self.padron}
        reservas = self.http.load('reserva-stock', datos)
        if reservas:
            dialog = ReservaStock(self.padron, self.selector, self.http, reservas)
            if dialog.iniciar():
                self.escribir(None, dialog.respuesta)
            dialog.cerrar()

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def set_cursor(self):
        self.treeview.set_cursor(0, self.column, True)

    def liquidar(self, *args):
        datos = {
            'padron': self.padron,
            'liquidacion_id': '0',
            'ruta_id': self.ruta,
            'lado': self.lado
        }
        self.liquidacion = self.http.load('liquidar', datos)
        if self.liquidacion:
            Liquidar(self.http, self.padron, '0', self)

    def deudas(self, *args):
        if self.padron:
            data = self.http.load('deudas-unidad', {
                'ruta_id': self.ruta,
                'lado': self.lado,
                'padron': self.padron
            })
            if isinstance(data, list):
                dialogo = Deudas(self, data, self.padron, self.dia)
                respuesta = dialogo.iniciar()
                dialogo.cerrar()

    def ticket_reporte(self, *args):
        if self.padron:
            data = self.http.load('ticket-salidas', {'ruta_id': self.ruta,
             'lado': self.lado,
             'padron': self.padron,
             'dia': self.dia})

    def pagar(self, *args):
        dialogo = Pagar(self, self.padron)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()

    def transbordo(self, *args):
        dialog = Transbordo(self.http, self)

    def corte(self, *args):
        dialog = Corte(self.http, inspectoria)
        data = dialog.iniciar()
        dialog.cerrar()

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def reporte(self, *args):
        url = 'preview/%d?padron=%s' % (self.dia.toordinal(), self.padron)
        self.http.webbrowser(url)

    def actualizar_datos(self, *args):
        if self.padron is None:
            return
        if self.salida is None:
            return
        datos = {'salida_id': self.salida,
         'padron': self.padron,
         'ruta_id': self.ruta,
         'lado': self.lado}
        data = self.http.load('tabla-boletaje', datos)
        if data:
            self.actualizar(data)

    def actualizar(self, diccionario):
        self.model.clear()
        lista = diccionario['tabla']
        self.flag_editado = []
        self.backup = False
        for fila in lista:
            self.but_guardar.set_sensitive(True)
            self.model.append(fila)
            self.flag_editado.append(False)

        self.escribir(diccionario['padron'], diccionario['id'], diccionario['hora'], diccionario['dia'])
        if diccionario['id'] is None:
            self.no_editar = True
        else:
            self.no_editar = False
        self.but_guardar.set_sensitive(False)

    def escribir(self, padron = None, salida = None, hora = None, dia = None):
        if padron is None:
            self.label_padron.set_markup('No hay salida')
            self.padron = None
        else:
            self.label_padron.set_markup('Padr\xc3\xb3n %s' % padron)
            self.padron = int(padron)
        self.salida = salida
        if hora is None:
            self.label_hora.set_markup('--:--')
        else:
            self.label_hora.set_markup(hora)
        if dia is None:
            self.label_dia.set_markup('--/--/--')
        else:
            self.label_dia.set_markup(dia)
        if salida is None:
            self.but_guardar.set_sensitive(False)

    def rellenar(self, cell, editable, path):
        boleto = self.model[path][4]
        cell.reserva = self.model[path][14]
        cell.inicio = boleto
        if self.model[path][6] == '':
            editable.set_text(boleto)

    def editado(self, widget, path, new_text):
        if self.no_editar:
            self.http.sonido.error()
            Widgets.Alerta('Finalice la salida', 'fin_de_ruta.png', 'Para poder grabar boletaje finalice la salida primero.')
            return
        try:
            actual = int(new_text)
        except:
            self.http.sonido.error()
            return

        fila = self.model[path]
        serie = fila[3]
        inicio = int(fila[4])
        fin = int(fila[10])
        self.model[path][11] = '#FFFFFF'
        if inicio <= actual <= fin:
            cantidad = actual - inicio
            limite = self.http.boletos_limites[str(fila[9])]
            if cantidad > limite:
                self.http.sonido.error()
                dialogo = Widgets.Alerta_SINO('Cuidado Boletaje Excesivo', 'error_numero.png', 'Est\xc3\xa1 intentando digitar un boletaje mayor a <span foreground="#F00" weight="bold">%d</span> boletos.\n' % limite + '\xc2\xbfDesea continuar de todas maneras?')
                if not dialogo.iniciar():
                    dialogo.cerrar()
                    return
                dialogo.cerrar()
            self.model[path][6] = new_text
            self.model[path][5] = str(cantidad)
            self.flag_editado[path] = True
            self.but_guardar.set_sensitive(True)
            for b in self.flag_editado:
                if not b:
                    self.but_guardar.set_sensitive(False)

            if path + 1 == len(self.model):
                self.but_guardar.grab_focus()
            else:
                self.treeview.set_cursor(path + 1, self.column, True)
        else:
            serie = fila[13]
            inicio = int(fila[14])
            fin = int(fila[15])
            if inicio <= actual and actual <= fin:
                cantidad = cantidad = int(fila[10]) - int(fila[4]) + actual - inicio
                limite = self.http.boletos_limites[str(fila[9])]
                if cantidad > limite:
                    self.http.sonido.error()
                    dialogo = Widgets.Alerta_SINO('Cuidado Boletaje Excesivo', 'error_numero.png', 'Est\xc3\xa1 intentando digitar un boletaje mayor a <span foreground="#F00" weight="bold">%d</span> boletos.\n' % limite + '\xc2\xbfDesea continuar de todas maneras?')
                    if not dialogo.iniciar():
                        dialogo.cerrar()
                        return
                    dialogo.cerrar()
                self.model[path][6] = new_text
                self.model[path][5] = str(cantidad)
                self.model[path][11] = '#DDCC99'
                self.flag_editado[path] = True
                self.but_guardar.set_sensitive(True)
                for b in self.flag_editado:
                    if not b:
                        self.but_guardar.set_sensitive(False)

                if path + 1 == len(self.model):
                    self.but_guardar.grab_focus()
                else:
                    self.treeview.set_cursor(path + 1, self.column, True)
            else:
                self.http.sonido.error()

    def guardar(self, widget):
        boletaje = []
        serie = []
        actual = []
        reserva = []
        for i, fila in enumerate(self.model):
            boletaje.append(fila[8])
            serie.append(fila[5])
            actual.append(fila[6])
            reserva.append(fila[16])

        datos = {'salida_id': self.salida,
                 'boletaje': json.dumps(boletaje),
                 'serie': json.dumps(serie),
                 'actual': json.dumps(actual),
                 'reserva': json.dumps(reserva),
                 'dia': self.dia,
                 'ruta_id': self.ruta,
                 'lado': self.lado,
                 'padron': self.padron}
        print 'guardar boletaje', datos
        data = self.http.load('guardar-boletaje', datos)
        if data:
            if self.padre._vuelta_completa:
                dialogo = Widgets.Alerta_Dia_Hora('Salida del lado Contrario', 'regreso.png', 'Indique la hora de regreso de la unidad %s' % self.padron)
                respuesta = dialogo.iniciar()
                if respuesta:
                    hora = dialogo.hora.get_time()
                    dia = dialogo.fecha.get_date()
                    datos = {
                        'dia': dia,
                        'hora': hora,
                        'ruta_id': self.ruta,
                        'lado': int(not self.lado),
                        'padron': self.padron
                    }
                    data = self.http.load('despachar-otrolado', datos)
                dialogo.cerrar()
            if data:
                self.emit('actualizar', data)
                if self.padre._vuelta_completa:
                    self.padre.emit('cambiar-a-llegadas')
                    self.padre._vuelta_completa = False

    def borrar(self, widget):
        dialogo = Widgets.Alerta_SINO('Cuidado Borrar Boletaje', 'warning.png', '\xc2\xbfEst\xc3\xa1 seguro de borrar el boletaje?')
        if dialogo.iniciar():
            dialogo.cerrar()
            datos = {'salida_id': self.salida,
             'dia': self.dia,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'padron': self.padron}
            data = self.http.load('borrar-boletaje', datos)
            if data:
                backup = []
                for fila in self.model:
                    if fila[6] == '' or self.backup:
                        backup.append(fila[4])
                    else:
                        backup.append(fila[6])

                self.emit('actualizar', data)
                for i, b in enumerate(backup):
                    self.model[i][6] = b

                self.backup = True
            return
        dialogo.cerrar()

    def corregir(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][8]
        except:
            return

        dialogo = Widgets.Alerta_Numero('Corregir boletaje', 'editar.png', 'Indique el boleto con el\nque termino la vuelta.', 6)
        numero = int(dialogo.iniciar())
        if numero:
            datos = {'stock_id': stock_id,
             'salida_id': self.salida,
             'numero': numero,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'dia': self.dia,
             'padron': self.padron}
            data = self.http.load('corregir-boletaje', datos)
            if data:
                self.emit('actualizar', data)
        dialogo.cerrar()

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][8]
        except:
            return

        dialogo = Widgets.Alerta_Anular_Numeros('Anular boletaje', 'error_numero.png', 'Indique el PRIMER boleto a anular y\nel \xc3\x9aLTIMO boleto a anular')
        numeros = dialogo.iniciar()
        if numeros and len(numeros) == 2:
            inicio = int(self.model[path][4])
            fin = int(self.model[path][6])
            if numeros[0] < inicio or numeros[1] >= fin:
                dialogo.cerrar()
                return Widgets.Alerta('Error N\xc3\xbameros', 'error_numero.png', 'Los n\xc3\xbameros no pertenecen a la venta seleccionada "%s - %s".' % (inicio, fin - 1))
            if numeros[0] > numeros[1]:
                dialogo.cerrar()
                return Widgets.Alerta('Error N\xc3\xbameros', 'error_numero.png', 'El rango est\xc3\xa1 invertido.')
            pregunta = Widgets.Alerta_Texto('Anulaci\xc3\xb3n de Boletos', ('Perdida', 'Salteo', 'Retenido por Inspector', 'Deteriorado'))
            motivo = pregunta.iniciar()
            if motivo:
                datos = {'stock_id': stock_id,
                 'inicio': numeros[0],
                 'fin': numeros[1],
                 'ruta_id': self.ruta,
                 'lado': self.lado,
                 'dia': self.dia,
                 'padron': self.padron,
                 'motivo': motivo}
                data = self.http.load('anular-boletaje', datos)
                if data:
                    self.emit('actualizar', data)
        dialogo.cerrar()

    def eliminar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][8]
        except:
            return

        datos = {'stock_id': stock_id,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'dia': self.dia,
         'padron': self.padron}
        data = self.http.load('eliminar-anulacion', datos)
        if data:
            self.emit('actualizar', data)


class Inspectoria(gtk.VBox):
    __gsignals__ = {'actualizar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))}

    def __init__(self, http):
        super(Inspectoria, self).__init__()
        self.http = http
        self.w = self.get_parent_window()
        hbox_label = gtk.HBox(True, 0)
        self.pack_start(hbox_label, False, False, 0)
        self.label_padron = gtk.Label('No hay salida')
        self.label_hora = gtk.Label('--:--')
        self.label_dia = gtk.Label('--/--/--')
        hbox_label.pack_start(self.label_padron, False, False, 0)
        hbox_label.pack_start(self.label_hora, False, False, 0)
        hbox_label.pack_start(self.label_dia, False, False, 0)
        sw = gtk.ScrolledWindow()
        self.selector = None
        self.pack_start(sw, True, True, 0)
        sw.set_size_request(200, 100)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.model = gtk.ListStore(str, str, str, str)
        columnas = ('COD.INS.', 'HORA', 'LUGAR')
        self.treeview = Widgets.TreeView(self.model)
        sw.add(self.treeview)
        self.treeview.set_enable_search(False)
        self.columns = []
        self.cells = []
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            if i == 0:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado)
            elif i == 1:
                cell = Widgets.CellHora()
                cell.connect('editado', self.editado_hora)
            else:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado_lugar)
            cell.set_property('editable', True)
            column.set_flags(gtk.CAN_FOCUS)
            self.columns.append(column)
            self.cells.append(cell)
            column.pack_start(cell, True)
            column.set_attributes(cell, text=i)
            self.treeview.append_column(column)
            column.encabezado()

        hbox_botones = gtk.HBox(False, 0)
        self.pack_start(hbox_botones, False, False, 0)
        but_actualizar = Widgets.Button('actualizar.png', '', 16, tooltip='Actualizar')
        hbox_botones.pack_start(but_actualizar, False, False, 0)
        but_actualizar.connect('clicked', self.actualizar_datos)
        self.but_guardar = Widgets.Button('guardar.png', 'Guardar')
        hbox_botones.pack_end(self.but_guardar, False, False, 0)
        self.but_guardar.connect('clicked', self.guardar)
        self.menu = gtk.Menu()
        item2 = gtk.MenuItem('Borrar Registro')
        item2.connect('activate', self.borrar)
        self.menu.append(item2)
        self.treeview.connect('button-release-event', self.on_release_button)

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def update_selector(self):
        self.dia, self.ruta, self.lado = self.selector.get_datos()

    def escribir(self, padron = None, salida = None, hora = None, dia = None):
        if padron is None:
            self.label_padron.set_markup('No hay salida')
            self.padron = None
        else:
            self.label_padron.set_markup('Padr\xc3\xb3n %s' % padron)
            self.padron = int(padron)
        self.salida = salida
        if hora is None:
            self.label_hora.set_markup('--:--')
        else:
            self.label_hora.set_markup(hora)
        if dia is None:
            self.label_dia.set_markup('--/--/--')
        else:
            self.label_dia.set_markup(dia)
        if salida is None:
            self.but_guardar.set_sensitive(False)

    def actualizar_datos(self, *args):
        if self.padron is None:
            return
        if self.salida is None:
            return
        datos = {'salida_id': self.salida,
         'padron': self.padron,
         'ruta_id': self.ruta,
         'lado': self.lado}
        data = self.http.load('tabla-inspectoria', datos)
        if data:
            self.actualizar(data)

    def actualizar(self, diccionario):
        lista = diccionario['tabla']
        self.model.clear()
        for fila in lista:
            self.model.append(fila)

        self.model.append(('', '', '', 0))
        self.escribir(diccionario['padron'], diccionario['id'], diccionario['hora'], diccionario['dia'])
        if diccionario['id'] is None:
            self.but_guardar.set_sensitive(False)
        else:
            self.but_guardar.set_sensitive(True)
        h, m = diccionario['hora'].split(':')
        try:
            self.inicio = int(h) * 60 + int(m)
        except:
            self.fin = None
            return

        h, m = diccionario['fin'].split(':')
        try:
            self.fin = int(h) * 60 + int(m)
        except:
            self.fin = None
        else:
            if self.fin < self.inicio:
                self.fin += 1440

    def editado(self, widget, path, new_text):
        if new_text == '':
            if path + 1 == len(self.model):
                self.but_guardar.grab_focus()
            return
        try:
            try:
                int(new_text)
            except:
                return

            self.model[path][0] = new_text
        finally:
            self.treeview.set_cursor(path, self.columns[1], True)

    def editado_hora(self, widget, path, new_text):
        if new_text == '':
            if path + 1 == len(self.model):
                self.but_guardar.grab_focus()
            return
        try:
            h, m = new_text.split(':')
            if int(h) > 23:
                return
            if int(m) > 59:
                return
        except:
            return

        if self.fin is None:
            Widgets.Alerta('La Salida no ha Terminado', 'error.png', 'Guarde las voladas primero')
        h, m = new_text.split(':')
        minutos = int(h) * 60 + int(m)
        self.model[path][1] = new_text
        self.treeview.set_cursor(path, self.columns[2], True)

    def editado_lugar(self, widget, path, new_text):
        if new_text == '':
            if path + 1 == len(self.model):
                self.but_guardar.grab_focus()
            return
        self.model[path][2] = new_text
        if path + 1 == len(self.model):
            self.model.append(('', '', '', 0))
        self.treeview.set_cursor(path + 1, self.columns[0], True)

    def guardar(self, widget):
        inspectores = []
        horas = []
        lugares = []
        ids = []
        for i, fila in enumerate(self.model):
            inspectores.append(fila[0])
            horas.append(fila[1])
            lugares.append(fila[2])
            ids.append(fila[3])

        datos = {'inspectores': json.dumps(inspectores),
         'horas': json.dumps(horas),
         'lugares': json.dumps(lugares),
         'ids': json.dumps(ids),
         'salida_id': self.salida,
         'dia': self.dia,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron}
        data = self.http.load('guardar-inspectoria', datos)
        if data:
            self.emit('actualizar', data)

    def borrar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            inspectoria = row[3]
        except:
            raise
            return

        if inspectoria == 0:
            return
        datos = {'salida_id': self.salida,
         'dia': self.dia,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron,
         'inspectoria_id': inspectoria}
        data = self.http.load('borrar-inspectoria', datos)
        if data:
            treeiter = self.model.get_iter(path)
            self.model.remove(treeiter)


class Llamada(gtk.HBox):
    __gsignals__ = {'llamar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, str)),
     'stop': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

    def __init__(self):
        super(Llamada, self).__init__()
        self.button = Widgets.Button('llamar.png', tooltip='Emitir llamado')
        self.button.connect('clicked', self.llamar)
        self.pack_start(self.button, False, False, 0)
        self.entry_padron = Widgets.Numero(4)
        self.entry_padron.connect('activate', self.llamar)
        self.pack_start(self.entry_padron, False, False, 0)
        self.combo = Widgets.ComboBox((str,
         int,
         str,
         str))
        self.combo.set_size_request(200, 25)
        self.pack_start(self.combo)
        self.button_stop = Widgets.Button('stop.png', None, tooltip='Detener el sonido')
        self.pack_start(self.button_stop, False, False, 0)
        self.button_stop.connect('clicked', self.stop)

    def stop(self, *args):
        self.emit('stop')

    def set_ruta(self, nombre):
        dir_inicio = os.getcwd()
        os.chdir('sounds')
        if os.path.isdir(nombre):
            os.chdir(nombre)
            folder = nombre
        else:
            os.chdir('H1')
            folder = 'H1'
        os.chdir('..')
        os.chdir('..')
        lista = [('Ubicarse ...', 1, 'Unidad', 'Ubicar'),
         ('Ultimo Llamado ...', 2, 'Ultimo', 'CasoContrario'),
         ('Preparse ...', 3, 'Unidad', 'Preparar'),
         ('Salir ...', 4, 'Unidad', 'Salir'),
         ('Cobrador a Despacho', 5, 'Cobrador', 'Despacho'),
         ('Conductor a Despacho', 6, 'Conductor', 'Despacho'),
         ('Personal a Despacho', 7, 'Personal', 'Despacho'),
         ('Cobrador a Of. Operaciones', 8, 'Cobrador', 'OfOperaciones'),
         ('Conductor a Of. Operaciones', 9, 'Conductor', 'OfOperaciones'),
         ('Personal a Of. Operaciones', 10, 'Personal', 'OfOperaciones'),
         ('Cobrador a Of. Cobranza', 11, 'Cobrador', 'Cobranza'),
         ('Conductor a Of. Cobranza', 12, 'Conductor', 'Cobranza'),
         ('Personal a Of. Cobranza', 13, 'Personal', 'Cobranza'),
         ('Unidad a Limpieza', 14, 'Unidad', 'Limpieza')]
        self.combo.set_lista(lista)
        return os.path.abspath('sounds/' + folder) + '/'

    def llamar(self, *args):
        sonido = self.combo.get_item()
        self.emit('llamar', sonido[2], sonido[3])


class Frecuencia(Widgets.Numero):
    __gsignals__ = {'frecuencia-auto': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
     'frecuencia-manual': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT,))}

    def __init__(self, label):
        super(Frecuencia, self).__init__(3)
        self.label = label
        self.label.set_size_request(75, 25)
        self.connect('activate', self.manual)
        self.connect('cancel', self.auto)
        self.es_auto = True

    def auto(self, *args):
        self.set_text(str(self.frec))
        self.emit('frecuencia-auto')

    def manual(self, *args):
        frec = self.get_int()
        self.emit('frecuencia-manual', frec)

    def set_frec(self, f, manual):
        self.frec = f
        self.set_text(str(f))
        if manual:
            self.label.set_markup('<b>Frec Manual</b>')
        else:
            self.label.set_markup('Frec Auto')

    def get(self):
        return int(self.get_text())


class Reloj(gtk.HBox):

    def __init__(self, http):
        super(Reloj, self).__init__(0, False)
        self.http = http
        self.horas = []
        self.frecuencia = 0
        self.espacio = datetime.timedelta(seconds=60)
        self.limite = self.get_time() + self.espacio + self.espacio
        self.estado = 'NORMAL'
        url = 'http://%s/despacho/reloj' % self.http.dominio
        if os.name == 'nt':
            self.www = Chrome.Browser(url, 230, 35)
        else:
            self.www = Chrome.IFrame(url, 230, 35)
        self.pack_start(self.www, True, True, 0)
        http.reloj.connect('tic-tac', self.run)

    def run(self, *args):
        t = self.get_time()
        if not self.horas == []:
            h, p = self.horas[0]
            if t == h:
                self.emit('llamar', p)
                self.horas.remove((h, p))
            elif t > h:
                self.horas.remove((h, p))
        if self.limite < t:
            if self.estado != 'ERROR':
                self.www.execute_script('error();')
                self.estado = 'ERROR'
        elif self.limite - self.espacio < t:
            if self.estado != 'CERCA':
                self.www.execute_script('cerca();')
                self.estado = 'CERCA'
        elif self.estado != 'NORMAL':
            self.www.execute_script('normal();')
            self.estado = 'NORMAL'

    def get_text(self):
        hora = time.localtime()
        string = time.strftime('%H:%M:%S', hora)
        return string

    def get_time(self):
        t = time.localtime()
        return datetime.timedelta(seconds=(t.tm_hour * 60 + t.tm_min) * 60 + t.tm_sec)

    def add_hora(self, hora):
        self.horas.append(hora)

    def clear_limite(self):
        self.limite = self.get_time()

    def set_limite(self, enruta, disponibles, frecuencia):
        self.frecuencia = int(frecuencia) * 60
        if len(disponibles) == 0:
            if len(enruta) == 0:
                self.clear_limite()
            else:
                limite = enruta[-1][2]
                h, m = limite.split(':')
                limite = datetime.timedelta(seconds=(int(h) * 60 + int(m)) * 60)
                self.limite = limite + datetime.timedelta(seconds=self.frecuencia)
        else:
            limite = disponibles[0][2]
            h, m = limite.split(':')
            self.limite = datetime.timedelta(seconds=(int(h) * 60 + int(m)) * 60)
        self.limite -= datetime.timedelta(0, 120)

    def cambiar_frecuencia(self, frecuencia):
        antes = self.limite - datetime.timedelta(seconds=self.frecuencia)
        self.frecuencia = frecuencia * 60
        self.limite = antes + datetime.timedelta(seconds=self.frecuencia)


class RelojInterno(gtk.EventBox):
    __gsignals__ = {'llamar': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,))}

    def __init__(self, http):
        super(Reloj, self).__init__()
        self.set_size_request(280, 35)
        self.blanco = gtk.gdk.color_parse('#e5e8e8')
        self.modify_bg(gtk.STATE_NORMAL, self.blanco)
        self.label = gtk.Label('00:00:00')
        self.add(self.label)
        self.rojo = gtk.gdk.color_parse('#FF0000')
        self.amarillo = gtk.gdk.color_parse('#FFFF00')
        self.verde = gtk.gdk.color_parse('#328aa4')
        self.negro = gtk.gdk.color_parse('#000000')
        self.html = "<span foreground='%s' background='%s' weight='ultrabold'            font-desc='Ubuntu 16' stretch='ultraexpanded'>%s</span>"
        self.fondo = self.negro
        self.letra = self.verde
        self.horas = []
        self.espacio = datetime.timedelta(seconds=123)
        self.limite = self.espacio
        http.reloj.connect('tic-tac', self.run)

    def run(self, *args):
        hora = time.localtime()
        string = time.strftime('%H:%M:%S', hora)
        t = self.get_time()
        if not self.horas == []:
            h, p = self.horas[0]
            if t == h:
                self.emit('llamar', p)
                self.horas.remove((h, p))
            elif t > h:
                self.horas.remove((h, p))
        if self.limite < t:
            self.error()
        elif self.limite - t < self.espacio:
            self.cerca()
        else:
            self.normal()
        self.modify_bg(gtk.STATE_NORMAL, self.fondo)
        reloj = self.html % (self.letra, self.fondo, string)
        self.label.set_markup(reloj)

    def normal(self):
        self.fondo = self.blanco
        self.letra = self.verde

    def cerca(self):
        self.fondo = self.amarillo
        self.letra = self.negro

    def error(self):
        self.fondo = self.rojo
        self.letra = self.blanco

    def get_text(self):
        return self.label.get_text()

    def get_time(self):
        s = self.label.get_text()
        h, m, s = s.split(':')
        return datetime.timedelta(seconds=(int(h) * 60 + int(m)) * 60 + int(s))

    def add_hora(self, hora):
        self.horas.append(hora)

    def clear_limite(self):
        self.limite = self.get_time()

    def set_limite(self, enruta, disponibles, frecuencia):
        self.frecuencia = int(frecuencia) * 60
        if len(disponibles) == 0:
            if len(enruta) == 0:
                self.clear_limite()
            else:
                limite = enruta[-1][2]
                h, m = limite.split(':')
                limite = datetime.timedelta(seconds=(int(h) * 60 + int(m)) * 60)
                self.limite = limite + datetime.timedelta(seconds=self.frecuencia)
        else:
            limite = disponibles[0][2]
            h, m = limite.split(':')
            self.limite = datetime.timedelta(seconds=(int(h) * 60 + int(m)) * 60)

    def cambiar_frecuencia(self, frecuencia):
        antes = self.limite - datetime.timedelta(seconds=self.frecuencia)
        self.frecuencia = frecuencia * 60
        self.limite = antes + datetime.timedelta(seconds=self.frecuencia)


class Personal(gtk.Dialog):

    def __init__(self, tipo, lista, http):
        super(Personal, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.lista = lista
        self.http = http
        self.tipo = tipo
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(400, 400)
        self.set_title('B\xc3\xbasqueda de Personal: %s' % tipo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Por Nombre:'))
        self.entry_nombre = Widgets.Texto(45)
        self.entry_nombre.set_width_chars(10)
        hbox.pack_start(self.entry_nombre)
        hbox.pack_start(gtk.Label('Por DNI:'))
        self.entry_dni = Widgets.Numero(8)
        self.entry_dni.set_width_chars(10)
        hbox.pack_start(self.entry_dni)
        button_actualizar = Widgets.Button('actualizar.png', tooltip='Actualizar datos del Personal')
        hbox.pack_start(button_actualizar)
        button_actualizar.connect('clicked', self.actualizar)
        button_castigos = Widgets.Button('castigos.png', 'Castigos')
        hbox.pack_start(button_castigos)
        button_castigos.connect('clicked', self.castigar)
        button_deudas = Widgets.Button('caja.png', 'Deudas')
        hbox.pack_start(button_deudas)
        button_deudas.connect('clicked', self.deudas)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(400, 300)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, int, gobject.TYPE_PYOBJECT)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('NOMBRE', 'DNI')
        self.treeview.connect('cursor-changed', self.cursor_changed)
        self.treeview.connect('row-activated', self.row_activated)
        sw.add(self.treeview)
        for i, name in enumerate(columnas):
            cell = gtk.CellRendererText()
            column = gtk.TreeViewColumn(name, cell, text=i)
            self.treeview.append_column(column)

        self.but_ok = Widgets.Button('aceptar.png', '_Ok')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.set_focus(self.entry_nombre)
        self.entry_nombre.connect('key-release-event', self.filtrar)
        self.entry_dni.connect('key-release-event', self.filtrar)
        self.row = False

    def deudas(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
        except:
            raise
            return

        Prestamos(self, row[2], row[0])

    def castigar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
        except:
            raise
            return

        dialogo = Castigar(self, row[2], row[0])
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        self.actualizar()
        return
        if respuesta:
            if self.tipo == 'Conductor':
                for p in self.http.conductores:
                    if p[2] == row[2]:
                        p = respuesta

                self.lista = self.http.conductores
            else:
                for p in self.http.cobradores:
                    if p[2] == row[2]:
                        p = respuesta

                self.lista = self.http.cobradores
            self.filtrar()

    def actualizar(self, *args):
        datos = {'tipo': self.tipo,
         'empresa_id': self.http.empresa}
        lista = self.http.load('personal', datos)
        if lista:
            if self.tipo == 'Conductor':
                self.http.conductores = lista
            else:
                self.http.cobradores = lista
            self.lista = lista
            self.filtrar()

    def filtrar_nombre(self):
        nombre = self.entry_nombre.get()
        if nombre == '':
            return self.lista
        lista = []
        for fila in self.lista:
            lista.append(fila)
            for n in nombre.split(' '):
                if not fila[0].upper().find(n.upper()) >= 0:
                    lista.remove(fila)
                    break

        return lista

    def filtrar_dni(self, filtrado):
        dni = self.entry_dni.get()
        if dni == '':
            return filtrado
        lista = []
        for fila in filtrado:
            if str(fila[1]).find(dni) >= 0:
                lista.append(fila)

        return lista

    def filtrar(self, *args):
        lista = self.filtrar_nombre()
        lista = self.filtrar_dni(lista)
        self.model.clear()
        for fila in lista:
            self.model.append(fila)

    def cursor_changed(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            self.row = row
            self.but_ok.set_sensitive(True)
        except:
            self.but_ok.set_sensitive(False)

    def iniciar(self):
        self.show_all()
        self.filtrar()
        self.but_ok.set_sensitive(False)
        if self.run() == gtk.RESPONSE_OK:
            return self.row
        else:
            return False

    def row_activated(self, *args):
        self.but_ok.clicked()

    def cerrar(self, *args):
        self.destroy()


class Aporte(gtk.Dialog):

    def __init__(self, http):
        super(Aporte, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title('Registrar Aporte')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        tabla = gtk.Table(3, 3)
        self.vbox.pack_start(tabla, False, False, 5)
        labels = ('Boleta', 'Padron', 'Monto')
        self.ruta = Widgets.Numero(3)
        self.lado = Widgets.Numero(3)
        for i, name in enumerate(labels):
            label = gtk.Label(name)
            tabla.attach(label, 0, 1, i, i + 1)

        self.serie = Widgets.Numero(3)
        tabla.attach(self.serie, 1, 2, 0, 1)
        self.numero = Widgets.Numero(6)
        tabla.attach(self.numero, 2, 3, 0, 1)
        self.padron = Widgets.Numero(3)
        tabla.attach(self.padron, 1, 2, 1, 2)
        self.monto = Widgets.Texto(5)
        tabla.attach(self.monto, 1, 2, 2, 3)
        but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.but_ok = Widgets.Button('aceptar.png', '_OK')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.set_focus(self.serie)
        self.params = {'monto': self.monto,
         'padron': self.padron,
         'serie': self.serie,
         'numero': self.numero,
         'ruta_id': self.ruta,
         'lado': self.lado}
        self.salida = {}

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            serie = self.serie.get_text()
            numero = self.numero.get_text()
            padron = self.padron.get_text()
            monto = self.monto.get_text()
            ruta = self.ruta.get_text()
            lado = self.lado.get_text()
            self.datos = {'serie': serie,
             'numero': numero,
             'padron': padron,
             'monto': monto,
             'ruta_id': ruta,
             'lado': int(lado)}
            return True
        else:
            return False

    def set_defaults(self, defaults):
        for key in defaults:
            self.params[key].set(defaults[key])

    def cerrar(self, *args):
        self.destroy()


class Liquidaciones(gtk.Window):

    def __init__(self, http, ruta, lado):
        super(Liquidaciones, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.http = http
        self.ruta = ruta
        self.lado = lado
        self.fecha = Widgets.Fecha()
        self.por_unidad = False
        self.fecha.set_size_request(150, 30)
        vbox_main = gtk.VBox(False, 0)
        self.add(vbox_main)
        hbox = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('D\xc3\xada:'), False, False, 0)
        hbox.pack_start(self.fecha, False, False, 0)
        self.padron = Widgets.Numero(3)
        self.padron.connect('activate', self.nueva)
        hbox.pack_start(gtk.Label('Padr\xc3\xb3n:'), False, False, 0)
        hbox.pack_start(self.padron, False, False, 0)
        self.but_nueva = Widgets.Button('nuevo.png', 'Nueva Liq.')
        hbox.pack_start(self.but_nueva, False, False, 0)
        self.but_nueva.connect('clicked', self.nueva)
        self.but_actualizar = Widgets.Button('actualizar.png', 'Reporte Padrón')
        hbox.pack_start(self.but_actualizar, False, False, 0)
        self.but_actualizar.connect('clicked', self.actualizar)
        self.but_reporte = Widgets.Button('reporte.png', 'Reporte Flota')
        hbox.pack_start(self.but_reporte, False, False, 0)
        self.but_reporte.connect('clicked', self.reporte)

        hbox = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox, False, False, 0)
        self.but_anular = Widgets.Button('error.png', 'Anular')
        hbox.pack_start(self.but_anular, False, False, 0)
        self.but_anular.connect('clicked', self.anular)
        self.but_imprimir = Widgets.Button('imprimir.png', 'Imprimir')
        hbox.pack_start(self.but_imprimir, False, False, 0)
        self.but_imprimir.connect('clicked', self.imprimir)
        self.but_previa = Widgets.Button('buscar.png', 'Vista Previa')
        hbox.pack_start(self.but_previa, False, False, 0)
        self.but_previa.connect('clicked', self.previa)
        self.but_bloquear = Widgets.Button('bloqueado.png', 'Bloquear/Desbloquear')
        hbox.pack_start(self.but_bloquear, False, False, 0)
        self.but_bloquear.connect('clicked', self.bloquear)
        self.dia = self.fecha.get_date()
        self.set_title('Reporte de Liquidaciones')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            self.set_size_request(720, 540)
        else:
            self.set_size_request(800, 600)
        self.model = gtk.ListStore(int)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.connect('row-activated', self.editar)
        selection = self.treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        vbox_main.pack_start(sw, True, True, 0)
        sw.add(self.treeview)
        self.show_all()
        self.set_focus(self.padron)

    def ticket(self, *args):
        datos = {'padron': self.padron.get_text(),
         'dia': self.fecha.get_date()}
        self.http.load('ticket-dia', datos)

    def actualizar(self, *args):
        datos = {'dia': self.fecha.get_date(),
         'padron': self.padron.get_text(),
         'ruta_id': self.ruta,
         'lado': self.lado}
        data = self.http.load('liquidaciones', datos)
        if data:
            self.escribir(data)
            self.por_unidad = True

    def reporte(self, *args):
        datos = {'dia': self.fecha.get_date(),
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron.get_text()}
        data = self.http.load('flota-liquidacion', datos)
        if data:
            self.escribir(data)
            self.por_unidad = False

    def bloquear(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            liq_id = row[len(row) - 1]
        except:
            raise
            return

        datos = {
            'dia': self.fecha.get_date(),
            'ruta_id': self.ruta,
            'lado': self.lado,
            'padron': self.model[path][0],
            'liquidacion': True
        }

        bloqueos = self.http.load('bloqueos-unidad', datos)
        antes = len(bloqueos) > 0
        dialogo = Widgets.DesbloquearUnidad(self, bloqueos, datos)
        respuesta = dialogo.iniciar()
        despues = dialogo.bloqueado
        dialogo.cerrar()
        if antes != despues:
            self.actualizar()

    def imprimir(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            liq_id = row[len(row) - 1]
        except:
            raise
            return

        datos = {'dia': self.fecha.get_date(),
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron.get_text(),
         'liquidacion_id': liq_id}
        data = self.http.load('liquidacion-imprimir', datos)
        if data:
            self.destroy()

    def previa(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            liq_id = row[len(row) - 1]
        except:
            raise
            return
        url = 'liquidacion/%d' % (liq_id)
        self.http.webbrowser(url)

    def escribir(self, data):
        if data:
            columnas = data['columnas']
            lista = data['liststore']
            liststore = []
            for l in lista:
                liststore.append(eval(l))

            tabla = data['tabla']
            self.model = gtk.ListStore(*liststore)
            cols = self.treeview.get_columns()
            for c in cols:
                self.treeview.remove_column(c)

            for i, columna in enumerate(columnas):
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
                self.treeview.append_column(tvcolumn)
                tvcolumn.encabezado()

            self.treeview.set_model(self.model)
            for fila in tabla:
                self.model.append(fila)

    def crear_nueva(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            padron = self.model[path][0]
        except:
            return

        self.padron.set_text(str(padron))
        self.nueva()

    def nueva(self, *args):
        try:
            padron = self.padron.get()
        except:
            return

        datos = {'padron': padron,
         'liquidacion_id': '0',
         'ruta_id': self.ruta,
         'lado': self.lado}
        self.liquidacion = self.http.load('liquidar', datos)
        if self.liquidacion:
            Liquidar(self.http, padron, '0', self)

    def editar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        padron = self.model[path][0]
        l = len(self.model[path])
        liquidacion = self.model[path][l - 1]
        datos = {'padron': padron,
         'liquidacion_id': liquidacion,
         'ruta_id': self.ruta,
         'lado': self.lado}
        self.liquidacion = self.http.load('liquidar', datos)
        if self.liquidacion:
            Liquidar(self.http, padron, liquidacion, self)

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            liq_id = row[len(row) - 1]
        except:
            return

        datos = {'liquidacion_id': liq_id,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': row[0],
         'dia': self.fecha.get_date(),
         'bruto': row[5],
         'neto': row[8]
        }
        data = self.http.load('anular-liquidacion', datos)
        if data:
            treeiter = self.model.get_iter(path)
            self.model.remove(treeiter)


class Liquidar(Widgets.Window):

    def __init__(self, http, padron, liq_id, parent):
        self.padre = parent
        liquidacion = self.padre.liquidacion
        super(Liquidar, self).__init__('Liquidar Padron %s - %s' % (padron, liquidacion['dia']))
        if os.name == 'nt':
            self.set_size_request(600, 700)
        else:
            self.set_size_request(650, 700)
        self.http = http
        self.ruta = self.padre.ruta
        self.lado = self.padre.lado
        self.editar = liquidacion['editar']
        self.liquidacion_id = liq_id
        vueltas = liquidacion['vueltas']
        transbordos = liquidacion['transbordos']
        retiros = liquidacion['retiros2']
        gastos = liquidacion['gastos2']
        self.pasivos = liquidacion['pasivos2']
        self.dia = liquidacion['dia']
        self.padron = int(padron)
        tabla = gtk.Table(3, 2)
        self.vbox.pack_start(tabla, False, False, 5)
        labels = ('Pago Conductor:', 'Pago Cobrador:', 'Vi\xc3\xa1ticos:')
        self.conductor = Widgets.Texto(32)
        self.cobrador = Widgets.Texto(32)
        self.alimentos = Widgets.Texto(6)
        self.conductor_data = liquidacion['conductor']
        self.conductor.set_text(self.conductor_data[0])
        self.cobrador_data = liquidacion['cobrador']
        self.cobrador.set_text(self.cobrador_data[0])
        self.alimentos.set_text(str(liquidacion['alimentos']))
        self.alimentos.set_property('editable', True)
        self.alimentos.connect('key-release-event', self.calcular)
        for i, name in enumerate(labels):
            label = gtk.Label(name)
            tabla.attach(label, 0, 1, i, i + 1)

        tabla.attach(self.conductor, 1, 2, 0, 1)
        tabla.attach(self.cobrador, 1, 2, 1, 2)
        tabla.attach(self.alimentos, 2, 3, 2, 3)
        self.conductor_pago = Widgets.Texto(6)
        self.conductor_pago.set_property('editable', True)
        self.conductor_pago.connect('key-release-event', self.calcular)
        self.conductor_pago.set_text(str(self.conductor_data[1]))
        self.conductor_pago.set_size_request(75, 25)
        tabla.attach(self.conductor_pago, 2, 3, 0, 1)
        self.cobrador_pago = Widgets.Texto(6)
        self.cobrador_pago.set_size_request(75, 25)
        self.cobrador_pago.set_property('editable', True)
        self.cobrador_pago.connect('key-release-event', self.calcular_wrapped)
        self.cobrador_pago.set_text(str(self.cobrador_data[1]))
        tabla.attach(self.cobrador_pago, 2, 3, 1, 2)
        button = Widgets.Button('dinero.png', 'Calcular Pa_go')
        button.vertical()
        button.connect('clicked', self.calcular_pago)
        tabla.attach(button, 3, 4, 0, 3)
        hbox_main = gtk.HBox(True, 5)
        self.vbox.pack_start(hbox_main, True, True, 0)
        sw_vueltas = gtk.ScrolledWindow()
        sw_vueltas.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw_vueltas.set_size_request(200, 170)
        else:
            sw_vueltas.set_size_request(250, 170)
        self.model_vueltas = gtk.ListStore(bool, str, str, str, str, str)
        self.treeview_vueltas = Widgets.TreeView(self.model_vueltas)
        self.treeview_vueltas.set_rubber_banding(True)
        self.treeview_vueltas.set_enable_search(False)
        self.treeview_vueltas.set_reorderable(False)
        vbox_ingresos = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox_ingresos, True, True, 5)
        frame = Widgets.Frame('INGRESOS')
        vbox_ingresos.pack_start(frame, True, True, 0)
        sw_vueltas.add(self.treeview_vueltas)
        frame.add(sw_vueltas)
        columnas = ('USAR', 'PRODUC.', 'SALIDA', 'RUTA')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i, foreground=5)
            self.treeview_vueltas.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.salidas_json = liquidacion['salidas_json']
        for v in vueltas:
            print v[4]
            if self.salidas_json[str(v[4])]['recaudo']:
                color = '#800'
            else:
                color = '#000'
            self.model_vueltas.append(v + [color])
        self.treeview_vueltas.connect('row-activated', self.liquidar_salida)
        self.treeview_vueltas.connect('cursor-changed', self.marcar_cobranzas_wrap)

        sw_transbordo = gtk.ScrolledWindow()
        sw_transbordo.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw_transbordo.set_size_request(200, 100)
        else:
            sw_transbordo.set_size_request(250, 100)
        self.model_transbordo = gtk.ListStore(bool, str, str, str, str)
        self.treeview_transbordo = Widgets.TreeView(self.model_transbordo)
        self.treeview_transbordo.set_rubber_banding(True)
        self.treeview_transbordo.set_enable_search(False)
        self.treeview_transbordo.set_reorderable(False)
        frame = Widgets.Frame('TRANSBORDOS')
        vbox_ingresos.pack_start(frame, True, True, 0)
        sw_transbordo.add(self.treeview_transbordo)
        frame.add(sw_transbordo)
        columnas = ('USAR', 'MONTO.', 'PADRON', 'SALIDA')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview_transbordo.append_column(tvcolumn)
            tvcolumn.encabezado()

        for t in transbordos:
            self.model_transbordo.append(t)

        frame = Widgets.Frame('RECAUDO COBRADOR')
        tabla = gtk.Table(2, 4)
        frame.add(tabla)
        vbox_ingresos.pack_start(frame, False, 0)
        label = gtk.Label('El Cobrador Tiene:')
        self.cobrador_tiene = Widgets.Texto(9)
        tabla.attach(label, 0, 1, 0, 1)
        tabla.attach(self.cobrador_tiene, 1, 2, 0, 1)
        self.cobrador_tiene.set_property('editable', False)
        label = gtk.Label('Debe quedarse con:')
        self.quedarse = Widgets.Texto(9)
        tabla.attach(label, 0, 1, 1, 2)
        tabla.attach(self.quedarse, 1, 2, 1, 2)
        self.quedarse.set_property('editable', False)
        label = gtk.Label('Va Recaudando:')
        self.recaudado = Widgets.Texto(9)
        tabla.attach(label, 0, 1, 2, 3)
        tabla.attach(self.recaudado, 1, 2, 2, 3)
        self.recaudado.set_property('editable', False)
        label = gtk.Label('Falta Recaudar:')
        self.por_recaudar = Widgets.Texto(9)
        tabla.attach(label, 0, 1, 3, 4)
        tabla.attach(self.por_recaudar, 1, 2, 3, 4)
        self.por_recaudar.set_property('editable', False)
        frame = Widgets.Frame('PRODUCCION PROPIETARIO')
        tabla = gtk.Table(2, 4)
        frame.add(tabla)
        vbox_ingresos.pack_start(frame, False, 0)
        label = gtk.Label('Total Ingresos:')
        self.bruto = Widgets.Texto(9)
        self.bruto.set_text(str(liquidacion['bruto']))
        tabla.attach(label, 0, 1, 1, 2)
        tabla.attach(self.bruto, 1, 2, 1, 2)
        self.bruto.set_property('editable', False)
        label = gtk.Label('Total Egresos:')
        self.gastos = Widgets.Texto(9)
        self.gastos.set_text(str(liquidacion['gastototal']))
        tabla.attach(label, 0, 1, 2, 3)
        tabla.attach(self.gastos, 1, 2, 2, 3)
        self.gastos.set_property('editable', False)
        label = gtk.Label('Total Neto:')
        self.neto = Widgets.Texto(9)
        self.neto.set_text(str(liquidacion['neto']))
        tabla.attach(label, 0, 1, 3, 4)
        tabla.attach(self.neto, 1, 2, 3, 4)
        self.neto.set_property('editable', False)
        sw_gastos = gtk.ScrolledWindow()
        sw_gastos.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw_gastos.set_size_request(300, 300)
        else:
            sw_gastos.set_size_request(340, 320)
        self.model_gastos = gtk.ListStore(bool, str, str, str, str, str, str)
        tms = gtk.TreeModelSort(self.model_gastos)
        tms.set_sort_column_id(3, gtk.SORT_ASCENDING)
        self.treeview_gastos = Widgets.TreeView(tms)
        self.treeview_gastos.set_rubber_banding(True)
        self.treeview_gastos.set_enable_search(False)
        self.treeview_gastos.set_reorderable(False)
        sw_gastos.add(self.treeview_gastos)
        columnas = ('USAR', 'CONCEPTO', 'MONTO', 'HORA', 'USUARIO')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled, self.treeview_gastos)
                cell.set_property('activatable', True)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i, foreground=6)
            self.treeview_gastos.append_column(tvcolumn)
            tvcolumn.encabezado()

        for g in gastos:
            self.model_gastos.append([True] + list(g) + ['#000'])

        vbox = gtk.VBox(False, 0)
        frame = Widgets.Frame('GASTOS Y COBROS')
        hbox_main.pack_start(vbox, True, True, 5)
        vbox.pack_start(frame, True, True, 0)
        frame.add(sw_gastos)
        sw_retiros = gtk.ScrolledWindow()
        sw_retiros.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw_retiros.set_size_request(200, 250)
        else:
            sw_retiros.set_size_request(250, 280)
        self.model_retiros = gtk.ListStore(bool, str, str, str, str, str, str)
        self.treeview_retiros = Widgets.TreeView(self.model_retiros)
        self.treeview_retiros.set_rubber_banding(True)
        self.treeview_retiros.set_enable_search(False)
        self.treeview_retiros.set_reorderable(False)
        frame = Widgets.Frame('RECAUDOS')
        vbox.pack_start(frame, True, True, 0)
        sw_retiros.add(self.treeview_retiros)
        frame.add(sw_retiros)
        columnas = ('USAR', 'CONCEPTO', 'MONTO', 'HORA', 'USUARIO')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled, self.treeview_retiros)
                cell.set_property('activatable', True)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i, foreground=6)
            self.treeview_retiros.append_column(tvcolumn)
            tvcolumn.encabezado()

        for r in retiros:
            self.model_retiros.append([True] + r + ['#000'])

        sw_pasivos = gtk.ScrolledWindow()
        sw_pasivos.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw_pasivos.set_size_request(300, 200)
        else:
            sw_pasivos.set_size_request(340, 220)
        self.model_pasivos = gtk.ListStore(bool, str, str, str, str, str, str)
        self.treeview_pasivos = Widgets.TreeView(self.model_pasivos)
        self.treeview_pasivos.set_rubber_banding(True)
        self.treeview_pasivos.set_enable_search(False)
        self.treeview_pasivos.set_reorderable(False)
        sw_pasivos.add(self.treeview_pasivos)
        columnas = ('USAR', 'CONCEPTO', 'MONTO', 'HORA', 'USUARIO')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled, self.treeview_pasivos)
                cell.set_property('activatable', True)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i, foreground=6)
            self.treeview_pasivos.append_column(tvcolumn)
            tvcolumn.encabezado()

        for g in self.pasivos:
            self.model_pasivos.append([True] + list(g) + ['#000'])

        frame = Widgets.Frame('PAGOS A CUENTA')
        vbox.pack_start(frame, True, True, 0)
        frame.add(sw_pasivos)
        hbox_gastos = gtk.HBox(False, 0)
        but_recaudo = Widgets.Button('dinero.png', '_Recaudo')
        but_cobro = Widgets.Button('caja.png', '_Cobros')
        but_gasto = Widgets.Button('caja.png', '_Gasto')
        but_tercero = Widgets.Button('caja.png', '_A Cuenta')
        but_fondo = Widgets.Button('fondo.png', '_Fondo')
        #but_anular = Widgets.Button('anular.png', 'Anular')
        hbox_gastos.pack_start(but_recaudo, True, False, 0)
        hbox_gastos.pack_start(but_cobro, True, False, 0)
        hbox_gastos.pack_start(but_gasto, True, False, 0)
        hbox_gastos.pack_start(but_tercero, True, False, 0)
        hbox_gastos.pack_start(but_fondo, True, False, 0)
        but_recaudo.connect('clicked', self.recaudo)
        but_cobro.connect('clicked', self.cobro, True)
        but_gasto.connect('clicked', self.cobro, False)
        but_tercero.connect('clicked', self.cobro, None)
        but_fondo.connect('clicked', self.fondo)
        #but_anular.connect('clicked', self.anular)
        vbox.pack_start(hbox_gastos, False, False, 0)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Observaci\xc3\xb3n:'), False, False, 0)
        self.observacion = Widgets.Texto(256)
        hbox.pack_start(self.observacion, True, True, 0)
        self.observacion.set_text(liquidacion['observacion'])
        self.but_salir = self.crear_boton('cancelar.png', 'Cancelar', self.cerrar)
        self.but_imprimir = self.crear_boton('imprimir.png', '_Liquidar', self.imprimir)
        self.but_salir = self.crear_boton('reporte.png', 'Boletaje', self.preview)
        #self.but_ticket = self.crear_boton('imprimir.png', '_Ticket D\xc3\xada', self.ticket)
        self.calcular()
        self.show_all()
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Editar Producción')
        item1.connect('activate', self.editar_recaudo)
        self.menu.append(item1)
        item2 = gtk.MenuItem('Recaudar por Salida')
        item2.connect('activate', self.liquidar_salida)
        self.menu.append(item2)
        item3 = gtk.MenuItem('Reimprimir Recaudo')
        item3.connect('activate', self.reimprimir_recaudo)
        self.menu.append(item3)
        self.treeview_vueltas.connect('button-release-event', self.on_release_button)
        self.treeview_gastos.connect('button-release-event', self.on_release_button_gastos)
        self.treeview_retiros.connect('button-release-event', self.on_release_button_gastos)
        self.treeview_pasivos.connect('button-release-event', self.on_release_button_gastos)
        self.menu_retiros = gtk.Menu()
        item1 = gtk.MenuItem('Anular Item')
        item1.connect('activate', self.anular)
        self.menu_retiros.append(item1)
        if int(self.liquidacion_id) == 0:
            self.conductor_pago.set_text('0.0')
            self.cobrador_pago.set_text('0.0')
            self.alimentos.set_text('0.0')
            self.calcular()
        else:
            but_recaudo.set_sensitive(False)
            but_cobro.set_sensitive(False)
            but_gasto.set_sensitive(False)
            but_tercero.set_sensitive(False)
            but_fondo.set_sensitive(False)
            self.but_imprimir.set_sensitive(False)

    def marcar_cobranzas_wrap(self, *args):
        self.marcar_cobranzas()

    def marcar_cobranzas(self, salida=None):
        if salida is None:
            try:
                path, column = self.treeview_vueltas.get_cursor()
                self.path = int(path[0])
                row = self.model_vueltas[path]
            except:
                for i in self.model_vueltas:
                    if self.salidas_json[salida]['recaudo']:
                        i[5] = '#F00'
                    else:
                        i[5] = '#000'
                return False
            salida = row[4]
        self.gasto_total = 0
        self.recaudo_id = None
        cobranzas = self.salidas_json[salida]['cobranzas']
        recaudo = self.salidas_json[salida]['recaudo']
        color = '#080'
        for i in self.model_vueltas:
            if int(i[4]) == salida:
                i[5] = color
            else:
                if self.salidas_json[i[4]]['recaudo']:
                    i[5] = '#F00'
                else:
                    i[5] = '#000'
        for i in self.model_gastos:
            if int(i[5]) in cobranzas:
                i[6] = color
                self.gasto_total += Decimal(i[2])
            else:
                i[6] = '#000'
        for i in self.model_retiros:
            if int(i[5]) == recaudo:
                i[6] = color
                self.gasto_total += Decimal(i[2])
            else:
                i[6] = '#000'


    def liquidar_salida(self, *args):
        if not self.editar:
            return
        try:
            path, column = self.treeview_vueltas.get_cursor()
            self.path = int(path[0])
            row = self.model_vueltas[path]
        except:
            return False
        salida = row[4]
        if self.salidas_json[salida]['recaudo']:
            return Widgets.Alerta('Salida Recaudada', 'error.png', 'Ya está registrado un recaudo de esta unidad')
        dialogo = Factura(self, True, salida)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            for r in respuesta['pagos2']:
                self.model_gastos.append([True] + list(r) + ['#080'])
                self.salidas_json[salida]['cobranzas'].append(r[4])
            self.calcular()
        dialogo = Factura(self, False, salida)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            for r in respuesta['pagos2']:
                self.model_gastos.append([True] + list(r) + ['#080'])
                self.salidas_json[salida]['cobranzas'].append(r[4])
            self.calcular()
        self.marcar_cobranzas(salida)
        dialogo = Widgets.Alerta_Numero('Nuevo Recaudo', 'dinero.png', 'Escriba la cantidad de dinero recibido', 10, True)
        restante = Decimal(row[1]) - self.gasto_total
        dialogo.entry.set_text(str(restante))
        dialogo.entry.set_editable(False)
        numero = dialogo.iniciar()
        if numero:
            ids = []
            for r in self.model_vueltas:
                ids.append(r[4])
            transbordo = 0
            for f in self.model_transbordo:
                transbordo += Decimal(f[1])

            row = self.http.load('recaudar', {'ruta_id': self.ruta,
                'lado': self.lado,
                'padron': self.padron,
                'ids': json.dumps(ids),
                'monto': numero,
                'transbordo': str(transbordo),
                'salida': salida})
            if row:
                if isinstance(row, list):
                    self.model_retiros.append((True,
                     row[0],
                     row[1],
                     row[2],
                     row[3],
                     row[5],
                    '#080'))
                    self.salidas_json[salida]['recaudo'] = row[5]
                else:
                    self.model_retiros.append([True] + row['recaudo'] + ['#080'])
                    self.salidas_json[salida]['recaudo'] = row[4]
                for row in self.model_vueltas:
                    if row[4] == str(salida):
                        row[2] += ' BLOQ'
                self.calcular()
                self.marcar_cobranzas()
        dialogo.cerrar()


    def calcular_wrapped(self, widgets, event):
        if event.keyval == 65421 or event.keyval == 65293:
            self.do_move_focus(self, gtk.DIR_TAB_FORWARD)
        self.calcular()


    def calcular_pago(self, *args):
        salidas = []
        for v in self.model_vueltas:
            salidas.append(v[4])

        datos = {'padron': self.padron,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'salidas': json.dumps(salidas)}
        data = self.http.load('calcular-pago', datos)
        if data:
            self.conductor_pago.set_text(data['conductor'])
            self.cobrador_pago.set_text(data['cobrador'])
            self.alimentos.set_text(data['alimentos'])
            self.conductor.set_text(data['conductor_nombre'])
            self.cobrador.set_text(data['cobrador_nombre'])
            self.calcular()
            dialogo = CuadroPagos(self, data)
            dialogo.cerrar()

    def on_release_button(self, treeview, event):
        if not self.editar:
            return
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True

    def on_release_button_gastos(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.treeview = treeview
                self.menu_retiros.popup(None, None, None, event.button, t)
                self.menu_retiros.show_all()
            return True

    def editar_recaudo(self, *args):
        try:
            path, column = self.treeview_vueltas.get_cursor()
            path = int(path[0])
        except:
            return

        dialogo = Widgets.Alerta_Numero('Editar Producci\xc3\xb3n', 'editar.png', 'Escriba el recaudo para corregir la salida.\nLuego cierre y vuelva a abrir la ventana de liquidaci\xc3\xb3n.', 10, True)
        monto = dialogo.iniciar()
        dialogo.cerrar()
        if monto:
            try:
                float(monto)
            except:
                Widgets.Alerta('Monto inv\xc3\xa1lido', 'error.png', 'El monto es un n\xc3\xbamero inv\xc3\xa1lido')
                return

            datos = {'salida_id': self.model_vueltas[path][4],
             'padron': self.padron,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'monto': monto,
             'antes': self.model_vueltas[path][1],
             # 'calcular': self.calcular_siempre
                     }
            data = self.http.load('editar-recaudo', datos)
            if data:
                self.model_vueltas[path][1] = monto
                if data == self.padron:
                    bruto = 0
                    for f in self.model_vueltas:
                        bruto += Decimal(f[1])
                    self.bruto.set_text(str(bruto))
                self.calcular()

    def reimprimir_recaudo(self, *args):
        try:
            path, column = self.treeview_vueltas.get_cursor()
            path = int(path[0])
        except:
            return
        datos = {
            'salida': self.model_vueltas[path][4],
            'ruta_id': self.padre.ruta,
            'lado': self.padre.lado
        }
        self.http.load('reimprimir-recaudo', datos)

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return
        dialogo = Widgets.Alerta_SINO_Clave('Anular Item', 'warning.png', '\xc2\xbfEst\xc3\xa1 seguro de Anular este Item?')
        respuesta = dialogo.iniciar()
        clave = dialogo.clave
        dialogo.cerrar()
        model = self.treeview.get_model()
        for s in model:
            print list(s)
        if respuesta:
            i = model[path][5]
            datos = {'voucher_id': i,
             'padron': self.padron,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'dia': self.dia,
             'monto': model[path][2],
             'usuario': model[path][4],
             'detalle': model[path][1],
             'hora': model[path][2],
             'clave': clave
                     }
            print datos
            data = self.http.load('anular-pago', datos)
            if data:
                treeiter = model.get_iter(path)
                child_iter = model.convert_iter_to_child_iter(None, treeiter)
                model.get_model().remove(child_iter)
                for k in self.salidas_json.keys():
                    print k
                    v = self.salidas_json[k]
                    if v['recaudo'] == int(i):
                        v['recaudo'] = None
                        for row in self.model_vueltas:
                            print row[4], row[4] == str(k), row[4] == int(k), row[4] == k
                            if row[4] == str(k):
                                row[2] = row[2][:row[2].find(' BLOQ')]
                self.calcular()

    def toggled(self, widget, path, treeview):
        model = treeview.get_model()
        model[path][0] = not model[path][0]
        self.calcular()

    def recaudo(self, *args):
        dialogo = Widgets.Alerta_Numero('Nuevo Recaudo', 'dinero.png', 'Escriba la cantidad de dinero recibido', 10, True)
        numero = dialogo.iniciar()
        if numero:
            ids = []
            for r in self.model_vueltas:
                ids.append(r[4])

            transbordo = 0
            for f in self.model_transbordo:
                transbordo += Decimal(f[1])

            row = self.http.load('recaudar', {'ruta_id': self.ruta,
             'lado': self.lado,
             'padron': self.padron,
             'ids': json.dumps(ids),
             'monto': numero,
             'transbordo': str(transbordo)})
            if row:
                if isinstance(row, list):
                    self.model_retiros.append((True,
                     row[0],
                     row[1],
                     row[2],
                     row[3],
                     row[5],
                     '#222'))
                else:
                    self.model_retiros.append([True] + row['recaudo'])
                self.calcular()
        dialogo.cerrar()

    def ticket(self, *args):
        datos = {'padron': self.padron,
         'dia': self.dia}
        self.http.load('ticket-dia', datos)

    def preview(self, *args):
        dia = datetime.datetime.strptime(self.dia, '%Y-%m-%d')
        url = 'preview/%d?padron=%s' % (dia.toordinal(), self.padron)
        self.http.webbrowser(url)

    def fondo(self, *args):
        dialogo = Widgets.Alerta_Numero('Pago de Fondo de Unidad', 'fondo.png', 'Escriba la cantidad de dinero recibido', 10, True)
        numero = dialogo.iniciar()
        if numero:
            row = self.http.load('recaudar', {
                'ruta_id': self.ruta,
                'lado': self.lado,
                'padron': self.padron,
                'monto': numero})
            if row:
                if isinstance(row, list):
                    self.model_gastos.append((True,
                     row[0],
                     row[1],
                     row[2],
                     row[3],
                     row[5]))
                else:
                    self.model_gastos.append([True] + row['recaudo'])
                self.calcular()
        dialogo.cerrar()

    def cobro(self, widgets, tipo):
        dialogo = Factura(self, tipo)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            for r in respuesta['pagos2']:
                self.model_gastos.append([True] + list(r) + ['#222'])

            for r in respuesta['retiros2']:
                self.model_retiros.append([True] + list(r) + ['#222'])

            for r in respuesta['pasivos2']:
                self.model_pasivos.append([True] + list(r) + ['#222'])

            self.calcular()

    def entregado_toggled(self, *args):
        if self.check_entregado.get_active():
            self.entregado.set_property('editable', True)
        else:
            self.entregado.set_property('editable', False)
            self.entregado.set_text(self.neto.get_text())

    def calcular(self, *args):
        self.ver_editar()
        gastos = 0
        gastos_ids = []
        for r in self.model_gastos:
            if r[0]:
                gastos += Decimal(r[2])
                gastos_ids.append(r[4])

        bruto = Decimal(self.bruto.get_text())
        conductor = self.conductor_pago.get_text()
        cobrador = self.cobrador_pago.get_text()
        alimentos = self.alimentos.get_text()
        if conductor == '':
            conductor = 0
        if cobrador == '':
            cobrador = 0
        if alimentos == '':
            alimentos = 0
        quedarse = 0
        try:
            quedarse += Decimal(conductor)
            quedarse += Decimal(cobrador)
            quedarse += Decimal(alimentos)
        except:
            self.but_imprimir.set_sensitive(False)
        else:
            self.but_imprimir.set_sensitive(True)

        entregado = 0
        for r in self.model_retiros:
            if r[0]:
                entregado += Decimal(r[2])

        pasivos = 0
        for p in self.model_pasivos:
            if p[0]:
                pasivos += Decimal(p[2])

        transbordos = 0
        for f in self.model_transbordo:
            transbordos += Decimal(f[1])

        tiene = bruto - gastos - entregado + transbordos
        self.cobrador_tiene.set_text(str(tiene))
        self.quedarse.set_text(str(quedarse))
        self.recaudado.set_text(str(entregado))
        por_recaudar = (tiene - quedarse).quantize(Decimal('0.01'))
        self.por_recaudar.set_text(str(por_recaudar))
        gastos += quedarse + pasivos
        neto = bruto - gastos
        self.neto.set_text(str(neto))
        self.gastos.set_text(str(gastos))

    def ver_editar(self):
        return
        if self.editar:
            self.treeview_vueltas.set_sensitive(True)
        else:
            self.treeview_vueltas.set_sensitive(False)

    def guardar(self, *args):
        return self.preparar(False)

    def imprimir(self, *args):
        return self.preparar(True)

    def preparar(self, imprimir):
        por_recaudar = Decimal(self.por_recaudar.get_text())
        neto = float(self.neto.get_text())
        gastos = []
        salidas = []
        transbordos = []
        for v in self.model_vueltas:
            if v[0]:
                salidas.append(v[4])

        for t in self.model_transbordo:
            if t[0]:
                transbordos.append(t[4])

        for r in self.model_gastos:
            if r[0]:
                gastos.append(r[5])

        for r in self.model_retiros:
            if r[0]:
                gastos.append(r[5])

        for r in self.model_pasivos:
            if r[0]:
                gastos.append(r[5])

        self.datos = {'dia': self.dia,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron,
         'conductor': self.conductor.get_text(),
         'cobrador': self.cobrador.get_text(),
         'conductor_pago': self.conductor_pago.get_text(),
         'cobrador_pago': self.cobrador_pago.get_text(),
         'alimentos': self.alimentos.get_text(),
         'bruto': self.bruto.get_text(),
         'gastototal': self.gastos.get_text(),
         'neto': self.neto.get_text(),
         'observacion': self.observacion.get_text()[:256],
         'salidas': json.dumps(salidas),
         'gastos': json.dumps(gastos),
         'transbordos': json.dumps(transbordos),
         'liquidacion_id': self.liquidacion_id,
         'imprimir': imprimir}
        print self.datos
        response = self.http.load('guardar-liquidacion', self.datos)
        if response:
            self.cerrar()


class CuadroPagos(gtk.Dialog):

    def __init__(self, padre, data):
        super(CuadroPagos, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = padre.http
        self.padron = padre.padron
        self.ruta = padre.ruta
        self.lado = padre.lado
        self.dia = padre.dia
        self.set_transient_for(parent)
        self.set_title('Calculo de Pagos al Personal Padron:%d D\xc3\xada: %s' % (self.padron, self.dia))
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        self.treeview = Widgets.TreeViewId('PERSONAL', ('PERSONAL', 'VUELTAS', 'PAGO', 'FONDO', 'TOTAL'))
        self.treeview.escribir(data['personal_completo'])
        self.treeview.scroll.set_size_request(600, 300)
        self.vbox.pack_start(self.treeview)
        self.ticket = data['ticket']
        fondo = Widgets.Button('fondo.png', 'Cobrar Fondo')
        fondo.connect('clicked', self.cobrar_fondo)
        self.action_area.pack_start(fondo, False, False, 0)
        reporte = Widgets.Button('reporte.png', 'Reporte Fondo')
        reporte.connect('clicked', self.reporte)
        self.action_area.pack_start(reporte, False, False, 0)
        self.but_ok = Widgets.Button('imprimir.png', '_Imprimir')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.but_imprimir = Widgets.Button('imprimir.png', '_Imprimir')
        self.action_area.pack_start(self.but_imprimir, False, False, 0)
        self.but_imprimir.connect('clicked', self.imprimir)
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.iniciar()

    def reporte(self, *args):
        row = self.treeview.get_selected()
        if row:
            datos = {'trabajador_id': row[5],
             'dia': self.dia,
             'ruta_id': self.ruta,
             'padron': self.padron}
            respuesta = self.http.load('reporte-fondo', datos)
            if respuesta:
                dialog = Widgets.Alerta_TreeView('Reporte de Fondo: %s' % row[0], 'Estado de Cuenta TOTAL: %s' % respuesta['total'], 'Fondos', ('DIA', 'TICKET', 'MONTO'), respuesta['tabla'])
                dialog.set_default_size(400, 500)
                dialog.iniciar()

    def cobrar_fondo(self, *args):
        row = self.treeview.get_selected()
        if row:
            datos = {'trabajador_id': row[5],
             'monto': row[3],
             'dia': self.dia,
             'ruta_id': self.ruta,
             'padron': self.padron}
            respuesta = self.http.load('pagar-fondo', datos)
            if respuesta:
                Widgets.Alerta('Pago de Fondo', 'caja.png', 'Se ha hecho un pago de fondo por %s a %s' % (row[3], row[0]))

    def imprimir(self, *args):
        self.http.ticket(self.ticket)
        self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        respuesta = self.run()
        if respuesta == gtk.RESPONSE_OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Factura(gtk.Dialog):

    def __init__(self, padre, tipo, salida=None):
        super(Factura, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.salida = salida
        self.http = padre.http
        self.padron = padre.padron
        self.ruta = padre.ruta
        self.lado = padre.lado
        self.dia = padre.dia
        self.tipo = tipo
        self.pagos = self.http.get_pagos(self.ruta)
        self.data = False
        self.seriacion = None
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Nueva Factura')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        tabla = gtk.Table(2, 2)
        tabla.attach(gtk.Label('Padr\xc3\xb3n:'), 0, 1, 0, 1)
        tabla.attach(gtk.Label('D\xc3\xada:'), 0, 1, 1, 2)
        tabla.attach(gtk.Label('Numero:'), 0, 1, 2, 3)
        tabla.attach(gtk.Label('Venta al Crédito:'), 0, 1, 3, 4)
        self.entry_padron = Widgets.Numero(11)
        self.fecha = Widgets.Fecha()
        self.entry_numero = Widgets.Numero(10)
        self.check_credito = gtk.CheckButton()
        tabla.attach(self.entry_padron, 1, 2, 0, 1)
        tabla.attach(self.fecha, 1, 2, 1, 2)
        tabla.attach(self.entry_numero, 1, 2, 2, 3)
        tabla.attach(self.check_credito, 1, 2, 3, 4)
        self.entry_padron.set_text(str(self.padron))
        self.fecha.set_date(self.dia)
        self.vbox.pack_start(tabla, False, False, 0)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(400, 300)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, bool, int, int, gobject.TYPE_PYOBJECT, bool, bool)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('CONCEPTO', 'MONTO', 'A CAJA')
        sw.add(self.treeview)
        self.columns = []
        for i, columna in enumerate(columnas):
            tvcolumn = Widgets.TreeViewColumn(columna)
            if i == 2:
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled)
                cell.set_property('activatable', True)
            else:
                cell_text = Widgets.Cell()
                tvcolumn.pack_start(cell_text, True)
                if i == 0:
                    tvcolumn.set_attributes(cell_text, markup=i, editable=6)
                elif i == 1:
                    tvcolumn.set_attributes(cell_text, markup=i, editable=7)
                cell_text.connect('editado', self.editado, i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()
            self.columns.append(tvcolumn)

        self.but_ok = Widgets.Button('dinero.png', '_Facturar')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.but_facturar = Widgets.Button('dinero.png', '_Facturar')
        self.action_area.pack_start(self.but_facturar, False, False, 0)
        self.but_facturar.connect('clicked', self.facturar)
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        if self.tipo:
            conceptos = self.pagos['cobros']
        elif tipo is None:
            conceptos = self.pagos['pasivos']
        else:
            conceptos = self.pagos['gastos']
        self.conceptos = conceptos
        for p in conceptos:
            self.model.append((p[0],
             p[1],
             False,
             p[5],
             p[4],
             p[6],
             p[2],
             p[3]))

        self.set_focus(self.treeview)
        self.treeview.set_cursor(0, self.columns[2], True)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('TOTAL:'), False, False, 0)
        self.entry_total = Widgets.Entry()
        self.entry_total.set_property('editable', False)
        hbox.pack_end(self.entry_total, False, False, 0)

    def toggled(self, widget, path):
        path = int(path)
        self.model[path][2] = not self.model[path][2]
        if self.model[path][2]:
            if self.model[path][6]:
                self.treeview.set_cursor(path, self.columns[0], True)
            elif self.model[path][7]:
                self.treeview.set_cursor(path, self.columns[1], True)
            elif path + 1 == len(self.model):
                self.but_facturar.grab_focus()
            else:
                self.treeview.set_cursor(path + 1, self.columns[2], False)
        self.calcular()

    def editado(self, widget, path, new_text, i):
        if not self.model[path][2]:
            new_text = self.model[path][i]
        if i == 0:
            self.model[path][0] = new_text
            self.treeview.set_cursor(path, self.columns[1], True)
        else:
            try:
                n = Decimal(new_text)
            except:
                return

            self.model[path][1] = new_text
            if path + 1 == len(self.model):
                self.but_facturar.grab_focus()
            else:
                self.treeview.set_cursor(path + 1, self.columns[2], False)
        self.calcular()

    def calcular(self):
        total = 0
        for r in self.model:
            if r[2]:
                total += Decimal(r[1])
        self.entry_total.set_text(str(total))

    def nuevo(self, *args):
        dialogo = Pago(self, self.tipo)
        data = dialogo.iniciar()
        dialogo.cerrar()
        if data:
            if self.seriacion == None:
                self.seriacion = data[4]
            elif self.seriacion != data[4]:
                return Widgets.Alerta('Pagos diferentes', 'warning.png', 'El pago no pertenece a la serie de la Factura')
            self.model.append(data)

    def borrar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        treeiter = self.model.get_iter(path)
        self.model.remove(treeiter)

    def facturar(self, *args):
        credito = self.check_credito.get_active()
        if credito:
            mensaje = 'Confirme que desea grabar la facturaci\xc3\xb3n.\n<span foreground="#FF0000">PAGO AL CREDITO</span>'
        else:
            mensaje = 'Confirme que desea grabar la facturaci\xc3\xb3n.\nPAGO AL CONTADO'
        dialogo = Widgets.Alerta_SINO('Facturar', 'caja.png', mensaje)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        self.padron = self.entry_padron.get_text()
        self.dia = self.fecha.get_date()
        if respuesta:
            lista = []
            for f in self.model:
                if f[2]:
                    lista.append((f[0],
                     f[1],
                     f[5],
                     f[4],
                     f[3]))

            datos = {
                'json': json.dumps(lista),
                'padron': self.padron,
                'dia': self.dia,
                'ruta_id': self.ruta,
                'credito': int(credito),
                'salida': self.salida
            }
            try:
                datos['numero'] = self.entry_numero.get_text()
            except:
                pass
            respuesta = self.http.load('pago-multiple', datos)
            if respuesta:
                self.data = respuesta
                self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        respuesta = self.run()
        if respuesta == gtk.RESPONSE_OK:
            return self.data
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Pago(gtk.Dialog):

    def __init__(self, padre, tipo):
        super(Pago, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = padre.http
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(300, 200)
        self.set_title('Nuevo Pago')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        tabla = gtk.Table(3, 3)
        self.vbox.pack_start(tabla, False, False, 5)
        labels = ('Concepto:', 'Nombre:', 'Monto:')
        for i, name in enumerate(labels):
            label = gtk.Label(name)
            tabla.attach(label, 0, 1, i, i + 1)

        pagos = [('Escoja un Concepto', 0)]
        if tipo:
            conceptos = self.pagos['cobros']
        elif tipo is None:
            conceptos = self.pagos['pasivos']
        else:
            conceptos = self.pagos['gastos']
        self.tipo = tipo
        self.conceptos = conceptos
        for p in conceptos:
            pagos.append((p[0], p[4]))

        self.concepto = Widgets.ComboBox()
        self.concepto.set_lista(pagos)
        self.concepto.connect('changed', self.concepto_changed)
        tabla.attach(self.concepto, 1, 2, 0, 1)
        self.nombre = Widgets.Texto(128)
        tabla.attach(self.nombre, 1, 2, 1, 2)
        self.monto = Widgets.Texto(16)
        tabla.attach(self.monto, 1, 2, 2, 3)
        self.caja = gtk.Label('')
        tabla.attach(self.caja, 0, 2, 3, 4)
        self.but_ok = Widgets.Button('confirmar.png', 'Aceptar')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.but_cancel = Widgets.Button('cancelar.png', 'Cancelar')
        self.add_action_widget(self.but_cancel, gtk.RESPONSE_CANCEL)
        self.seriacion = False
        self.efectivo = False
        self.concepto_changed()

    def concepto_changed(self, *args):
        pago = self.concepto.get_id()
        if pago:
            for p in self.conceptos:
                if p[4] == pago:
                    pago = p
                    break

            self.nombre.set_sensitive(pago[2])
            if pago[2]:
                texto = ''
            else:
                texto = self.concepto.get_text()
            self.nombre.set_text('')
            self.monto.set_sensitive(pago[3])
            self.monto.set_text(pago[1])
            self.seriacion = pago[5]
            self.efectivo = pago[6]
            if pago[6]:
                self.caja.set_markup('<span foreground="#B00">RECIBIR EFECTIVO</span>')
            else:
                self.caja.set_markup('GASTO EXTERNO')
        else:
            self.nombre.set_sensitive(False)
            self.nombre.set_text('')
            self.monto.set_sensitive(False)
            self.monto.set_text('')
            self.caja.set_markup('')

    def iniciar(self):
        self.show_all()
        respuesta = self.run()
        if respuesta == gtk.RESPONSE_OK:
            if self.nombre.get_sensitive():
                concepto = '%s - %s' % (self.concepto.get_text(), self.nombre.get_text())
            else:
                concepto = self.concepto.get_text()
            monto = self.monto.get_text()
            pago = self.concepto.get_id()
            return (concepto,
             monto,
             self.efectivo,
             pago,
             self.seriacion)
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class BuscarBoleto(gtk.Dialog):

    def __init__(self, http, ruta):
        super(BuscarBoleto, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = http
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(300, 500)
        self.set_title('Buscar Boleto por N\xc3\xbamero')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        tabla = gtk.Table(3, 3)
        self.vbox.pack_start(tabla, False, False, 5)
        labels = ('Boleto:', u'N\xfamero:')
        for i, name in enumerate(labels):
            label = gtk.Label(name)
            tabla.attach(label, 0, 1, i, i + 1)

        self.boleto = Widgets.ComboBox()
        datos = {'ruta_id': ruta}
        self.ruta = ruta
        lista = self.http.load('boletos-ruta', datos)
        if lista:
            pass
        else:
            return
        lista_arreglada = []
        for l in lista:
            lista_arreglada.append(('%s %s' % (l[1], l[2]), l[0]))

        self.boleto.set_lista(lista_arreglada)
        tabla.attach(self.boleto, 1, 2, 0, 1)
        self.numero = Widgets.Numero(6)
        self.numero.connect('activate', self.buscar)
        tabla.attach(self.numero, 1, 2, 1, 2)
        but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.but_ok = Widgets.Button('buscar.png', '_Buscar')
        self.model = gtk.ListStore(int, str, str, str, str, str)
        self.treeview = Widgets.TreeView(self.model)
        for i, c in enumerate(('UNIDAD', 'SERIE', 'ACTUAL', 'ESTADO', 'HORA')):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(c)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.connect('row-activated', self.row_activated)
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(self.sw)
        self.sw.add(self.treeview)
        self.frame_mensaje = Widgets.Frame('Resultados')
        self.vbox.pack_start(self.frame_mensaje, False, False, 0)
        self.label = gtk.Label('')
        self.frame_mensaje.add(self.label)
        self.action_area.pack_start(self.but_ok)
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok.connect('clicked', self.buscar)
        self.set_focus(self.boleto)
        self.iniciar()

    def iniciar(self):
        self.show_all()
        self.frame_mensaje.hide_all()
        self.run()
        self.cerrar()

    def buscar(self, *args):
        boleto = self.boleto.get_id()
        numero = self.numero.get_text()
        datos = {'boleto_id': boleto,
         'numero': numero,
         'ruta_id': self.ruta}
        mensajes = self.http.load('buscar-serie', datos)
        self.model.clear()
        for r in mensajes:
            self.model.append(r)
            self.frame_mensaje.show_all()
            self.label.set_markup('<b>Suministros que coinciden con la busqueda.</b>\nPara ver el boleto haga doble clic en un suministro\nde la lista.')

    def row_activated(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        datos = {'suministro_id': self.model[path][5],
         'numero': self.numero.get_text(),
         'ruta_id': self.ruta}
        mensaje = self.http.load('buscar-boleto', datos)
        if mensaje:
            self.frame_mensaje.show_all()
            self.label.set_markup(mensaje)

    def set_defaults(self, defaults):
        for key in defaults:
            self.params[key].set(defaults[key])

    def cerrar(self, *args):
        self.destroy()


class ReservaStock(gtk.Dialog):

    def __init__(self, padron, selector, http, reservas):
        super(ReservaStock, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.padron = padron
        self.dia, self.ruta, self.lado = selector.get_datos()
        self.padron = padron
        self.http = http
        self.but_guardar = Widgets.Button('aceptar.png', '_Aceptar')
        self.action_area.pack_start(self.but_guardar, False, False, 0)
        self.but_guardar.connect('clicked', self.comprobar)
        self.but_ok = Widgets.Button('aceptar.png', '_Aceptar')
        but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.but_guardar.set_sensitive(False)
        self.set_default_size(200, 200)
        self.set_border_width(10)
        self.set_title('Anular Stock: PADRON %d' % self.padron)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        self.model = gtk.ListStore(str, str, int, str, str, str, str, str, str, bool, str, str)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('BOLETO', 'TARIFA', 'QUEDAN', 'SERIE', 'INICIO', 'ACTUAL', 'FIN', 'HORA', 'DESPACHADOR', 'ANULAR')
        for i, columna in enumerate(columnas):
            if i == 9:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i, background=11)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.connect('row-activated', self.anular)
        self.vbox.pack_start(self.treeview, True, True, 0)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        label = gtk.Label('Motivo de anulaci\xc3\xb3n: (obligatorio)')
        hbox.pack_start(label, False, False, 0)
        self.motivo = gtk.Entry(128)
        hbox.pack_start(self.motivo, True, True, 0)
        self.motivo.connect('key-release-event', self.revisar_texto)
        self.motivo.connect('activate', self.activate_motivo)
        for r in reservas:
            self.model.append(r)

        self.menu = gtk.Menu()
        # item1 = gtk.MenuItem('Anular Taco')
        # item1.connect('activate', self.anular_taco)
        # self.menu.append(item1)
        item1 = gtk.MenuItem('Recuperar Taco')
        item1.connect('activate', self.recuperar_taco)
        self.menu.append(item1)
        item1 = gtk.MenuItem('Anular Rango')
        item1.connect('activate', self.anular_pedazo)
        self.menu.append(item1)
        item2 = gtk.MenuItem('Definir como Actual')
        item2.connect('activate', self.definir_actual)
        self.menu.append(item2)
        item3 = gtk.MenuItem('Definir como Reserva')
        item3.connect('activate', self.definir_reserva)
        self.menu.append(item3)
        self.treeview.connect('button-release-event', self.on_release_button)

    def anular_taco(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][10]
        except:
            return
        dialogo = Widgets.Alerta_Numero('Anular Taco', 'error_numero.png', 'Indique el PRIMER boleto del taco a anular')
        numero = dialogo.iniciar()
        tipo = self.model[path][0]
        if numero:
            inicio = int(self.model[path][5])
            fin = int(self.model[path][6])
            if not inicio <= numero <= fin:
                dialogo.cerrar()
                return Widgets.Alerta('Error Número', 'error_numero.png', 'El número no pertenece al suministro seleccionado.')
            pregunta = Widgets.Alerta_Texto('Anulaci\xc3\xb3n de Boletos', ('Perdida', 'Salteo', 'Inspectoria'))
            motivo = pregunta.iniciar()
            if motivo:
                datos = {'stock_id': stock_id,
                 'taco': numero,
                 'motivo': motivo,
                 'ruta_id': self.ruta,
                 'lado': self.lado,
                 'dia': self.dia,
                 'padron': self.padron,
                 'tipo': tipo}
                self.http.load('anular-taco', datos)
        dialogo.cerrar()

    def recuperar_taco(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][10]
        except:
            return
        tipo = self.model[path][0]
        dialogo = Widgets.Alerta_Numero('Recuperar Taco', 'actualizar.png', 'Indique el PRIMER boleto del taco a anular', digitos=6)
        numero = dialogo.iniciar()
        if numero:
            inicio = int(self.model[path][5])
            fin = int(self.model[path][6])
            if not inicio <= int(numero) <= fin:
                print inicio, numero, fin
                dialogo.cerrar()
                return Widgets.Alerta('Error Número', 'error_numero.png', 'El número no pertenece al suministro seleccionado.')
            pregunta = Widgets.Alerta_Texto('Recuperación de Boletos', ('Salteo', 'Inspectoria'))
            motivo = pregunta.iniciar()
            if motivo:
                datos = {'stock_id': stock_id,
                 'taco': numero,
                 'motivo': motivo,
                 'ruta_id': self.ruta,
                 'lado': self.lado,
                 'dia': self.dia,
                 'padron': self.padron,
                 'tipo': tipo}
                self.http.load('recuperar-taco', datos)
        dialogo.cerrar()

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def anular_pedazo(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][10]
        except:
            return
        tipo = self.model[path][0]
        if self.model[path][11] == '#FFF':
            estado = 'EN USO'
        elif self.model[path][11] == '#CFC':
            estado = 'RESERVA'
        else:
            estado = 'STOCK'
        dialogo = Widgets.Alerta_Anular_Numeros('Anular boletaje', 'error_numero.png', 'Indique el PRIMER boleto a anular y\nel ULTIMO boleto a anular')
        numeros = dialogo.iniciar()
        if numeros and len(numeros) == 2:
            inicio = int(self.model[path][5])
            fin = int(self.model[path][6])
            if numeros[0] > fin or numeros[0] < inicio or numeros[1] > fin or numeros[1] < inicio:
                dialogo.cerrar()
                return Widgets.Alerta('Error N\xc3\xbameros', 'error_numero.png', 'Los n\xc3\xbameros no pertenecen al suministro seleccionado.')
            pregunta = Widgets.Alerta_Texto('Anulaci\xc3\xb3n de Boletos', ('Perdida', 'Salteo', 'Inspectoria'))
            motivo = pregunta.iniciar()
            if motivo:
                datos = {'stock_id': stock_id,
                 'inicio': numeros[0],
                 'fin': numeros[1],
                 'motivo': motivo,
                 'ruta_id': self.ruta,
                 'lado': self.lado,
                 'dia': self.dia,
                 'padron': self.padron,
                 'tipo': tipo,
                 'estado': estado}
                self.http.load('anular-pedazo-stock', datos)
        dialogo.cerrar()

    def definir_reserva(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][10]
        except:
            return
        tipo = self.model[path][0]
        estado = ''
        for r in self.model:
            if tipo == r[0]:
                if r[11] == '#FFF':
                    estado += '</br>EN USO:%s-%s' % (r[4], r[5])
                elif r[11] == '#CFC':
                    estado += '</br>RESERVA:%s-%s' % (r[4], r[5])
                else:
                    estado += '</br>STOCK:%s-%s' % (r[4], r[5])
        cambiar = '%s-%s' % (r[4], r[5])
        dialogo = Widgets.Alerta_SINO('Definir Reserva', 'warning.png', '\xc2\xbfDesea definir el suministro como reserva?')
        if dialogo.iniciar():
            datos = {'stock_id': stock_id,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'dia': self.dia,
             'padron': self.padron,
             'estado': estado,
             'cambiar actual': cambiar,
             'tipo': tipo}
            self.http.load('definir-reserva', datos)
        dialogo.cerrar()
        self.cerrar()

    def definir_actual(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            stock_id = self.model[path][10]
        except:
            return
        tipo = self.model[path][0]
        estado = ''
        for r in self.model:
            if tipo == r[0]:
                if r[11] == '#FFF':
                    estado += '</br>EN USO:%s-%s' % (r[4], r[5])
                elif r[11] == '#CFC':
                    estado += '</br>RESERVA:%s-%s' % (r[4], r[5])
                else:
                    estado += '</br>STOCK:%s-%s' % (r[4], r[5])
        cambiar = '%s-%s' % (r[4], r[5])
        dialogo = Widgets.Alerta_SINO('Definir Actual', 'warning.png', '\xc2\xbfDesea definir el suministro el actualmente en uso?')
        if dialogo.iniciar():
            datos = {'stock_id': stock_id,
             'ruta_id': self.ruta,
             'lado': self.lado,
             'dia': self.dia,
             'padron': self.padron,
             'estado': estado,
             'cambiar actual': cambiar,
             'tipo': tipo
                     }
            self.http.load('definir-actual', datos)
        dialogo.cerrar()
        self.cerrar()

    def comprobar(self, widget):
        motivo = self.motivo.get_text()
        ids = []
        detalle = ''
        for i, d in enumerate(self.model):
            if d[9]:
                ids.append(d[10])
                detalle += '</br>%s(%s-%s)=%s' % (d[0], d[5], d[6], d[2])
        datos = {
         'id': json.dumps(ids),
         'motivo': motivo,
         'dia': self.dia,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'padron': self.padron,
         'detalle': detalle
        }
        self.respuesta = self.http.load('anular-stock', datos)
        if self.respuesta:
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            return True
        else:
            return False

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        b = self.model[path][9]
        self.model[path][9] = not b

    def revisar_texto(self, *args):
        motivo = self.motivo.get_text()
        if motivo == '':
            self.but_guardar.set_sensitive(False)
        else:
            self.but_guardar.set_sensitive(True)

    def activate_motivo(self, *args):
        motivo = self.motivo.get_text()
        if motivo != '':
            self.but_guardar.clicked()

    def cerrar(self, *args):
        self.destroy()


class Reporte(gtk.Window):

    def __init__(self, http, dia, ruta, lado):
        super(Reporte, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.http = http
        self.fecha = Widgets.Fecha()
        self.fecha.set_size_request(150, 30)
        vbox_main = gtk.VBox(False, 0)
        self.add(vbox_main)
        self.datos = {}
        self.unidad = 0
        self.dia = None
        hbox = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('D\xc3\xada:'), False, False, 0)
        hbox.pack_start(self.fecha, False, False, 0)
        self.ruta = Widgets.ComboBox()
        hbox.pack_start(gtk.Label('Ruta:'), False, False, 0)
        hbox.pack_start(self.ruta, False, False, 0)
        self.lado = Widgets.ComboBox()
        hbox.pack_start(gtk.Label('Lado:'), False, False, 0)
        hbox.pack_start(self.lado, False, False, 0)
        self.tipo = Widgets.ComboBox()
        hbox.pack_start(gtk.Label('Tipo:'), False, False, 0)
        hbox.pack_start(self.tipo, False, False, 0)
        self.tipo.set_lista((('Voladas', 0),
         ('Retardos', 1),
         ('Horas', 2),
         ('Frecuencia', 3)))
        self.tipo.connect('changed', self.cambiar_contenido)
        self.controles = gtk.CheckButton('Mostrar Todos')
        self.controles.connect('toggled', self.mostrar_controles)
        hbox.pack_start(self.controles, False, False, 0)
        self.but_actualizar = Widgets.Button('actualizar.png', 'Actualizar')
        hbox.pack_start(self.but_actualizar, False, False, 0)
        self.but_actualizar.connect('clicked', self.actualizar)
        self.but_web = Widgets.Button('chrome.png', 'Monitoreo Web')
        hbox.pack_start(self.but_web, False, False, 0)
        self.but_web.connect('clicked', self.web)
        self.but_imprimir = Widgets.Button('imprimir.png', 'Imprimir')
        hbox.pack_start(self.but_imprimir, False, False, 0)
        self.but_imprimir.connect('clicked', self.imprimir)
        self.but_video = Widgets.Button('video.png', 'Video')
        hbox.pack_start(self.but_video, False, False, 0)
        self.but_video.connect('clicked', self.video)
        herramientas = [('-30 min', 'skip-backward.png', self.skip_backward),
         ('x100', 'fast-backward.png', self.fast_backward),
         ('-1 seg', 'backward.png', self.backward),
         ('Play x20', 'play.png', self.play_pause),
         ('+1 seg', 'forward.png', self.forward),
         ('x100', 'fast-forward.png', self.fast_forward),
         ('+30min', 'skip-forward.png', self.skip_forward),
         ('Finalizar', 'eject.png', self.eject)]
        self.toolbar = Widgets.Toolbar(herramientas)
        vbox_main.pack_start(self.toolbar, False, False, 0)
        self.dia = self.fecha.get_date()
        self.lado.set_lista((('A', 0), ('B', 1)))
        lista = self.http.datos['rutas']
        self.ruta.set_lista(lista)
        self.set_title('Monitoreo de Flota')
        vpaned = gtk.VPaned()
        vbox_main.pack_start(vpaned, True, True, 0)
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.set_size_request(100, 100)
        vpaned.pack1(self.sw, True, False)
        hpaned = gtk.HPaned()
        vpaned.pack2(hpaned, True, True)
        url = 'http://%s/despacho/ingresar/?sessionid=%s&next=monitoreo' % (self.http.appengine, self.http.sessionid)
        if os.name == 'nt':
            self.www = Chrome.Browser(url, 550, 100)
        else:
            self.www = Chrome.IFrame(url, 550, 100)
            print url
        hpaned.pack1(self.www, True, False)
        self.sw_eventos = gtk.ScrolledWindow()
        hpaned.pack2(self.sw_eventos, True, True)
        if os.name == 'nt':
            self.set_size_request(720, 540)
        else:
            self.set_size_request(800, 600)
        self.model = gtk.ListStore(int)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        selection = self.treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        self.sw.add(self.treeview)
        self.model_eventos = gtk.ListStore(str, str, str, str)
        self.treeview_eventos = Widgets.TreeView(self.model_eventos)
        self.treeview_eventos.set_rubber_banding(False)
        self.treeview_eventos.set_enable_search(False)
        self.treeview_eventos.set_reorderable(False)
        self.sw_eventos.add(self.treeview_eventos)
        self.sw_eventos.set_size_request(100, 100)
        columnas = ['HORA', 'EVENTO']
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            tvcolumn.set_clickable(True)
            self.treeview_eventos.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.show_all()
        self.toolbar.hide_all()
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Refrecuenciar')
        item1.connect('activate', self.refrecuenciar)
        self.menu.append(item1)
        self.treeview.connect('row-activated', self.salida_seleccionada)
        self.treeview_eventos.connect('row-activated', self.evento_seleccionado)
        self.fecha.set_date(dia)
        self.ruta.set_id(ruta)
        self.lado.set_id(lado)
        self.lado.connect('changed', self.escribir_tabla)

    def web(self, *args):
        url = '/monitoreo/mapa'
        self.http.webbrowser(url)

    def actualizar(self, *args):
        ruta = self.ruta.get_id()
        lado = self.lado.get_id()
        datos = {'dia': self.fecha.get_date(),
         'ruta_id': ruta}
        data = self.http.load('flota-llegadas', datos)
        if data:
            self.data = data
            self.escribir_tabla()

    def escribir_tabla(self, *args):
        ruta = self.ruta.get_id()
        lado = self.lado.get_id()
        data = self.data[lado]
        self.columnas = data['columnas']
        lista = data['liststore']
        self.geocercas = data['geocercas']
        self.salidas = data['salidas']
        self.widths = data['widths']
        self.cabeceras = data['cabeceras']
        liststore = []
        for l in lista:
            liststore.append(eval(l))
        print 'lado', lado
        print self.salidas
        self.tabla = data['tabla']
        self.model = gtk.ListStore(*liststore)
        cols = self.treeview.get_columns()
        for c in cols:
            self.treeview.remove_column(c)

        for i, columna in enumerate(self.columnas):
            cell_text = gtk.CellRendererText()
            if isinstance(columna, list):
                tvcolumn = Widgets.TreeViewColumn(columna[0])
            else:
                tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            tvcolumn.set_clickable(True)
            tvcolumn.connect('clicked', self.centrar, i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.set_model(self.model)
        i = self.tipo.get_id()
        for fila in self.tabla:
            try:
                self.model.append(fila)
            except:
                print len(data['liststore']), data['liststore']
                print len(fila), fila
                raise

        self.cambiar_contenido()
        self.mostrar_controles()
        self.www.execute_script('set_ruta_lado(%d, %d);' % (ruta, lado))
        self.treeview_changed()

    def cambiar_contenido(self, *args):
        i = self.tipo.get_id()
        if i == 3:
            hora = {}
            dia = 0
            for y, fila in enumerate(self.tabla):
                for x, f in enumerate(fila):
                    if isinstance(f, list):
                        try:
                            int(f[0])
                            try:
                                hm = f[2].split(':')
                                minutos = int(hm[0]) * 60 + int(hm[1])
                            except:
                                minutos = None

                        except:
                            minutos = None

                        if x in hora:
                            hora[x].append([minutos, y, None])
                        else:
                            hora[x] = [[minutos, y, None]]

            for x in hora.keys():
                primero = hora[x][0]
                for row in hora[x]:
                    if row[0]:
                        if row[0] < primero:
                            row[0] += 1440

                hora[x].sort(key=itemgetter(0))

            for x in hora.keys():
                anterior = None
                for row in hora[x]:
                    if row[0]:
                        if anterior:
                            row[2] = row[0] - anterior
                        else:
                            row[2] = '?'
                    else:
                        row[2] = 'NM'
                    anterior = row[0]

            for x in hora.keys():
                hora[x].sort(key=itemgetter(1))

            for y, fila in enumerate(self.tabla):
                for x, f in enumerate(fila):
                    if isinstance(f, list):
                        self.model[y][x] = hora[x][y][2]

        else:
            for y, fila in enumerate(self.tabla):
                for x, f in enumerate(fila):
                    if isinstance(f, list):
                        try:
                            self.model[y][x] = f[i]
                        except:
                            raise

    def mostrar_controles(self, *args):
        todos = self.controles.get_active()
        for i, c in enumerate(self.columnas):
            if isinstance(c, list):
                self.treeview.get_column(i).set_visible(c[1] or todos)

    def treeview_changed(self, *args):
        adj = self.sw.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)

    def salida_seleccionada(self, *args):
        self.eject()
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return
        print 'path', path
        salida, unidad, padron = self.salidas[path]
        self.www.execute_script('set_salida(%d);' % salida)
        dia = self.fecha.get_date()
        if self.unidad != unidad or self.dia != dia:
            self.unidad = unidad
            self.dia = dia
            datos = {'unidad_id': unidad,
             'dia': dia,
             'salida_id': salida}
            eventos = self.http.load('registro', datos)
            self.model_eventos.clear()
            if eventos:
                for e in eventos:
                    self.model_eventos.append(e)

        else:
            self.www.execute_script('show_hide();')
        self.www.execute_script('update(%d);' % padron)

    def evento_seleccionado(self, *args):
        try:
            path, column = self.treeview_eventos.get_cursor()
            path = int(path[0])
        except:
            return

        lat = self.model_eventos[path][2]
        lng = self.model_eventos[path][3]
        self.www.execute_script('set_center(%s, %s);' % (lat, lng))

    def centrar(self, tv, i):
        try:
            geocerca = self.geocercas[i]
        except:
            return

        lat = geocerca[0]
        lng = geocerca[1]
        self.www.execute_script('set_center(%s, %s);' % (lat, lng))

    def imprimir(self, *args):
        reporte = Impresion.Excel('Reporte de Voladas', 'D\xc3\xada: %s Ruta: %s Lado: %s' % (self.fecha.get_date(), self.ruta.get_text(), self.lado.get_text()), self.cabeceras, list(self.model), self.widths)
        a = os.path.abspath(reporte.archivo)
        if os.name == 'nt':
            com = 'cd "%s" & start reporte.xls' % a[:12]
            print com
            os.system(com)
        else:
            os.system('gnome-open ' + a)

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def refrecuenciar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            salida_id = row[len(row) - 1]
        except:
            return

        dialogo = Widgets.Alerta_Entero('Refrecuenciar', 'editar.png', 'Indique La variaci\xc3\xb3n en minutos.', 2)
        numero = int(dialogo.iniciar())
        dialogo.cerrar()
        if numero:
            datos = {'salida_id': salida_id,
             'delta': numero,
             'dia': self.fecha.get_date(),
             'ruta_id': self.ruta.get_id(),
             'lado': self.lado.get_id(),
             'tipo': self.tipo.get_id()}
            data = self.http.load('refrecuenciar', datos)
            if data:
                columnas = data['columnas']
                lista = data['liststore']
                liststore = []
                for l in lista:
                    liststore.append(eval(l))

                tabla = data['tabla']
                self.model = gtk.ListStore(*liststore)
                cols = self.treeview.get_columns()
                for c in cols:
                    self.treeview.remove_column(c)

                for i, columna in enumerate(columnas):
                    cell_text = gtk.CellRendererText()
                    tvcolumn = Widgets.TreeViewColumn(columna)
                    tvcolumn.pack_start(cell_text, True)
                    tvcolumn.set_attributes(cell_text, markup=i)
                    self.treeview.append_column(tvcolumn)
                    tvcolumn.encabezado()

                self.treeview.set_model(self.model)
                for fila in tabla:
                    self.model.append(fila)

    def video(self, *args):
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()
        salidas = [0] * 4
        padrones = [0] * 4
        for i, p in enumerate(pathlist):
            if i > 3:
                selection.unselect_path(p)
            else:
                salida, unidad, padron = self.salidas[p[0]]
                salidas[i] = salida
                padrones[i] = padron

        self.www.execute_script('video(0, %d, %d, 1, %d, %d, 2, %d, %d, 3, %d, %d);' % (salidas[0],
         padrones[0],
         salidas[1],
         padrones[1],
         salidas[2],
         padrones[2],
         salidas[3],
         padrones[3]))
        self.toolbar.show_all()

    def play_pause(self, *args):
        if self.toolbar.get_label(3) == 'Play x20':
            self.toolbar.set_imagen_label(3, 'pause.png', 'Pause')
            self.www.execute_script('play();')
        else:
            self.toolbar.set_imagen_label(3, 'play.png', 'Play x20')
            self.www.execute_script('stop();')

    def skip_backward(self, *args):
        self.www.execute_script('skip_backward();')

    def skip_forward(self, *args):
        self.www.execute_script('skip_forward();')

    def fast_backward(self, *args):
        self.www.execute_script('fast_backward();')
        self.toolbar.set_imagen_label(3, 'pause.png', 'Pause')

    def fast_forward(self, *args):
        self.www.execute_script('fast_forward();')
        self.toolbar.set_imagen_label(3, 'pause.png', 'Pause')

    def forward(self, *args):
        self.www.execute_script('forward();')
        self.toolbar.set_imagen_label(3, 'play.png', 'Play x20')

    def backward(self, *args):
        self.www.execute_script('backward();')
        self.toolbar.set_imagen_label(3, 'play.png', 'Play x20')

    def eject(self, *args):
        self.www.execute_script('eject();')
        self.toolbar.set_imagen_label(3, 'play.png', 'Play x20')
        self.toolbar.hide_all()


class Relojes(gtk.Dialog):

    def __init__(self, llegadas):
        super(Relojes, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.llegadas = llegadas
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(220, 50)
        self.set_title('Registrar Relojes')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        formulario = gtk.HBox(False, 0)
        self.vbox.pack_start(formulario, False, False, 0)
        formulario.pack_start(gtk.Label('Nueva Hora:'), False, False, 0)
        self.entry_hora = Widgets.Hora()
        formulario.pack_start(self.entry_hora, False, False, 0)
        self.entry_hora.connect('enter', self.nueva_hora)
        self.button_deshacer = Widgets.Button('cancelar.png', '_Borrar')
        self.button_deshacer.connect('clicked', self.deshacer)
        formulario.pack_start(self.button_deshacer, False, False, 0)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        self.model = gtk.ListStore(int, str, str, str)
        self.treeview = Widgets.TreeView(self.model)
        columnas = ['N\xc2\xba',
         'CONTROL',
         'HORA',
         'VOLADA']
        self.http = llegadas.http
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_enable_search(False)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, text=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview.set_reorderable(False)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_size_request(200, 350)
        sw.add(self.treeview)
        hbox.pack_start(sw, False, False, 0)
        vbox = gtk.VBox(False, 0)
        hbox.pack_start(vbox, False, False, 0)
        self.but_arriba = Widgets.Button('arriba.png', None, 24, tooltip='Subir NM')
        vbox.pack_start(self.but_arriba, False, False, 0)
        self.but_abajo = Widgets.Button('abajo.png', None, 24, tooltip='Bajar NM')
        vbox.pack_start(self.but_abajo, False, False, 0)
        self.but_falla = Widgets.Button('mantenimiento.png', 'Falla Mec.')
        self.action_area.pack_start(self.but_falla, False, False, 0)
        self.but_falla.connect('clicked', self.falla_mecanica)
        self.but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.add_action_widget(self.but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('aceptar.png', '_Aceptar')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.but_arriba.connect('clicked', self.arriba)
        self.but_abajo.connect('clicked', self.abajo)
        self.lista_horas = []
        for f in self.llegadas.model:
            self.model.append((f[0],
             f[1],
             'NM',
             ''))

        self.falla = False

    def deshacer(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            hora = self.model[path][2]
            h, m = hora.split(':')
            hora = datetime.time(int(h), int(m))
        except:
            raise
            return

        self.lista_horas.remove(hora)
        self.actualizar()
        self.set_focus(self.entry_hora)

    def nueva_hora(self, widget, hora):
        if len(self.lista_horas) == len(self.llegadas.model):
            return
        self.lista_horas.append(hora)
        self.entry_hora.select_region(0, 2)
        self.actualizar()
        if len(self.lista_horas) == len(self.llegadas.model):
            self.set_focus(self.but_ok)

    def actualizar(self):
        lista = list(self.lista_horas)
        lista.sort()
        for i, f in enumerate(self.model):
            try:
                f[2] = lista[i].strftime('%H:%M')
                real = datetime.datetime.strptime(f[2], '%H:%M')
                original = datetime.datetime.strptime(self.llegadas.model[i][2], '%H:%M')
                if real > original:
                    v = (real - original).seconds / 60
                else:
                    v = -(original - real).seconds / 60
                f[3] = str(v)
            except:
                f[2] = 'NM'
                f[3] = 'NM'

    def arriba(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            hora = self.model[path][2]
        except:
            return

        if hora != 'NM':
            return
        if path == 0:
            return
        orden = self.model[path][0]
        control = self.model[path][1]
        self.model[path][0] = self.model[path - 1][0]
        self.model[path][1] = self.model[path - 1][1]
        self.model[path - 1][0] = orden
        self.model[path - 1][1] = control
        uno = self.model.get_iter(path)
        otro = self.model.get_iter(path - 1)
        self.model.swap(uno, otro)
        voladas = self.calcular()
        for i, f in enumerate(self.model):
            try:
                f[3] = voladas[i]
            except:
                f[3] = 'NM'

    def abajo(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            hora = self.model[path][2]
        except:
            return

        if hora != 'NM':
            return
        if len(self.model) == path + 1:
            return
        orden = self.model[path][0]
        control = self.model[path][1]
        self.model[path][0] = self.model[path + 1][0]
        self.model[path][1] = self.model[path + 1][1]
        self.model[path + 1][0] = orden
        self.model[path + 1][1] = control
        uno = self.model.get_iter(path)
        otro = self.model.get_iter(path + 1)
        self.model.swap(uno, otro)
        voladas = self.calcular()
        for i, f in enumerate(self.model):
            try:
                f[3] = voladas[i]
            except:
                f[3] = 'NM'

    def calcular(self):
        voladas = []
        for i, f in enumerate(self.model):
            if f[2] == 'NM':
                voladas.append('NM')
            else:
                real = datetime.datetime.strptime(f[2], '%H:%M')
                original = datetime.datetime.strptime(self.llegadas.model[i][2], '%H:%M')
                if real > original:
                    v = (real - original).seconds / 60
                else:
                    v = -(original - real).seconds / 60
                voladas.append(v)

        n = len(voladas)
        while self.falla:
            if voladas[-1] == 'NM':
                voladas.pop()
            else:
                voladas.append('FM')
                break

        while len(voladas) < n:
            voladas.append('NM')

        return voladas

    def falla_mecanica(self, *args):
        dialogo = Widgets.Alerta_SINO('Precauci\xc3\xb3n', 'warning.png', 'Est\xc3\xa1 seguro de guardar la salida como Falla Mec\xc3\xa1nica')
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            self.falla = True
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.set_focus(self.entry_hora)
        if self.run() == gtk.RESPONSE_OK:
            voladas = self.calcular()
            datos = {'salida_id': self.llegadas.salida,
             'voladas': json.dumps(voladas),
             'actualizar': False,
             'dia': self.llegadas.dia,
             'ruta_id': self.llegadas.ruta,
             'lado': self.llegadas.lado,
             'padron': self.llegadas.padron}
            data = self.http.load('guardar-llegadas', datos)
            if data:
                return True
        return False

    def cerrar(self, *args):
        self.destroy()


class Grifo(Widgets.Window):

    def __init__(self, http, ruta, lado):
        super(Grifo, self).__init__('Servicio de Grifo')
        if os.name == 'nt':
            self.set_size_request(380, 300)
        else:
            self.set_size_request(420, 350)
        self.http = http
        self.ruta = ruta
        self.lado = lado
        tabla = gtk.Table(2, 6)
        self.vbox.pack_start(tabla)
        y = 0
        for t in ('Fecha:', 'Petroleo:', 'Al Contado:', 'Serie', 'Padr\xc3\xb3n:', 'Monto:', 'Galones:'):
            tabla.attach(gtk.Label(t), 0, 1, y, y + 1)
            y += 1

        self.but_dia = Widgets.Fecha()
        tabla.attach(self.but_dia, 1, 2, 0, 1)
        self.combo_petroleo = Widgets.ComboBox((str, int, float))
        self.combo_petroleo.set_lista(self.http.grifo)
        tabla.attach(self.combo_petroleo, 1, 2, 1, 2)
        self.check_contado = gtk.CheckButton()
        self.check_contado.set_active(True)
        tabla.attach(self.check_contado, 1, 2, 2, 3)
        self.combo_serie = Widgets.ComboBox()
        self.combo_serie.set_lista(self.http.seriacion['facturas'])
        tabla.attach(self.combo_serie, 1, 2, 3, 4)
        self.entry_padron = Widgets.Numero(11)
        tabla.attach(self.entry_padron, 1, 2, 4, 5)
        self.entry_monto = Widgets.Texto(10)
        tabla.attach(self.entry_monto, 1, 2, 5, 6)
        self.entry_galones = Widgets.Texto(10)
        tabla.attach(self.entry_galones, 1, 2, 6, 7)
        self.entry_galones.set_sensitive(False)
        self.but_salir = self.crear_boton('cancelar.png', '_Cancelar', self.cerrar)
        # self.but_ventas = self.crear_boton('dinero.png', 'Reporte _Ventas', self.ventas)
        self.but_reporte = self.crear_boton('reporte.png', '_Registrar Contómetro', self.reporte)
        self.but_imprimir = self.crear_boton('guardar.png', '_Guardar', self.guardar)
        self.entry_monto.connect('key-release-event', self.calcular_galones)
        self.show_all()
        self.set_focus(self.entry_padron)

    def ventas(self, *args):
        dia = self.but_dia.get_date()
        petroleo = self.combo_petroleo.get_id()
        datos = {'dia': dia,
         'petroleo': petroleo}
        lista = self.http.load('ventas-grifo', datos)
        if lista:
            VentasGrifo(self, lista)
        else:
            Widgets.Aletra('Lista vac\xc3\xada', 'warning.png', 'No hay ventas en el d\xc3\xada seleccionado.')

    def reporte(self, *args):
        dia = self.but_dia.get_date()
        petroleo = self.combo_petroleo.get_id()
        precio = self.combo_petroleo.get_item()[2]
        dialogo = Widgets.Alerta_Numero('Generar Reporte', 'dinero.png', 'Escriba el N\xc3\xbamero de Registro para el d\xc3\xada\n%s' % dia, 12, True)
        registro = dialogo.iniciar()
        dialogo.cerrar()
        if registro:
            datos = {'dia': dia,
             'registro': registro,
             'petroleo': petroleo,
             'precio': precio}
            if self.http.load('previa-grifo', datos):
                dialogo = Widgets.Alerta_SINO('Confirmar Reporte', 'imprimir.png', 'Confirme si desea guardar el reporte:')
                if dialogo.iniciar():
                    lista = self.http.load('reporte-grifo', datos)
                    if lista:
                        VentasGrifo(self, lista)
                dialogo.cerrar()

    def calcular_galones(self, *args):
        precio = self.combo_petroleo.get_item()[2]
        monto = self.entry_monto.get_text()
        galones = float(monto) / precio
        self.entry_galones.set_text(str(round(galones, 3)))

    def guardar(self, *args):
        padron = self.entry_padron.get_text()
        if not padron.isdigit():
            return Widgets.Alerta('Error Padr\xc3\xb3n', 'error_numero.png', 'Digite un N\xc3\xbamero V\xc3\xa1lido.')
        pedido = []
        try:
            galones = float(self.entry_galones.get_text())
        except:
            return Widgets.Alerta('Error en galones', 'error_numero.png', 'La cantidad no es un n\xc3\xbamero v\xc3\xa1lido')
        if galones == 0:
            return Widgets.Alerta('Monto 0.00', 'error_numero.png', 'No puede imprimir un recibo por 0.00')
        precio = self.entry_monto.get_text()
        try:
            float(precio)
        except:
            return Widgets.Alerta('Error en Precio', 'error_numero.png', 'La cantidad no es un n\xc3\xbamero v\xc3\xa1lido')
        if self.check_contado.get_active():
            tipo = 'AL CONTADO'
        else:
            tipo = 'AL CR\xc3\x89DITO'
        recibo = '\nPADRON: %s\nPRECIO: %s\nGALONES: %s\n<span foreground="#FF0000" weight="bold">%s</span>' % (padron,
         precio,
         galones,
         tipo)
        dialogo = Widgets.Alerta_SINO('Confirmaci\xc3\xb3n', 'imprimir.png', '\xc2\xbfEst\xc3\xa1 seguro de Imprimir este recibo?' + recibo)
        if dialogo.iniciar():
            datos = {'ruta_id': self.ruta,
             'lado': self.lado,
             'dia': self.but_dia.get_date(),
             'padron': padron,
             'petroleo': self.combo_petroleo.get_id(),
             'monto': precio,
             'galones': galones,
             'serie': self.combo_serie.get_id(),
             'contado': int(self.check_contado.get_active())}
            response = self.http.load('orden-petroleo', datos)
            if response:
                self.entry_padron.set_text('')
                self.entry_monto.set_text('')
                self.entry_galones.set_text('')
                self.check_contado.set_active(True)
        dialogo.cerrar()

    def deudas(self, *args):
        padron = self.entry_padron.get_text()
        if padron.isdigit():
            data = self.http.load('deudas-unidad', {'ruta': self.ruta,
             'lado': self.lado,
             'padron': padron})
            if isinstance(data, list):
                dialogo = Deudas(self, data, padron)
                respuesta = dialogo.iniciar()
                dialogo.cerrar()
        else:
            Widgets.Alerta('Error Padr\xc3\xb3n', 'error_numero.png', 'Digite un N\xc3\xbamero V\xc3\xa1lido.')

    def cerrar(self, *args):
        self.destroy()


class Mantenimiento(Widgets.Window):

    def __init__(self, http, ruta, lado, dia):
        super(Mantenimiento, self).__init__('Servicio de Mantenimiento %s' % dia)
        if os.name == 'nt':
            self.set_size_request(550, 500)
        else:
            self.set_size_request(600, 550)
        self.http = http
        self.ruta = ruta
        self.lado = lado
        self.dia = dia
        self.codigo_back = None
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 5)
        button_actualizar = Widgets.Button('actualizar.png', tooltip='Actualizar Productos')
        hbox.pack_start(button_actualizar)
        button_actualizar.connect('clicked', self.actualizar)
        button_borrar = Widgets.Button('cancelar.png', tooltip='Eliminar Item')
        hbox.pack_start(button_borrar)
        button_borrar.connect('clicked', self.borrar)
        self.historia_but = Widgets.Button('relojes.png', '_Historia Compras')
        self.historia_but.connect('clicked', self.historia)
        hbox.pack_start(self.historia_but, False, False, 0)
        self.piezas_but = Widgets.Button('calendario.png', '_Programaci\xc3\xb3n')
        self.piezas_but.connect('clicked', self.programacion)
        hbox.pack_start(self.piezas_but, False, False, 0)
        self.odometro_but = Widgets.Button('odometro.png', '_Od\xc3\xb3metro')
        self.odometro_but.connect('clicked', self.odometro)
        hbox.pack_start(self.odometro_but, False, False, 0)
        #hbox.pack_start(gtk.Label('Padr\xc3\xb3n:'), False, False, 0)
        #self.entry_padron = Widgets.Numero(3)
        #hbox.pack_start(self.entry_padron, False, False, 0)

        frame = Widgets.Frame('Datos Comprador')
        self.vbox.pack_start(frame, False, False, 0)
        hb = gtk.HBox(False, 0)
        frame.add(hb)
        hb.pack_start(gtk.Label('Código: '), False, False, 0)
        self.entry_codigo = Widgets.Numero(8)
        hb.pack_start(self.entry_codigo, False, False, 0)
        self.entry_codigo.connect('activate', self.buscar_aportante)
        self.entry_codigo.connect('key-release-event', self.entry_codigo_release)
        but_buscar = Widgets.Button('buscar.png', '', 16, tooltip='Buscar Cliente')
        hb.pack_start(but_buscar, False, False, 0)
        but_buscar.connect('clicked', self.buscar_aportante)
        self.entry_nombre = Widgets.Texto(64)
        hb.pack_start(self.entry_nombre, False, False, 0)
        self.entry_nombre.set_sensitive(False)

        sw = gtk.ScrolledWindow()
        self.vbox.pack_start(sw, True, True, 5)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw.set_size_request(500, 350)
        else:
            sw.set_size_request(450, 350)
        self.model = gtk.ListStore(str, str, str, str, str, str, int, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        columnas = ('CANT', 'DESCRIPCION', 'PRECIO.', 'SUBTOTAL')
        self.columns = []
        self.cells = []
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            if i == 0:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado, i)
                cell.set_property('editable', True)
            elif i == 1:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado, i)
                cell.set_property('editable', True)
            elif i == 3:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado, i)
                cell.set_property('editable', True)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', False)
            self.cells.append(cell)
            column.set_flags(gtk.CAN_FOCUS)
            self.columns.append(column)
            column.pack_start(cell, True)
            column.set_attributes(cell, text=i)
            self.treeview.append_column(column)
            column.encabezado()

        self.model.append(('', '', '0.00', '0.00', 0, 0, 0, '0'))
        sw.add(self.treeview)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 5)
        hbox.pack_start(gtk.Label('TOTAL:'), True, False, 0)
        self.entry_total = gtk.Entry()
        self.entry_total.set_property('editable', False)
        hbox.pack_start(self.entry_total, True, False, 0)
        self.combo_credito = Widgets.ComboBox()
        self.combo_credito.set_lista((('Al Contado', 0), ('Al Crédito', 1)))
        hbox.pack_start(self.combo_credito, True, False, 0)
        self.but_salir = self.crear_boton('cancelar.png', '_Cancelar', self.cerrar)
        self.but_imprimir = self.crear_boton('imprimir.png', '_Imprimir', self.imprimir)
        self.show_all()
        self.set_focus(self.entry_codigo)
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Cambiar el Precio')
        item1.connect('activate', self.cambiar_precio)
        self.menu.append(item1)
        item2 = gtk.MenuItem('Aplicar Cargos')
        item2.connect('activate', self.aplicar_cargos)
        self.menu.append(item2)
        self.treeview.connect('button-release-event', self.on_release_button)
        if not self.http.productos:
            self.actualizar()

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def cambiar_precio(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        dialogo = Widgets.Alerta_Numero('Escriba el Nuevo Precio', 'dinero.png', 'El precio que escriba se guardar\xc3\xa1 como el precio PREDETERMINADO.', 10, True)
        precio = dialogo.iniciar()
        dialogo.cerrar()
        fila = self.model[path]
        datos = {'producto_id': fila[4],
         'precio': precio,
         'dia': self.dia,
         'lado': self.lado}
        response = self.http.load('cambiar-precio', datos)
        if response:
            fila[2] = precio
            fila[3] = round(float(precio) * float(fila[0]), 2)
            self.calcular()
            for p in self.http.productos:
                if p[7] == fila[4]:
                    p[2] = float(precio)

    def aplicar_cargos(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        dialogo = Widgets.Alerta_Numero('Escriba el Precio para esta venta', 'dinero.png', 'El precio que escriba se usar\xc3\xa1 s\xc3\xb3lo en ESTA VENTA.', 10, True)
        precio = dialogo.iniciar()
        dialogo.cerrar()
        fila = self.model[path]
        if float(fila[2]) < float(precio):
            fila[2] = precio
            fila[3] = round(float(precio) * float(fila[0]), 2)
            self.calcular()
        else:
            Widgets.Alerta('Operaci\xc3\xb3n no Permitida', 'warning.png', 'No puede reducir el precio de los productos.\nPero puede fijar un precio m\xc3\xa1s bajo con la opci\xc3\xb3n\nCAMBIAR DE PRECIO')

    def borrar(self, *args):
        if len(self.model) > 1:
            try:
                path, column = self.treeview.get_cursor()
                path = int(path[0])
                del self.model[path]
            except:
                return

    def editado(self, widget, path, new_text, i):
        if i == 0:
            if new_text == '':
                self.set_focus(self.but_imprimir)
            try:
                cantidad = Decimal(new_text)
            except:
                return
            self.model[path][0] = new_text
        elif i == 3:
            if new_text == '':
                self.set_focus(self.but_imprimir)
            try:
                subtotal = Decimal(new_text)
            except:
                return
            self.model[path][3] = new_text
        else:
            dialogo = Productos(self.http.productos, new_text, self)
            respuesta = dialogo.iniciar()
            dialogo.cerrar()
            if respuesta:
                self.model[path][1] = respuesta[1] # nombre
                self.model[path][2] = respuesta[2] # precio unit
                self.model[path][4] = respuesta[7] # id producto
                self.model[path][5] = respuesta[3] # stock
                self.model[path][6] = respuesta[6] # servicio
                self.model[path][7] = respuesta[5] # moneda
            else:
                return
        self.calcular()
        if path + 1 == len(self.model):
            try:
                cant = float(self.model[path][0])
            except:
                self.set_focus(self.but_imprimir)
            else:
                if cant == 0:
                    self.set_focus(self.but_imprimir)
                elif i == 0:
                    self.treeview.set_cursor(path, self.columns[i + 1], True)
                else:
                    self.model.append(('', '', '0.00', '0.00', 0, 0, 0, '0'))
                    self.treeview.set_cursor(path + 1, self.columns[0], True)
        elif i == 0:
            self.treeview.set_cursor(path, self.columns[i + 1], True)
        else:
            self.model.append(('', '', '0.00', '0.00', 0, 0, 0, '0'))
            self.treeview.set_cursor(path + 1, self.columns[0], True)

    def calcular(self, *args):
        total = 0
        for r in self.model:
            try:
                pedido = float(r[0])
            except:
                pass
            else:
                if r[1]:  # producto
                    if not r[6] and float(r[5]) < pedido:  # Servicio, stock insuficiente
                        Widgets.Alerta('Falta Stock', 'error.png', 'No hay suficiente stock.\nHay disponible de %s de %s' % (r[5], r[1]))
                    subtotal = Decimal(r[0]) * Decimal(r[2]).quantize(Decimal('0.01'), rounding=ROUND_UP)
                    r[3] = str(subtotal)
                    total += subtotal
                    lleno = True
                else:
                    lleno = False
        self.entry_total.set_text(str(total))

    def historia(self, *args):
        padron = self.entry_padron.get_text()
        if padron.isdigit():
            data = self.http.load('trabajos-unidad', {'ruta': self.ruta,
             'lado': self.lado,
             'padron': padron,
             'dia': self.dia})
            if isinstance(data, list):
                dialogo = Trabajos(self, data, padron)
                respuesta = dialogo.iniciar()
                dialogo.cerrar()
        else:
            Widgets.Alerta('Error Padr\xc3\xb3n', 'error_numero.png', 'Digite un N\xc3\xbamero V\xc3\xa1lido.')

    def programacion(self, *args):
        padron = self.entry_padron.get_text()
        if not padron.isdigit():
            padron = None
        data = self.http.load('mantenimiento-unidad', {'ruta': self.ruta,
         'lado': self.lado,
         'padron': padron})
        if isinstance(data, list):
            ProgramacionUnidad(self, data, padron, self.dia)

    def odometro(self, *args):
        padron = self.entry_padron.get_text()
        if padron.isdigit():
            dialogo = Widgets.Alerta_Numero('Ajustar Od\xc3\xb3metro', 'odometro.png', 'Escriba el n\xc3\xbamero que aparece en el od\xc3\xb3metro', 15, True)
            odometro = dialogo.iniciar()
            dialogo.cerrar()
            if odometro:
                data = self.http.load('editar-odometro', {'ruta': self.ruta,
                 'lado': self.lado,
                 'padron': padron,
                 'odometro': odometro})
        else:
            Widgets.Alerta('Error Padr\xc3\xb3n', 'error_numero.png', 'Digite un N\xc3\xbamero V\xc3\xa1lido.')

    def buscar_aportante(self, *args):
        codigo = self.entry_codigo.get_text()
        if codigo == self.codigo_back:
            self.do_move_focus(self, gtk.DIR_TAB_FORWARD)
        self.entry_nombre.set_text('')
        llave = None
        if self.http.conductores == []:
            datos = {'tipo': 'Conductor',
             'empresa_id': self.http.empresa}
            lista = self.http.load('personal', datos)
            if lista:
                self.http.conductores = lista
        if self.http.cobradores == []:
            datos = {'tipo': 'Cobrador',
             'empresa_id': self.http.empresa}
            lista = self.http.load('personal', datos)
            if lista:
                self.http.cobradores = lista
        self.lista = self.http.cobradores + self.http.conductores
        if codigo == '':
            dialogo = Personal(None, self.lista, self.http)
            js = dialogo.iniciar()
            dialogo.cerrar()
            codigo = js[1]
            self.entry_codigo.set_text(str(codigo))
            cod = int(codigo)
            llave = self.buscar_dni(cod)
        elif codigo.isdigit():
            llave = self.buscar_padron(int(codigo))
            if not llave:
                llave = self.buscar_placa(codigo)
            if not llave:
                llave = self.buscar_dni(int(codigo))
        if llave:
            self.entry_nombre.set_text(self.referencia)
            self.llave = llave
            self.codigo = codigo
            self.codigo_back = codigo

    def buscar_dni(self, dni):
        for l in self.lista:
            if l[1] == dni:
                self.referencia = l[0]
                self.tipo = 'Personal'
                return l[2]
        self.referencia = ''

    def buscar_padron(self, padron):
        if self.http.unidades == []:
            datos = {'tipo': 'Unidad'}
            lista = self.http.load('unidades', datos)
            if lista:
                self.http.unidades = lista
        for f in self.http.unidades:
            if f[0] == padron:
                self.referencia = '%s %s' % (f[1], f[2])
                self.tipo = 'Unidad'
                return f[2]
        self.referencia = ''
        return False

    def buscar_placa(self, placa):
        if self.http.unidades == []:
            datos = {'tipo': 'Unidad'}
            lista = self.http.load('unidades', datos)
            if lista:
                self.http.unidades = lista
        for f in self.http.unidades:
            if f[1].replace('-', '') == placa.upper().replace('-', ''):
                self.referencia = '%s %s' % (f[1], f[2])
                self.tipo = 'Unidad'
                return f[2]
        self.referencia = ''


    def entry_codigo_release(self, *args):
        codigo = self.entry_codigo.get_text()
        if self.codigo_back == codigo:
            self.entry_codigo.blanco()
        else:
            self.entry_codigo.rojo()

    def imprimir(self, *args):
        pedido = []
        try:
            total = float(self.entry_total.get_text())
        except:
            return Widgets.Alerta('Error en monto', 'error_numero.png', 'El monto no es un n\xc3\xbamero v\xc3\xa1lido')

        if total == 0:
            return Widgets.Alerta('Monto 0.00', 'error_numero.png', 'No puede imprimir un recibo por 0.00')
        moneda = None
        for r in self.model:
            if float(r[2]) == 0:
                continue
            if moneda is None:
                moneda = r[7]
            else:
                if moneda != r[7]:
                    if r[7]:
                        mensaje = 'Retire el producto %s su precio está en soles' % r[1]
                    else:
                        mensaje = 'Retire el producto %s su precio está en dólares' % r[1]
                    return Widgets.Alerta('No puede mezclar monedas', 'dinero.png', mensaje)

            if float(r[0]) > float(r[5]) and self.http.datos['almacen-stock']:
                mensaje = 'S\xc3\xb3lo hay %s unidades de %s' % (r[5], r[1])
                return Widgets.Alerta('Falta de existencias', 'error_numero.png', mensaje)
            pedido.append([r[0], r[1], r[2], r[3], r[4]])
        datos = {
            'ruta_id': self.ruta,
            'dia': self.dia,
            'lado': self.lado,
            'codigo': self.codigo,
            'llave': self.llave,
            'tipo': self.tipo,
            'credito': self.combo_credito.get_id(),
            'pedido': json.dumps(pedido),
            'total': self.entry_total.get_text(),
            'almacen_id': self.http.datos['almacen'][0][1]}
        response = self.http.load('guardar-servicio', datos)
        if response:
            if self.http.datos['almacen-stock']:
                for i, r in enumerate(self.model):
                    if r[4] > 0:
                        for p in self.http.productos:
                            if p[7] == r[4]:
                                queda = float(p[3]) - float(r[0])
                                p[3] = queda

            self.cerrar()

    def actualizar(self, *args):
        almacenes = []
        for a in self.http.datos['almacen']:
            almacenes.append(a[1])
        datos = {'ruta': self.ruta, 'lado': self.lado, 'almacen_id': json.dumps(almacenes)}
        data = self.http.load('almacen', datos)
        if data:
            self.http.productos = data['productos']
        for r in self.model:
            if r[4] in self.http.productos:
                p = self.http.productos
                r[2] = p[2]
                r[5] = p[3]
        self.calcular()

    def cerrar(self, *args):
        self.destroy()

class Productos(gtk.Dialog):

    def __init__(self, lista, search, parent):
        super(Productos, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.http = parent.http
        self.ruta = parent.ruta
        self.lado = parent.lado
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(650, 400)
        self.set_title('B\xc3\xbasqueda de Productos: ' + search)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Por Nombre:'))
        self.entry_nombre = Widgets.Texto(45)
        self.entry_nombre.set_width_chars(10)
        hbox.pack_start(self.entry_nombre)
        button_actualizar = Widgets.Button('actualizar.png', tooltip='Actualizar Productos')
        hbox.pack_start(button_actualizar)
        button_actualizar.connect('clicked', self.actualizar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(650, 300)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, str, str, str, str, int, str)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('CODIGO', 'NOMBRE', 'VENTA', 'CANT', 'UBICACI\xc3\x93N')
        self.treeview.connect('cursor-changed', self.cursor_changed)
        self.treeview.connect('row-activated', self.row_activated)
        sw.add(self.treeview)
        for i, name in enumerate(columnas):
            cell = gtk.CellRendererText()
            column = gtk.TreeViewColumn(name, cell, text=i)
            self.treeview.append_column(column)

        self.but_ok = Widgets.Button('aceptar.png', '_Ok')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.entry_nombre.set_text(search)
        self.entry_nombre.connect('key-release-event', self.filtrar)
        self.row = False
        if self.http.productos == []:
            self.actualizar()
        self.lista = self.http.productos
        self.filtrar()

    def actualizar(self, *args):
        almacenes = []
        for a in self.http.datos['almacen']:
            almacenes.append(a[1])
        data = self.http.load('almacen', {'ruta': self.ruta,
                                          'lado': self.lado, 'almacen_id': json.dumps(almacenes)})
        self.http.productos = data['productos']
        self.lista = self.http.productos
        self.filtrar()

    def filtrar(self, *args):
        nombre = self.entry_nombre.get()
        if nombre == '':
            lista = self.lista
        else:
            lista = []
            for fila in self.lista:
                for n in nombre.split(' '):
                    if fila[1].upper().find(n.upper()) >= 0 or fila[0].upper().find(n.upper()) >= 0:
                        lista.append(fila)
                        break
        self.model.clear()
        for fila in lista:
            self.model.append(fila)

    def cursor_changed(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            self.row = row
            self.but_ok.set_sensitive(True)
        except:
            self.but_ok.set_sensitive(False)

    def iniciar(self):
        self.show_all()
        self.but_ok.set_sensitive(False)
        self.set_focus(self.entry_nombre)
        if self.run() == gtk.RESPONSE_OK:
            return self.row
        else:
            return False

    def row_activated(self, *args):
        self.but_ok.clicked()

    def cerrar(self, *args):
        self.destroy()


class Trabajos(gtk.Dialog):

    def __init__(self, parent, lista, padron):
        super(Trabajos, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = parent.http
        self.padron = padron
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Trabajos de la Unidad: %s' % padron)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(600, 500)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, str, str, bool, str)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('DIA', 'OBSERVACION', 'MON', 'SALDO', 'FACTURADO')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            if i == 4:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        for l in lista:
            self.model.append(l)

        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.treeview.connect('row-activated', self.detalle)
        self.modificaciones = False
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Anular Orden de Pago')
        item1.connect('activate', self.anular_orden)
        self.menu.append(item1)
        self.treeview.connect('button-release-event', self.on_release_button)

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def anular_orden(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            raise
            return

        facturado = self.model[path][4]
        if facturado:
            return Widgets.Alerta('Error al Anular', 'warning.png', 'No puede anular un pago si ya est\xc3\xa1 facturado')
        dialogo = Widgets.Alerta_SINO('Anular Orden', 'anular.png', '\xc2\xbfEst\xc3\xa1 seguro de anular esta cotizaci\xc3\xb3n?.')
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            datos = {'padron': self.padron,
             'voucher_id': self.model[path][5]}
            respuesta = self.http.load('anular-cotizacion', datos)
            if respuesta:
                treeiter = self.model.get_iter(path)
                self.model.remove(treeiter)

    def detalle(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        datos = {'orden_id': self.model[path][5]}
        respuesta = self.http.load('items-orden', datos)
        if respuesta:
            dialogo = DetalleTrabajo(self, respuesta)

    def iniciar(self):
        self.show_all()
        self.run()
        return self.modificaciones

    def cerrar(self, *args):
        self.destroy()


class DetalleTrabajo(Widgets.Window):

    def __init__(self, padre, lista):
        super(DetalleTrabajo, self).__init__('Detalle de Mantenimiento')
        if os.name == 'nt':
            self.set_size_request(550, 500)
        else:
            self.set_size_request(600, 550)
        self.http = padre.http
        sw = gtk.ScrolledWindow()
        self.vbox.pack_start(sw, True, True, 5)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw.set_size_request(500, 350)
        else:
            sw.set_size_request(450, 350)
        self.model = gtk.ListStore(str, str, str, str, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        columnas = ('CANT', 'DESCRIPCION', 'PRECIO.', 'SUBTOTAL')
        self.columns = []
        self.cells = []
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            cell = gtk.CellRendererText()
            cell.set_property('editable', False)
            self.cells.append(cell)
            column.set_flags(gtk.CAN_FOCUS)
            self.columns.append(column)
            column.pack_start(cell, True)
            column.set_attributes(cell, text=i)
            self.treeview.append_column(column)
            column.encabezado()

        sw.add(self.treeview)
        for l in lista:
            self.model.append(l)

        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 5)
        hbox.pack_start(gtk.Label('TOTAL:'), True, False, 0)
        self.entry_total = gtk.Entry()
        self.entry_total.set_property('editable', False)
        hbox.pack_start(self.entry_total, True, False, 0)
        self.combo_moneda = Widgets.ComboBox()
        self.combo_moneda.set_lista((('Soles', 0), ('D\xc3\xb3lares', 1)))
        hbox.pack_start(self.combo_moneda, True, False, 0)
        self.but_salir = self.crear_boton('cancelar.png', '_Cancelar', self.cerrar)
        self.show_all()
        self.calcular()

    def calcular(self, *args):
        total = 0
        for r in self.model:
            total += Decimal(r[3])

        self.entry_total.set_text(str(total))

    def cerrar(self, *args):
        self.destroy()


class ProgramacionUnidad(gtk.Dialog):

    def __init__(self, parent, lista, padron, dia):
        super(ProgramacionUnidad, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = parent.http
        self.padron = padron
        self.dia = dia
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Programacion de la Unidad: %s' % padron)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(600, 600)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, True, True, 0)
        self.model = gtk.ListStore(int, str, int, int, str, str, str, str, int)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('PADRON', 'PIEZA', 'KM', 'LIMITE', 'INICIO', 'ESTIMADO')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i, background=6)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        for l in lista:
            self.model.append(l)

        if padron:
            hbox = gtk.HBox()
            self.vbox.pack_start(hbox, False, False, 0)
            but_cambiar = Widgets.Button('servicio.png', '_Nuevo Trabajo')
            but_cambiar.connect('clicked', self.nuevo_trabajo)
            self.action_area.pack_start(but_cambiar, False, False, 0)
            self.treeview.connect('row_activated', self.cambiar_pieza)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.iniciar()
        self.cerrar()

    def nuevo_trabajo(self, *args):
        grupos = []
        i = 0
        mttos = self.http.piezas.keys()
        mttos.sort()
        for k in mttos:
            if k != 'null':
                i += 1
                grupos.append((k, i))

        dialogo = Widgets.Alerta_Combo('Registrar Nuevo Trabajo', 'servicio.png', 'Escoja el tipo de pieza que va a agregar.', grupos)
        pieza = dialogo.iniciar()
        mtto = dialogo.combo.get_text()
        dialogo.cerrar()
        print mtto, pieza
        for g in grupos:
            print g
            print self.http.piezas[g[0]]

        limite = int(mtto.split(' ')[-1])
        if pieza:
            piezas = self.http.piezas[mtto]
            print piezas
            lista = []
            if len(lista) != len(piezas):
                for p in piezas:
                    esta = False
                    for l in self.model:
                        print 'buscando', p[1]
                        if p[1] == l[1]:
                            esta = True
                            print 'cambio de pieza', l
                            lista.append(l)
                        else:
                            print ' no es', l[1]

                    if not esta:
                        print 'nueva pieza'
                        lista.append((self.padron,
                         p[1],
                         0,
                         limite,
                         '-',
                         '-',
                         '#F99',
                         0,
                         p[0]))

            dialogo = Trabajo(self, lista)
            data = dialogo.iniciar()
            dialogo.cerrar()
            if data:
                self.model.clear()
                for r in data:
                    print
                    self.model.append(r)

    def cambiar_pieza(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        padron = self.model[path][0]
        for k in self.http.piezas.keys():
            for i, nombre in self.http.piezas[k]:
                if nombre == self.model[path][1]:
                    pieza = i
                    break

        dialogo = Widgets.Alerta_Numero('Registrar Cambio de Pieza', 'servicio.png', 'Escriba el kilometraje para el cambio de pieza.', 6)
        limite = dialogo.iniciar()
        dialogo.cerrar()
        if limite:
            datos = {'pieza_id': pieza,
             'limite': limite,
             'padron': padron}
            respuesta = self.http.load('nueva-pieza', datos)
            if respuesta:
                self.model.clear()
                for r in respuesta:
                    self.model.append(r)

    def iniciar(self):
        self.show_all()
        self.run()

    def cerrar(self, *args):
        self.destroy()


class Trabajo(gtk.Dialog):

    def __init__(self, padre, lista):
        super(Trabajo, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.lista = lista
        self.http = padre.http
        self.dia = padre.dia
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(650, 400)
        self.set_title('Nuevo Trabajo de Mantenimiento')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(800, 400)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(int, str, int, str, str, bool, int, str, str, str, int)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('PAD', 'PIEZA', 'KM', 'INICIO', 'ESTIMADO', 'HECHO', 'LIMITE', 'OBSERVACION')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            if i == 5:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled)
                cell.set_property('activatable', True)
                self.treeview.append_column(tvcolumn)
                tvcolumn.encabezado()
            elif i == 6:
                cell = Widgets.Cell()
                tvcolumn = Widgets.TreeViewColumn(columna)
                cell.connect('editado', self.editado_limite)
                cell.set_property('editable', True)
                tvcolumn.set_flags(gtk.CAN_FOCUS)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, text=i)
                self.column6 = tvcolumn
                self.cell = cell
                self.treeview.append_column(tvcolumn)
                tvcolumn.encabezado()
            elif i == 7:
                cell = Widgets.Cell()
                tvcolumn = Widgets.TreeViewColumn(columna)
                cell.connect('editado', self.editado_observacion)
                cell.set_property('editable', True)
                tvcolumn.set_flags(gtk.CAN_FOCUS)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, text=i)
                self.column7 = tvcolumn
                self.cell = cell
                self.treeview.append_column(tvcolumn)
                tvcolumn.encabezado()
            else:
                cell = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                print columna
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, text=i, background=8)
                self.treeview.append_column(tvcolumn)
                tvcolumn.encabezado()

        for l in lista:
            print (int(l[0]),
             l[1],
             l[2],
             l[4],
             l[5],
             False,
             l[3],
             '',
             l[6],
             l[7],
             l[8])
            self.model.append((int(l[0]),
             l[1],
             l[2],
             l[4],
             l[5],
             False,
             l[3],
             '',
             l[6],
             l[7],
             l[8]))

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        but_guardar = Widgets.Button('servicio.png', '_Guardar')
        but_guardar.connect('clicked', self.guardar)
        self.action_area.pack_start(but_guardar, False, False, 0)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('ok.png', 'OK')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.data = False

    def toggled(self, cell, path):
        self.model[path][5] = not self.model[path][5]

    def editado_limite(self, widget, path, new_text):
        if new_text.isdigit():
            self.model[path][6] = int(new_text)
            self.treeview.set_cursor(path, self.column7, True)

    def editado_observacion(self, widget, path, new_text):
        self.model[path][7] = new_text
        path += 1
        if len(self.model) > path:
            self.treeview.set_cursor(path, self.column6, True)

    def guardar(self, *args):
        lista = []
        for f in self.model:
            padron = int(f[0])
            lista.append((f[10],
             f[6],
             f[7],
             f[5],
             f[9]))

        if lista:
            datos = {'dia': self.dia,
             'padron': padron,
             'json': json.dumps(lista)}
            self.data = self.http.load('guardar-trabajo', datos)
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            return self.data
        else:
            return False

    def cerrar(self, *args):
        self.destroy()



class Servicio(gtk.Dialog):

    def __init__(self, parent, nombre, precio):
        super(Servicio, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Descripci\xc3\xb3n de Servicio')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        frame = Widgets.Frame('Descripci\xc3\xb3n')
        self.vbox.pack_start(frame, False, False, 0)
        self.entry_nombre = gtk.TextView()
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        frame.add(sw)
        sw.add(self.entry_nombre)
        sw.set_size_request(200, 200)
        buff = self.entry_nombre.get_buffer()
        buff.set_text(nombre)
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Precio:'), False, False, 0)
        self.entry_precio = Widgets.Entry()
        self.entry_precio.connect('key-release-event', self.precio_change)
        self.entry_precio.connect('activate', self.precio_activate)
        self.entry_precio.set_text(precio)
        hbox.pack_start(self.entry_precio, False, False, 0)
        self.but_ok = Widgets.Button('aceptar.png', '_Ok')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)

    def precio_change(self, *args):
        text = self.entry_precio.get_text()
        try:
            float(text)
        except:
            self.but_ok.set_sensitive(False)
        else:
            self.but_ok.set_sensitive(True)

    def precio_activate(self, *args):
        if self.but_ok.get_sensitive():
            self.set_focus(self.but_ok)

    def iniciar(self):
        self.show_all()
        self.set_focus(self.entry_precio)
        if self.run() == gtk.RESPONSE_OK:
            buff = self.entry_nombre.get_buffer()
            inicio = buff.get_start_iter()
            fin = buff.get_end_iter()
            nombre = buff.get_text(inicio, fin, 0)
            precio = self.entry_precio.get_text()
            return (nombre, precio)
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Deudas(gtk.Dialog):

    def __init__(self, parent, lista, padron, dia):
        super(Deudas, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.dia = dia
        self.http = parent.http
        self.padron = padron
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Deudas de la Unidad: %s' % padron)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(600, 500)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, str, gobject.TYPE_PYOBJECT)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('DIA', 'DETALLE', 'MONTO')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        for l in lista:
            self.model.append((l['dia'], l['nombre'], l['saldo'], l))

        but_prestamo = Widgets.Button('credito.png', '_Nuevo Pr\xc3\xa9stamo')
        but_prestamo.connect('clicked', self.prestamo)
        # self.action_area.pack_start(but_prestamo, False, False, 0)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.treeview.connect('row-activated', self.pagar)

    def prestamo(self, *args):
        dialogo = FechaConceptoMonto(self)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            datos = {'dia': respuesta[0],
             'concepto': respuesta[1],
             'monto': respuesta[2],
             'padron': self.padron}
            respuesta = self.http.load('nuevo-prestamo-unidad', datos)
            if respuesta:
                self.model.append(respuesta)

    def pagar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return
        dialogo = PagarDeuda(self, self.model[path][3], self.dia)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()

    def iniciar(self):
        self.show_all()
        self.run()
        return

    def cerrar(self, *args):
        self.destroy()


class Facturar(gtk.Dialog):

    def __init__(self, parent, monto):
        super(Facturar, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = parent.http
        self.set_modal(True)
        self.set_transient_for(parent)
        if self.http.seriacion == []:
            datos = {'post': True}
            respuesta = self.http.load('lista-series', datos)
            if respuesta:
                self.http.seriacion = respuesta
        self.set_title('Facturar Compra o Servicio: ' + monto)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        self.fecha = Widgets.Fecha()
        self.vbox.pack_start(self.fecha, False, False, 0)
        self.inafecto_check = gtk.CheckButton('Inafecto al IGV')
        self.vbox.pack_start(self.inafecto_check, False, False, 0)
        self.combo_serie = Widgets.ComboBox()
        self.combo_serie.set_lista(self.http.seriacion['facturas'])
        self.vbox.pack_start(self.combo_serie, False, False, 0)
        self.pagado_check = gtk.CheckButton('Pago al Contado')
        self.vbox.pack_start(self.pagado_check, False, False, 0)
        self.combo_serie_cobro = Widgets.ComboBox()
        self.combo_serie_cobro.set_lista(self.http.seriacion['cobranzas'])
        self.vbox.pack_start(self.combo_serie_cobro, False, False, 0)
        self.but_ok = Widgets.Button('dinero.png', '_Facturar')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.pagado_check.connect('toggled', self.pagado_toggled)

    def pagado_toggled(self, *args):
        if self.pagado_check.get_active():
            self.combo_serie_cobro.show_all()
        else:
            self.combo_serie_cobro.hide_all()

    def iniciar(self):
        self.show_all()
        self.combo_serie_cobro.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            serie = self.combo_serie.get_id()
            pagado = self.pagado_check.get_active()
            inafecto = self.inafecto_check.get_active()
            cobro = self.combo_serie_cobro.get_id()
            dia = self.fecha.get_date()
            return (serie,
             pagado,
             inafecto,
             cobro,
             dia)
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class PagarDeuda(gtk.Dialog):

    def __init__(self, parent, cobranza, dia):
        super(PagarDeuda, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.cobranza = cobranza
        self.dia = dia
        self.http = parent.http
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Pagar Deuda Cr\xc3\xa9dito: %s' % cobranza['nombre'])
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(gtk.Label('Monto Total:'), False, False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        self.entry_total = gtk.Entry()
        self.entry_total.set_sensitive(False)
        self.entry_total.set_text(str(round(cobranza['saldo'], 2)))
        hbox.pack_start(self.entry_total, False, False, 0)
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(gtk.Label('Monto a Pagar:'), False, False, 0)
        self.vbox.pack_start(hbox, False, False, 0)

        self.entry_monto = gtk.Entry()
        hbox.pack_start(self.entry_monto, False, False, 0)
        self.entry_monto.connect('key-release-event', self.calcular)
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(gtk.Label('Saldo Restante:'), False, False, 0)
        self.entry_saldo = gtk.Entry()
        self.entry_saldo.set_sensitive(False)
        hbox.pack_start(self.entry_saldo, False, False, 0)

        self.vbox.pack_start(hbox, False, False, 0)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.but_ok = Widgets.Button('dinero.png', '_Pagar')
        self.but_pagar = Widgets.Button('dinero.png', '_Pagar')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.action_area.pack_start(self.but_pagar, False, False, 0)
        self.entry_monto.connect('activate', self.entry_activate)
        self.but_pagar.connect('activate', self.pagar)
        self.set_focus(self.entry_monto)

    def calcular(self, *args):
        try:
            total = Decimal(self.entry_total.get_text())
            pagar = Decimal(self.entry_monto.get_text())
        except:
            self.entry_saldo.set_text('ERROR')
            self.but_pagar.set_sensitive(False)
        else:
            saldo = total - pagar
            self.entry_saldo.set_text(str(saldo))
            self.but_pagar.set_sensitive(True)

    def entry_activate(self, *args):
        self.set_focus(self.but_pagar)

    def pagar(self, *args):
        pagar = Decimal(self.entry_monto.get_text())
        saldo = Decimal(self.entry_saldo.get_text())
        datos = {
            'dia': self.dia,
            'padron': self.cobranza['padron'],
            'pagar': str(pagar),
            'saldo': str(saldo),
            'cobranza': self.cobranza['id']
        }
        self.data = self.http.load('pagar-deuda', datos)
        if self.data:
            self.but_ok.clicked()


    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            return self.data
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Stock(gtk.Dialog):

    def __init__(self, padron, selector, http, boletos):
        super(Stock, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.set_modal(True)
        self.set_transient_for(parent)
        self.padron = padron
        self.http = http
        self.dia, self.ruta, self.lado = selector.get_datos()
        self.set_default_size(200, 200)
        self.set_border_width(10)
        self.set_title('Asignar Stock: PADRON %d' % self.padron)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        n = len(boletos)
        self.series = [None] * n
        self.inicios = [None] * n
        self.finales = [None] * n
        self.ids = [None] * n
        self.checks = [None] * n
        tabla = gtk.Table()
        self.vbox.pack_start(tabla, False, False, 0)
        label = gtk.Label()
        label.set_markup('<b>BOLETO</b>')
        tabla.attach(label, 0, 1, 0, 1)
        label = gtk.Label()
        label.set_markup('<b>TARIFA</b>')
        tabla.attach(label, 1, 2, 0, 1)
        label = gtk.Label()
        label.set_markup('<b>SERIE</b>')
        tabla.attach(label, 2, 3, 0, 1)
        label = gtk.Label()
        label.set_markup('<b>INICIO</b>')
        tabla.attach(label, 3, 4, 0, 1)
        label = gtk.Label()
        label.set_markup('<b>TACOS</b>')
        tabla.attach(label, 4, 5, 0, 1)
        label = gtk.Label()
        label.set_markup('<b>ENTREGAR</b>')
        tabla.attach(label, 5, 6, 0, 1)
        for i, boleto in enumerate(boletos):
            self.ids[i] = boleto[0]
            if boleto[3]:
                color = '#FFCCCC'
            else:
                color = '#CCFFCC'
            hbox = gtk.HBox()
            label = gtk.Label()
            label.set_markup('<b>%s</b>' % boleto[1][:7])
            tabla.attach(label, 0, 1, i + 1, i + 2)
            tabla.attach(gtk.Label(boleto[2]), 1, 2, i + 1, i + 2)
            self.vbox.pack_start(hbox, True, True, 0)
            entry = Widgets.Texto(3)
            entry.set_text(boleto[4])
            entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))
            tabla.attach(entry, 2, 3, i + 1, i + 2)
            self.series[i] = entry
            entry = Widgets.Numero(6)
            entry.set_text(str(boleto[5]))
            entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))
            tabla.attach(entry, 3, 4, i + 1, i + 2)
            self.inicios[i] = entry
            entry = Widgets.Numero(6)
            entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))
            tabla.attach(entry, 4, 5, i + 1, i + 2)
            self.finales[i] = entry
            entry.set_text(str(boleto[6]))
            check = gtk.CheckButton()
            tabla.attach(check, 5, 6, i + 1, i + 2)
            self.checks[i] = check
            check.set_active(False)

        self.but_guardar = Widgets.Button('aceptar.png', '_Aceptar')
        self.action_area.pack_start(self.but_guardar, False, False, 0)
        self.but_guardar.connect('clicked', self.comprobar)
        self.but_ok = Widgets.Button('aceptar.png', '_Aceptar')
        but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        try:
            self.series[0].grab_focus()
        except:
            pass

    def comprobar(self, widget):
        serie = []
        inicio = []
        fin = []
        ids = []
        for i, d in enumerate(self.ids):
            if self.checks[i].get_active():
                serie.append(self.series[i].get_text())
                inicio.append(self.inicios[i].get_text())
                fin.append(self.finales[i].get_text())
                ids.append(self.ids[i])
        bg = self.http.datos['boleto_gasto']
        print 'BOLETO GASTO', bg, str(self.ruta), type(bg)
        if str(self.ruta) in bg:
            gasto = bg[str(self.ruta)]
        else:
            gasto = None
        datos = {'id': json.dumps(ids),
         'serie': json.dumps(serie),
         'inicio': json.dumps(inicio),
         'taco': json.dumps(fin),
         'padron': self.padron,
         'ruta_id': self.ruta,
         'dia': self.dia,
         'lado': self.lado,
         'boleto_gasto': gasto}
        self.respuesta = self.http.load('asignar-stock', datos)
        if self.respuesta:
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Pagar(gtk.Dialog):

    def __init__(self, padre, padron):
        super(Pagar, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.cambiado = False
        self.http = padre.http
        self.padron = padron
        self.ruta = padre.ruta
        self.lado = padre.lado
        self.dia = padre.dia
        self.pagos = self.http.get_pagos(self.ruta)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Pagos de la Unidad: %s del d\xc3\xada %s' % (padron, self.dia))
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        self.datos = {'padron': padron,
         'ruta_id': self.ruta,
         'lado': self.lado,
         'dia': self.dia}
        sw = gtk.ScrolledWindow()
        sw.set_size_request(400, 300)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, str, str)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('CONCEPTO', 'MONTO', 'HORA')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        lista = self.http.load('pagos-unidad', self.datos)
        if lista:
            for l in lista:
                self.model.append(l)

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        but_pagar = Widgets.Button('caja.png', '_Cobrar')
        but_pagar.connect('clicked', self.cobrar, True)
        hbox.pack_start(but_pagar, False, False, 0)
        but_pagar = Widgets.Button('caja.png', '_Gastar')
        but_pagar.connect('clicked', self.cobrar, False)
        hbox.pack_start(but_pagar, False, False, 0)
        but_pagar = Widgets.Button('caja.png', '_Declarar')
        but_pagar.connect('clicked', self.cobrar, None)
        hbox.pack_start(but_pagar, False, False, 0)
        but_anular = Widgets.Button('anular.png', '_Anular Pago')
        but_anular.connect('clicked', self.anular)
        hbox.pack_start(but_anular, False, False, 0)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)

    def cobrar(self, widget, tipo):
        dialogo = Factura(self, tipo)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            for r in respuesta:
                self.model.append(respuesta)
                self.cambiado = True

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        dialogo = Widgets.Alerta_SINO_Clave('Anular Pago', 'anular.png', '\xc2\xbfEst\xc3\xa1 seguro de anular este pago?.')
        respuesta = dialogo.iniciar()
        clave = dialogo.clave
        dialogo.cerrar()
        if respuesta:
            datos = {'padron': self.padron,
             'voucher_id': self.model[path][3],
             'padron': self.model[path][1],
             'ruta_id': self.ruta,
             'lado': self.lado,
             'dia': self.dia,
             'monto': self.model[path][2],
             'usuario': self.http.datos['despachador'],
             'detalle': self.model[path][0],
             'hora': '',
             'clave': clave}
            respuesta = self.http.load('anular-pago', datos)
            if respuesta:
                treeiter = self.model.get_iter(path)
                self.model.remove(treeiter)
            else:
                self.model.clear()
                lista = self.http.load('pagos-unidad', self.datos)
                if lista:
                    for l in lista:
                        self.model.append(l)

    def iniciar(self):
        self.show_all()
        self.run()
        return self.cambiado

    def cerrar(self, *args):
        self.destroy()


class Fondo(gtk.Dialog):

    def __init__(self, padre, cond, cobr, padron):
        super(Fondo, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = padre.http
        self.ruta = padre.ruta
        self.lado = padre.lado
        self.dia = padre.dia
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Cobro de Fondos y Multas:')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        frame = Widgets.Frame('Aportante')
        self.vbox.pack_start(frame, False, False, 0)
        hb = gtk.HBox(False, 5)
        frame.add(hb)
        self.entry_codigo = Widgets.Numero(8)
        hb.pack_start(self.entry_codigo, False, False, 0)
        self.entry_codigo.connect('activate', self.buscar_aportante)
        but_buscar = Widgets.Button('buscar.png', '', 16, tooltip='Buscar Cliente')
        hb.pack_start(but_buscar, False, False, 0)
        but_buscar.connect('clicked', self.buscar_aportante)
        self.entry_nombre = Widgets.Texto(64)
        hb.pack_start(self.entry_nombre, False, False, 0)
        self.entry_nombre.set_sensitive(False)
        try:
            self.fondos = self.http.fondos
            self.multas = self.http.multas
        except:
            fondos = self.http.load('lista-fondos', {'vacio': None})
            self.fondos = []
            self.multas = []
            for f in fondos:
                if f[4] is None:
                    self.multas.append(f)
                else:
                    self.fondos.append(f)
            self.http.fondos = self.fondos
            self.http.multas = self.multas


        frame = Widgets.Frame('Tipo de Cuenta')
        if len(self.http.multas):  # solo STA CRUZ, por compatibilidad
            self.vbox.pack_start(frame, False, False, 0)
        hb = gtk.HBox(False, 5)
        frame.add(hb)
        self.radio_fondos = gtk.RadioButton(None, 'Fondos y Deudas', False)
        hb.pack_start(self.radio_fondos, False, False, 0)
        self.radio_multas = gtk.RadioButton(self.radio_fondos, 'Multas y otros', False)
        hb.pack_start(self.radio_multas, False, False, 0)
        self.radio_fondos.connect('toggled', self.radio_toggled)

        frame = Widgets.Frame('Detalle del Pago')
        self.vbox.pack_start(frame, False, False, 0)
        vbox = gtk.VBox(False, 5)
        frame.add(vbox)

        self.hbox_fondos = gtk.HBox(False, 5)
        vbox.pack_start(self.hbox_fondos)
        self.hbox_fondos.pack_start(gtk.Label('Cuenta:'), False, False, 0)
        self.combo_fondos = Widgets.ComboBox()
        fondos = []
        for f in self.http.datos['seriacion']['fondo']:
            fondos.append((f[0], f[2]))
        self.combo_fondos.set_lista(fondos)
        self.hbox_fondos.pack_start(self.combo_fondos)

        # self.series = []
        # grupo = None
        # for f in self.http.datos['seriacion']['fondo']:
        #     if self.ruta == f[1]:
        #         radiobutton = gtk.RadioButton(grupo, f[0], False)
        #         vbox.pack_start(radiobutton, False, False, 0)
        #         self.series.append((radiobutton, f[2]))
        #         radiobutton.set_active(False)
        #         if grupo is None:
        #             grupo = radiobutton
        self.hbox_multas = gtk.HBox(False, 5)
        vbox.pack_start(self.hbox_multas, False, False, 0)
        # radiobutton = gtk.RadioButton(grupo, 'Multas', False)
        # if len(self.http.multas):
        #     self.hbox_multas.pack_start(radiobutton, False, False, 0)
        # self.series.append([radiobutton, None])
        # radiobutton.set_active(True)

        self.hbox_multas.pack_start(gtk.Label('Multa:'), False, False, 5)
        self.combo_multa = Widgets.ComboBox()
        self.combo_multa.set_lista(self.http.multas)
        self.hbox_multas.pack_start(self.combo_multa)

        self.entry_monto = Widgets.Texto(7)
        hb = gtk.HBox(False, 5)
        vbox.pack_start(hb, False, False, 0)
        self.entry_almacen = Widgets.Texto(16)
        hb.pack_start(gtk.Label('Ref. Almacén:'), False, False, 0)
        hb.pack_start(self.entry_almacen, False, False, 0)
        self.entry_almacen.connect('activate', self.buscar_producto)
        hb.pack_start(gtk.Label('Padrón Referencia:'), False, False, 0)
        self.entry_padron = Widgets.Texto(4)
        hb.pack_start(self.entry_padron, False, False, 0)
        hb = gtk.HBox(False, 5)
        hb.pack_start(gtk.Label('Monto:'), False, False, 0)
        hb.pack_start(self.entry_monto, False, False, 0)
        vbox.pack_start(hb, False, False, 0)
        self.entry_concepto = Widgets.Texto(32)
        hb.pack_start(gtk.Label('Detalle:'), False, False, 0)
        hb.pack_start(self.entry_concepto, False, False, 0)
        but_pagar = Widgets.Button('caja.png', '_Cobrar')
        but_pagar.connect('clicked', self.cobrar, True)
        self.action_area.pack_start(but_pagar, False, False)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.codigo_back = None
        self.cuenta_back = None

    def radio_toggled(self, *args):
        if self.radio_multas.get_active():
            self.hbox_multas.show_all()
            self.hbox_fondos.hide_all()
        else:
            self.hbox_multas.hide_all()
            self.hbox_fondos.show_all()



    def buscar_dni(self, dni):
        for l in self.lista:
            if l[1] == dni:
                self.referencia = l[0]
                self.tipo = 'Personal'
                return l[2]
        self.referencia = ''
        1/0

    def buscar_padron(self, padron):
        if self.http.unidades == []:
            datos = {'tipo': 'Unidad'}
            lista = self.http.load('unidades', datos)
            if lista:
                self.http.unidades = lista
        for f in self.http.unidades:
            if f[0] == padron:
                self.referencia = '%s %s' % (f[1], f[3])
                self.tipo = 'Unidad'
                return f[2]
        self.referencia = ''
        1/0

    def buscar_placa(self, placa):
        if self.http.unidades == []:
            datos = {'tipo': 'Unidad'}
            lista = self.http.load('unidades', datos)
            if lista:
                self.http.unidades = lista
        for f in self.http.unidades:
            if f[1].replace('-', '') == placa.upper().replace('-', ''):
                self.referencia = '%s %s' % (f[1], f[2])
                self.tipo = 'Unidad'
                return f[2]
        self.referencia = ''
        1/0

    def buscar_aportante(self, *args):
        codigo = self.entry_codigo.get_text()
        self.entry_nombre.set_text('')
        llave = None
        if self.http.conductores == []:
            datos = {'tipo': 'Conductor',
             'empresa_id': self.http.empresa}
            lista = self.http.load('personal', datos)
            if lista:
                self.http.conductores = lista
        if self.http.cobradores == []:
            datos = {'tipo': 'Cobrador',
             'empresa_id': self.http.empresa}
            lista = self.http.load('personal', datos)
            if lista:
                self.http.cobradores = lista
        self.lista = self.http.cobradores + self.http.conductores
        if codigo == '':
            dialogo = Personal(None, self.lista, self.http)
            js = dialogo.iniciar()
            dialogo.cerrar()
            if js:
                codigo = js[1]
                self.entry_codigo.set_text(str(codigo))
                cod = int(codigo)
                llave = js[2]
                self.referencia = js[0]
                self.tipo = 'Personal'
        elif codigo.isdigit():
            try:
                llave = self.buscar_padron(int(codigo))
            except:
                try:
                    llave = self.buscar_placa(codigo)
                except:
                    try:
                        llave = self.buscar_dni(int(codigo))
                    except:
                        try:
                            self.dnis = self.http.dnis
                        except:
                            respuesta = self.http.load('todos-dnis', {'algo': True})
                            if respuesta:
                                self.http.dnis = respuesta
                                self.dnis = respuesta
                        dialogo = Personal(None, self.dnis, self.http)
                        js = dialogo.iniciar()
                        dialogo.cerrar()
                        if js:
                            codigo = js[1]
                            self.entry_codigo.set_text(str(codigo))
                            llave = js[2]
                            self.referencia = js[0]
                            self.tipo = 'Personal'
        if llave:
            self.entry_nombre.set_text(self.referencia)
            self.llave = llave
            self.codigo = codigo

    def buscar_producto(self, *args):
        codigo = self.entry_almacen.get_text()
        self.entry_monto.set_text('')
        self.entry_concepto.set_text('')
        if self.http.productos == []:
            almacenes = []
            for a in self.http.datos['almacen']:
                almacenes.append(a[1])
            datos = {'ruta': self.ruta, 'lado': self.lado, 'almacen_id': json.dumps(almacenes)}
            data = self.http.load('almacen', datos)
            if data:
                self.http.productos = data['productos']

        for p in self.http.productos:
            if p[0] == codigo:
                self.entry_concepto.set_text(p[1])
                self.entry_monto.set_text(p[2])

    def cobrar(self, *args):
        monto = self.entry_monto.get_text()
        try:
            monto = Decimal(monto)
        except:
            return Widgets.Alerta('Error en el monto', 'warning.png', 'El monto est\xc3\xa1 mal escrito')

        dialogo = Widgets.Alerta_SINO('Confirme la acci\xc3\xb3n', 'caja.png', 'Confirme que desea registrar el abono.')
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            if self.radio_multas.get_active():
                multa = self.combo_multa.get_id()
            else:
                multa = None
                self.hbox_fondos.show_all()
            seriacion = self.combo_fondos.get_id()
            concepto = self.entry_concepto.get_text()
            datos = {
                'llave': self.llave,
                'seriacion': seriacion,
                'multa': multa,
                'tipo': self.tipo,
                'monto': monto,
                'codigo': self.codigo,
                'liquidacion': 0,
                'ruta_id': self.ruta,
                'padron': self.entry_padron.get_text(),
                'concepto': concepto,
                'dia': self.dia}
            if float(monto) < 0:
                if len(concepto) < 5:
                    return Widgets.Alerta('Error', 'error.png', 'El concepto debe tener al menos 5 caracteres')
            respuesta = self.http.load('pagar-abono-seriacion', datos)
            if respuesta:
                Widgets.Alerta('Pago de Fondo / Multa Realizado', 'caja.png', 'Se ha hecho un abono por S/. %s a %s' % (monto, self.entry_nombre.get_text()))
                self.cerrar()

    def iniciar(self):
        self.show_all()
        self.hbox_multas.hide_all()
        self.run()

    def cerrar(self, *args):
        self.destroy()


class Recaudo(gtk.Dialog):

    def __init__(self, parent, padron):
        super(Recaudo, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.cambiado = False
        self.http = parent.http
        self.ruta = parent.ruta
        self.lado = parent.lado
        self.padron = padron
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Recaudo de la Unidad: %d' % padron)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(250, 300)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(bool, str, str, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        sw.add(self.treeview)
        columnas = ('USAR', 'SALIDA', 'RUTA')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled)
                cell.set_property('activatable', True)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        datos = {'padron': padron}
        lista = self.http.load('salidas-recaudar', datos)
        if lista:
            pass
        else:
            self.cerrar()
            return
        for f in lista:
            self.model.append(f)

        tabla = gtk.Table()
        self.vbox.pack_start(tabla, False, False, 0)
        tabla.attach(gtk.Label('Monto:'), 0, 1, 1, 2)
        self.entry_monto = Widgets.Texto(10)
        tabla.attach(self.entry_monto, 1, 2, 1, 2)
        but_pagar = Widgets.Button('dinero.png', '_Recaudar')
        but_pagar.connect('clicked', self.recaudar)
        self.action_area.pack_start(but_pagar, False, False, 0)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('aceptar.png', '_OK')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.respuesta = False
        self.iniciar()

    def toggled(self, cell, path):
        self.model[path][0] = not self.model[path][0]
        i = 0
        check = True
        for f in self.model:
            if not f[0]:
                check = False
            f[0] = check
            i += 1

    def recaudar(self, *args):
        monto = self.entry_monto.get_text()
        try:
            float(monto)
        except:
            Widgets.Alerta('Error N\xc3\xbamero', 'error.png', 'El monto es inv\xc3\xa1lido')
            return

        ids = []
        for f in self.model:
            if f[0]:
                ids.append(f[3])

        datos = {'padron': self.padron,
         'monto': monto,
         'ids': json.dumps(ids),
         'ruta_id': self.ruta,
         'lado': self.lado}
        respuesta = self.http.load('recaudar', datos)
        if respuesta:
            self.respuesta = respuesta
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        self.run()

    def cerrar(self, *args):
        self.destroy()


class Programacion(gtk.Dialog):

    def __init__(self, parent, ruta):
        super(Recaudo, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.cambiado = False
        self.http = parent.http
        self.ruta = parent.ruta
        self.lado = parent.lado
        datos = {'ruta': self.ruta}
        unidades = self.http.load('unidades', datos)
        self.padron = padron
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Programaci\xc3\xb3n de Flota: %s' % ruta)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(250, 300)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(bool, str, str, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        sw.add(self.treeview)
        columnas = ('USAR', 'SALIDA', 'RUTA')
        for i, columna in enumerate(columnas):
            if i == 0:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
                cell.connect('toggled', self.toggled)
                cell.set_property('activatable', True)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        datos = {'padron': padron}
        lista = self.http.load('salidas-recaudar', datos)
        if lista:
            pass
        else:
            self.cerrar()
            return
        for f in lista:
            self.model.append(f)

        tabla = gtk.Table()
        self.vbox.pack_start(tabla, False, False, 0)
        tabla.attach(gtk.Label('Monto:'), 0, 1, 1, 2)
        self.entry_monto = Widgets.Texto(10)
        tabla.attach(self.entry_monto, 1, 2, 1, 2)
        but_pagar = Widgets.Button('dinero.png', '_Recaudar')
        but_pagar.connect('clicked', self.recaudar)
        self.action_area.pack_start(but_pagar, False, False, 0)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('aceptar.png', '_OK')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.iniciar()

    def toggled(self, cell, path):
        self.model[path][0] = not self.model[path][0]
        i = 0
        check = True
        for f in self.model:
            if not f[0]:
                check = False
            f[0] = check
            i += 1

    def recaudar(self, *args):
        monto = self.entry_monto.get_text()
        try:
            float(monto)
        except:
            Widgets.Alerta('Error N\xc3\xbamero', 'error.png', 'El monto es inv\xc3\xa1lido')
            return

        ids = []
        for f in self.model:
            if f[0]:
                ids.append(f[3])

        datos = {'padron': self.padron,
         'monto': monto,
         'ids': json.dumps(ids),
         'ruta_id': self.ruta,
         'lado': self.lado}
        respuesta = self.http.load('recaudar', datos)
        if respuesta:
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class ProgramacionFlota(gtk.Dialog):

    def __init__(self, padre):
        super(ProgramacionFlota, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = padre.http
        ruta = padre.selector.ruta.get_text()
        self.dia = padre.dia
        self.ruta = padre.ruta
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Programaci\xc3\xb3n de Flota: %s' % ruta)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Mes: '), False, False, 0)
        self.combo_mes = Widgets.ComboBox()
        self.combo_mes.set_lista((('Enero', 1),
         ('Febrero', 2),
         ('Marzo', 3),
         ('Abril', 4),
         ('Mayo', 5),
         ('Junio', 6),
         ('Julio', 7),
         ('Agosto', 8),
         ('Setiembre', 9),
         ('Octubre', 10),
         ('Noviembre', 11),
         ('Diciembre', 12)))
        hbox.pack_start(self.combo_mes, False, False, 0)
        hbox.pack_start(gtk.Label('A\xc3\xb1o: '), False, False, 0)
        self.combo_year = Widgets.ComboBox()
        self.combo_year.set_lista((('2014', 2014),
         ('2015', 2015),
         ('2016', 2016),
         ('2017', 2017),
         ('2018', 2018)))
        hbox.pack_start(self.combo_year, False, False, 0)
        self.combo_mes.set_id(self.dia.month)
        self.combo_year.set_id(self.dia.year)
        hbox.pack_start(gtk.Label('Lado: '), False, False, 0)
        self.combo_lado = Widgets.ComboBox()
        self.combo_lado.set_lista((('A', 0), ('B', 1)))
        hbox.pack_start(self.combo_lado, False, False, 0)
        self.but_actualizar = Widgets.Button('actualizar.png', '_Actualizar')
        self.but_actualizar.connect('clicked', self.actualizar)
        hbox.pack_start(self.but_actualizar, False, False, 0)
        self.but_editar = Widgets.Button('editar.png', '_Editar')
        self.but_editar.connect('clicked', self.editar)
        hbox.pack_start(self.but_editar, False, False, 0)
        self.model = gtk.ListStore(int, str, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(920, 600)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        sw.add(self.treeview)
        columnas = ('N', 'HORA', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31')
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i, background=33)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.programaciones = None
        datos = {'ruta_id': self.ruta}
        self.unidades = self.http.load('unidades', datos)
        self.colores = ['#FF8', '#8F8', '#88F'] * 10
        self.iniciar()

    def actualizar(self, *args):
        datos = {'mes': self.combo_mes.get_id(),
         'year': self.combo_year.get_id(),
         'lado': self.combo_lado.get_id(),
         'ruta_id': self.ruta}
        programas = self.http.load('programacion-mes', datos)
        self.model.clear()
        if programas:
            filas = 0
            colores = []
            for programa in programas:
                filas = max(filas, len(programa['tabla'][0]) + programa['orden'])
                colores.append(programa['orden'])

            i = 1
            while i < filas:
                j = 0
                for e, c in enumerate(colores):
                    if i >= c:
                        j = e
                    else:
                        break

                color = self.colores[j]
                self.model.append((i,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 color))
                i += 1

            dias = {}
            for programa in programas:
                orden = programa['orden']
                desde = programa['desde']
                hasta = programa['hasta']
                offset = 0
                for columna in programa['tabla']:
                    o = orden - 1
                    for cell in columna:
                        self.model[o][desde + offset + 1] = cell
                        o += 1

                    offset += 1

    def editar(self, *args):
        datos = {'mes': self.combo_mes.get_id(),
         'year': self.combo_year.get_id(),
         'ruta_id': self.ruta}
        programas = self.http.load('programaciones', datos)
        self.programaciones = programas
        NuevaProgramacion(self)

    def iniciar(self):
        self.show_all()
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class NuevaProgramacion(gtk.Dialog):

    def __init__(self, padre):
        super(NuevaProgramacion, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = padre.http
        self.ruta = padre.ruta
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Editar Programaci\xc3\xb3n: %s-%s' % (padre.combo_mes.get_text(), padre.combo_year.get_text()))
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        hbox = gtk.HBox()
        self.programaciones = {}
        self.unidades = padre.unidades
        self.unidades.append([0, 0])
        lista = []
        self.fecha = Widgets.Fecha()
        hbox.pack_end(self.fecha, False, False, 0)
        if padre.programaciones:
            for p in padre.programaciones:
                lista.append((p['nombre'], p['id']))
                self.programaciones[p['id']] = p

        else:
            dia = datetime.date(padre.combo_year.get_id(), padre.combo_mes.get_id(), 1)
            self.fecha.set_date(dia)
            self.fecha.hide_all()
        self.vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Programacion:'), False, False, 0)
        self.combo_prog = Widgets.ComboBox()
        self.combo_prog.set_lista(lista)
        hbox.pack_start(self.combo_prog, False, False, 0)
        self.combo_prog.connect('changed', self.leer)
        self.but_borrar = Widgets.Button('anular.png', '_Borrar Programaci\xc3\xb3n')
        self.but_borrar.connect('clicked', self.borrar)
        hbox.pack_start(self.but_borrar, False, False, 0)
        self.but_nueva = Widgets.Button('nuevo.png', '_Nueva Programaci\xc3\xb3n')
        self.but_nueva.connect('clicked', self.nueva)
        hbox.pack_start(self.but_nueva, False, False, 0)
        self.but_guardar = Widgets.Button('guardar.png', '_Guardar Programaci\xc3\xb3n')
        self.but_guardar.connect('clicked', self.guardar)
        hbox.pack_start(self.but_guardar, False, False, 0)
        hbox_main = gtk.HBox(True, 10)
        self.vbox.pack_start(hbox_main, True, True, 0)
        vbox = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox, True, True, 0)
        vbox.pack_start(gtk.Label('LADO A'), False, False, 0)
        hbox_in = gtk.HBox(True, 0)
        vbox.pack_start(hbox_in, False, False, 0)
        self.but_a_up = Widgets.Button('arriba.png', None, tooltip='Subir')
        self.but_a_down = Widgets.Button('abajo.png', None, tooltip='Bajar')
        self.but_a_remove = Widgets.Button('derecha.png', None, tooltip='Quitar de la lista')
        hbox_in.pack_start(self.but_a_up, True, True, 0)
        hbox_in.pack_start(self.but_a_down, True, True, 0)
        hbox_in.pack_start(self.but_a_remove, True, True, 0)
        sw_a = gtk.ScrolledWindow()
        sw_a.set_size_request(250, 600)
        sw_a.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw_a, True, True, 0)
        vbox = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox, True, True, 0)
        hbox_in = gtk.HBox(True, 0)
        vbox.pack_start(gtk.Label('UNIDADES RESTANTES'), False, False, 0)
        vbox.pack_start(hbox_in, False, False, 0)
        self.but_a = Widgets.Button('izquierda.png', None, tooltip='Mover al Lado A')
        self.but_a.connect('clicked', self.lado_a)
        self.but_b = Widgets.Button('derecha.png', None, tooltip='Mover al Lado B')
        self.but_b.connect('clicked', self.lado_b)
        hbox_in.pack_start(self.but_a, True, True, 0)
        hbox_in.pack_start(self.but_b, True, True, 0)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(60, 600)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw, True, True, 0)
        vbox = gtk.VBox(False, 0)
        hbox_main.pack_start(vbox, True, True, 0)
        vbox.pack_start(gtk.Label('LADO B'), False, False, 0)
        hbox_in = gtk.HBox(True, 0)
        vbox.pack_start(hbox_in, False, False, 0)
        self.but_b_remove = Widgets.Button('izquierda.png', None, tooltip='No usar')
        self.but_b_up = Widgets.Button('arriba.png', None, tooltip='Subir')
        self.but_b_down = Widgets.Button('abajo.png', None, tooltip='Bajar')
        hbox_in.pack_start(self.but_b_remove, True, True, 0)
        hbox_in.pack_start(self.but_b_up, True, True, 0)
        hbox_in.pack_start(self.but_b_down, True, True, 0)
        sw_b = gtk.ScrolledWindow()
        sw_b.set_size_request(250, 600)
        sw_b.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw_b, True, True, 0)
        self.model_a = gtk.ListStore(int, int, str, str)
        self.treeview_a = Widgets.TreeView(self.model_a)
        self.treeview_a.set_rubber_banding(True)
        self.treeview_a.set_enable_search(False)
        self.treeview_a.set_reorderable(False)
        sw_a.add(self.treeview_a)
        columnas = ('N', 'PADRON')
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i, background=3)
            self.treeview_a.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.model_b = gtk.ListStore(int, int, str, str)
        self.treeview_b = Widgets.TreeView(self.model_b)
        self.treeview_b.set_rubber_banding(True)
        self.treeview_b.set_enable_search(False)
        self.treeview_b.set_reorderable(False)
        sw_b.add(self.treeview_b)
        columnas = ('N', 'PADRON')
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i, background=3)
            self.treeview_b.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.model = gtk.ListStore(int, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        sw.add(self.treeview)
        columnas = ('PADRON',)
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.but_a_up.connect('clicked', self.up, self.treeview_a)
        self.but_a_down.connect('clicked', self.down, self.treeview_a)
        self.but_a_remove.connect('clicked', self.remove, self.treeview_a)
        self.but_b_remove.connect('clicked', self.remove, self.treeview_b)
        self.but_b_up.connect('clicked', self.up, self.treeview_b)
        self.but_b_down.connect('clicked', self.down, self.treeview_b)
        hbox = gtk.HBox(True, 10)
        self.vbox.pack_start(hbox, False, False, 0)
        vbox = gtk.VBox(False, 0)
        hbox.pack_start(vbox, True, True, 0)
        vbox.pack_start(gtk.Label('GRUPOS LADO A'), False, False, 0)
        sw_a = gtk.ScrolledWindow()
        sw_a.set_size_request(290, 100)
        sw_a.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw_a, True, True, 0)
        vbox = gtk.VBox(False, 0)
        hbox.pack_start(vbox, True, True, 0)
        vbox.pack_start(gtk.Label('GRUPOS LADO B'), False, False, 0)
        sw_b = gtk.ScrolledWindow()
        sw_b.set_size_request(290, 100)
        sw_b.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw_b, True, True, 0)
        self.model_grupo_a = gtk.ListStore(int, gobject.TYPE_OBJECT, str, int)
        self.treeview_grupo_a = Widgets.TreeView(self.model_grupo_a)
        self.treeview_grupo_a.set_rubber_banding(True)
        self.treeview_grupo_a.set_enable_search(False)
        self.treeview_grupo_a.set_reorderable(False)
        sw_a.add(self.treeview_grupo_a)
        columnas = ('CANTIDAD', 'PATRON')
        model = gtk.ListStore(str, int)
        model.append(('ROMBO ASC', 1))
        model.append(('ROMBO DESC', 2))
        model.append(('ASCENDENTE', 3))
        model.append(('DESCENDENTE', 4))
        for i, columna in enumerate(columnas):
            if i == 1:
                cell_text = gtk.CellRendererCombo()
                cell_text.set_property('model', model)
                cell_text.set_property('text-column', 0)
                cell_text.set_property('editable', True)
                cell_text.connect('changed', self.cambiar_patron, self.treeview_grupo_a)
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, text=2)
                self.treeview_grupo_a.append_column(tvcolumn)
                tvcolumn.encabezado()
            else:
                cell_text = Widgets.Cell()
                cell_text.connect('editado', self.editado, self.treeview_grupo_a)
                cell_text.set_property('editable', True)
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.set_flags(gtk.CAN_FOCUS)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
                self.treeview_grupo_a.append_column(tvcolumn)
                tvcolumn.encabezado()

        self.model_grupo_b = gtk.ListStore(int, gobject.TYPE_OBJECT, str, int)
        self.treeview_grupo_b = Widgets.TreeView(self.model_grupo_b)
        self.treeview_grupo_b.set_rubber_banding(True)
        self.treeview_grupo_b.set_enable_search(False)
        self.treeview_grupo_b.set_reorderable(False)
        sw_b.add(self.treeview_grupo_b)
        columnas = ('CANTIDAD', 'PATRON')
        for i, columna in enumerate(columnas):
            if i == 1:
                cell_text = gtk.CellRendererCombo()
                cell_text.set_property('model', model)
                cell_text.set_property('text-column', 0)
                cell_text.set_property('editable', True)
                cell_text.connect('changed', self.cambiar_patron, self.treeview_grupo_b)
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, text=2)
                self.treeview_grupo_b.append_column(tvcolumn)
                tvcolumn.encabezado()
            else:
                cell_text = Widgets.Cell()
                cell_text.connect('editado', self.editado, self.treeview_grupo_b)
                cell_text.set_property('editable', True)
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.set_flags(gtk.CAN_FOCUS)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
                self.treeview_grupo_b.append_column(tvcolumn)
                tvcolumn.encabezado()

        self.colores = ['#FF8', '#8F8', '#88F'] * 10
        self.liststore = model
        self.iniciar()

    def cambiar_patron(self, combo, path, iter, treeview):
        model = treeview.get_model()
        select = self.liststore.get_value(iter, 0)
        model[path][2] = select
        select = self.liststore.get_value(iter, 1)
        model[path][3] = select

    def editado(self, widget, path, new_text, treeview):
        if new_text == '':
            new_text = '0'
        model = treeview.get_model()
        try:
            try:
                int(new_text)
            except:
                return

            model[path][0] = int(new_text)
        finally:
            for f in model:
                if f[0] == 0:
                    it = model.get_iter(path)
                    model.remove(it)

            model.append((0,
             self.liststore,
             '',
             0))

        self.colorear()

    def colorear(self):
        i = 0
        j = 0
        for f in self.model_grupo_a:
            color = self.colores[i]
            n = f[0]
            if n == 0:
                n = len(self.model_a) - j
            while n > 0:
                n -= 1
                if j >= len(self.model_a):
                    break
                self.model_a[j][3] = color
                j += 1

            i += 1

        i = 0
        j = 0
        for f in self.model_grupo_b:
            color = self.colores[i]
            n = f[0]
            if n == 0:
                n = len(self.model_b) - j
            while n > 0:
                n -= 1
                if j >= len(self.model_b):
                    break
                self.model_b[j][3] = color
                j += 1

            i += 1

    def up(self, button, treeview):
        model = treeview.get_model()
        try:
            path, column = treeview.get_cursor()
            path = int(path[0])
            orden = model[path][0]
        except:
            return

        if orden < 2:
            return
        model[path][0] = orden - 1
        model[path - 1][0] = orden
        uno = model.get_iter(path)
        otro = model.get_iter(path - 1)
        model.swap(uno, otro)
        self.colorear()

    def down(self, button, treeview):
        model = treeview.get_model()
        try:
            path, column = treeview.get_cursor()
            path = int(path[0])
            orden = model[path][0]
        except:
            return

        if orden == len(model) or orden == 1:
            return
        model[path][0] = orden + 1
        model[path + 1][0] = orden
        uno = model.get_iter(path)
        otro = model.get_iter(path + 1)
        model.swap(uno, otro)
        self.colorear()

    def remove(self, button, treeview):
        model = treeview.get_model()
        try:
            path, column = treeview.get_cursor()
            path = int(path[0])
            orden = model[path][0]
            padron = model[path][1]
            unidad = model[path][2]
        except:
            return

        uno = model.get_iter(path)
        model.remove(uno)
        for f in model:
            if f[0] > orden:
                f[0] = f[0] - 1

        self.model.append((padron, unidad))
        self.colorear()

    def lado_a(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            padron = self.model[path][0]
            unidad = self.model[path][1]
        except:
            pass

        self.model_a.append((len(self.model_a) + 1,
         padron,
         unidad,
         '#FFF'))
        treeiter = self.model.get_iter(path)
        self.model.remove(treeiter)
        self.colorear()

    def lado_b(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            padron = self.model[path][0]
            unidad = self.model[path][1]
        except:
            pass

        self.model_b.append((len(self.model_b) + 1,
         padron,
         unidad,
         '#FFF'))
        treeiter = self.model.get_iter(path)
        self.model.remove(treeiter)
        self.colorear()

    def borrar(self, *args):
        pass

    def guardar(self, *args):
        grupos_a = []
        i = 0
        for a in self.model_grupo_a:
            if a[3] == 0:
                return Widgets.Alerta('Error', 'warning.png', 'Tiene que definir el Patr\xc3\xb3n para cada grupo')
            grupo = []
            cont = a[0]
            if cont == 0:
                cont = len(self.model_a) - i
            while cont > 0:
                grupo.append(self.model_a[i][1])
                cont -= 1
                i += 1

            grupos_a.append((a[3], grupo))

        grupos_b = []
        i = 0
        for a in self.model_grupo_b:
            if a[3] == 0:
                return Widgets.Alerta('Error', 'warning.png', 'Tiene que definir el Patr\xc3\xb3n para cada grupo')
            grupo = []
            cont = a[0]
            if cont == 0:
                cont = len(self.model_b) - i
            while cont > 0:
                grupo.append(self.model_b[i][1])
                cont -= 1
                i += 1

            grupos_b.append((a[3], grupo))

        datos = {'lado_a': json.dumps(grupos_a),
         'lado_b': json.dumps(grupos_b),
         'dia': self.fecha.get_date(),
         'ruta_id': self.ruta}
        respuesta = self.http.load('guardar-programacion', datos)
        if respuesta:
            self.cerrar()

    def nueva(self, *args):
        datos = {'ruta_id': self.ruta,
         'dia': self.fecha.get_date()}
        inicio = self.http.load('nueva-programacion', datos)
        if inicio:
            self.escribir(inicio)
        else:
            self.model_a.clear()
            self.model_b.clear()
            self.model_grupo_a.clear()
            self.model_grupo_b.clear()
            self.model.clear()
            for u in self.unidades:
                self.model.append(u)

            self.model_grupo_a.append((0,
             self.liststore,
             '',
             0))
            self.model_grupo_b.append((0,
             self.liststore,
             '',
             0))

    def leer(self, *args):
        if len(self.combo_prog.lista) > 0:
            self.fecha.show_all()
        prog_id = self.combo_prog.get_id()
        programacion = self.programaciones[prog_id]
        self.fecha.set_date(programacion['nombre'])
        self.escribir(programacion)

    def escribir(self, programacion):
        self.model_a.clear()
        self.model_b.clear()
        self.model_grupo_a.clear()
        self.model_grupo_b.clear()
        self.model.clear()
        grupo_a = 0
        grupo_b = 0
        lado_a = 0
        lado_b = 0
        unidades = {}
        for u in self.unidades:
            unidades[u[0]] = u[1]

        for g in programacion['grupos']:
            count = 0
            if g['lado']:
                color = self.colores[grupo_b]
                for p in g['padrones']:
                    lado_b += 1
                    count += 1
                    i = unidades[p]
                    del unidades[p]
                    self.model_b.append((lado_b,
                     p,
                     i,
                     color))

                pt, pi = g['patron']
                self.model_grupo_b.append((count,
                 self.liststore,
                 pt,
                 pi))
                grupo_b += 1
            else:
                color = self.colores[grupo_a]
                for p in g['padrones']:
                    lado_a += 1
                    count += 1
                    i = unidades[p]
                    del unidades[p]
                    self.model_a.append((lado_a,
                     p,
                     i,
                     color))

                pt, pi = g['patron']
                self.model_grupo_a.append((count,
                 self.liststore,
                 pt,
                 pi))
                grupo_a += 1

        for u in unidades:
            self.model.append((u, unidades[u]))

    def iniciar(self):
        self.show_all()
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class Prestamos(gtk.Dialog):

    def __init__(self, parent, trabajador_id, nombre):
        super(Prestamos, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = parent.http
        self.trabajador = trabajador_id
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Pr\xc3\xa9stamos del Trabajador: %s' % nombre)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(600, 500)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, str, str, bool, str)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('DIA', 'OBSERVACION', 'MON', 'SALDO', 'FACT')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            if i == 4:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        datos = {'trabajador_id': trabajador_id}
        lista = self.http.load('prestamos', datos)
        for l in lista:
            self.model.append(l)

        but_nuevo = Widgets.Button('nuevo.png', '_Nuevo')
        self.action_area.pack_start(but_nuevo, False, False, 0)
        but_nuevo.connect('clicked', self.nuevo)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('ok.png', '_OK')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.treeview.connect('row-activated', self.facturar)
        self.modificaciones = False
        self.menu = gtk.Menu()
        item1 = gtk.MenuItem('Anular Orden de Pago')
        item1.connect('activate', self.anular_orden)
        self.menu.append(item1)
        self.treeview.connect('button-release-event', self.on_release_button)
        self.iniciar()

    def nuevo(self, *args):
        dialogo = FechaConceptoMonto(self)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            datos = {'dia': respuesta[0],
             'concepto': respuesta[1],
             'monto': respuesta[2],
             'trabajador_id': self.trabajador}
            self.http.load('nuevo-prestamo', datos)
            self.cerrar()

    def on_release_button(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.menu.popup(None, None, None, event.button, t)
                self.menu.show_all()
            return True
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            self.treeview.set_cursor(path, self.column, True)
        except:
            return

    def anular_orden(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            raise
            return

        amortizado = self.model[path][4]
        if amortizado:
            return Widgets.Alerta('Error al Anular', 'warning.png', 'No puede anular un pr\xc3\xa9stamo si ya est\xc3\xa1 amortizado')
        dialogo = Widgets.Alerta_SINO('Anular Orden', 'anular.png', '\xc2\xbfEst\xc3\xa1 seguro de anular esta cotizaci\xc3\xb3n?.')
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            datos = {'trabajador_id': self.trabajador,
             'voucher_id': self.model[path][5]}
            respuesta = self.http.load('anular-prestamo', datos)
            if respuesta:
                treeiter = self.model.get_iter(path)
                self.model.remove(treeiter)

    def facturar(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        facturado = self.model[path][4]
        dialogo = Widgets.Alerta_FechaNumero('Amortizar Pr\xc3\xa9stamo', 'dinero.png', 'Escriba el monto a pagar', 10, True)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            datos = {'cotizacion_id': self.model[path][5],
             'trabajador_id': self.trabajador,
             'dia': respuesta[0],
             'monto': respuesta[1]}
            if self.http.load('pagar-prestamo', datos):
                self.cerrar()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class Castigar(gtk.Dialog):

    def __init__(self, parent, trabajador_id, nombre):
        super(Castigar, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = parent.http
        self.trabajador = trabajador_id
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Castigar Trabajador: %s' % nombre)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        if not self.http.castigos:
            data = self.http.load('castigos', {'trabajador_id': self.trabajador})
            if data:
                self.http.castigos = data
            else:
                self.cerrar()
                return
        tabla = gtk.Table(2, 3)
        self.vbox.pack_start(tabla, False, False, 0)
        tabla.attach(gtk.Label('D\xc3\xada:'), 0, 1, 0, 1)
        self.fecha = Widgets.Fecha()
        tabla.attach(self.fecha, 1, 2, 0, 1)
        tabla.attach(gtk.Label('Motivo:'), 0, 1, 1, 2)
        self.combo_motivo = Widgets.ComboBox()
        tabla.attach(self.combo_motivo, 1, 2, 1, 2)
        self.combo_motivo.set_lista(self.http.castigos)
        tabla.attach(gtk.Label('Detalle:'), 0, 1, 2, 3)
        self.entry_detalle = Widgets.Texto(64)
        tabla.attach(self.entry_detalle, 1, 2, 2, 3)
        but_ok = Widgets.Button('castigos.png', '_Castigar')
        self.action_area.pack_start(but_ok, False, False, 0)
        but_ok.connect('clicked', self.castigar)
        self.but_ok = Widgets.Button('castigos.png', 'Castigar')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.respuesta = False

    def castigar(self, *args):
        datos = {'motivo_id': self.combo_motivo.get_id(),
         'trabajador_id': self.trabajador,
         'dia': self.fecha.get_date(),
         'detalle': self.entry_detalle.get_text()}
        self.respuesta = self.http.load('castigar', datos)
        self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            return self.respuesta

    def cerrar(self, *args):
        self.destroy()


class FechaConceptoMonto(gtk.Dialog):

    def __init__(self, parent):
        super(FechaConceptoMonto, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = parent.http
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Pr\xc3\xa9stamo Nuevo:')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        tabla = gtk.Table(2, 3)
        self.vbox.pack_start(tabla, False, False, 0)
        tabla.attach(gtk.Label('D\xc3\xada:'), 0, 1, 0, 1)
        self.fecha = Widgets.Fecha()
        tabla.attach(self.fecha, 1, 2, 0, 1)
        tabla.attach(gtk.Label('Concepto:'), 0, 1, 1, 2)
        self.entry_concepto = Widgets.Texto(128)
        tabla.attach(self.entry_concepto, 1, 2, 1, 2)
        tabla.attach(gtk.Label('Monto:'), 0, 1, 2, 3)
        self.entry_monto = Widgets.Texto(10)
        tabla.attach(self.entry_monto, 1, 2, 2, 3)
        but_ok = Widgets.Button('dinero.png', '_Facturar')
        self.action_area.pack_start(but_ok, False, False, 0)
        but_ok.connect('clicked', self.enviar)
        self.but_ok = Widgets.Button('dinero.png', '_Facturar')
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)

    def enviar(self, *args):
        try:
            fecha = self.fecha.get_date()
            concepto = self.entry_concepto.get_text()
            monto = float(self.entry_monto.get_text())
        except:
            return Widgets.Alerta('Error', 'warning.png', 'Monto inv\xc3\xa1lido')

        self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        if self.run() == gtk.RESPONSE_OK:
            fecha = self.fecha.get_date()
            concepto = self.entry_concepto.get_text()
            monto = float(self.entry_monto.get_text())
            return (fecha, concepto, monto)
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class VentasGrifo(gtk.Dialog):

    def __init__(self, padre, lista):
        super(VentasGrifo, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.http = padre.http
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_title('Ventas del d\xc3\xada')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('delete_event', self.cerrar)
        sw = gtk.ScrolledWindow()
        sw.set_size_request(600, 500)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(sw, False, False, 0)
        self.model = gtk.ListStore(str, str, int, str, bool, bool, str)
        self.treeview = gtk.TreeView(self.model)
        columnas = ('N\xc2\xba COMPROBANTE', 'HORA', 'PAD', 'MONTO', 'CONTADO', 'ANULADO')
        sw.add(self.treeview)
        for i, columna in enumerate(columnas):
            if i > 3:
                cell = gtk.CellRendererToggle()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, active=i)
            else:
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        for l in lista:
            self.model.append(l)

        but_anular = Widgets.Button('anular.png', '_Anular')
        self.action_area.pack_start(but_anular, False, False, 0)
        but_anular.connect('clicked', self.anular)
        but_salir = Widgets.Button('cancelar.png', '_Salir')
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('ok.png', '_OK')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.iniciar()

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
        except:
            return

        dialogo = Widgets.Alerta_SINO('Anular Venta', 'anular.png', '\xc2\xbfEst\xc3\xa1 seguro de anular esta venta?')
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            datos = {'padron': self.model[path][2],
             'voucher_id': self.model[path][6]}
            respuesta = self.http.load('anular-venta-grifo', datos)
            if respuesta:
                self.model[path][5] = True

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class ReporteCobro(gtk.Window):

    def __init__(self, http, padre):
        super(ReporteCobro, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.http = http
        vbox_main = gtk.VBox(False, 0)
        self.add(vbox_main)
        hbox = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('D\xc3\xada:'), False, False, 0)
        self.fecha = Widgets.Fecha()
        self.fecha.set_size_request(150, 30)
        hbox.pack_start(self.fecha, False, False, 0)
        hbox.pack_start(gtk.Label('Concepto:'), False, False, 0)
        self.concepto = Widgets.ComboBox()
        hbox.pack_start(self.concepto, False, False, 0)
        self.dia, self.ruta, self.lado = padre.padre.selector.get_datos()
        self.pagos = self.http.get_pagos(self.ruta)
        self.concepto.column = 4
        self.concepto.set_lista(self.pagos['cobros'])
        self.but_actualizar = Widgets.Button('actualizar.png', 'Actualizar')
        hbox.pack_start(self.but_actualizar, False, False, 0)
        self.but_actualizar.connect('clicked', self.actualizar)
        self.but_bloquear = Widgets.Button('bloqueado.png', 'Bloquear/Desbloquear')
        #hbox.pack_start(self.but_bloquear, False, False, 0)
        self.dia = self.fecha.get_date()
        self.set_title('Reporte de Cobros')
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw.set_size_request(720, 540)
        else:
            sw.set_size_request(800, 600)
        self.model = gtk.ListStore(int, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        selection = self.treeview.get_selection()
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        vbox_main.pack_start(sw, True, True, 0)
        sw.add(self.treeview)
        columnas = ('PADRON', 'MONTO')
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.show_all()

    def actualizar(self, *args):
        datos = {
            'dia': self.fecha.get_date(),
            'concepto': self.concepto.get_id(),
            'ruta_id': self.ruta
        }
        data = self.http.load('reporte-cobros', datos)
        if data:
            totales = {}
            self.model.clear()
            for u in data['unidades']:
                totales[u] = 0
            for c in data['cobros']:
                totales[c[0]] += Decimal(c[1])
            for u in data['unidades']:
                self.model.append((u, totales[u]))


    def bloquear(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            liq_id = row[len(row) - 1]
        except:
            raise
            return

        datos = {'dia': self.fecha.get_date(),
            'ruta_id': self.ruta,
            'lado': self.lado,
            'padron': self.model[path][0],
            'liquidacion': True
        }
        data = self.http.load('bloquear-unidad', datos)
        if data:
            self.escribir(data)
            self.por_unidad = False

    def cerrar(self, *args):
        self.destroy()


class MiCaja(gtk.Window):

    def __init__(self, http, padre):
        super(MiCaja, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.http = http
        vbox_main = gtk.VBox(False, 0)
        self.add(vbox_main)
        self.padre = padre
        self.dia = padre.dia
        hbox = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox, False, False, 0)
        self.but_gasto = Widgets.Button('dinero.png', 'Reg. Gasto')
        hbox.pack_start(self.but_gasto, False, False, 0)
        self.but_gasto.connect('clicked', self.gasto)
        self.but_imprimir = Widgets.Button('imprimir.png', 'Imprimir Reporte')
        hbox.pack_start(self.but_imprimir, False, False, 0)
        self.but_imprimir.connect('clicked', self.imprimir)
        self.but_cerrar = Widgets.Button('central.png', 'Cerrar Caja')
        hbox.pack_start(self.but_cerrar, False, False, 0)
        self.but_cerrar.connect('clicked', self.cerrar_caja)
        self.but_reporte = Widgets.Button('reporte.png', 'Por Concepto')
        hbox.pack_start(self.but_reporte, False, False, 0)
        self.but_reporte.connect('clicked', self.reporte)

        hbox = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox, False, False, 0)
        self.but_actualizar = Widgets.Button('actualizar.png', 'Resumen')
        hbox.pack_start(self.but_actualizar, False, False, 0)
        self.but_actualizar.connect('clicked', self.actualizar, True)
        self.but_actualizar2 = Widgets.Button('actualizar.png', 'Detallado')
        hbox.pack_start(self.but_actualizar2, False, False, 0)
        self.but_actualizar2.connect('clicked', self.actualizar, False)
        self.but_reimprimir = Widgets.Button('imprimir.png', tooltip='Reimprimir Ticket')
        hbox.pack_start(self.but_reimprimir, False, False, 0)
        self.but_reimprimir.connect('clicked', self.reimprimir)
        self.but_anular = Widgets.Button('cancelar.png', tooltip='Anular Ticket')
        hbox.pack_start(self.but_anular, False, False, 0)
        self.but_anular.connect('clicked', self.anular)
        self.set_title('Reporte de Caja: ' + self.http.despachador)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw.set_size_request(720, 540)
        else:
            sw.set_size_request(800, 600)
        self.model = gtk.ListStore(str, str, str)
        self.treeview = Widgets.TreeView(self.model)
        self.treeview.set_rubber_banding(True)
        selection = self.treeview.get_selection()
        self.treeview.set_enable_search(False)
        self.treeview.set_reorderable(False)
        vbox_main.pack_start(sw, True, True, 0)
        sw.add(self.treeview)
        self.show_all()
        self.actualizar(None, True)

    def reporte(self, *args):
        ReporteCobro(self.http, self)

    def anular(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            i = row[3]
        except:
            return
        if i.isdigit():
            dialogo = Widgets.Alerta_SINO_Clave('Anular Cobro', 'warning.png', 'Confirme que desea anular el cobro de %s por S/. %s' % (row[0], row[2]))
            if dialogo.iniciar():
                clave = dialogo.clave
                datos = {'movimiento': int(self.model[path][1] == '-'),
                 'voucher_id': i,
                 'ruta_id': self.padre.ruta,
                 'lado': self.padre.lado,
                 'dia': self.dia,
                 'monto': row[2],
                 'usuario': self.http.despachador,
                 'detalle': row[0],
                 'padron': row[1],
                 'hora': '',
                 'clave': clave,
                }
                data = self.http.load('anular-pago', datos)
                if data:
                    ultimo = self.model[len(self.model) - 1]
                    ultimo[2] = str(Decimal(ultimo[2]) - Decimal(self.model[path][2]))
                    self.model[path][2] = 'ANULADO'
            dialogo.cerrar()

    def reimprimir(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
            i = row[3]
        except:
            return
        if i.isdigit():
            datos = {'movimiento': int(self.model[path][1] == '-'),
             'voucher_id': i,
             'ruta_id': self.padre.ruta,
             'lado': self.padre.lado}
            self.http.load('reimprimir-pago', datos)

    def actualizar(self, widget, resumen):
        self.resumen = resumen
        data = self.http.load('reporte-caja', {'imprimir': False,
         'resumen': resumen})
        if data:
            lista = data['liststore']
            liststore = []
            for l in lista:
                liststore.append(eval(l))

            self.model = gtk.ListStore(*liststore)
            cols = self.treeview.get_columns()
            for c in cols:
                self.treeview.remove_column(c)

            columnas = data['columnas']
            self.treeview.set_model(self.model)
            for i, columna in enumerate(columnas):
                cell_text = gtk.CellRendererText()
                tvcolumn = Widgets.TreeViewColumn(columna)
                tvcolumn.pack_start(cell_text, True)
                tvcolumn.set_attributes(cell_text, markup=i)
                self.treeview.append_column(tvcolumn)
                tvcolumn.encabezado()

            for l in data['lista']:
                self.model.append(l)

    def imprimir(self, *args):
        data = self.http.load('reporte-caja', {'imprimir': True,
         'resumen': self.resumen})
        self.cerrar()

    def cerrar_caja(self, *args):
        dialogo = Widgets.Alerta_Dia('Advertencia Operaci\xc3\xb3n Irreversible', 'warning.png', 'Antes de CERRAR SU CAJA asegurese de haber impreso los reportes necesarios.\nSi desea continuar de todas maneras, <b>Indique el d\xc3\xada al que pertenece sus cobros.</b>')
        if dialogo.iniciar():
            data = self.http.load('cerrar-caja', {'dia': dialogo.dia.get_date().strftime('%d-%m-%Y')})
            dialogo.cerrar()
            if data:
                self.cerrar()

    def cerrar(self, *args):
        self.destroy()

    def gasto(self, *args):
        dialogo = Gasto(self)
        if dialogo.iniciar():
            datos = dialogo.datos
            data = self.http.load('registrar-gasto', datos)
            if data:
                n = len(self.model)
                try:
                    self.model.insert(n - 1, (datos['concepto'],
                     '-',
                     '-' + datos['monto'],
                     data))
                except:
                    self.model[n - 1][2] = str(Decimal(self.model[n - 1][2]) - Decimal(datos['monto']))
                else:
                    self.model[n][2] = str(Decimal(self.model[n][2]) - Decimal(datos['monto']))

        dialogo.cerrar()


class Gasto(gtk.Dialog):

    def __init__(self, padre):
        super(Gasto, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.set_modal(True)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_transient_for(parent)
        self.padre = padre
        self.http = padre.http
        self.connect('delete_event', self.cerrar)
        self.set_title('Registrar Gasto')
        table = gtk.Table(2, 2)
        self.vbox.pack_start(table, False, False, 0)
        self.entry_concepto = Widgets.Texto(64)
        table.attach(gtk.Label('Concepto:'), 0, 1, 0, 1, gtk.FILL, gtk.FILL, 2, 2)
        table.attach(self.entry_concepto, 1, 2, 0, 1, gtk.FILL, gtk.FILL, 2, 2)
        self.entry_monto = Widgets.Texto(7)
        table.attach(gtk.Label('Monto:'), 0, 1, 1, 2, gtk.FILL, gtk.FILL, 2, 2)
        table.attach(self.entry_monto, 1, 2, 1, 2, gtk.FILL, gtk.FILL, 2, 2)
        self.but_ok = Widgets.Button('aceptar.png', '_Aceptar')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.add_action_widget(self.but_salir, gtk.RESPONSE_CANCEL)

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            self.datos = {'concepto': self.entry_concepto.get_text(),
             'monto': self.entry_monto.get_text(),
             'ruta_id': self.padre.padre.ruta,
             'lado': self.padre.padre.lado,
             'dia': self.padre.padre.dia}
            return True
        return False

    def cerrar(self, *args):
        self.destroy()


class Transbordo(gtk.Window):

    def __init__(self, http, padre):
        super(Transbordo, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.http = http
        vbox_main = gtk.VBox(False, 0)
        self.set_position(gtk.WIN_POS_CENTER)
        self.padre = padre
        self.ruta = self.padre.ruta
        self.lado = self.padre.lado
        self.padron = self.padre.padron
        self.set_title('Transbordos A Favor de la Unidad %s' % self.padre.padron)
        self.add(vbox_main)
        hbox_main = gtk.HBox(False, 2)
        vbox_main.pack_start(hbox_main, False, False, 0)
        frame = gtk.Frame('Transbordos de La Unidad')
        hbox_main.pack_start(frame, False, False, 0)
        vbox_transbordos = gtk.VBox(False, 0)
        frame.add(vbox_transbordos)
        hbox = gtk.HBox(False, 0)
        vbox_transbordos.pack_start(hbox, False, False, 0)
        self.but_nuevo = Widgets.Button('nuevo.png', 'Nuevo')
        hbox.pack_start(self.but_nuevo, False, False, 0)
        self.but_nuevo.connect('clicked', self.nuevo)
        self.but_anular = Widgets.Button('cancelar.png', 'Anular')
        hbox.pack_start(self.but_anular, False, False, 0)
        self.but_anular.connect('clicked', self.anular)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw.set_size_request(180, 300)
        else:
            sw.set_size_request(200, 300)
        self.model_transbordo = gtk.ListStore(str, str, str, str, str, str, gobject.TYPE_PYOBJECT)
        self.treeview_transbordo = Widgets.TreeView(self.model_transbordo)
        columnas = ['PAD',
         'RUTA',
         'SALIDA',
         'ESTADO']
        for i, columna in enumerate(columnas):
            cell_text = gtk.CellRendererText()
            tvcolumn = Widgets.TreeViewColumn(columna)
            tvcolumn.pack_start(cell_text, True)
            tvcolumn.set_attributes(cell_text, markup=i)
            self.treeview_transbordo.append_column(tvcolumn)
            tvcolumn.encabezado()

        self.treeview_transbordo.set_rubber_banding(True)
        self.treeview_transbordo.connect('row-activated', self.actualizar)
        selection = self.treeview_transbordo.get_selection()
        self.treeview_transbordo.set_enable_search(False)
        self.treeview_transbordo.set_reorderable(False)
        vbox_transbordos.pack_start(sw, True, True, 0)
        sw.add(self.treeview_transbordo)
        frame = gtk.Frame('Boletos del Transbordo')
        hbox_main.pack_start(frame, False, False, 0)
        vbox_boletos = gtk.VBox(False, 0)
        frame.add(vbox_boletos)
        self.label = gtk.Label()
        vbox_boletos.pack_start(self.label, False, False, 0)
        hbox = gtk.HBox(False, 0)
        vbox_boletos.pack_start(hbox, False, False, 0)
        self.boleto = Widgets.ComboBox()
        datos = {'ruta_id': self.padre.ruta}
        if datos:
            lista = self.http.load('boletos-ruta', datos)
        else:
            self.destroy()
            return
        lista_arreglada = []
        for l in lista:
            lista_arreglada.append(('%s %s' % (l[1], l[2]), l[0]))

        self.boleto.set_lista(lista_arreglada)
        hbox.pack_start(self.boleto, False, False, 0)
        self.entry_numero = Widgets.Numero(6)
        self.entry_numero.connect('activate', self.agregar)
        self.entry_numero.connect('key-release-event', self.retroceder)
        hbox.pack_start(self.entry_numero, False, False, 0)
        self.but_agregar = Widgets.Button('nuevo.png', 'Agregar')
        hbox.pack_start(self.but_agregar, False, False, 0)
        self.but_agregar.connect('clicked', self.agregar)
        self.but_eliminar = Widgets.Button('cancelar.png', 'Eliminar')
        hbox.pack_start(self.but_eliminar, False, False, 0)
        self.but_eliminar.connect('clicked', self.eliminar)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if os.name == 'nt':
            sw.set_size_request(400, 300)
        else:
            sw.set_size_request(450, 300)
        self.model_boleto = gtk.ListStore(str, int, str)
        self.treeview_boleto = Widgets.TreeView(self.model_boleto)
        columnas = ['BOLETO', 'NUMERO', 'PAGAR']
        for i, columna in enumerate(columnas):
            column = Widgets.TreeViewColumn(columna)
            if i == 2:
                cell = Widgets.Cell()
                cell.connect('editado', self.editado)
                cell.set_property('editable', True)
                column.set_flags(gtk.CAN_FOCUS)
                self.column = column
                self.cell = cell
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', False)
            column.pack_start(cell, True)
            column.set_attributes(cell, text=i)
            self.treeview_boleto.append_column(column)
            column.encabezado()

        self.treeview_boleto.set_rubber_banding(True)
        selection = self.treeview_boleto.get_selection()
        self.treeview_boleto.set_enable_search(False)
        self.treeview_boleto.set_reorderable(False)
        vbox_boletos.pack_start(sw, True, True, 0)
        sw.add(self.treeview_boleto)
        self.cargar()
        hbox = gtk.HBox(False, 0)
        hbox.pack_start(gtk.Label('TOTAL TRANSBORDO:'))
        self.entry_total = Widgets.Texto(10)
        self.entry_total.set_sensitive(False)
        hbox.pack_start(self.entry_total, False, False, 0)
        vbox_main.pack_start(hbox, False, False, 0)
        self.but_guardar = Widgets.Button('guardar.png', 'Guardar')
        hbox.pack_end(self.but_guardar, False, False, 0)
        self.but_guardar.connect('clicked', self.guardar)
        self.but_cerrar = Widgets.Button('salir.png', 'Cerrar')
        hbox.pack_end(self.but_cerrar, False, False, 0)
        self.but_cerrar.connect('clicked', self.cerrar)
        self.entry_numero.set_sensitive(False)
        self.treeview_boleto.set_sensitive(False)
        self.editable = False
        self.show_all()

    def editado(self, widget, path, new_text):
        if new_text == '':
            new_text = '0'
        try:
            try:
                Decimal(new_text)
            except:
                return

            self.model_boleto[path][2] = new_text
        finally:
            self.calcular()
            if path + 1 == len(self.model_boleto):
                self.but_guardar.grab_focus()
            else:
                self.treeview_boleto.set_cursor(path + 1, self.column, True)

    def cargar(self):
        self.model_transbordo.clear()
        data = self.http.load('transbordo-lista', {'padron': self.padron,
         'ruta_id': self.padre.ruta,
         'lado': self.padre.lado})
        if data:
            for l in data:
                self.model_transbordo.append(l)

    def nuevo(self, *args):
        dialogo = BuscarSalida(self)
        if dialogo.iniciar():
            salida = dialogo.data
            self.model_transbordo.append((salida['padron'],
             salida['ruta'],
             salida['nombre'],
             'EDITAR',
             '',
             salida['id'],
             None))
            self.boletos = salida['boletos']
            dialogo.cerrar()
            self.label.set_markup('<b>PAD: %s  SALIDA: %s</b>' % (salida['padron'], salida['nombre']))
            self.transbordo_id = None
            self.editable = 'EDITAR'
            self.malogrado = salida['padron']
            self.salida = salida['id']
            self.model_boleto.clear()
            if self.editable:
                self.entry_numero.set_sensitive(True)
                self.treeview_boleto.set_sensitive(True)
                self.but_guardar.set_sensitive(True)
        else:
            dialogo.cerrar()

    def anular(self, *args):
        try:
            path, column = self.treeview_transbordo.get_cursor()
            path = int(path[0])
            row = self.model_transbordo[path]
            i = row[len(row) - 1]
        except:
            return

        if row[3] == 'ANULADO':
            return Widgets.Alerta('Ya est\xc3\xa1 anulado', 'error.png', 'El transbordo ya est\xc3\xa1 anulado')
        if row[3] == 'EDITAR':
            treeiter = self.model_transbordo.get_iter(path)
            self.model_transbordo.remove(treeiter)
        dialogo = Widgets.Alerta_SINO('Anular Transbordo', 'warning.png', 'Confirme que desea anular el transbordo del padr\xc3\xb3n %s' % row[0])
        if dialogo.iniciar():
            datos = {'transbordo_id': i,
             'padron': row[0],
             'ruta_id': self.padre.ruta,
             'lado': self.padre.lado}
            data = self.http.load('transbordo-anular', datos)
            if data:
                treeiter = self.model_transbordo.get_iter(path)
                self.model_transbordo.remove(treeiter)
        dialogo.cerrar()

    def actualizar(self, *args):
        if self.editable:
            dialogo = Widgets.Alerta_SINO('Advertencia', 'salir.png', '\xc2\xbfEst\xc3\xa1 seguro de cancelar el ingreso de este transbordo?')
            if dialogo.iniciar():
                path = 0
                for b in self.model_boleto:
                    if b[3] == 'EDITAR':
                        treeiter = self.model_transbordo.get_iter(path)
                        self.model_transbordo.remove(treeiter)
                    path += 1

                dialogo.cerrar()
            else:
                dialogo.cerrar()
                return
        self.model_boleto.clear()
        try:
            path, column = self.treeview_transbordo.get_cursor()
            path = int(path[0])
            row = self.model_transbordo[path]
            i = row[len(row) - 1]
            s = row[len(row) - 2]
        except:
            return

        self.label.set_markup('<b>PAD: %s  SALIDA: %s</b>' % (row[0], row[2]))
        self.malogrado = row[0]
        self.transbordo_id = i
        self.editable = row[3] == 'EDITAR'
        boletos = json.loads(row[4])
        for b in boletos:
            self.model_boleto.append(b)

        if self.editable:
            self.entry_numero.set_sensitive(True)
            self.treeview_boleto.set_sensitive(True)
            self.but_guardar.set_sensitive(True)
        else:
            self.entry_numero.set_sensitive(False)
            self.treeview_boleto.set_sensitive(False)
            self.but_guardar.set_sensitive(False)
        self.calcular()

    def agregar(self, *args):
        boleto = self.boleto.get_id()
        numero = self.entry_numero.get_int()
        for b in self.model_boleto:
            if int(b[1]) == numero:
                return Widgets.Alerta('No se puede usar el Boleto', 'warning.png', 'El boleto ya est\xc3\xa1 repetido')

        existe = False
        anulado = False
        tarifa = '0.00'
        for b in self.boletos:
            if b['boleto'] == boleto:
                if b['anulado']:
                    if b['inicio'] <= numero <= b['fin']:
                        anulado = True
                elif b['inicio'] <= numero < b['fin']:
                    tarifa = b['tarifa']
                    existe = True

        if not self.editable:
            return Widgets.Alerta('El transbordo est\xc3\xa1 cerrado', 'warning.png', 'No puede agregar m\xc3\xa1s boletos al transbordo,\ndebe anularlo y crear uno nuevamente')
        if anulado:
            return Widgets.Alerta('No se puede usar el Boleto', 'warning.png', 'El boleto ha sido anulado')
        if not existe:
            return Widgets.Alerta('No se puede usar el Boleto', 'warning.png', 'El boleto no pertenece a la salida')
        self.model_boleto.append((self.boleto.get_text(), numero, tarifa))
        self.calcular()

    def retroceder(self, widget, event):
        if event.keyval == 65293 or event.keyval == 65421:
            self.do_move_focus(self, gtk.DIR_TAB_BACKWARD)

    def eliminar(self, *args):
        try:
            path, column = self.treeview_boleto.get_cursor()
            path = int(path[0])
            row = self.model_boleto[path]
        except:
            return

        treeiter = self.model_boleto.get_iter(path)
        self.model_boleto.remove(treeiter)
        self.calcular()

    def calcular(self, *args):
        total = 0
        for b in self.model_boleto:
            total += Decimal(b[2])

        self.entry_total.set_text(str(total))

    def guardar(self, *args):
        boletos = []
        for b in self.model_boleto:
            boletos.append((b[0], b[1], b[2]))

        datos = {'recibe': self.padron,
         'malogrado': self.malogrado,
         'monto': self.entry_total.get_text(),
         'salida_id': self.salida,
         'boletos': json.dumps(boletos),
         'ruta_id': self.padre.ruta,
         'lado': self.padre.lado}
        data = self.http.load('transbordo-agregar', datos)
        if data:
            Widgets.Alerta('Transbordo registrado', 'transbordo.png', 'Se registro un transbordo por %s\nde la unidad %d a la unidad %s' % (datos['monto'], datos['malogrado'], datos['recibe']))
            self.cerrar()

    def imprimir(self, *args):
        resumen = self.check_resumen.get_active()
        data = self.http.load('reporte-caja', {'imprimir': True,
         'resumen': resumen})
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class BuscarSalida(gtk.Dialog):

    def __init__(self, padre):
        super(BuscarSalida, self).__init__(flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break

        self.set_modal(True)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_transient_for(parent)
        self.padre = padre
        self.http = padre.http
        self.connect('delete_event', self.cerrar)
        self.set_title('Buscar Salida')
        hbox = gtk.HBox(False, 2)
        self.vbox.pack_start(hbox, False, False, 0)
        self.fecha = Widgets.Fecha()
        self.fecha.set_size_request(90, 30)
        hbox.pack_start(self.fecha, False, False, 0)
        hbox.pack_start(gtk.Label('Padr\xc3\xb3n:'), False, False, 0)
        self.entry_padron = Widgets.Numero(4)
        hbox.pack_start(self.entry_padron, False, False, 0)
        self.entry_padron.connect('activate', self.buscar)
        self.vueltas = Vueltas(self.http)
        self.vbox.pack_start(self.vueltas, True, True, 0)
        self.vueltas.connect('editar-llegadas', self.aceptar)
        self.vueltas.connect('salida-seleccionada', self.seleccionada)
        self.salida = None
        self.but_salir = Widgets.Button('cancelar.png', '_Cancelar')
        self.add_action_widget(self.but_salir, gtk.RESPONSE_CANCEL)
        self.but_ok = Widgets.Button('aceptar.png', '_Aceptar')
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)

    def buscar(self, *args):
        datos = {'padron': self.entry_padron.get_int(),
         'ruta_id': self.padre.ruta,
         'lado': self.padre.lado,
         'dia': self.fecha.get_date()}
        if self.padre.padron == self.entry_padron.get_int():
            return Widgets.Alerta('No puede usar ese padron', 'error.png', 'No se puede usar el mismo padr\xc3\xb3n para el transbordo')
        data = self.http.load('salidas-unidad', datos)
        if data:
            self.padron = self.entry_padron.get_int()
            self.vueltas.actualizar(data)

    def seleccionada(self, widget, padron, salida):
        self.salida = salida

    def aceptar(self, *args):
        datos = {'salida_id': self.salida,
         'dia': self.fecha.get_date(),
         'ruta_id': self.padre.ruta,
         'lado': self.padre.lado,
         'padron': self.padron}
        self.data = self.http.load('salida-json', datos)
        if self.data['transbordo'] is None:
            self.but_ok.clicked()
        else:
            return Widgets.Alerta('No puede usar esta salida', 'error.png', 'Esta salida ya tiene un transbordo')

    def iniciar(self):
        self.show_all()
        self.but_ok.hide()
        if self.run() == gtk.RESPONSE_OK:
            return True
        return False

    def cerrar(self, *args):
        self.destroy()


class Trackers(gtk.Window):

    def __init__(self, http, dia, ruta, lado, padron):
        super(Trackers, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.http = http
        self.dia = dia
        self.ruta = ruta
        self.lado = lado
        if padron:
            self.padron = padron
        else:
            self.padron = None
        hbox_main = gtk.HBox(False, 0)
        self.add(hbox_main)
        frame = Widgets.Frame('Configuración Tracker')
        hbox_main.pack_start(frame, False, False, 5)
        vbox = gtk.VBox(False, 2)
        frame.add(vbox)
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Buscar Padrón:'), False, False, 0)
        self.entry_padron = Widgets.Numero(4)
        hbox.pack_start(self.entry_padron, False, False, 0)
        tabla = Widgets.Tabla()
        vbox.pack_start(tabla, False, False, 0)
        titulos = (
            ('padron', 'PADRON:'),
            ('placa', 'PLACA:'),
            ('tracker', 'Nº Serie GPS:'),
            ('celular', 'Celular:'),
            ('estado', 'Estado:'),
            ('salida', 'Última Salida:'),
            ('latitud', 'Latitud:'),
            ('longitud', 'Longitud:'),
            ('hora', 'Hora Actualizada:'),
            ('version', 'Versión:')
        )
        i = 0
        self.datos = {}
        for k, t in titulos:
            tit = gtk.Label()
            tit.set_markup('<b>%s</b>   ' % t)
            tit.set_alignment(1, 0.5)
            tabla.attach(tit, 0, 1, i, i + 1)
            label = gtk.Label('-')
            label.set_alignment(0, 0.5)
            self.datos[k] = label
            tabla.attach(label, 1, 2, i, i + 1)
            i += 1
        frame = Widgets.Frame('Emparejar Dispositivo GPS')
        vbox.pack_start(frame, False, False, 0)
        hbox = gtk.HBox(False, 0)
        frame.add(hbox)
        hbox.pack_start(gtk.Label('Nº Serie GPS:'), False, False, 0)
        self.entry_tracker = Widgets.Numero(5)
        hbox.pack_start(self.entry_tracker, False, False, 0)
        self.but_emparejar = Widgets.Button('icono.png', 'Busque una unidad', 48)
        self.but_emparejar.set_sensitive(False)
        hbox.pack_start(self.but_emparejar, False, False, 0)
        frame = Widgets.Frame('Enviar Mensaje de Texto')
        hbox_main.pack_start(frame, False, False, 5)
        vbox = gtk.VBox(False, 0)
        frame.add(vbox)
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(gtk.Label('Mensaje (max 64):'), False, False, 0)
        self.entry_mensaje = Widgets.Texto(64)
        hbox.pack_start(self.entry_mensaje, False, False, 0)
        self.radio_padrones = gtk.RadioButton(None, 'Enviar a: ', False)
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(self.radio_padrones, False, False, 0)
        self.radio_todos = gtk.RadioButton(self.radio_padrones, 'Todos', True)
        vbox.pack_start(self.radio_todos, False, False, 0)
        self.entry_padrones = Widgets.Texto(64)
        hbox.pack_end(self.entry_padrones, False, False, 0)
        but_enviar = Widgets.Button('SMS.png', 'Enviar Mensaje', 48)
        vbox.pack_start(but_enviar, False, False, 0)
        self.entry_padron.connect('activate', self.buscar_padron)
        self.but_emparejar.connect('clicked', self.emparejar)
        but_enviar.connect('clicked', self.enviar_mensaje)
        self.unidad = None
        if self.padron:
            self.entry_padron.set_text(str(self.padron))
            self.entry_padrones.set_text(str(self.padron))
            self.buscar_padron()
        self.show_all()

    def buscar_padron(self, *args):
        padron = self.entry_padron.get_text()
        datos = {
            'ruta': self.ruta,
            'lado': self.lado,
            'dia': self.dia,
            'padron': padron
        }
        respuesta = self.http.load('buscar-tracker', datos)
        if respuesta:
            for k in self.datos:
                self.datos[k].set_text(str(respuesta[k]))
            self.unidad = respuesta['unidad_id']
            self.padron = padron
        else:
            self.unidad = None
        if self.unidad:
            self.but_emparejar.set_text('Emparejar con PAD%s' % self.padron.zfill(3))
            self.but_emparejar.set_sensitive(True)
        else:
            self.but_emparejar.set_text('Busque una unidad')
            self.but_emparejar.set_sensitive(False)

    def emparejar(self, *args):
        tracker = self.entry_tracker.get_text()
        datos = {
            'ruta': self.ruta,
            'lado': self.lado,
            'dia': self.dia,
            'unidad': self.unidad,
            'padron': self.padron,
            'tracker': tracker
        }
        respuesta = self.http.load('emparejar-tracker', datos)
        if respuesta:
            for k in self.datos:
                self.datos[k].set_text(str(respuesta[k]))
            self.but_emparejar.set_text('Busque una unidad')
            self.but_emparejar.set_sensitive(False)

    def enviar_mensaje(self, *args):
        mensaje = self.entry_mensaje.get_text().replace(' ', '_')
        todos = self.radio_todos.get_active()
        padrones = self.entry_padrones.get_text()
        datos = {
            'ruta': self.ruta,
            'lado': self.lado,
            'dia': self.dia,
            'mensaje': mensaje,
            'todos': int(todos),
            'padrones': padrones
        }
        self.http.load('enviar-mensaje', datos)