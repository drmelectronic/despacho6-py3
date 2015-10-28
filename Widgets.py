##! /usr/bin/python
# -*- coding: utf-8 -*-
# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__ = "daniel"
__date__ = "$06-mar-2012 16:15:38$"

import gtk
import gobject
import datetime
import os
if os.name != 'nt':
    import pynotify
    pynotify.init('despacho')
import time
import json
import base64
from uuid import getnode


class Entry(gtk.Entry):

    def __init__(self, n=None):
        if n is None:
            super(Entry, self).__init__()
        else:
            super(Entry, self).__init__(n)
        self.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        #self.modify_base(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        #self.modify_base(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        #self.modify_base(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        #self.modify_base(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

        #self.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))
        #self.modify_text(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#FF0000'))
        #self.modify_text(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#00FF00'))
        #self.modify_text(gtk.STATE_SELECTED, gtk.gdk.color_parse('#0000FF'))
        #self.modify_text(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#FFFF00'))


class OSD:

    def __init__(self, text):
        if os.name != 'nt':
            ruta = os.getcwd() + '/'
            p = pynotify.Notification(
                'Sonido', text, ruta + 'images/PNG-48/sonido.png')
            p.show()


class Frame(gtk.Frame):

    def __init__(self, label=None):
        super(Frame, self).__init__()
        self.set_border_width(2)
        if not label is None:
            self.set_label(label)
        self.set_property('shadow-type', gtk.SHADOW_NONE)


class Fecha(gtk.Button):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ())
        }

    def __init__(self):
        super(Fecha, self).__init__()
        self.calendar = gtk.Calendar()
        self.set_size_request(90, 25)
        self.cwindow = gtk.Window(gtk.WINDOW_POPUP)
        self.cwindow.set_position(gtk.WIN_POS_MOUSE)
        self.cwindow.set_decorated(False)
        self.cwindow.set_modal(True)
        self.eb = gtk.EventBox()
        self.eb.add(self.calendar)
        self.cwindow.add(self.eb)
        self.currentDate = datetime.date.today()
        self.year, self.month, self.day = self.calendar.get_date()
        self.calendar.mark_day(self.day)
        self.month += 1
        self.cerrar = False
        self.calendar.connect('day-selected', self.update_entry)
        self.calendar.connect('button-release-event', self.close)
        self.connect('clicked', self.show_widget)
        self.connect('focus-out-event', self.focus_out_event)
        self.cwindow.connect('key-release-event', self.hide_widget)
        self.update_entry()
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def get_text(self):
        return self.get_label()

    def get_date(self):
        return self.currentDate

    def show_widget(self, *args):
        self.cwindow.show_all()
        self.cerrar = False

    def hide_widget(self, *args):
        self.cwindow.hide_all()

    def update_entry(self, *args):
        year, month, day = self.calendar.get_date()
        self.currentDate = datetime.date(year, month + 1, day)
        text = self.currentDate.strftime('%d/%m/%Y')
        self.set_label(text)
        if year == self.year and month + 1 == self.month:
            self.cerrar = True
        else:
            self.year = year
            self.month = month + 1

    def close(self, *args):
        if self.cerrar:
            self.hide_widget()
            self.emit('changed')

    def focus_out_event(self, *args):
        self.hide_widget()

    def autodate(self):
        d = datetime.date.today()
        self.calendar.select_month(d.month - 1, d.year)
        self.calendar.select_day(d.day)
        self.update_entry()

    def set_date(self, d):
        try:
            d.month
        except:
            d = datetime.datetime.strptime(d, '%Y-%m-%d')
        self.calendar.select_month(d.month - 1, d.year)
        self.calendar.select_day(d.day)
        self.update_entry()

    def add_day(self, d):
        self.currentDate += datetime.timedelta(d)
        self.set_date(self.currentDate)


class FechaSpin(gtk.HBox):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ())
        }

    def __init__(self):
        super(FechaSpin, self).__init__(False, 0)
        self.set_size_request(90, 30)
        self.year = gtk.SpinButton(digits=0)
        self.year.set_range(1900, 2100)
        self.year.set_increments(1, 2)
        self.year.set_wrap(False)
        self.month = gtk.SpinButton(digits=0)
        self.month.set_range(1, 12)
        self.month.set_increments(1, 2)
        self.month.set_wrap(True)
        self.month.connect('wrapped', self.wrap_mes)
        self.month.set_size_request(45, 25)
        self.day = gtk.SpinButton(digits=0)
        self.day.set_range(1, 31)
        self.day.set_increments(1, 2)
        self.day.set_wrap(True)
        self.day.connect('wrapped', self.wrap_dia)
        self.day.set_size_request(45, 25)
        self.clear = Button('limpiar.png', None, 16)
        self.pack_start(self.day, False, False, 0)
        self.pack_start(gtk.Label('/'), False, False, 0)
        self.pack_start(self.month, False, False, 0)
        self.pack_start(gtk.Label('/'), False, False, 0)
        self.pack_start(self.year, False, False, 0)
        self.pack_start(self.clear, False, False, 0)
        self.clear.connect('clicked', self.limpiar)
        self.month.connect('change-value', self.cambio_mes)
        self.day.connect('button-press-event', self.habilitar)
        self.month.connect('button-press-event', self.habilitar)
        self.year.connect('button-press-event', self.habilitar)
        self.habilitado = True
        self.set(datetime.date.today())

    def cambio_mes(self, *args):
        mes = self.month.get_value()
        year = self.year.get_value()
        if mes == 2:
            if year % 4:
                self.day.set_range(1, 28)
            else:
                self.day.set_range(1, 29)
        elif mes < 8:
            if mes % 2:
                self.day.set_range(1, 31)
            else:
                self.day.set_range(1, 30)
        else:
            if mes % 2:
                self.day.set_range(1, 30)
            else:
                self.day.set_range(1, 31)

    def wrap_mes(self, *args):
        mes = self.month.get_value()
        if mes == 1:
            self.year.spin(gtk.SPIN_STEP_FORWARD)
        else:
            self.year.spin(gtk.SPIN_STEP_BACKWARD)

    def wrap_dia(self, *args):
        dia = self.day.get_value()
        if dia == 1:
            self.month.spin(gtk.SPIN_STEP_FORWARD)
        else:
            self.month.spin(gtk.SPIN_STEP_BACKWARD)

    def get(self):
        if self.year.get_value_as_int() == 0:
            return None
        return datetime.date(self.year.get_value_as_int(),
            self.month.get_value_as_int(), self.day.get_value_as_int())

    def set(self, date):
        if date is None:
            y, m, d = (0, 0, 0)
            self.day.set_range(0, 0)
            self.month.set_range(0, 0)
            self.year.set_range(0, 0)
            self.habilitado = False
        else:
            y, m, d = str(date).split('-')
        self.year.set_value(float(y))
        self.month.set_value(float(m))
        self.day.set_value(float(d))

    def habilitar(self, *args):
        if not self.habilitado:
            self.habilitado = True
            self.year.set_range(1900, 2100)
            self.month.set_range(1, 12)
            self.day.set_range(1, 31)
            self.set(datetime.date.today())

    def limpiar(self, *args):
        self.set(None)


class ComboBox(gtk.Button):

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ())
        }

    def __init__(self, liststore=(str, int)):
        super(ComboBox, self).__init__()
        self.column = 1
        self.lista = []
        self.connect('button-press-event', self.on_click)
        self.menu = gtk.Menu()
        self.label = gtk.Label()
        self.hbox = gtk.HBox(False, 0)
        self.add(self.hbox)
        self.hbox.pack_start(self.label)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def on_click(self, widget, event):
        self.menu.popup(None, None, None, event.button, event.time)
        self.menu.show_all()

    def set_lista(self, lista):
        self.label.set_text('-')
        self.lista = lista
        del self.menu
        self.menu = gtk.Menu()
        for l in lista:
            item = gtk.MenuItem(l[0])
            item.connect('activate', self.change, l[self.column])
            self.menu.append(item)
        if len(lista) != 0:
            self.set_id(lista[0][self.column])
            self.emit('changed')

    def change(self, menu, i):
        self.set_id(i)

    def set_id(self, i):
        for row in self.lista:
            if row[self.column] == i:
                self.label.set_markup(row[0])
                self.id = row[self.column]
                self.emit('changed')
                return True
        return False

    def get_id(self):
        if len(self.lista) == 0:
            return False
        return self.id

    def add_item(self, item):
        if self.set_id(item[self.column]):
            return
        else:
            self.lista.append(item)
            self.set_id(item[self.column])
            menuitem = gtk.MenuItem(item[0])
            menuitem.connect('activate', self.change, item[self.column])
            self.menu.append(menuitem)

    def prepend_item(self, item):
        self.lista.prepend(item)

    def get_item(self):
        if len(self.lista) == 0:
            return False
        for l in self.lista:
            if l[self.column] == self.id:
                return l

    def get_text(self):
        return self.label.get_text()


class ComboBoxBack(gtk.ComboBox):

    def __init__(self, liststore=(str, int)):
        self.lista = gtk.ListStore(*liststore)
        super(ComboBox, self).__init__(self.lista)
        cell = gtk.CellRendererText()
        self.pack_start(cell, False)
        self.add_attribute(cell, 'text', 0)

    def set_lista(self, lista):
        self.lista.clear()
        for item in lista:
            self.lista.append(item)
        if len(lista) != 0:
            self.set_id(lista[0][1])

    def set_id(self, id):
        for row in self.lista:
            if row[1] == id:
                self.set_active_iter(row.iter)
                return True
        return False

    def get_id(self):
        if len(self.lista) == 0:
            return False
        path = self.get_active()
        return self.lista[path][1]

    def add_item(self, item):
        if self.set_id(item[1]):
            return
        else:
            self.lista.append(item)
            self.set_id(item[1])

    def prepend_item(self, item):
        self.lista.prepend(item)

    def get_item(self):
        if len(self.lista) == 0:
            return False
        path = self.get_active()
        return self.lista[path]

    def get_text(self):
        path = self.get_active()
        return self.lista[path][0]


class Hora(Entry):
    __gsignals__ = {
        'enter': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,)),
        'escape': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ()),
        'cambio': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT,))}

    def __init__(self):
        super(Hora, self).__init__(5)
        self.set_text('--:--')
        self.set_width_chars(5)
        self.spin_h = gtk.SpinButton(digits=0)
        self.spin_m = gtk.SpinButton(digits=0)
        self.spin_h.set_range(0, 23)
        self.spin_m.set_range(0, 59)
        self.spin_h.set_increments(1, 2)
        self.spin_m.set_increments(1, 2)
        self.spin_h.set_wrap(True)
        self.spin_m.set_wrap(True)
        self.spin_m.connect('wrapped', self.wrap_min)
        self.connect('scroll-event', self.spin_mouse)
        self.connect('activate', self.on_enter)
        self.connect('key-press-event', self.key_press)
        self.connect('key-release-event', self.spin_key)
        self.date = datetime.date.today()
        self.spin = True

    def set_time(self, t):
        txt = str(t)
        l = txt.split(':')
        if len(l) == 3:
            h, m, s = l
        else:
            h, m = l
        self.spin_h.set_value(float(h))
        self.spin_m.set_value(float(m))
        self.set_text(h.zfill(2) + ':' + m.zfill(2))

    def set_date(self, d):
        self.date = d

    def set_datetime(self, dt):
        self.set_date(dt.date())
        self.set_time(dt.time())

    def set_actual(self):
        t = time.localtime()
        h = t.tm_hour
        m = t.tm_min
        d = datetime.timedelta(0, seconds=(h * 60 + m) * 60)
        self.set_time(d)

    def get_time(self):
        h = self.spin_h.get_value_as_int()
        m = self.spin_m.get_value_as_int()
        return datetime.time(h, m)

    def get_datetime(self):
        return datetime.datetime.combine(self.date, self.get_time())

    def on_enter(self, *args):
        txt = self.get_text()
        lst = txt.split(':')
        try:
            self.spin_m.set_value(float(lst[1]))
            self.spin_h.set_value(float(lst[0]))
            self.update()
        except:
            Alerta('Error', 'error.png', 'Hora inválida')
        else:
            self.emit('enter', self.get_time())

    def key_press(self, widget, event):
        key = event.keyval
        if (48 <= key and key <= 57) or (65456 <= key and key <= 65465) or (
            key == 65361 or key == 65363 or key == 65293) or (
                key == 65421 or key == 65307 or key == 65288 or key == 65535):
                 # return = 65293 intro= 65421 escape=65307
            return False  # escribir
        else:
            return True  # terminar señal

    def spin_key(self, widget, event):
        key = event.keyval
        txt = self.get_text()
        cur = self.get_property('cursor-position')
        pos = txt.find(':')
        self.spin = False
        if cur > pos:
            spin = self.spin_m
        else:
            spin = self.spin_h
        if key == 65361:  # izquierda
            if pos == -1:
                return False
            else:
                self.select_region(0, pos)
        elif key == 65363:  # derecha
            if pos == -1:
                return False
            else:
                self.select_region(pos + 1, len(txt))
        elif key == 65362:  # arriba
            spin.spin(gtk.SPIN_STEP_FORWARD)
            self.spin = True
            self.update(seleccionar=False)
        elif key == 65364:  # abajo
            self.spin = True
            spin.spin(gtk.SPIN_STEP_BACKWARD)
            self.update(seleccionar=False)
        elif (48 <= key and key <= 57) or (65456 <= key and key <= 65465):
            # numeros, teclado numerico, backspace=65288, delete=65535
            lst = txt.split(':')
            if len(lst) == 2:
                h = float(lst[0])
                m = float(lst[1])
                if h > 23 or m > 59:
                    self.update()
                else:
                    self.spin_m.set_value(float(lst[1]))
                    self.spin_h.set_value(float(lst[0]))
                    if cur > pos:
                        if len(lst[1]) == 2:
                            self.update()
                        elif m > 5:
                            self.update()
                    else:
                        if len(lst[0]) == 2:
                            self.update()
                        elif h > 2:
                            self.update()
            else:
                h = int(txt)
                self.spin_h.set_value(float(h))
                self.spin_m.set_value(float(0))
                if h < 3:
                    self.set_text(txt + ':00')
                    self.set_position(1)
                else:
                    self.update()
                    self.select_region(3, 5)
        elif key == 65293 or 65421:
            return True
        elif key == 65307:
            self.emit('escape')

    def spin_mouse(self, widget, event):
        cur = self.get_property('cursor-position')
        txt = self.get_text()
        pos = txt.find(':')
        if cur > pos:
            spin = self.spin_m
        else:
            spin = self.spin_h
        if event.direction == gtk.gdk.SCROLL_UP:
            spin.spin(gtk.SPIN_STEP_FORWARD)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            spin.spin(gtk.SPIN_STEP_BACKWARD)
        self.update()

    def update(self, seleccionar=True):
        cur = self.get_property('cursor-position')
        h = str(self.spin_h.get_value_as_int()).zfill(2)
        m = str(self.spin_m.get_value_as_int()).zfill(2)
        self.set_text(h + ':' + m)
        txt = self.get_text()
        pos = txt.find(':')
        l = len(txt)
        if cur > pos:
            m = int(m)
            if self.spin:
                self.select_region(pos + 1, l)
            elif m > 59:
                self.select_region(pos + 1, l)
            elif m > 5:
                #self.select_region(0, pos)
                self.spin = False
        else:
            h = int(h)
            if self.spin:
                self.select_region(0, pos)
            elif h > 23:
                self.select_region(0, pos)
            elif h > 2:
                self.spin = False
        if seleccionar:
            self.select_region(pos + 1, l)
        self.emit('cambio', self.get_time())

    def wrap_min(self, spin):
        if self.spin_m.get_value_as_int() == 0:
            self.spin_h.spin(gtk.SPIN_STEP_FORWARD)
        else:
            self.spin_h.spin(gtk.SPIN_STEP_BACKWARD)


class Button(gtk.Button):

    def __init__(self, archivo, string=None, size=24):
        super(Button, self).__init__()
        self.hbox = gtk.HBox(False, 0)
        path = 'images/PNG-%d/' % size
        if not archivo is None:
            self.imagen = gtk.Image()
            self.imagen.set_from_file(path + archivo)
            self.hbox.pack_start(self.imagen, True, True, 0)
        if not string is None:
            self.label = gtk.Label()
            self.label.set_markup(string)
            self.label.set_use_underline(True)
            self.hbox.pack_start(self.label, True, True, 0)
        self.add(self.hbox)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def set_text(self, text):
        self.label.set_markup(text)

    def get_text(self):
        return self.label.get_text()

    def vertical(self):
        self.hbox.set_orientation(gtk.ORIENTATION_VERTICAL)

    def set_imagen(self, archivo, size=24):
        path = 'images/PNG-%d/' % size
        self.imagen.set_from_file(path + archivo)

    def label_visible(self, visible):
        if visible:
            self.label.show()
        else:
            self.label.hide()


class ButtonDoble(gtk.Button):

    def __init__(self, file1, file2, motivo, size=16):
        super(ButtonDoble, self).__init__()
        hbox = gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        path = 'images/PNG-%d/' % size
        imagen = gtk.Image()
        imagen.set_from_file(path + file1)
        self.hbox1.pack_start(imagen, True, True, 0)
        path = 'images/PNG-%d/' % size
        imagen = gtk.Image()
        imagen.set_from_file(path + file2)
        self.hbox2.pack_start(imagen, True, True, 0)
        self.set(False, 'No seleccionado')
        self._motivo = motivo
        self.ok = False
        self.connect('clicked', self.click)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def set(self, ok, motivo=None):
        self.ok = ok
        if motivo is None:
            self.motivo = self._motivo
        else:
            self.motivo = motivo
        if ok:
            self.hbox1.hide_all()
            self.hbox2.show_all()
            self.set_sensitive(True)
        else:
            self.hbox1.show_all()
            self.hbox2.hide_all()
            self.set_sensitive(False)

    def click(self, *args):
        Alerta('Motivo', 'error.png', self.motivo)


class ButtonDoblePersonal(gtk.Button):

    def __init__(self, http):
        super(ButtonDoblePersonal, self).__init__()
        self.http = http
        hbox = gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        self.hbox3 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox3, False, False, 0)
        path = 'images/PNG-16/'
        imagen = gtk.Image()
        imagen.set_from_file(path + 'no_castigado.png')
        self.hbox1.pack_start(imagen, True, True, 0)
        imagen = gtk.Image()
        imagen.set_from_file(path + 'warning.png')
        self.hbox2.pack_start(imagen, True, True, 0)
        imagen = gtk.Image()
        imagen.set_from_file(path + 'castigado.png')
        self.hbox3.pack_start(imagen, True, True, 0)
        self.set(None)
        self.ok = False
        self.t_id = 0
        self.motivo = ''
        self.connect('clicked', self.click)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def set(self, ok, i=0):
        self.t_id = i
        self.hbox1.hide_all()
        self.hbox2.hide_all()
        self.hbox3.hide_all()
        self.ok = ok
        if ok:
            self.hbox3.show_all()
        elif ok is None:
            self.hbox1.show_all()
        else:
            self.hbox2.show_all()

    def click(self, *args):
        datos = {'trabajador_id': self.t_id}
        respuesta = self.http.load('datos-personal', datos)
        if respuesta:
            Alerta(respuesta['nombre'], '../../outs/imagen.png', respuesta['motivo'])


class ButtonDobleBloquear(gtk.Button):

    def __init__(self, file1, file2, size=16):
        super(ButtonDobleBloquear, self).__init__()
        hbox = gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        path = 'images/PNG-%d/' % size
        imagen = gtk.Image()
        imagen.set_from_file(path + file1)
        self.hbox1.pack_start(imagen, True, True, 0)
        path = 'images/PNG-%d/' % size
        imagen = gtk.Image()
        imagen.set_from_file(path + file2)
        self.hbox2.pack_start(imagen, True, True, 0)
        self.set(False)
        self.ok = False
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def set(self, ok):
        self.ok = ok
        if ok:
            self.hbox1.hide_all()
            self.hbox2.show_all()
        else:
            self.hbox1.show_all()
            self.hbox2.hide_all()

class ButtonTwist(gtk.Button):

    def __init__(self, file1, file2):
        super(ButtonTwist, self).__init__()
        hbox = gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        imagen = gtk.Image()
        imagen.set_from_file('images/PNG-16/' + file1)
        self.hbox1.pack_start(imagen, True, True, 0)
        imagen = gtk.Image()
        imagen.set_from_file('images/PNG-16/' + file2)
        self.hbox2.pack_start(imagen, True, True, 0)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#328aa4'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

    def activar(self):
        self.hbox1.hide_all()
        self.hbox2.show_all()

    def desactivar(self):
        self.hbox1.show_all()
        self.hbox2.hide_all()

class Mensaje(gtk.Window):

    def __init__(self, parent, titulo, imagen, mensaje):
        super(Mensaje, self).__init__(gtk.WINDOW_POPUP)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        hbox.pack_start(label, False, False, 5)
        self.show_all()

    def cerrar(self, *args):
        self.destroy()


class Alerta(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(Alerta, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        hbox.pack_start(label, False, False, 5)
        self.but_salir = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(self.but_salir, gtk.RESPONSE_CANCEL)
        self.set_focus(self.but_salir)
        self.iniciar()

    def iniciar(self):
        self.show_all()
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class AlertaTwist(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(AlertaTwist, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        hbox.pack_start(label, False, False, 5)
        self.but_salir = Button('aceptar.png', "_Aceptar")
        self.action_area.pack_start(self.but_salir, False, False, 0)
        self.but_salir.connect('clicked', self.cerrar)
        self.set_focus(self.but_salir)
        self.show_all()

    def cerrar(self, *args):
        self.destroy()


class Mensaje(gtk.Dialog):

    def __init__(self, titulo, imagen, mensajes):
        super(Mensaje, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        print parent
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        self.label = []
        self.count = 0
        for m in mensajes:
            label = gtk.Label()
            label.set_markup(m)
            self.label.append(label)
            hbox.pack_start(label, False, False, 5)
        if len(mensajes) == 0:
            label = gtk.Label()
            label.set_markup('No hay coincidencias para la búsqueda')
            self.label.append(label)
            hbox.pack_start(label, False, False, 5)
        self.but_atras = Button('atras.png', u"_Atrás")
        self.action_area.pack_start(self.but_atras, False, False, 0)
        self.but_siguiente = Button('siguiente.png', u"_Siguiente")
        self.action_area.pack_start(self.but_siguiente, False, False, 0)
        self.but_salir = Button('cancelar.png', "_Cancelar")
        self.add_action_widget(self.but_salir, gtk.RESPONSE_CANCEL)
        self.but_atras.connect('clicked', self.atras)
        self.but_siguiente.connect('clicked', self.siguiente)
        self.set_focus(self.but_salir)
        self.iniciar()

    def atras(self, *args):
        self.but_siguiente.set_sensitive(True)
        self.label[self.count].hide()
        self.count -= 1
        self.label[self.count].show()
        if self.count == 0:
            self.but_atras.set_sensitive(False)

    def siguiente(self, *args):
        self.but_atras.set_sensitive(True)
        self.label[self.count].hide()
        self.count += 1
        self.label[self.count].show()
        if self.count == len(self.label) - 1:
            self.but_siguiente.set_sensitive(False)

    def iniciar(self):
        self.show_all()
        for l in self.label:
            l.hide()
        self.label[0].show()
        self.but_atras.set_sensitive(False)
        if len(self.label) == 1:
            self.but_siguiente.set_sensitive(False)
        self.run()
        self.cerrar()

    def cerrar(self, *args):
        self.destroy()


class Alerta_SINO(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, default=True):
        super(Alerta_SINO, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        print parent
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        hbox.pack_start(label, False, False, 5)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        if default:
            self.set_focus(self.but_ok)
        else:
            self.set_focus(but_salir)

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class AlertaAuto(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, default=True):
        super(AlertaAuto, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        hbox.pack_start(label, False, False, 5)
        but_salir = Button('aceptar.png', "_Aceptar")
        self.action_area.pack_start(but_salir, False, False, 0)
        but_salir.connect('clicked', self.cerrar)
        self.set_focus(but_salir)
        self.show_all()

    def cerrar(self, *args):
        self.destroy()


class Alerta_Dia_Hora(gtk.Dialog):
    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Dia_Hora, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.fecha = Fecha()
        vbox.pack_start(self.fecha, False, False, 0)
        self.hora = Hora()
        vbox.pack_start(self.hora, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.hora.connect('enter', lambda s, w: self.but_ok.clicked())
        self.hora.connect('escape', lambda s, w: but_salir.clicked())
        self.set_focus(self.hora)

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            return self.hora.get_time()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_FechaNumero(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, digitos=3, decimal=False, default=''):
        super(Alerta_FechaNumero, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        print parent
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.decimal = decimal
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.dia = Fecha()
        vbox.pack_start(self.dia, False, False, 0)
        if decimal:
            self.entry = Texto(digitos)
        else:
            self.entry = Numero(digitos)
            self.entry.connect('ok', self.entry_ok)
            self.entry.connect('error', self.entry_error)
        vbox.pack_start(self.entry, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.entry.connect('activate', self.activate)
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.entry.set_text(default)

    def activate(self, *args):
        try:
            if self.decimal:
                float(self.entry.get_text())
            else:
                int(self.entry.get_text())
        except:
            pass
        else:
            self.but_ok.clicked()

    def entry_ok(self, *args):
        self.but_ok.set_sensitive(True)

    def entry_error(self, *args):
        self.but_ok.set_sensitive(False)
        self.entry.grab_focus()

    def iniciar(self):
        self.show_all()
        text = self.entry.get_text()
        self.entry.select_region(0, len(text))
        self.set_focus(self.entry)
        if self.run() == gtk.RESPONSE_OK:
            return self.dia.get_date(), self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Dia(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Dia, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.dia = Fecha()
        vbox.pack_start(self.dia, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        but_ok = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(but_ok, gtk.RESPONSE_OK)
        self.set_focus(but_ok)

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            return self.dia.get_date()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Numero(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, digitos=3, decimal=False, default=''):
        super(Alerta_Numero, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        print parent
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.decimal = decimal
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        if decimal:
            self.entry = Texto(digitos)
        else:
            self.entry = Numero(digitos)
            self.entry.connect('ok', self.entry_ok)
            self.entry.connect('error', self.entry_error)
        vbox.pack_start(self.entry, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.entry.connect('activate', self.activate)
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.entry.set_text(default)

    def activate(self, *args):
        try:
            if self.decimal:
                float(self.entry.get_text())
            else:
                int(self.entry.get_text())
        except:
            pass
        else:
            self.but_ok.clicked()

    def entry_ok(self, *args):
        self.but_ok.set_sensitive(True)

    def entry_error(self, *args):
        self.but_ok.set_sensitive(False)
        self.entry.grab_focus()

    def iniciar(self):
        self.show_all()
        text = self.entry.get_text()
        self.entry.select_region(0, len(text))
        self.set_focus(self.entry)
        if self.run() == gtk.RESPONSE_OK:
            return self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Combo(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, lista, liststore=(str, int)):
        super(Alerta_Combo, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.combo = ComboBox(liststore)
        self.combo.set_lista(lista)
        vbox.pack_start(self.combo, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)

    def iniciar(self):
        self.show_all()
        self.set_focus(self.but_ok)
        if self.run() == gtk.RESPONSE_OK:
            return self.combo.get_id()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Anular_Numeros(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Anular_Numeros, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        hbox = gtk.HBox(False, 0)
        label = gtk.Label('Inicio')
        self.entry1 = Numero(6)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.entry1, False, False, 0)
        label = gtk.Label('Fin')
        self.entry2 = Numero(6)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.entry2, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.entry2.connect('ok', self.entry_ok)
        self.entry1.connect('error', self.entry_error)
        self.entry2.connect('error', self.entry_error)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.set_focus(self.entry1)

    def activate(self, entry):
        try:
            int(entry.get_text())
        except:
            pass
        else:
            self.but_ok.clicked()

    def entry_ok(self, *args):
        try:
            inicio = int(self.entry1.get_text())
            fin = int(self.entry2.get_text())
            self.but_ok.set_sensitive(inicio <= fin)
        except:
            self.but_ok.set_sensitive(False)

    def entry_error(self, entry):
        self.but_ok.set_sensitive(False)
        entry.grab_focus()

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            return (int(self.entry1.get_text()), int(self.entry2.get_text()))
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Texto(gtk.Dialog):

    def __init__(self, titulo, lista):
        super(Alerta_Texto, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.lista = lista
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(250, 100)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        self.radio = [None] * len(lista)
        for i, string in enumerate(lista):
            if i == 0:
                self.radio[i] = gtk.RadioButton(None, string, True)
            else:
                self.radio[i] = gtk.RadioButton(self.radio[0], string, True)
            self.vbox.pack_start(self.radio[i], False, False, 0)
        self.entry = Entry()
        self.entry.set_width_chars(15)
        self.vbox.pack_start(self.entry, False, False, 0)
        self.but_ok = Button('aceptar.png', "_Aceptar")
        but_salir = Button('cancelar.png', "_Cancelar")
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.entry.connect('activate', self.entry_activate)
        self.set_focus(self.entry)

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            string = self.entry.get_text()
            if string == '':
                for i, radio in enumerate(self.radio):
                    if radio.get_active():
                        string = self.lista[i]
            return string
        else:
            return False

    def entry_activate(self, *args):
        self.but_ok.clicked()

    def cerrar(self, *args):
        self.destroy()


class Alerta_Entero(gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, digitos=3):
        super(Alerta_Entero, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.entry = Entry(digitos)
        vbox.pack_start(self.entry, False, False, 0)
        but_salir = Button('cancelar.png', "_Cancelar")
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(but_salir, gtk.RESPONSE_CANCEL)
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.set_focus(self.entry)
        self.entry.connect('activate', self.activate)

    def activate(self, *args):
        try:
            int(self.entry.get_text())
        except:
            pass
        else:
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        if self.run() == gtk.RESPONSE_OK:
            return self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Login(gtk.Dialog):

    def __init__(self, http):
        super(Login, self).__init__(
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        ventanas = gtk.window_list_toplevels()
        parent = ventanas[0]
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.user = None
        self.pw = None
        self.sessionid = None
        self.set_modal(True)
        self.http = http
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title('Login')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = gtk.Image()
        image.set_from_file('images/PNG-48/login.png')
        hbox.pack_start(image, False, False, 5)
        vbox = gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = gtk.Label()
        label.set_markup('Ingrese su usuario y contraseña')
        vbox.pack_start(label, False, False, 5)
        self.usuario = Entry()
        vbox.pack_start(self.usuario, False, False, 0)
        self.usuario.connect('activate', lambda w: self.set_focus(self.password))
        self.password = Entry()
        self.password.set_visibility(False)
        vbox.pack_start(self.password, False, False, 0)
        self.password.connect('activate', lambda w: self.set_focus(self.clave))
        self.clave = Entry()
        self.clave.set_visibility(False)
        vbox.pack_start(self.clave, False, False, 0)
        self.but_aceptar = Button('aceptar.png', "_Aceptar")
        self.action_area.pack_start(self.but_aceptar, False, False, 0)
        self.but_aceptar.connect('clicked', self.comprobar)
        self.but_ok = Button('aceptar.png', "_Aceptar")
        self.add_action_widget(self.but_ok, gtk.RESPONSE_OK)
        self.clave.connect('activate', self.comprobar)
        self.set_focus(self.usuario)
        self.mac = str(getnode())
        try:
            a = os.path.abspath("outs/pdfcreator.dll")
            archivo = open(a, 'rb')
            content = archivo.read()
            archivo.close()
            js = base64.b64decode(content)
            d = json.loads(js)
            usuario, password = d[self.mac]
            self.usuario.set_text(usuario)
            self.password.set_text(password)
        except:
            pass

    def comprobar(self, *args):
        print 'LOGIN Comprobar'
        self.user = self.usuario.get_text()
        self.pw = self.password.get_text()
        self.cl = self.clave.get_text()
        self.sessionid = self.http.login(self.user, self.pw, self.cl)
        print 'LOGIN SEND'
        if self.sessionid:
            d = {self.mac: (self.user, self.pw)}
            js = json.dumps(d)
            content = base64.b64encode(js)
            a = os.path.abspath("outs/pdfcreator.dll")
            archivo = open(a, 'wb')
            archivo.write(content)
            archivo.close()
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide_all()
        print 'LOGIN'
        if self.run() == gtk.RESPONSE_OK:
            print 'LOGIN widget'
            return True
        else:
            print 'LOGN False'
            return False

    def cerrar(self, *args):
        self.destroy()


class Cell(gtk.CellRendererText):

    __gsignals__ = {'editado': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_PYOBJECT,
        (int, str))}

    def __init__(self):
        super(Cell, self).__init__()
        gtk.CellRendererText.__init__(self)
        self.connect_after('editing-started', self.edicion)

    def edicion(self, cell, editable, path):
        if isinstance(editable, gtk.Entry):
            editable.connect('key-release-event', self.key_release)
            editable.connect('key-press-event', self.key_press, path)

    def key_release(self, widget, event):
        if event.keyval == 65421 or event.keyval == 65293:
            return True

    def key_press(self, widget, event, path):
        if event.keyval == 65421 or event.keyval == 65293:
            self.emit('editado', int(path), widget.get_text())


class CellBoleto(gtk.CellRendererText):

    __gsignals__ = {'editado': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_PYOBJECT,
        (int, str)),
            'inicio': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_PYOBJECT,
        (gobject.TYPE_PYOBJECT, int))}

    def __init__(self):
        super(CellBoleto, self).__init__()
        self.reserva = False
        self.inicio = False
        self.connect_after('editing-started', self.edicion)

    def edicion(self, cell, editable, path):
        if isinstance(editable, gtk.Entry):
            editable.connect('key-release-event', self.key_release)
            editable.connect('key-press-event', self.key_press, editable, path)
            editable.connect_after('visibility-notify-event',
                self.iniciar, path)
            return True

    def iniciar(self, editable, event, path):
        self.emit('inicio', editable, int(path))
        editable.set_max_length(6)
        editable.select_region(3, 6)

    def key_release(self, widget, event):
        text = widget.get_text()
        l = len(text)
        if event.keyval == 65421 or event.keyval == 65293:
            # intro= 65421 return = 65293
            return True
        elif event.keyval == 65361:  # izquierda
            if self.reserva:
                widget.set_text(str(self.reserva).zfill(6))
                widget.select_region(3, l)
            else:
                Alerta('Sin Reserva', 'error_numero.png',
                    'No hay reserva de este boleto')
        elif event.keyval == 65363:  # derecha
            widget.set_text(str(self.inicio))
            widget.select_region(3, l)

    def key_press(self, widget, event, editable, path):
        if event.keyval == 65421 or event.keyval == 65293:
            txt = editable.get_text()
            try:
                int(txt)
            except:
                return True
            else:
                self.emit('editado', int(path), editable.get_text())
                return True


class CellHora(gtk.CellRendererText):

    __gsignals__ = {'editado': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_PYOBJECT,
        (int, str)),
            'inicio': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_PYOBJECT,
        (gobject.TYPE_PYOBJECT, int))}

    def __init__(self):
        super(CellHora, self).__init__()
        self.reserva = False
        self.inicio = False
        self.connect_after('editing-started', self.edicion)

    def edicion(self, cell, editable, path):
        if isinstance(editable, gtk.Entry):
            editable.connect('activate', self.on_enter, editable, path)
            editable.connect('key-release-event', self.key_release)
            editable.connect('key-press-event', self.key_press)
            editable.connect_after('visibility-notify-event',
                self.iniciar, path)
            return True

    def iniciar(self, editable, event, path):
        editable.set_max_length(5)
        editable.select_region(0, 2)
        editable.set_text('00:00')
        editable.set_width_chars(5)
        self.spin_h = gtk.SpinButton(digits=0)
        self.spin_m = gtk.SpinButton(digits=0)
        self.spin_h.set_range(0, 23)
        self.spin_m.set_range(0, 59)
        self.spin_h.set_increments(1, 2)
        self.spin_m.set_increments(1, 2)
        self.spin_h.set_wrap(True)
        self.spin_m.set_wrap(True)
        self.spin_m.connect('wrapped', self.wrap_min)
        self.spin = False
        editable.connect('scroll-event', self.spin_mouse)

    def wrap_min(self, spin):
        if self.spin_m.get_value_as_int() == 0:
            self.spin_h.spin(gtk.SPIN_STEP_FORWARD)
        else:
            self.spin_h.spin(gtk.SPIN_STEP_BACKWARD)

    def spin_mouse(self, widget, event):
        cur = widget.get_property('cursor-position')
        txt = widget.get_text()
        pos = txt.find(':')
        if cur > pos:
            spin = self.spin_m
        else:
            spin = self.spin_h
        if event.direction == gtk.gdk.SCROLL_UP:
            spin.spin(gtk.SPIN_STEP_FORWARD)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            spin.spin(gtk.SPIN_STEP_BACKWARD)
        self.update(widget)

    def update(self, widget):
        cur = widget.get_property('cursor-position')
        h = str(self.spin_h.get_value_as_int()).zfill(2)
        m = str(self.spin_m.get_value_as_int()).zfill(2)
        widget.set_text(h + ':' + m)
        txt = widget.get_text()
        pos = txt.find(':')
        l = len(txt)
        if cur > pos:
            m = int(m)
            if self.spin:
                widget.select_region(pos + 1, l)
            elif m > 59:
                widget.select_region(pos + 1, l)
            elif m > 5:
                widget.select_region(0, pos)
                self.spin = False
        else:
            h = int(h)
            if self.spin:
                widget.select_region(0, pos)
            elif h > 23:
                widget.select_region(0, pos)
            elif h > 2:
                widget.select_region(pos + 1, l)
                self.spin = False

    def key_press(self, widget, event):
        key = event.keyval
        if (48 <= key and key <= 57) or (65456 <= key and key <= 65465) or (
            key == 65361 or key == 65363 or key == 65293) or (
                key == 65421 or key == 65307 or key == 65288 or key == 65535):
                 # return = 65293 intro= 65421 escape=65307
            return False  # escribir
        else:
            return True  # terminar señal

    def on_enter(self, widget, editable, path):
        self.emit('editado', int(path), editable.get_text())
        return True

    def key_release(self, widget, event):
        key = event.keyval
        txt = widget.get_text()
        cur = widget.get_property('cursor-position')
        pos = txt.find(':')
        self.spin = False
        if cur > pos:
            spin = self.spin_m
        else:
            spin = self.spin_h
        if key == 65361:  # izquierda
            if pos == -1:
                return False
            else:
                widget.select_region(0, pos)
        elif key == 65363:  # derecha
            if pos == -1:
                return False
            else:
                widget.select_region(pos + 1, len(txt))
        elif key == 65362:  # arriba
            spin.spin(gtk.SPIN_STEP_FORWARD)
            self.spin = True
            self.update(widget)
        elif key == 65364:  # abajo
            self.spin = True
            spin.spin(gtk.SPIN_STEP_BACKWARD)
            self.update(widget)
        elif (48 <= key and key <= 57) or (65456 <= key and key <= 65465):
            # numeros, teclado numerico, backspace=65288, delete=65535
            lst = txt.split(':')
            if len(lst) == 2:
                h = float(lst[0])
                m = float(lst[1])
                if h > 23 or m > 59:
                    self.update(widget)
                else:
                    self.spin_m.set_value(float(lst[1]))
                    self.spin_h.set_value(float(lst[0]))
                    if cur > pos:
                        if len(lst[1]) == 2:
                            self.update(widget)
                        elif m > 5:
                            self.update(widget)
                    else:
                        if len(lst[0]) == 2:
                            self.update(widget)
                        elif h > 2:
                            self.update(widget)
            else:
                h = int(txt)
                self.spin_h.set_value(float(h))
                self.spin_m.set_value(float(0))
                if h < 3:
                    widget.set_text(txt + ':00')
                    widget.set_position(1)
                else:
                    self.update(widget)
                    widget.select_region(3, 5)

class Numero(Entry):

    __gsignals__ = {'ok': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ()),
        'error': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ()),
        'cancel': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ())}

    def __init__(self, n):
        super(Numero, self).__init__(n)
        if n > 15:
            n = 15
        self.set_width_chars(n)
        self.connect('key-press-event', self.key_press)
        self.connect('key-release-event', self.key_release)

    def key_press(self, widget, event):
        k = event.keyval
        if (48 <= k and k <= 57) or (65456 <= k and k <= 65465):
            # numeros
            return False
        elif k == 65288 or k == 65535 or k == 65293 or k == 65421:
            # backspace=65288, delete=65535, return = 65293, intro= 65421
            return False
        elif k == 65307:
            self.emit('cancel')
            return False
        elif k == 65361 or k == 65363 or k == 65289:  # izquierda derecha tab
            return False
        elif k == 65360 or k == 65367:  # inicio fin
            return False
        else:
            return True

    def key_release(self, widget, event):
        txt = self.get_text()
        if txt == '':
            self.emit('error')
        else:
            self.emit('ok')
        if event.keyval == 65293 or event.keyval == 65421:
            w = self.get_toplevel()
            w.do_move_focus(w, gtk.DIR_TAB_FORWARD)

    def get(self):
        txt = self.get_text()
        return txt

    def get_int(self):
        txt = self.get_text()
        if txt == '':
            return 0
        return int(txt)

    def set(self, n):
        if n is None:
            return
        self.set_text(str(n))


class Texto(Entry):

    def __init__(self, n, up=True):
        super(Texto, self).__init__(n)
        if n > 15:
            n = 15
        self.set_width_chars(n)
        self.up = up
        self.connect('key-release-event', self.on_activate)

    def get(self):
        txt = unicode(self.get_text(), 'utf-8')
        if self.up:
            return txt.upper()
        else:
            return txt

    def set(self, text):
        if text is None:
            return
        self.set_text(text)

    def on_activate(self, widget, event):
        if event.keyval == 65421 or event.keyval == 65293:
            w = self.get_toplevel()
            w.do_move_focus(w, gtk.DIR_TAB_FORWARD)


class ToolButton(gtk.ToolButton):

    def __init__(self, texto, imagen, funcion):
        icon = gtk.Image()
        icon.set_from_file('images/toolbar/' + imagen)
        super(ToolButton, self).__init__(icon, texto)
        self.set_tooltip_text(texto)
        self.connect('clicked', funcion)

class Toolbar(gtk.HBox):

    def __init__(self, herramientas):
        super(Toolbar, self).__init__()
        self.buttons = []
        for h in herramientas:
            b = ToolButton(h[0], h[1], h[2])
            self.pack_start(b, False, False, 0)
            self.buttons.append(b)

    def add_button(self, texto, imagen, funcion):
        b = ToolButton(texto, imagen, funcion)
        self.pack_start(b, False, False, 0)

    def set_imagen_label(self, i, imagen, label):
        b = self.buttons[i]
        icon = gtk.Image()
        icon.set_from_file('images/toolbar/' + imagen)
        b.set_icon_widget(icon)
        icon.show()
        b.set_label(label)

    def get_label(self, i):
        b = self.buttons[i]
        return b.get_label()


class VBox(gtk.VBox):

    def __init__(self):
        super(VBox, self).__init__(False, 5)

    def get(self):
        return False

    def set(self, id):
        return False


class Tabla(gtk.Table):

    def __init__(self):
        super(Tabla, self).__init__()
        self.y = 0

    def attach_label(self, l):
        label = gtk.Label(l)
        label.set_size_request(75, 25)
        label.set_alignment(0, 0.5)
        self.attach(label, 0, 1, self.y, self.y + 1, gtk.EXPAND | gtk.FILL,
            gtk.EXPAND | gtk.FILL)

    def attach_widget(self, w):
        self.attach(w, 1, 2, self.y, self.y + 1,
            gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        self.y += 1

    def get(self):
        return False

    def set(self, id):
        return False


class TreeView(gtk.TreeView):

    def __init__(self, model):
        super(TreeView, self).__init__(model)
        self.set_reorderable(False)
        self.set_enable_tree_lines(True)
        self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)
        self.set_rules_hint(True)
        self.set_name("enruta-treeview")

        #GtkTreeView::even_row_color = "#A0DB8E"
                #GtkTreeView::odd_row_color = "#C0FBAE"
        #style = self.get_style().copy()
        #pixbuf = gtk.gdk.pixbuf_new_from_file("images/fondo-treeview.jpg")
        #pixmap, mask = pixbuf.render_pixmap_and_mask()
        #for i in range(5):
            #style.bg_pixmap[i] = pixmap
        #self.set_style(style)


class TreeViewColumn(gtk.TreeViewColumn):

    def __init__(self, columna):
        super(TreeViewColumn, self).__init__()
        self.columna = columna

    def encabezado(self):
        header = gtk.Label()
        header.show()
        if os.name == 'nt':
            header.set_markup('<span foreground="#000" weight="bold">%s</span>' % self.columna)
        else:
            header.set_markup('<span foreground="#FFFFFF" weight="bold">%s</span>' % self.columna)
        self.set_widget(header)
        align = header.get_parent()
        hbox = align.get_parent()
        button = hbox.get_parent()
        if os.name == 'nt':
            button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        else:
            button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#328aa4'))
            button.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#328aa4'))


class Notebook(gtk.Notebook):

    def __init__(self):
        super(Notebook, self).__init__()

        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.modify_bg(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse('#e5e8e8'))
        self.modify_bg(gtk.STATE_SELECTED, gtk.gdk.color_parse('#f8fbfc'))
        self.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse('#e5f1f4'))

class Statusbar(gtk.Label):

    def __init__(self):
        super(Statusbar, self).__init__()
        self.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFFFFF'))
        self.set_alignment(0, 0.5)

    def push(self, texto):
        self.set_markup(texto)


class Window(gtk.Window):

    def __init__(self, titulo):
        super(Window, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_title(titulo)
        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)
        self.action_area = gtk.HBox(False, 0)
        self.vbox.pack_end(self.action_area, False, False, 0)
        self.connect("delete_event", self.cerrar)

    def crear_boton(self, imagen, label, funcion):
        boton = Button(imagen, label)
        boton.connect('clicked', funcion)
        self.action_area.pack_end(boton, False, False, 0)
        return boton

    def cerrar(self, *args):
        self.destroy()

if __name__ == '__main__':
    w = gtk.Window()
    h = Hora()
    h.set_time(datetime.time(0, 0))
    w.add(h)
    w.show_all()
    l = Login(2)
    l.iniciar()
    gtk.main()

gtk.rc_parse_string("""
    style "enruta-treestyle" {
        GtkTreeView::even_row_color = "#e5f1f4"
        GtkTreeView::odd_row_color = "#f8fbfc"
        GtkTreeView::allow-rules = 1
    }
    widget "*.enruta-treeview" style "enruta-treestyle"

    style "disponibles-treestyle" {
        GtkTreeView::even_row_color = "#e5f1f4"
        GtkTreeView::odd_row_color = "#f8fbfc"
        GtkTreeView::allow-rules = 1
    }
    widget "*.disponibles-treeview" style "disponibles-treestyle"

    style "excluidos-treestyle" {
        GtkTreeView::even_row_color = "#e5f1f4"
        GtkTreeView::odd_row_color = "#f8fbfc"
        GtkTreeView::allow-rules = 1
    }
    widget "*.excluidos-treeview" style "excluidos-treestyle"

    style "vueltas-treestyle" {
        GtkTreeView::even_row_color = "#e5f1f4"
        GtkTreeView::odd_row_color = "#f8fbfc"
        GtkTreeView::allow-rules = 1
    }
    widget "*.vueltas-treeview" style "vueltas-treestyle"
""")
gobject.type_register(Cell)