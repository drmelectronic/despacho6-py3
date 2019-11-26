##! /usr/bin/python
# -*- coding: utf-8 -*-
# To change this template, choose Tools | Templates
# and open the template in the editor.
import models

__author__ = "daniel"
__date__ = "$06-mar-2012 16:15:38$"
import os, sys
if os.name == 'nt':
    import win32print
import Impresion
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import GObject
import datetime
import os
import time
import json
import base64
from uuid import getnode
import xlrd

class Entry(Gtk.Entry):

    def __init__(self, n=None):
        super(Entry, self).__init__()
        # self.modify_base(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))

        # self.modify_base(Gtk.StateType(0), Gdk.color_parse('#FFFFFF'))  # NORMAL
        # self.modify_base(Gtk.StateType(4), Gdk.color_parse('#e5e8e8'))  # INSENSITIVE
        # self.modify_base(Gtk.StateType(1), Gdk.color_parse('#e5e8e8'))  # active
        # self.modify_base(Gtk.StateType(3), Gdk.color_parse('#f8fbfc'))  # selected
        # self.modify_base(Gtk.StateType(2), Gdk.color_parse('#e5f1f4'))  # prelight

        #self.modify_base(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        #self.modify_base(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        #self.modify_base(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        #self.modify_base(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))

        #self.modify_text(Gtk.StateType.NORMAL, Gdk.color_parse('#000000'))
        #self.modify_text(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#FF0000'))
        #self.modify_text(Gtk.STATE_ACTIVE, Gdk.color_parse('#00FF00'))
        #self.modify_text(Gtk.STATE_SELECTED, Gdk.color_parse('#0000FF'))
        #self.modify_text(Gtk.STATE_PRELIGHT, Gdk.color_parse('#FFFF00'))

    def rojo(self):
        self.modify_base(Gtk.StateType.NORMAL,Gdk.color_parse('#FCC'))

    def blanco(self):
        self.modify_base(Gtk.StateType.NORMAL,Gdk.color_parse('#FFF'))


class Frame(Gtk.Frame):

    def __init__(self, label=None):
        super(Frame, self).__init__()
        self.set_border_width(5)
        if not label is None:
            self.set_label(label)
        self.set_property('shadow-type', Gtk.ShadowType.NONE)


class Fecha(Gtk.Button):

    __gsignals__ = {
        'changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            ())
        }

    def __init__(self):
        super(Fecha, self).__init__()
        self.cwindow = None
        self.set_size_request(90, 25)
        self.cerrar = False
        self.calendar = None
        self.connect('clicked', self.show_widget)
        self.connect('focus-out-event', self.focus_out_event)
        self.currentDate = datetime.date.today()
        text = self.currentDate.strftime('%d/%m/%Y')
        self.set_label(text)
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))

    def get_text(self):
        return self.get_label()

    def get_date(self):
        return self.currentDate

    def show_widget(self, *args):
        self.create_calendar()
        self.cwindow = Gtk.Window(Gtk.WindowType.POPUP)
        self.cwindow.set_position(Gtk.WindowPosition.MOUSE)
        self.cwindow.set_decorated(False)
        self.cwindow.set_modal(True)
        w = self.get_toplevel()
        self.cwindow.set_transient_for(w)
        self.eb = Gtk.EventBox()
        print((self.calendar.get_date()))
        self.calendar.mark_day(self.day)
        self.eb.add(self.calendar)
        self.cwindow.add(self.eb)
        self.calendar.connect('day-selected', self.update_entry)
        self.calendar.connect('button-release-event', self.close)
        self.cwindow.connect('key-release-event', self.hide_widget)
        self.cwindow.show_all()
        # self.cwindow.activate_focus()

        self.cerrar = False
        # w = self.get_toplevel()
        # w.do_move_focus(w, Gtk.DirectionType.TAB_FORWARD)

    def hide_widget(self, *args):
        if self.cwindow:
            self.cwindow.destroy()
            self.cwindow = None

    def update_entry(self, *args):
        print('update_entry')
        year, month, day = self.calendar.get_date()
        self.currentDate = datetime.date(year, month + 1, day)
        text = self.currentDate.strftime('%d/%m/%Y')
        self.set_label(text)
        if year == self.year and month + 1 == self.month:
            print('dia cambiado')
            self.cerrar = True
            self.close()
        else:
            print(('cambio de mes o año', year, month + 1, self.year, self.month))
            self.year = year
            self.month = month + 1

    def close(self, *args):
        print('close')
        if self.cerrar:
            self.hide_widget()
            self.emit('changed')

    def focus_out_event(self, *args):
        self.hide_widget()

    def autodate(self):
        d = datetime.date.today()
        self.create_calendar()
        self.calendar.select_month(d.month - 1, d.year)
        self.calendar.select_day(d.day)
        self.update_entry()

    def set_date(self, d):
        try:
            d.month
        except:
            d = datetime.datetime.strptime(d, '%Y-%m-%d')
        self.create_calendar()
        self.calendar.select_month(d.month - 1, d.year)
        self.calendar.select_day(d.day)
        self.update_entry()

    def add_day(self, d):
        self.currentDate += datetime.timedelta(d)
        self.set_date(self.currentDate)

    def create_calendar(self):
        if self.calendar is None:
            self.calendar = Gtk.Calendar()
            self.year, self.month, self.day = self.calendar.get_date()
            self.month += 1


class FechaSpin(Gtk.HBox):

    __gsignals__ = {
        'changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            ())
        }

    def __init__(self):
        super(FechaSpin, self).__init__(False, 0)
        self.set_size_request(160, 30)
        self.year = Gtk.SpinButton(digits=0)
        self.year.set_range(1900, 2100)
        self.year.set_increments(1, 2)
        self.year.set_wrap(False)
        self.month = Gtk.SpinButton(digits=0)
        self.month.set_range(1, 12)
        self.month.set_increments(1, 2)
        self.month.set_wrap(True)
        self.month.connect('wrapped', self.wrap_mes)
        self.month.set_size_request(45, 25)
        self.day = Gtk.SpinButton(digits=0)
        self.day.set_range(1, 31)
        self.day.set_increments(1, 2)
        self.day.set_wrap(True)
        self.day.connect('wrapped', self.wrap_dia)
        self.day.set_size_request(45, 25)
        self.clear = Button('delete.png', None, 16)
        self.pack_start(self.day, False, False, 0)
        self.pack_start(Gtk.Label('/'), False, False, 0)
        self.pack_start(self.month, False, False, 0)
        self.pack_start(Gtk.Label('/'), False, False, 0)
        self.pack_start(self.year, False, False, 0)
        self.pack_start(self.clear, False, False, 0)
        self.clear.connect('clicked', self.limpiar)
        self.month.connect('change-value', self.cambio_mes)
        self.day.connect('button-press-event', self.habilitar)
        self.month.connect('button-press-event', self.habilitar)
        self.year.connect('button-press-event', self.habilitar)
        self.day.connect('activate', self.key_enter_press)
        self.month.connect('activate', self.key_enter_press)
        self.year.connect('activate', self.key_enter_press)
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
            self.year.spin(Gtk.SPIN_STEP_FORWARD)
        else:
            self.year.spin(Gtk.SPIN_STEP_BACKWARD)

    def wrap_dia(self, *args):
        dia = self.day.get_value()
        if dia == 1:
            self.month.spin(Gtk.SPIN_STEP_FORWARD)
        else:
            self.month.spin(Gtk.SPIN_STEP_BACKWARD)

    def get(self):
        if self.year.get_value_as_int() == 0:
            return None
        return datetime.date(self.year.get_value_as_int(),
            self.month.get_value_as_int(), self.day.get_value_as_int())

    def get_date(self):
        # compatibilidad con Fecha()
        return self.get()

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

    def key_enter_press(self, *args):
        w = self.get_toplevel()
        w.do_move_focus(w, Gtk.DirectionType.TAB_FORWARD)

    def hide_clear_button(self):
        self.clear.hide()


class ComboBox(Gtk.Button):

    __gsignals__ = {
        'changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            ())
        }

    def __init__(self, liststore=(str, int)):
        super(ComboBox, self).__init__()
        self.column = 1
        self.lista = []
        self.connect('button-press-event', self.on_click)
        self.menu = Gtk.Menu()
        self.label = Gtk.Label()
        self.hbox = Gtk.HBox(False, 0)
        self.add(self.hbox)
        self.hbox.pack_start(self.label, False, False, 0)
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))

    def on_click(self, widget, event):
        self.menu.popup(None, None, None, None, event.button, event.time)
        self.menu.show_all()

    def set_lista(self, lista):
        self.label.set_text('-')
        self.lista = lista
        del self.menu
        self.menu = Gtk.Menu()
        for l in lista:
            item = Gtk.MenuItem(l[0])
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

    def set_text(self, t):
        for row in self.lista:
            if row[0] == t:
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
            menuitem = Gtk.MenuItem(item[0])
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


class ComboBoxBack(Gtk.ComboBox):

    def __init__(self, liststore=(str, int)):
        self.lista = Gtk.ListStore(*liststore)
        super(ComboBox, self).__init__(self.lista)
        cell = Gtk.CellRendererText()
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
        'enter': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            (GObject.TYPE_PYOBJECT,)),
        'escape': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            ()),
        'cambio': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            (GObject.TYPE_PYOBJECT,))}

    def __init__(self):
        super(Hora, self).__init__(5)
        self.set_text('--:--')
        self.set_width_chars(5)
        self.spin_h = Gtk.SpinButton(digits=0)
        self.spin_m = Gtk.SpinButton(digits=0)
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
            spin.spin(Gtk.SPIN_STEP_FORWARD)
            self.spin = True
            self.update(seleccionar=False)
        elif key == 65364:  # abajo
            self.spin = True
            spin.spin(Gtk.SPIN_STEP_BACKWARD)
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
        if event.direction == Gdk.SCROLL_UP:
            spin.spin(Gtk.SPIN_STEP_FORWARD)
        elif event.direction == Gtk.gdk.SCROLL_DOWN:
            spin.spin(Gtk.SPIN_STEP_BACKWARD)
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
            self.spin_h.spin(Gtk.SPIN_STEP_FORWARD)
        else:
            self.spin_h.spin(Gtk.SPIN_STEP_BACKWARD)


class Button(Gtk.Button):

    def __init__(self, archivo, string=None, size=24, tooltip=None):
        # type: (string, string, int, string) -> None
        super(Button, self).__init__()
        self.hbox = Gtk.HBox(False, 0)
        path = 'images/PNG-%d/' % size
        if not archivo is None:
            self.imagen = Gtk.Image()
            self.imagen.set_from_file(path + archivo)
            self.hbox.pack_start(self.imagen, True, True, 0)
        if not string is None:
            self.label = Gtk.Label()
            self.label.set_markup(string)
            self.label.set_use_underline(True)
            self.hbox.pack_start(self.label, True, True, 0)
        self.add(self.hbox)
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))
        # if tooltip:
        #     self.tooltips = Gtk.Tooltips()
        #     self.tooltips.set_tip(self, tooltip)

    def set_text(self, text):
        self.label.set_markup(text)

    def get_text(self):
        return self.label.get_text()

    def vertical(self):
        self.hbox.set_orientation(Gtk.ORIENTATION_VERTICAL)

    def set_imagen(self, archivo, size=24):
        path = 'images/PNG-%d/' % size
        self.imagen.set_from_file(path + archivo)

    def label_visible(self, visible):
        if visible:
            self.label.show()
        else:
            self.label.hide()


class ButtonDoble(Gtk.Button):

    def __init__(self, file1, file2, motivo, size=16, tooltip=None):
        super(ButtonDoble, self).__init__()
        hbox = Gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        path = 'images/PNG-%d/' % size
        imagen = Gtk.Image()
        imagen.set_from_file(path + file1)
        self.hbox1.pack_start(imagen, True, True, 0)
        path = 'images/PNG-%d/' % size
        imagen = Gtk.Image()
        imagen.set_from_file(path + file2)
        self.hbox2.pack_start(imagen, True, True, 0)
        self.set(False, 'No seleccionado')
        self._motivo = motivo
        self.ok = False
        self.connect('clicked', self.click)

        self.modify_bg(Gtk.StateType(0), Gdk.color_parse('#FFFFFF'))  # NORMAL
        self.modify_bg(Gtk.StateType(4), Gdk.color_parse('#e5e8e8'))  # INSENSITIVE
        self.modify_bg(Gtk.StateType(1), Gdk.color_parse('#e5e8e8'))  # active
        self.modify_bg(Gtk.StateType(3), Gdk.color_parse('#f8fbfc'))  # selected
        self.modify_bg(Gtk.StateType(2), Gdk.color_parse('#e5f1f4'))  # prelight
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))
        # if tooltip:
        #     self.tooltips = Gtk.Tooltips()
        #     self.tooltips.set_tip(self, tooltip)

    def set(self, ok, motivo=None):
        self.ok = ok
        if motivo is None:
            self.motivo = self._motivo
        else:
            self.motivo = motivo
        if ok:
            self.hbox1.hide()
            self.hbox2.show_all()
            self.set_sensitive(True)
        else:
            self.hbox1.show_all()
            self.hbox2.hide()
            self.set_sensitive(False)

    def click(self, *args):
        Alerta('Motivo', 'error.png', self.motivo)


class ButtonDoblePersonal(Gtk.Button):

    def __init__(self, http, padre, tooltip=None):
        super(ButtonDoblePersonal, self).__init__()
        self.http = http
        self.padre = padre
        hbox = Gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        self.hbox3 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox3, False, False, 0)
        path = 'images/PNG-16/'
        imagen = Gtk.Image()
        imagen.set_from_file(path + 'no_castigado.png')
        self.hbox1.pack_start(imagen, True, True, 0)
        imagen = Gtk.Image()
        imagen.set_from_file(path + 'warning.png')
        self.hbox2.pack_start(imagen, True, True, 0)
        imagen = Gtk.Image()
        imagen.set_from_file(path + 'castigado.png')
        self.hbox3.pack_start(imagen, True, True, 0)
        self.set(None)
        self.ok = False
        self.t_id = 0
        self.motivo = ''
        self.connect('clicked', self.click)
        self.modify_bg(Gtk.StateType(0), Gdk.color_parse('#FFFFFF'))  # NORMAL
        self.modify_bg(Gtk.StateType(4), Gdk.color_parse('#e5e8e8'))  # INSENSITIVE
        self.modify_bg(Gtk.StateType(1), Gdk.color_parse('#e5e8e8'))  # active
        self.modify_bg(Gtk.StateType(3), Gdk.color_parse('#f8fbfc'))  # selected
        self.modify_bg(Gtk.StateType(2), Gdk.color_parse('#e5f1f4'))  # prelight
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))
        # if tooltip:
        #     self.tooltips = Gtk.Tooltips()
        #     self.tooltips.set_tip(self, tooltip)

    def set(self, trabajador):
        self.hbox1.hide()
        self.hbox2.hide()
        self.hbox3.hide()
        self.trabajador = trabajador
        if isinstance(self.trabajador, models.model_base):
            self.hbox1.hide()
            self.hbox2.hide()
            self.hbox3.hide()
            self.ok = trabajador.get_icon_datos()
        else:
            self.ok = trabajador
        print(('ok', self.ok))
        if self.ok:
            self.hbox3.show_all()
        elif self.ok is None:
            self.hbox1.show_all()
        else:
            self.hbox2.show_all()

    def click(self, *args):
        datos = {'trabajador_id': self.t_id,}
        respuesta = self.http.load('datos-personal', datos)
        self.datos = datos
        if respuesta:
            if 'castigos' in respuesta:
                js = respuesta['json']
                if 'conductor' in respuesta:
                    if respuesta['conductor']:
                        for c in self.http.conductores:
                            if c[2] == js[2]:
                                c[3] = js[3]
                                break
                    else:
                        for c in self.http.cobradores:
                            if c[2] == js[2]:
                                c[3] = js[3]
                                break
                self.set(js[3], js[2])
                self.dialogo = Alerta_SINO(respuesta['nombre'], '../../outs/imagen.png', respuesta['motivo'])
                self.dialogo.but_ok.set_text('Pagar Multas')
                boton = Button('editar.png', 'Avalar')
                boton.connect('clicked', self.avalar)
                self.dialogo.action_area.pack_start(boton, False, False, 0)
                response = self.dialogo.iniciar()
                self.dialogo.cerrar()
                if response:
                    self.dialog = PagarMultas(respuesta, self.http, self.padre)
                    self.dialog.iniciar()
                    castigado = self.dialog.castigado
                    self.dialog.cerrar()
                    self.set(castigado, self.t_id)
            else:
                Alerta(respuesta['nombre'], '../../outs/imagen.png', respuesta['motivo'])

    def avalar(self, *args):
        dialog = Avalar(self.datos, self.http, self)
        if dialog.iniciar():
            self.dialogo.but_salir.clicked()
        dialog.cerrar()


class ButtonDobleUnidad(Gtk.Button):

    def __init__(self, http, padre, tooltip=None):
        super(ButtonDobleUnidad, self).__init__()
        self.http = http
        self.padre = padre
        hbox = Gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        self.hbox3 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox3, False, False, 0)
        path = 'images/PNG-16/'
        imagen = Gtk.Image()
        imagen.set_from_file(path + 'no_castigado.png')
        self.hbox1.pack_start(imagen, True, True, 0)
        imagen = Gtk.Image()
        imagen.set_from_file(path + 'warning.png')
        self.hbox2.pack_start(imagen, True, True, 0)
        imagen = Gtk.Image()
        imagen.set_from_file(path + 'castigado.png')
        self.hbox3.pack_start(imagen, True, True, 0)
        self.set(None)
        self.ok = False
        self.u_id = 0
        self.motivo = ''
        self.connect('clicked', self.click)
        self.modify_bg(Gtk.StateType(0), Gdk.color_parse('#FFFFFF'))  # NORMAL
        self.modify_bg(Gtk.StateType(4), Gdk.color_parse('#e5e8e8'))  # INSENSITIVE
        self.modify_bg(Gtk.StateType(1), Gdk.color_parse('#e5e8e8'))  # active
        self.modify_bg(Gtk.StateType(3), Gdk.color_parse('#f8fbfc'))  # selected
        self.modify_bg(Gtk.StateType(2), Gdk.color_parse('#e5f1f4'))  # prelight
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))
        # if tooltip:
        #     self.tooltips = Gtk.Tooltips()
        #     self.tooltips.set_tip(self, tooltip)

    def set(self, unidad):
        self.unidad = unidad
        if self.unidad is None:
            self.hbox1.hide()
            self.hbox2.hide()
            self.hbox3.hide()
            self.hbox3.show_all()
        else:
            self.hbox1.hide()
            self.hbox2.hide()
            self.hbox3.hide()
            self.ok = unidad.get_icon_datos()
            if self.ok:
                self.hbox3.show_all()
            elif self.ok is None:
                self.hbox1.show_all()
            else:
                self.hbox2.show_all()

    def click(self, *args):
        self.dialogo = Alerta_SINO(self.unidad.get_modelo(), 'unidad.png', self.unidad.get_motivo_no_disponible())
        self.dialogo.but_ok.set_text('Crear Incidencia')
        response = self.dialogo.iniciar()
        self.dialogo.cerrar()
        if response:
            self.dialog = Alerta_Texto('Crear Incidencia de Despacho', [])
            motivo = self.dialog.iniciar()
            if motivo:
                datos = {
                    'unidad_id': self.unidad.id,
                    'motivo': motivo
                }
                self.http.load('incidencia', datos)
            self.dialog.cerrar()


class Dialog(Gtk.Dialog):

    def __init__(self, titulo):
        flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        super(Dialog, self).__init__(titulo, None, flags)
        self.set_default_size(300, 100)
        self.set_position(Gtk.WindowPosition.CENTER)
        ventanas = Gtk.Window.list_toplevels()
        parent = ventanas[0]
        print(parent)
        for v in ventanas:
            if v.is_active():
                parent = v
                break
        self.set_modal(True)
        self.set_transient_for(parent)
        self.connect("delete_event", self.cerrar)
        self.set_border_width(10)

    def cerrar(self, *args):
        self.destroy()


class Avalar(Dialog):

    def __init__(self, datos, http, padre):
        super(Avalar, self).__init__(self.datos['nombre'])
        self.http = http
        self.padre = padre
        self.datos = self.http.load('avales', datos)
        self.combo_propietario = ComboBox()
        self.entry_padron = Numero(4)
        self.fin = Fecha()
        self.detalles = Texto(64)
        lista = [['Sin Aval', 0]] + self.datos['propietarios']
        self.combo_propietario.set_lista(lista)
        if 'aval_id'in self.datos:
            self.combo_propietario.set_id(self.datos['aval_id'])
        if 'temporal'in self.datos:
            self.entry_padron.set_text(str(self.datos['temporal']))
            self.fin.set_date(self.datos['fin_temporal'])
        self.aval_back = self.combo_propietario.get_id()
        self.temporal_back = self.entry_padron.get_text()
        self.fin_back = self.fin.get_text()
        tabla = Gtk.Table(2, 3)
        tabla.attach(Gtk.Label('Aval Permanente:'), 0, 1, 0, 1)
        tabla.attach(Gtk.Label('Unidad Temporal:'), 0, 1, 1, 2)
        tabla.attach(Gtk.Label('Fin Temporal:'), 0, 1, 2, 3)
        tabla.attach(Gtk.Label('Detalles autorizacion:'), 0, 1, 3, 4)
        tabla.attach(self.combo_propietario, 1, 2, 0, 1)
        tabla.attach(self.entry_padron, 1, 2, 1, 2)
        tabla.attach(self.fin, 1, 2, 2, 3)
        tabla.attach(self.detalles, 1, 2, 3, 4)
        self.vbox.pack_start(tabla, False, False, 0)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "ar")
        but_aceptar = Button('checkmark.png', "_Guardar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.action_area.pack_start(but_aceptar, False, False, 0)
        but_aceptar.connect('clicked', self.guardar)
        self.set_focus(but_salir)

    def guardar(self, *args):
        if len(self.detalles.get_text()) < 7:
            return Alerta('Error', 'warning.png', 'Debe escribir un detalle más completo')
        datos = {
            'trabajador_id': self.datos['trabajador_id'],
            'aval_id': self.combo_propietario.get_id(),
            'detalles': self.detalles.get_text(),
            'ruta_id': self.padre.padre.ruta,
            'lado': self.padre.padre.lado,
        }
        if self.aval_back != self.combo_propietario.get_id():
            datos['aval'] = self.combo_propietario.get_text()
            datos['aval_anterior'] = self.aval_back
        if self.temporal_back != self.entry_padron.get_text() or self.fin_back != self.fin.get_text():
            datos['padron_temporal'] = self.entry_padron.get_text()
            datos['padron_temporal_anterior'] = self.temporal_back
            datos['fin_temporal'] = self.fin.get_text()
        print(datos)
        respuesta = self.http.load('editar-avales', datos)
        if respuesta:
            self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        self.but_ok.hide()
        if self.run() == Gtk.ResponseType.OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class PagarMultas(Dialog):

    def __init__(self, datos, http, padre):
        nombre = datos['nombre']
        super(PagarMultas, self).__init__('Pago de Multas: ' + nombre)
        self.http = http
        self.padre = padre
        self.set_default_size(400, 400)
        castigos = datos['castigos']
        label = Gtk.Label()
        label.set_markup('Castigos con multa del personal\n' + nombre)
        self.vbox.pack_start(label, False, False, 10)
        self.treeview = TreeViewId('CASTIGOS', ('CODIGO', 'DETALLE', 'MULTA'))
        self.treeview.set_size_request(400, 400)
        self.vbox.pack_start(self.treeview)
        self.treeview.escribir(castigos)
        but_salir = Button('delete.png', "_Cancelar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.castigado = datos['castigado']
        self.treeview.connect('activado', self.pagar_multa)
        self.set_focus(but_salir)

    def pagar_multa(self, w, row):
        dialogo = Alerta_Numero('Pago de Multas', 'dinero.png', 'Escriba la cantidad de dinero recibido', 10, False)
        numero = dialogo.iniciar()
        dialogo.cerrar()
        if numero:
            datos = {
                'castigo_id': row[3],
                'ruta_id': self.padre.ruta,
                'monto': numero
            }
            respuesta = self.http.load('pagar-multa', datos)
            if respuesta:
                if int(numero) == int(self.treeview.model[self.treeview.path][2]):
                    treeiter = self.treeview.model.get_iter(self.treeview.path)
                    self.treeview.model.remove(treeiter)
                else:
                    self.treeview.model[self.treeview.path][2] = str(int(self.treeview.model[self.treeview.path][2]) - int(numero))
                self.castigado = respuesta['castigado']

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            return self.castigado
        else:
            return self.castigado

    def cerrar(self, *args):
        self.destroy()


class ButtonDobleBloquear(Gtk.Button):

    def __init__(self, file1, file2, size=16, tooltip=None):
        super(ButtonDobleBloquear, self).__init__()
        hbox = Gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        path = 'images/PNG-%d/' % size
        imagen = Gtk.Image()
        imagen.set_from_file(path + file1)
        self.hbox1.pack_start(imagen, True, True, 0)
        path = 'images/PNG-%d/' % size
        imagen = Gtk.Image()
        imagen.set_from_file(path + file2)
        self.hbox2.pack_start(imagen, True, True, 0)
        self.set(False)
        self.ok = False
        self.modify_bg(Gtk.StateType(0), Gdk.color_parse('#FFFFFF'))  # NORMAL
        self.modify_bg(Gtk.StateType(4), Gdk.color_parse('#e5e8e8'))  # INSENSITIVE
        self.modify_bg(Gtk.StateType(1), Gdk.color_parse('#e5e8e8'))  # active
        self.modify_bg(Gtk.StateType(3), Gdk.color_parse('#f8fbfc'))  # selected
        self.modify_bg(Gtk.StateType(2), Gdk.color_parse('#e5f1f4'))  # prelight
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))
        # if tooltip:
        #     self.tooltips = Gtk.Tooltips()
        #     self.tooltips.set_tip(self, tooltip)

    def set(self, ok):
        self.ok = ok
        if ok:
            self.hbox1.hide()
            self.hbox2.show_all()
        else:
            self.hbox1.show_all()
            self.hbox2.hide()

class ButtonTwist(Gtk.Button):

    def __init__(self, file1, file2, tooltip=None):
        super(ButtonTwist, self).__init__()
        hbox = Gtk.HBox(False, 0)
        self.add(hbox)
        self.hbox1 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox1, False, False, 0)
        self.hbox2 = Gtk.HBox(False, 0)
        hbox.pack_start(self.hbox2, False, False, 0)
        imagen = Gtk.Image()
        imagen.set_from_file('images/PNG-16/' + file1)
        self.hbox1.pack_start(imagen, True, True, 0)
        imagen = Gtk.Image()
        imagen.set_from_file('images/PNG-16/' + file2)
        self.hbox2.pack_start(imagen, True, True, 0)
        # self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#FFFFFF'))
        # self.modify_bg(Gtk.STATE_INSENSITIVE, Gdk.color_parse('#e5e8e8'))
        # self.modify_bg(Gtk.STATE_ACTIVE, Gdk.color_parse('#328aa4'))
        # self.modify_bg(Gtk.STATE_SELECTED, Gdk.color_parse('#f8fbfc'))
        # self.modify_bg(Gtk.STATE_PRELIGHT, Gdk.color_parse('#e5f1f4'))
        # if tooltip:
        #     self.tooltips = Gtk.Tooltips()
        #     self.tooltips.set_tip(self, tooltip)

    def activar(self):
        self.hbox1.hide()
        self.hbox2.show_all()

    def desactivar(self):
        self.hbox1.show_all()
        self.hbox2.hide()

class Mensaje(Gtk.Window):

    def __init__(self, parent, titulo, imagen, mensaje):
        super(Mensaje, self).__init__(Gtk.WindowType.POPUP)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(200, 50)
        self.set_title(titulo)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete_event", self.cerrar)
        self.vbox = Gtk.VBox(False, 0)
        self.add(self.vbox)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, False, False, 5)
        self.show_all()

    def cerrar(self, *args):
        self.destroy()


class Alerta(Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(Alerta, self).__init__(titulo)
        self.set_default_size(200, 50)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        frame = Frame()
        hbox.pack_start(frame, False, False, 5)
        frame.add(image)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        frame = Frame()
        hbox.pack_start(frame, False, False, 15)
        frame.add(label)
        self.but_salir = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(self.but_salir, Gtk.ResponseType.CANCEL)
        self.set_focus(self.but_salir)
        self.iniciar()

    def iniciar(self):
        self.show_all()
        self.run()
        self.cerrar()


class AlertaTwist(Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(AlertaTwist, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, True, True, 10)
        self.but_salir = Button('checkmark.png', "_Aceptar")
        self.action_area.pack_start(self.but_salir, False, False, 0)
        self.but_salir.connect('clicked', self.cerrar)
        self.set_focus(self.but_salir)
        self.show_all()

    def cerrar(self, *args):
        self.destroy()


class Mensaje(Dialog):

    def __init__(self, titulo, imagen, mensajes):
        super(Mensaje, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        self.label = []
        self.count = 0
        for m in mensajes:
            label = Gtk.Label()
            label.set_markup(m)
            label.set_alignment(0, 0.5)
            self.label.append(label)
            hbox.pack_start(label, True, True, 5)
        if len(mensajes) == 0:
            label = Gtk.Label()
            label.set_markup('No hay coincidencias para la búsqueda')
            label.set_alignment(0, 0.5)
            self.label.append(label)
            hbox.pack_start(label, True, True, 5)
        self.but_atras = Button('atras.png', "_Atrás")
        self.action_area.pack_start(self.but_atras, False, False, 0)
        self.but_siguiente = Button('siguiente.png', "_Siguiente")
        self.action_area.pack_start(self.but_siguiente, False, False, 0)
        self.but_salir = Button('delete.png', "_Cancelar")
        self.add_action_widget(self.but_salir, Gtk.ResponseType.CANCEL)
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


class Alerta_SINO(Dialog):

    def __init__(self, titulo, imagen, mensaje, default=True):
        super(Alerta_SINO, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        self.label = Gtk.Label()
        self.label.set_alignment(0, 0.5)
        self.label.set_markup(mensaje)
        hbox.pack_start(self.label, True, True, 10)
        self.but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(self.but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        if default:
            self.set_focus(self.but_ok)
        else:
            self.set_focus(self.but_salir)

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()



class Alerta_SINO_Clave(Dialog):

    def __init__(self, titulo, imagen, mensaje, default=True):
        super(Alerta_SINO_Clave, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, True, True, 10)
        frame = Frame()
        self.vbox.pack_start(frame, True, True, 5)
        hbox = Gtk.HBox(False, 0)
        hbox.pack_start(Gtk.Label('Autorización Supervisor:'), False, False, 20)
        frame.add(hbox)
        self.entry_clave = Entry()
        self.entry_clave.set_visibility(False)
        self.entry_clave.connect('activate', self.enter)
        hbox.pack_start(self.entry_clave, False, False, 5)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        if default:
            self.set_focus(self.but_ok)
        else:
            self.set_focus(but_salir)

    def enter(self, *args):
        self.but_ok.clicked()

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            self.clave = self.entry_clave.get_text()
            return True
        else:
            self.clave = self.entry_clave.get_text()
            return False

    def cerrar(self, *args):
        self.destroy()


class AlertaAuto(Dialog):

    def __init__(self, titulo, imagen, mensaje, default=True):
        super(AlertaAuto, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, True, True, 10)
        but_salir = Button('checkmark.png', "_Aceptar")
        self.action_area.pack_start(but_salir, False, False, 0)
        but_salir.connect('clicked', self.cerrar)
        self.set_focus(but_salir)
        self.show_all()

    def cerrar(self, *args):
        self.destroy()


class Alerta_Dia_Hora(Dialog):
    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Dia_Hora, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, True, True, 10)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 0)
        self.fecha = Fecha()
        vbox.pack_start(self.fecha, False, False, 10)
        self.hora = Hora()
        vbox.pack_start(self.hora, False, False, 5)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.hora.connect('enter', lambda s, w: self.but_ok.clicked())
        self.hora.connect('escape', lambda s, w: but_salir.clicked())
        self.set_focus(self.hora)

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            return self.hora.get_time()
        else:
            return False

    def hna(self, *args):
        self.hora.set_text('--:--')

    def cerrar(self, *args):
        self.destroy()


class Alerta_Hora(Dialog):
    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Hora, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 20)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, True, True, 10)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 0)
        self.hora = Hora()
        vbox.pack_start(self.hora, False, False, 5)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.hora.connect('enter', lambda s, w: self.but_ok.clicked())
        self.hora.connect('escape', lambda s, w: but_salir.clicked())
        self.set_focus(self.hora)

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            return self.hora.get_time()
        else:
            return False

    def hna(self, *args):
        self.hora.set_text('--:--')

    def cerrar(self, *args):
        self.destroy()


class BloquearUnidad(Dialog):
    def __init__(self, datos):
        super(BloquearUnidad, self).__init__('Bloquear Unidad')
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/bloqueado.png')
        hbox.pack_start(image, False, False, 5)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox)
        frame = Gtk.Frame()
        vbox.pack_start(frame)
        vb = Gtk.VBox()
        frame.add(vb)
        label = Gtk.Label()
        label.set_markup('Indique el día y hora del fin del bloqueo')
        vb.pack_start(label)
        self.radio1 = Gtk.RadioButton(None, 'Hasta Nuevo Aviso')
        vb.pack_start(self.radio1)
        self.radio2 = Gtk.RadioButton(self.radio1, 'Fecha y Hora')
        vb.pack_start(self.radio2)
        hbox = Gtk.HBox()
        vb.pack_start(hbox, False, False, 5)
        label = Gtk.Label('Día: ')
        hbox.pack_start(label, False, False, 5)
        self.fecha = Fecha()
        hbox.pack_start(self.fecha, False, False, 0)
        label = Gtk.Label('Hora: ')
        self.hora = Hora()
        hbox.pack_start(self.hora, False, False, 0)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 5)
        label = Gtk.Label('Detalle:')
        hbox.pack_start(label, False, False, 5)
        self.entry = Texto(64)
        hbox.pack_start(self.entry, False, False, 5)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 5)
        label = Gtk.Label('Tipo de Bloqueo:')
        hbox.pack_start(label, False, False, 5)
        self.radio3 = Gtk.RadioButton(None, 'Por nivel')
        hbox.pack_start(self.radio3, False, False, 5)
        radio4 = Gtk.RadioButton(self.radio3, 'Por usuario')
        hbox.pack_start(radio4, False, False, 5)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 5)
        label = Gtk.Label('Bloquear en:')
        hbox.pack_start(label, False, False, 5)
        self.radio5 = Gtk.RadioButton(None, 'Lado A')
        hbox.pack_start(self.radio5, False, False, 5)
        self.radio6 = Gtk.RadioButton(self.radio5, 'Lado B')
        hbox.pack_start(self.radio6, False, False, 5)
        self.radio7 = Gtk.RadioButton(self.radio5, 'Ambos')
        hbox.pack_start(self.radio7, False, False, 5)
        self.radio1.connect('toggled', self.toggled_tipo)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.hora.connect('enter', lambda s, w: self.but_ok.clicked())
        self.hora.connect('escape', lambda s, w: but_salir.clicked())
        self.hna()
        self.set_focus(self.hora)

    def por_hora(self):
        self.fecha.set_sensitive(True)
        self.hora.set_sensitive(True)
        if datetime.datetime.now().time() > datetime.time(14, 0):
            self.hora.set_time('03:00')
            self.fecha.set_date(datetime.datetime.today() + datetime.timedelta(1))
        else:
            self.hora.set_time('18:00')
            self.fecha.set_date(datetime.datetime.today())

    def hna(self, *args):
        self.hora.set_text('--:--')
        self.fecha.set_sensitive(False)
        self.hora.set_sensitive(False)

    def toggled_tipo(self, *args):
        if self.radio1.get_active():
            self.hna()
        else:
            self.por_hora()

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            if self.radio2.get_active():
                self.datos['dia'] = self.fecha.get_text()
                self.datos['hora'] = self.hora.get_text()
            self.datos['motivo'] = self.entry.get_text()
            if self.radio5.get_active():
                self.datos['bloqueo_lado'] = 'A'
            elif self.radio6.get_active():
                self.datos['bloqueo_lado'] = 'B'
            else:
                self.datos['bloqueo_lado'] = 'Ambos'
            if self.radio3.get_active():
                self.datos['tipo'] = 'NIVEL'
            else:
                self.datos['tipo'] = 'USUARIO'
            self.datos['tipo']
            return self.datos
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class DesbloquearUnidad(Dialog):
    def __init__(self, padre, bloqueos, datos):
        super(DesbloquearUnidad, self).__init__('Desbloquear Unidad')
        self.http = padre.http
        self.datos = datos
        self.bloqueos = []
        self.bloqueado = False
        self.label = Gtk.Label('No hay bloqueos activos')
        self.vbox.pack_start(self.label, False, False, 15)
        self.escribir(bloqueos)
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.but_bloquear = Button('bloqueado.png', "_Bloquear")
        self.but_bloquear.connect('clicked', self.bloquear)
        self.action_area.pack_start(self.but_bloquear)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)

    def escribir(self, bloqueos):
        if self.bloqueos:
            for b in self.bloqueos:
                self.vbox.remove(b['hbox'])
        else:
            self.vbox.remove(self.label)
        self.bloqueos = bloqueos
        if self.bloqueos:
            for b in self.bloqueos:
                hbox = Gtk.HBox(True, 0)
                b['hbox'] = hbox
                self.vbox.pack_start(hbox)
                frame = Gtk.Frame('TIPO')
                frame.set_border_width(10)
                hbox.pack_start(frame, True, True, 3)
                label = Gtk.Label()
                frame.add(label)
                if b['tipo'] == 'NIVEL':
                    label.set_label('NIVEL: %s' % b['nivel'])
                else:
                    label.set_label('USUARIO:\n  %s' % b['usuario'])
                frame = Gtk.Frame('DETALLES')
                frame.set_border_width(10)
                hb = Gtk.HBox(False, 0)
                hbox.pack_start(hb, True, True, 3)
                hb.pack_start(frame)
                label = Gtk.Label()
                frame.add(label)
                label.set_label('Por: %s\nFinaliza: %s\nMotivo: %s\nLado: %s' % (b['despachador'], b['fin'], b['motivo'], b['lado']))
                button = Button('no_bloqueado.png')
                hb.pack_end(button, False, False, 0)
                button.connect('clicked', self.desbloquear, b)
            self.bloqueado = True
            self.vbox.show_all()
        else:
            self.label = Gtk.Label('No hay bloqueos activos')
            self.vbox.pack_start(self.label, False, False, 15)
            self.bloqueado = False
            self.vbox.show_all()

    def bloquear(self, *args):
        dialogo = BloquearUnidad(self.datos)
        datos = dialogo.iniciar()
        dialogo.cerrar()
        if datos:
            respuesta = self.http.load('bloquear-unidad', datos)
            if isinstance(respuesta, list):
                self.escribir(respuesta)

    def desbloquear(self, widget, bloqueo):
        self.datos['bloqueoId'] = bloqueo['bloqueoId']
        respuesta = self.http.load('desbloquear-unidad', self.datos)
        if isinstance(respuesta, list):
            self.escribir(respuesta)

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_FechaNumero(Dialog):

    def __init__(self, titulo, imagen, mensaje, digitos=3, decimal=False, default=''):
        super(Alerta_FechaNumero, self).__init__(titulo)
        self.decimal = decimal
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, False, False, 5)
        label = Gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 15)
        self.dia = Fecha()
        vbox.pack_start(self.dia, False, False, 0)
        if decimal:
            self.entry = Texto(digitos)
        else:
            self.entry = Numero(digitos)
            self.entry.connect('ok', self.entry_ok)
            self.entry.connect('error', self.entry_error)
        vbox.pack_start(self.entry, False, False, 0)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.entry.connect('activate', self.activate)
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
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
        if self.run() == Gtk.ResponseType.OK:
            return self.dia.get_date(), self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Dia(Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Dia, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, False, False, 15)
        label = Gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.dia = Fecha()
        vbox.pack_start(self.dia, False, False, 0)
        but_salir = Button('delete.png', "_Cancelar")
        but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(but_ok, Gtk.ResponseType.OK)
        self.set_focus(but_ok)

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            return self.dia.get_date()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Numero(Dialog):

    def __init__(self, titulo, imagen, mensaje, digitos=3, decimal=False, default=''):
        super(Alerta_Numero, self).__init__(titulo)
        self.decimal = decimal
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, True, True, 10)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 15)
        if decimal:
            self.entry = Texto(digitos)
        else:
            self.entry = Numero(digitos, null=False)
            self.entry.connect('ok', self.entry_ok)
            self.entry.connect('error', self.entry_error)
        vbox.pack_start(self.entry, False, False, 10)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.entry.connect('activate', self.activate)
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.entry.set_text(default)
        self.entry.grab_focus()

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
        return True

    def iniciar(self):
        self.show_all()
        text = self.entry.get_text()
        self.entry.select_region(0, len(text))
        self.set_focus(self.entry)
        if self.run() == Gtk.ResponseType.OK:
            return self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Entry(Gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, password=False):
        super(Alerta_Entry, self).__init__(titulo)
        self.connect("delete_event", self.cerrar)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 20)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, True, True, 10)
        label = Gtk.Label()
        label.set_markup(mensaje)
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 15)
        self.entry = Texto(16)
        vbox.pack_start(self.entry, False, False, 10)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.entry.connect('activate', self.activate)
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.entry.grab_focus()

    def activate(self, *args):
        if self.entry.get_text() != '':
            self.but_ok.clicked()

    def entry_ok(self, *args):
        self.but_ok.set_sensitive(True)

    def entry_error(self, *args):
        self.but_ok.set_sensitive(False)
        self.entry.grab_focus()
        return True

    def iniciar(self):
        self.show_all()
        text = self.entry.get_text()
        self.entry.select_region(0, len(text))
        self.set_focus(self.entry)
        if self.run() == Gtk.ResponseType.OK:
            return self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Combo(Gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje, lista, liststore=(str, int)):
        super(Alerta_Combo, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, False, False, 15)
        label = Gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.combo = ComboBox(liststore)
        self.combo.set_lista(lista)
        vbox.pack_start(self.combo, False, False, 0)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)

    def iniciar(self):
        self.show_all()
        self.set_focus(self.but_ok)
        if self.run() == Gtk.ResponseType.OK:
            return self.combo.get_id()
        else:
            return False

    def get_item(self):
        return self.combo.get_item()

    def cerrar(self, *args):
        self.destroy()


class Alerta_Anular_Numeros(Gtk.Dialog):

    def __init__(self, titulo, imagen, mensaje):
        super(Alerta_Anular_Numeros, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, False, False, 15)
        label = Gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        hbox = Gtk.HBox(False, 0)
        label = Gtk.Label('Inicio')
        self.entry1 = Numero(6)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.entry1, False, False, 0)
        label = Gtk.Label('Fin')
        self.entry2 = Numero(6)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(self.entry2, False, False, 0)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.entry2.connect('ok', self.entry_ok)
        self.entry1.connect('error', self.entry_error)
        self.entry2.connect('error', self.entry_error)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
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
        if self.run() == Gtk.ResponseType.OK:
            return (int(self.entry1.get_text()), int(self.entry2.get_text()))
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Alerta_Texto(Gtk.Dialog):

    def __init__(self, titulo, lista):
        super(Alerta_Texto, self).__init__(titulo)
        self.lista = lista
        self.radio = [None] * len(lista)
        for i, string in enumerate(lista):
            if i == 0:
                self.radio[i] = Gtk.RadioButton()
            else:
                self.radio[i] = Gtk.RadioButton()
                self.radio[i].set_group(self.radio[0])
            self.radio[i].set_label(string)
            self.vbox.pack_start(self.radio[i], False, False, 0)
        self.entry = Entry()
        self.entry.set_width_chars(15)
        self.vbox.pack_start(self.entry, False, False, 0)
        self.but_ok = Button('checkmark.png', "_Aceptar")
        but_salir = Button('delete.png', "_Cancelar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.entry.connect('activate', self.entry_activate)
        self.set_focus(self.entry)

    def iniciar(self):
        self.show_all()
        string = ''
        if self.run() == Gtk.ResponseType.OK:
            for i, radio in enumerate(self.radio):
                if radio.get_active():
                    string += self.lista[i] + ': '
            string += self.entry.get_text()
            return string
        else:
            return False

    def entry_activate(self, *args):
        self.but_ok.clicked()

    def cerrar(self, *args):
        self.destroy()


class Alerta_Entero(Dialog):

    def __init__(self, titulo, imagen, mensaje, digitos=3):
        super(Alerta_Entero, self).__init__(titulo)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 10)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/' + imagen)
        hbox.pack_start(image, False, False, 5)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, False, False, 15)
        label = Gtk.Label()
        label.set_markup(mensaje)
        vbox.pack_start(label, False, False, 5)
        self.entry = Entry(digitos)
        vbox.pack_start(self.entry, False, False, 0)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
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
        if self.run() == Gtk.ResponseType.OK:
            return self.entry.get_text()
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class PlaceholderEntry(Gtk.Entry):

    placeholder = 'Username'
    _default = False
    visible = True

    def __init__(self, *args, **kwds):
        Gtk.Entry.__init__(self, *args, **kwds)
        self.connect('focus-in-event', self._focus_in_event)
        self.connect('focus-out-event', self._focus_out_event)
        self.set_visibility(self.visible)

    def _focus_in_event(self, widget, event):
        if self._default:
            self.set_text('')
            self.set_visibility(self.visible)
            self.modify_text(Gtk.StateType.NORMAL, Gdk.color_parse('black'))

    def _focus_out_event(self, widget, event):
        if Gtk.Entry.get_text(self) == '':
            self.set_text(self.placeholder)
            self.set_visibility(True)
            self.modify_text(Gtk.StateType.NORMAL, Gdk.color_parse('gray'))
            self._default = True
        else:
            self.set_visibility(self.visible)
            self._default = False

    def get_text(self):
        if self._default:
            return ''
        return Gtk.Entry.get_text(self)


class Login(Gtk.Dialog):

    tokens = []

    def __init__(self, http, parent):
        title = 'Inicie Sesión:'
        flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        super(Login, self).__init__(title, parent, flags)
        self.http = http
        self.set_default_size(200, 50)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete_event", self.cerrar)
        hbox = Gtk.HBox(False, 0)
        self.vbox.pack_start(hbox, False, False, 15)
        image = Gtk.Image()
        image.set_from_file('images/PNG-48/login.png')
        hbox.pack_start(image, False, False, 20)
        vbox = Gtk.VBox()
        hbox.pack_start(vbox, True, True, 10)
        self.usuario = PlaceholderEntry()
        self.usuario.placeholder = 'Username'
        vbox.pack_start(self.usuario, False, False, 5)
        self.usuario.connect('activate', lambda w: self.set_focus(self.password))
        self.password = PlaceholderEntry()
        self.password.placeholder = 'Password Perfil'
        self.password.visible = False
        vbox.pack_start(self.password, False, False, 5)
        self.password.connect('activate', lambda w: self.set_focus(self.clave))
        self.clave = PlaceholderEntry()
        self.clave.placeholder = 'Clave Personal'
        self.clave.visible = False
        vbox.pack_start(self.clave, False, False, 5)
        self.but_aceptar = Button('checkmark.png', "_Aceptar")
        self.action_area.pack_start(self.but_aceptar, False, False, 0)
        self.but_aceptar.connect('clicked', self.comprobar)
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.clave.connect('activate', self.comprobar)
        self.set_focus(self.usuario)
        self.mac = str(getnode())
        self.secret_key = 'S3CRE1K3Y'
        self.get_credentials()
        self.usuario._focus_out_event(None, None)
        self.password._focus_out_event(None, None)
        self.clave._focus_out_event(None, None)


    def get_credentials(self):
        try:
            a = os.path.abspath("outs/pdfcreator.dll")
            archivo = open(a, 'rb')
            content = archivo.read()
            archivo.close()
            js = base64.b64decode(content)
            d = json.loads(js)
        except:
            js = json.dumps({})
            content = base64.b64encode(js)
            d = os.path.abspath("outs/pdfcreator.dll")
            archivo = open(a, 'wb')
            archivo.write(content)
            archivo.close()
        else:
            if self.mac in d:
                usuario, password = d[self.mac]
                self.usuario.set_text(usuario)
                self.password.set_text(password)
            elif self.secret_key in d:
                usuario, password = d[self.secret_key]
                self.usuario.set_text(usuario)
                self.password.set_text(password)
            else:
                self.tokens = []
                i = 0
                for k in d:
                    i += 1
                    self.tokens.append({
                        'id': i,
                        'username': d[k][0],
                        'password': d[k][1],
                        'hash': k
                    })
                print(('login backup', self.tokens))
                self.not_mac()

    def not_mac(self):
        a = Alerta_SINO('Cambio de Equipo', 'hacking.png', 'Se ha detectado un cambio en el equipo,\npor seguridad pida a su administrador el acceso desde esta PC')
        a.but_salir.set_text("Ingresar Credenciales")
        a.but_ok.set_text("Asistencia Remota")
        respuesta = a.iniciar()
        a.cerrar()
        if respuesta:
            lista = []
            for token in self.tokens:
                lista.append(('%s %s' % (token['id'], token['username']), token['id']))
            b = Alerta_Combo('Usuarios Disponibles', 'login.png', 'Escoja el usuario con el que desea ingresar', lista)
            usuario_id = b.iniciar()
            b.cerrar()
            if usuario_id:
                token = self.tokens[usuario_id - 1]
                username = token['username']
                password = token['password']
                c = Alerta_Entry('Verificación de Seguridad', 'security.png', 'Ingrese la clave suministrada por su administrador')
                clave = c.iniciar()
                c.cerrar()
                if clave:
                    data = {'username': username, 'clave': clave}
                    response = self.http.load('nueva-pc', data)
                    if response:
                        if response['permiso']:
                            self.usuario.set_text(username)
                            self.password.set_text(password)
                            return
                        else:
                            Alerta('Sin acceso', 'no-login.png', 'Intente nuevamente, aún no tiene autorización.')
            self.not_mac()

    def comprobar(self, *args):
        self.clave._focus_out_event(None, None)
        self.user = self.usuario.get_text()
        self.pw = self.password.get_text()
        self.cl = self.clave.get_text()
        self.sessionid = self.http.login(self.user, self.pw, self.cl)
        print(('LOGIN SEND', self.sessionid))
        if self.sessionid:
            d = {self.secret_key: (self.user, self.pw)}
            js = json.dumps(d)
            content = base64.b64encode(js.encode())
            a = os.path.abspath("outs/pdfcreator.dll")
            archivo = open(a, 'wb')
            archivo.write(content)
            archivo.close()
            self.but_ok.clicked()
        elif self.tokens:
            self.not_mac()


    def iniciar(self):
        self.show_all()
        self.but_ok.hide()
        print('LOGIN')
        if self.run() == Gtk.ResponseType.OK:
            print('LOGIN widget')
            return True
        else:
            print('LOGIN False')
            return False

    def cerrar(self, *args):
        self.destroy()

    def autologin(self):
        self.clave.set_text('0000')
        self.comprobar()


class Cell(Gtk.CellRendererText):

    __gsignals__ = {'editado': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT,
        (int, str))}

    def __init__(self):
        super(Cell, self).__init__()
        Gtk.CellRendererText.__init__(self)
        self.connect_after('editing-started', self.edicion)

    def edicion(self, cell, editable, path):
        if isinstance(editable, Gtk.Entry):
            editable.connect('key-release-event', self.key_release)
            editable.connect('key-press-event', self.key_press, path)

    def key_release(self, widget, event):
        if event.keyval == 65421 or event.keyval == 65293:
            return True

    def key_press(self, widget, event, path):
        if event.keyval == 65421 or event.keyval == 65293:
            self.emit('editado', int(path), widget.get_text())


class CellBoleto(Gtk.CellRendererText):

    __gsignals__ = {
        'editado': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (int, str)),
        'inicio': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (int, )),
        'usar-reserva': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (int, ))
    }

    def __init__(self):
        super(CellBoleto, self).__init__()
        self.boleto = None
        self.inicio = None
        self.connect_after('editing-started', self.edicion)
        self.editable = None

    def set_text(self, text):
        if isinstance(self.editable, Gtk.Entry):
            self.editable.set_text(text)
        self.editable.set_max_length(6)
        self.editable.show()
        self.editable.select_region(3, 6)

    def edicion(self, cell, editable, path):
        if isinstance(editable, Gtk.Entry):
            editable.connect('key-release-event', self.key_release, path)
            editable.connect('key-press-event', self.key_press, editable, path)
            editable.connect('size-allocate', self.in_focus)
            self.editable = editable
            self.emit('inicio', int(path))
            return True

    def in_focus(self, *args):
        self.editable.select_region(3, 6)

    def key_release(self, widget, event, path):
        text = widget.get_text()
        l = len(text)
        if event.keyval == 65421 or event.keyval == 65293:
            # intro= 65421 return = 65293
            return True
        elif event.keyval == 65361:  # izquierda
            widget.set_text('TERMINADO')
            self.emit('usar-reserva', int(path))
            return True
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


class CellHora(Gtk.CellRendererText):

    __gsignals__ = {'editado': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT,
        (int, str)),
            'inicio': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT,
        (GObject.TYPE_PYOBJECT, int))}

    def __init__(self):
        super(CellHora, self).__init__()
        self.reserva = False
        self.inicio = False
        self.connect_after('editing-started', self.edicion)

    def edicion(self, cell, editable, path):
        if isinstance(editable, Gtk.Entry):
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
        self.spin_h = Gtk.SpinButton(digits=0)
        self.spin_m = Gtk.SpinButton(digits=0)
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
            self.spin_h.spin(Gtk.SPIN_STEP_FORWARD)
        else:
            self.spin_h.spin(Gtk.SPIN_STEP_BACKWARD)

    def spin_mouse(self, widget, event):
        cur = widget.get_property('cursor-position')
        txt = widget.get_text()
        pos = txt.find(':')
        if cur > pos:
            spin = self.spin_m
        else:
            spin = self.spin_h
        if event.direction == Gtk.gdk.SCROLL_UP:
            spin.spin(Gtk.SPIN_STEP_FORWARD)
        elif event.direction == Gtk.gdk.SCROLL_DOWN:
            spin.spin(Gtk.SPIN_STEP_BACKWARD)
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
            spin.spin(Gtk.SPIN_STEP_FORWARD)
            self.spin = True
            self.update(widget)
        elif key == 65364:  # abajo
            self.spin = True
            spin.spin(Gtk.SPIN_STEP_BACKWARD)
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

    __gsignals__ = {'ok': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
        ()),
        'error': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
        ()),
        'cancel': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
        ())}

    def __init__(self, n, null=True):
        super(Numero, self).__init__(n)
        if n > 15:
            n = 15
        self.null = null
        self.set_width_chars(n)
        self.connect('key-press-event', self.key_press)
        self.connect('key-release-event', self.key_release)

    def key_press(self, widget, event):
        k = event.keyval
        if (48 <= k and k <= 57) or (65456 <= k and k <= 65465):
            # numeros
            return False
        elif k == 65288 or k == 65535 or k == 65293 or k == 65421 or k == 65289 or k == 65505 or k == 65506 or k == 65056:
            # backspace=65288, delete=65535, return = 65293, intro= 65421, tab=65289, shiftL=65505, shiftR=65506, shift+tab=65056
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
            if not self.null:
                return
        else:
            self.emit('ok')
        if event.keyval == 65293 or event.keyval == 65421:
            w = self.get_toplevel()
            print(dir(Gtk.DirectionType))
            w.do_move_focus(w, Gtk.DirectionType.TAB_FORWARD)

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

    def __init__(self, n, up=True, DIR_TAB=True):
        super(Texto, self).__init__(n)
        if n > 30:
            n = 30
        elif n > 20:
            n = 20
        elif n > 15:
            n = 15
        self.set_width_chars(n)
        self.up = up
        self.connect('key-press-event', self.on_activate)

    def get(self):
        txt = str(self.get_text(), 'utf-8')
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
            w.do_move_focus(w, Gtk.DirectionType.TAB_FORWARD)


class ToolButton(Gtk.ToolButton):

    def __init__(self, texto, imagen, funcion):
        icon = Gtk.Image()
        icon.set_from_file('images/toolbar/' + imagen)
        super(ToolButton, self).__init__(None, texto)
        self.set_tooltip_text(texto)
        self.set_icon_widget(icon)
        self.connect('clicked', funcion)


class ToggleToolButton(Gtk.ToggleButton):

    def __init__(self, texto, imagen, funcion):
        super(ToggleToolButton, self).__init__()
        self.hbox = Gtk.HBox(False, 0)
        if not imagen is None:
            self.imagen = Gtk.Image()
            self.imagen.set_from_file('images/toolbar/' + imagen)
            self.hbox.pack_start(self.imagen, True, True, 0)
        self.set_tooltip_text(texto)
        # if not string is None:
        #     self.label = Gtk.Label()
        #     self.label.set_markup(string)
        #     self.label.set_use_underline(True)
        #     self.hbox.pack_start(self.label, True, True, 0)
        self.add(self.hbox)
        # self.props.relief = Gtk.RELIEF_NONE
        # self.set_tooltip_text(texto)
        if funcion:
            self.connect('clicked', funcion)


class Toolbar(Gtk.HBox):

    def __init__(self, herramientas):
        super(Toolbar, self).__init__(False, 0)
        self.buttons = []
        for h in herramientas:
            b = ToolButton(h[0], h[1], h[2])
            self.pack_start(b, False, False, 0)
            self.buttons.append(b)
        self.show_all()

    def add_button(self, texto, imagen, funcion):
        b = ToolButton(texto, imagen, funcion)
        self.pack_start(b, False, False, 0)
        return b

    def add_button_end(self, texto, imagen, funcion):
        b = ToolButton(texto, imagen, funcion)
        self.pack_end(b, False, False, 0)
        return b

    def add_toggle_button(self, texto, imagen, funcion):
        b = ToggleToolButton(texto, imagen, funcion)
        self.pack_start(b, False, False, 0)
        return b

    def set_imagen_label(self, i, imagen, label):
        b = self.buttons[i]
        icon = Gtk.Image()
        icon.set_from_file('images/toolbar/' + imagen)
        b.set_icon_widget(icon)
        icon.show()
        b.set_label(label)

    def get_label(self, i):
        b = self.buttons[i]
        return b.get_label()


class VBox(Gtk.VBox):

    def __init__(self):
        super(VBox, self).__init__(False, 5)

    def get(self):
        return False

    def set(self, id):
        return False


class Tabla(Gtk.Table):

    def __init__(self):
        super(Tabla, self).__init__()
        self.y = 0

    def attach_label(self, l):
        label = Gtk.Label(l)
        label.set_size_request(75, 25)
        label.set_alignment(0, 0.5)
        self.attach(label, 0, 1, self.y, self.y + 1, Gtk.EXPAND | Gtk.FILL,
            Gtk.EXPAND | Gtk.FILL)

    def attach_widget(self, w):
        self.attach(w, 1, 2, self.y, self.y + 1,
            Gtk.EXPAND | Gtk.FILL, Gtk.EXPAND | Gtk.FILL)
        self.y += 1

    def get(self):
        return False

    def set(self, id):
        return False


class TreeView(Gtk.TreeView):

    def __init__(self, model):
        super(TreeView, self).__init__(model)
        self.set_reorderable(False)
        self.set_enable_tree_lines(True)
        self.set_grid_lines(Gtk.TreeViewGridLines(2))
        self.set_rules_hint(True)
        self.set_name("enruta-treeview")
        self.length = model.get_n_columns()

    def get_modelo(self, path):
        return self.get_model()[path][self.length - 1]

    def get_path(self):
        try:
            path, column = self.get_cursor()
            path = int(path[0])
        except:
            return None
        return path

    def set_modelo(self, path, modelo):
        self.model[path][self.length - 1] = modelo

        #GtkTreeView::even_row_color = "#A0DB8E"
                #GtkTreeView::odd_row_color = "#C0FBAE"
        #style = self.get_style().copy()
        #pixbuf = Gtk.gdk.pixbuf_new_from_file("images/fondo-treeview.jpg")
        #pixmap, mask = pixbuf.render_pixmap_and_mask()
        #for i in range(5):
            #style.bg_pixmap[i] = pixmap
        #self.set_style(style)


class TreeViewColumn(Gtk.TreeViewColumn):

    def __init__(self, columna):
        super(TreeViewColumn, self).__init__()
        self.columna = columna

    def encabezado(self):
        header = Gtk.Label()
        header.show()
        # if os.name == 'nt':
        #     header.set_markup('<span foreground="#000" weight="bold">%s</span>' % self.columna)
        # else:
        #     header.set_markup('<span foreground="#FFFFFF" weight="bold">%s</span>' % self.columna)
        header.set_markup(f'<span weight="bold">{self.columna}</span>')
        self.set_widget(header)
        align = header.get_parent()
        hbox = align.get_parent()
        button = hbox.get_parent()
        if os.name == 'nt':
            button.modify_bg(Gtk.StateType(0), Gdk.color_parse('#328aa4'))  # NORMAL
            button.modify_bg(Gtk.StateType(4), Gdk.color_parse('#328aa4'))  # INSENSITIVE
        else:
            button.modify_bg(Gtk.StateType(0), Gdk.color_parse('#328aa4'))  # NORMAL
            button.modify_bg(Gtk.StateType(4), Gdk.color_parse('#328aa4'))  # INSENSITIVE

class TreeViewId(Frame):

    __gsignals__ = {
        'activado': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,))
    }

    def __init__(self, titulo, columnas):
        super(Frame, self).__init__(titulo)
        self.scroll = Gtk.ScrolledWindow()
        self.add(self.scroll)
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.treeview = TreeView(Gtk.ListStore(str))
        self.set_columnas(columnas)
        self.treeview.connect('row-activated', self.activated)
        self.scroll.add(self.treeview)

    def get_model(self):
        return self.treeview.get_model()

    def set_columnas(self, columnas):
        liststore = []
        self.columnas = columnas
        for i, c in enumerate(columnas):
            if c[0] == '*':
                liststore.append(GObject.TYPE_PYOBJECT)
            else:
                liststore.append(str)
        liststore.append(GObject.TYPE_INT64)
        self.set_liststore(liststore)

    def set_columnas_only(self, columnas):
        liststore = []
        self.columnas = columnas
        for i, c in enumerate(columnas):
            liststore.append(str)
        self.set_liststore(liststore)

    def set_columnas_object(self, columnas):
        liststore = []
        self.columnas = columnas
        for i, c in enumerate(columnas):
            liststore.append(str)
        liststore.append(GObject.TYPE_PYOBJECT)
        self.set_liststore(liststore)

    def set_liststore(self, liststore):
        cols = self.treeview.get_columns()
        for c in cols:
            self.treeview.remove_column(c)
        self.liststore = liststore
        self.model = Gtk.ListStore(*self.liststore)
        self.treeview.set_model(self.model)
        for i, c in enumerate(self.columnas):
            if c[0] == '*':
                break
            if self.liststore[i] == Gtk.gdk.Pixbuf:
                cell = Gtk.CellRendererPixbuf()
                tvcolumn = TreeViewColumn(c)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'pixbuf', i)
            elif self.liststore[i] == bool:
                cell = Gtk.CellRendererToggle()
                tvcolumn = TreeViewColumn(c)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'active', i)
            elif self.liststore[i] == GObject.TYPE_PYOBJECT:
                pass
            else:
                cell = Gtk.CellRendererText()
                tvcolumn = TreeViewColumn(c)
                tvcolumn.pack_start(cell, True)
                tvcolumn.set_attributes(cell, markup=i)
            if i == 0:
                tvcolumn.set_expand(True)
            self.treeview.append_column(tvcolumn)
            tvcolumn.encabezado()


    def activated(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            self.path = int(path[0])
            row = self.model[path]
        except:
            return False
        self.emit('activado', row)

    def activated(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            self.path = int(path[0])
            row = self.model[path]
        except:
            return False
        self.emit('activado', row)

    def get_selected(self, *args):
        try:
            path, column = self.treeview.get_cursor()
            path = int(path[0])
            row = self.model[path]
        except:
            return False
        return row

    def escribir(self, lista):
        self.model.clear()
        for l in lista:
            self.model.append(l)

    def modificar(self, nombre, _id, texto):
        i = 0
        for c in self.columnas:
            if c == nombre:
                for f in self.model:
                    if f[len(f) - 1] == _id:
                        f[i] = texto
                        return True
            i += 1
        print('Error', nombre, _id, texto)
        return False

    def set_size_request(self, x, y):
        self.scroll.set_size_request(x,  y)


class Alerta_TreeView(Dialog):

    def __init__(self, titulo, mensaje, frame, cabeceras, tabla, liststore=None, default=True):
        super(Alerta_TreeView, self).__init__(titulo)
        self.mensaje = mensaje
        if mensaje:
            self.label = Gtk.Label()
            self.label.set_markup(mensaje)
            self.background = Gtk.EventBox()
            self.background.add(self.label)
            self.vbox.pack_start(self.background, False, False, 10)
        self.treeview = TreeViewId(frame, cabeceras)
        self.vbox.pack_start(self.treeview)
        if liststore:
            self.treeview.set_liststore(liststore)
        self.treeview.escribir(tabla)
        but_salir = Button('delete.png', "_Cancelar")
        self.but_ok = Button('checkmark.png', "_Aceptar")
        self.add_action_widget(but_salir, Gtk.ResponseType.CANCEL)
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        if default:
            self.set_focus(self.but_ok)
        else:
            self.set_focus(but_salir)
        self.show_all()

    def set_background(self, color):
        self.background.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(color))

    def set_text_color(self, color):
        self.label.set_markup('<span color="%s">%s</span>' % (color, self.mensaje))

    def set_mensaje(self, text):
        self.mensaje = text
        self.label.set_markup(text)

    def iniciar(self):
        if self.run() == Gtk.ResponseType.OK:
            return True
        else:
            return False

    def cerrar(self, *args):
        self.destroy()


class Notebook(Gtk.Notebook):

    def __init__(self):
        super(Notebook, self).__init__()

        self.modify_bg(Gtk.StateType(0), Gdk.color_parse('#FFFFFF'))  # NORMAL
        self.modify_bg(Gtk.StateType(4), Gdk.color_parse('#e5e8e8'))  # INSENSITIVE
        self.modify_bg(Gtk.StateType(1), Gdk.color_parse('#e5e8e8'))  # active
        self.modify_bg(Gtk.StateType(3), Gdk.color_parse('#f8fbfc'))  # selected
        self.modify_bg(Gtk.StateType(2), Gdk.color_parse('#e5f1f4'))  # prelight

class Statusbar(Gtk.Label):

    def __init__(self):
        super(Statusbar, self).__init__()
        self.set_alignment(0, 0.5)

    def push(self, texto):
        self.set_markup(f'<span color="#FFF">{texto}</span>')


class Window(Gtk.Window):

    def __init__(self, titulo):
        super(Window, self).__init__(Gtk.WindowType.TOPLEVEL)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title(titulo)
        self.vbox = Gtk.VBox(False, 0)
        self.add(self.vbox)
        self.action_area = Gtk.HBox(False, 0)
        self.vbox.pack_end(self.action_area, False, False, 0)
        self.connect("delete_event", self.cerrar)

    def crear_boton(self, imagen, label, funcion):
        boton = Button(imagen, label)
        boton.connect('clicked', funcion)
        self.action_area.pack_end(boton, False, False, 0)
        return boton

    def cerrar(self, *args):
        self.destroy()

class Configuracion(Dialog):

    def __init__(self, http):
        super(Configuracion, self).__init__('Configuración')
        self.ticketera = http.ticketera
        self.http = http
        frame = Frame('CONFIGURACIÓN DE TICKETERA')
        frame.set_property('shadow-type', Gtk.ShadowType.OUT)
        self.vbox.pack_start(frame, False, False, 5)
        vbox = Gtk.VBox(False, 10)
        hbox = Gtk.HBox(True, 0)
        frame.add(vbox)
        tabla = Gtk.Table(2, 7)
        # tabla.set_col_spacings(5)
        tabla.set_row_spacings(5)
        vbox.pack_start(hbox, False, False, 10)
        hbox.pack_start(tabla, True, True, 10)
        self.lista = [('LPT1', 1), ('LPT2', 2), ('LPT3', 3)]
        self.lista_tarjeta = []
        i = 3
        for p in self.ticketera.seriales:
            i += 1
            self.lista.append((p, i))
        if os.name == 'nt':
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers:
                i += 1
                self.lista.append((p[2], i))
                self.lista_tarjeta.append((p[2], i))
        label = Gtk.Label('Ticketera por Defecto: ')
        label.set_alignment(0, 0.5)
        tabla.attach(label, 0, 1, 0, 1, Gtk.FILL, Gtk.EXPAND)
        self.combo = ComboBox()
        self.combo.set_lista(self.lista)
        tabla.attach(self.combo, 1, 2, 0, 1)
        label = Gtk.Label('Ticketera SUNAT: ')
        label.set_alignment(0, 0.5)
        tabla.attach(label, 0, 1, 1, 2, Gtk.FILL, Gtk.EXPAND)
        self.comboSunat = ComboBox()
        self.comboSunat.set_lista(self.lista)
        tabla.attach(self.comboSunat, 1, 2, 1, 2)
        label = Gtk.Label('Imprimir con Formato')
        label.set_alignment(0, 0.5)
        tabla.attach(label, 0, 1, 2, 3)
        self.formato = Gtk.CheckButton()
        tabla.attach(self.formato, 1, 2, 2, 3)
        label = Gtk.Label('Espacios al final del ticket')
        label.set_alignment(0, 0.5)
        tabla.attach(label, 0, 1, 3, 4)
        self.espacios = Numero(2)
        tabla.attach(self.espacios, 1, 2, 3, 4)
        self.radio_sin_corte = Gtk.RadioButton(None, 'Sin Corte de Papel')
        tabla.attach(self.radio_sin_corte, 0, 1, 4, 5)
        self.radio_corte = Gtk.RadioButton(self.radio_sin_corte, 'Corte por defecto')
        tabla.attach(self.radio_corte, 0, 1, 5, 6)
        self.radio_corte_custom = Gtk.RadioButton(self.radio_sin_corte, 'Corte Personalizado')
        tabla.attach(self.radio_corte_custom, 0, 1, 6, 7)
        self.entry_corte = Texto(24)
        tabla.attach(self.entry_corte, 1, 2, 6, 7)
        button = Button(None, 'Probar Ticketera')
        button.connect('clicked', self.probar)
        tabla.attach(button, 0, 2, 7, 8)

        frame = Frame('CONFIGURACIÓN DE IMPRESORA')
        frame.set_property('shadow-type', Gtk.ShadowType.IN)
        self.vbox.pack_start(frame, False, False, 0)
        vbox = Gtk.VBox(False, 0)
        frame.add(vbox)
        hbox = Gtk.HBox(False, 10)
        vbox.pack_start(hbox, False, False, 10)
        label = Gtk.Label('Impresora de Tarjetas')
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, False, False, 10)
        self.combo_tarjetas = ComboBox()
        hbox.pack_start(self.combo_tarjetas, True, True, 10)
        self.combo_tarjetas.set_lista(self.lista_tarjeta)
        button = Button(None, 'Probar Impresora')
        button.connect('clicked', self.probar_impresora)
        hbox = Gtk.HBox(False, 0)
        vbox.pack_start(hbox)
        hbox.pack_start(button, True, True, 10)

        frame = Frame('CONFIGURACIÓN DEL NAVEGADOR WEB')
        frame.set_property('shadow-type', Gtk.ShadowType.IN)
        self.vbox.pack_start(frame, False, False, 0)
        vbox = Gtk.VBox(False, 0)
        frame.add(vbox)
        hbox = Gtk.HBox(False, 10)
        vbox.pack_start(hbox, False, False, 10)
        label = Gtk.Label('Navegador')
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, False, False, 10)
        self.combo_browsers = ComboBox()
        hbox.pack_start(self.combo_browsers, True, True, 10)
        self.lista_browsers = [
            ('chrome', 1),
            ('firefox', 2),
            ('opera', 3),
            ('edge', 4),
            ('windows-default', 5)
        ]
        self.combo_browsers.set_lista(self.lista_browsers)
        self.combo_browsers.connect('changed', self.update_browser)
        self.entry_browser = Texto(256)
        hbox = Gtk.HBox(False, 0)
        label = Gtk.Label('Ubicación:')
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(label, False, False, 10)
        hbox.pack_start(self.entry_browser, True, True, 0)
        button = Button('buscar.png', None, 16, 'Buscar ejecutable')
        button.connect('clicked', self.choose_file)
        hbox.pack_start(button, False, False, 10)

        but_excel = Button('excel.png', 'XLS')
        self.action_area.pack_start(but_excel, False, False, 0)
        but_excel.connect('clicked', self.excel_dialog)
        self.but_ok = Button('guardar.png', "Guardar")
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.but_salir = Button('delete.png', "_Salir")
        self.add_action_widget(self.but_salir, Gtk.ResponseType.CANCEL)
        self.set_focus(self.but_salir)
        self.iniciar()

    def iniciar(self):
        self.show_all()
        config = self.ticketera.config
        if 'puerto' in config:
            for s, i in self.lista:
                if s == config['puerto']:
                    self.combo.set_id(i)
        if 'sunat' in config:
            for s, i in self.lista:
                if s == config['sunat']:
                    self.comboSunat.set_id(i)
        if 'tarjeta' in config:
            for s, i in self.lista:
                if s == config['tarjeta']:
                    self.combo_tarjetas.set_id(i)
        if isinstance(config['corte'], str) or isinstance(config['corte'], str):
            print('str', config['corte'])
            self.radio_corte_custom.set_active(True)
            self.entry_corte.set_text(config['corte'])
        elif config['corte'] is True:
            print('true', config['corte'])
            self.radio_corte.set_active(True)
        elif config['corte'] is False:
            print('false', config['corte'])
            self.radio_sin_corte.set_active(True)
        self.formato.set_active(config['formato'])
        self.espacios.set_text(str(config['lineas_final']))

        self.combo_browsers.set_text(self.http.config.browser)
        if self.http.config.browser == 'chrome':
            self.entry_browser.set_text(self.http.config.chrome)
        elif self.http.config.browser == 'firefox':
            self.entry_browser.set_text(self.http.config.firefox)
        elif self.http.config.browser == 'opera':
            self.entry_browser.set_text(self.http.config.opera)
        elif self.http.config.browser == 'edge':
            self.entry_browser.set_text(self.http.config.edge)
        else:
            self.combo_browsers.set_text('windows-default')

        if self.run() == Gtk.ResponseType.OK:
            puerto = self.combo.get_text()
            sunat = self.comboSunat.get_text()
            tarjeta = self.combo_tarjetas.get_text()
            if self.radio_corte.get_active():
                corte = True
            elif self.radio_sin_corte.get_active():
                corte = False
            else:
                corte = self.entry_corte.get_text()
            self.ticketera.config['tarjeta'] = tarjeta
            self.ticketera.config['puerto'] = puerto
            self.ticketera.config['sunat'] = sunat
            self.ticketera.config['corte'] = corte
            self.ticketera.config['formato'] = self.formato.get_active()
            self.ticketera.config['lineas_final'] = self.espacios.get_int()
            self.ticketera.guardar_config()
            self.ticketera.set_config()

            browser = self.combo_browsers.get_text()
            if browser == 'chrome':
                self.http.config.chrome = self.entry_browser.get_text()
            elif browser == 'firefox':
                self.http.config.firefox = self.entry_browser.get_text()
            elif browser == 'opera':
                self.http.config.opera = self.entry_browser.get_text()
            elif browser == 'edge':
                self.http.config.edge = self.entry_browser.get_text()
            self.http.config.save()
            return True
        else:
            return False

    def update_browser(self, *args):
        self.entry_browser.set_sensitive(True)
        self.http.config.browser = self.combo_browsers.get_text()
        if self.http.config.browser == 'chrome':
            browser = self.http.config.chrome
        elif self.http.config.browser == 'firefox':
            browser = self.http.config.firefox
        elif self.http.config.browser == 'opera':
            browser = self.http.config.opera
        elif self.http.config.browser == 'edge':
            browser = self.http.config.edge
        else:
            browser = ''
            self.entry_browser.set_sensitive(False)
        self.entry_browser.set_text(browser)

    def choose_file(self, *args):
        dlg = Gtk.FileChooserDialog(title='Encuentre la ruta al Navegador', parent=self,
                                    action=Gtk.FILE_CHOOSER_ACTION_OPEN,
                                    buttons=('Seleccionar', Gtk.ResponseType.OK, 'Cancelar', Gtk.ResponseType.CANCEL),
                                    backend=None)
        response = dlg.run()
        print(('response', response))
        if response == Gtk.ResponseType.OK:
            if dlg.get_filename():
                self.entry_browser.set_text(dlg.get_filename())
        dlg.destroy()

    def probar(self, *args):
        self.ticketera.probar()

    def probar_impresora(self, *args):
        Impresion.Test()

    def excel_dialog(self, *args):
        dialog = Excel_Dialog(self.http)
        dialog.cerrar()

    def cerrar(self, *args):
        self.destroy()


class Excel_Dialog(Dialog):
    UNIDADES = ('', 'UN ', 'DOS ', 'TRES ', 'CUATRO ', 'CINCO ', 'SEIS ', 'SIETE ', 'OCHO ', 'NUEVE ', 'DIEZ ', 'ONCE ', 'DOCE ', 'TRECE ', 'CATORCE ', 'QUINCE ', 'DIECISEIS ', 'DIECISIETE ', 'DIECIOCHO ', 'DIECINUEVE ', 'VEINTE ')
    DECENAS = ('VENTI', 'TREINTA ', 'CUARENTA ', 'CINCUENTA ', 'SESENTA ', 'SETENTA ', 'OCHENTA ', 'NOVENTA ', 'CIEN ')
    CENTENAS = ('CIENTO ', 'DOSCIENTOS ', 'TRESCIENTOS ', 'CUATROCIENTOS ', 'QUINIENTOS ', 'SEISCIENTOS ', 'SETECIENTOS ', 'OCHOCIENTOS ', 'NOVECIENTOS '  )

    def __init__(self, http):
        super(Excel_Dialog, self).__init__('Impresión de Excel')
        self.ticketera = http.ticketera
        self.http = http
        self.set_size_request(350, 250)
        frame = Frame('CONFIGURACIÓN DE IMPRESION')
        frame.set_property('shadow-type', Gtk.ShadowType.OUT)
        self.vbox.pack_start(frame, False, False, 10)
        vbox = Gtk.VBox(False, 10)
        frame.add(vbox)
        tabla = Gtk.Table(2, 7)
        vbox.pack_start(tabla, False, False, 5)
        self.lista = [('LPT1', 1), ('LPT2', 2), ('LPT3', 3)]
        self.lista_tarjeta = []
        i = 3
        for p in self.ticketera.seriales:
            i += 1
            self.lista.append((p, i))
        if os.name == 'nt':
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            for p in printers:
                i += 1
                self.lista.append((p[2], i))
                self.lista_tarjeta.append((p[2], i))
        tabla.attach(Gtk.Label('Escoja un archivo: '), 0, 1, 1, 2)
        self.chooserdialog = Gtk.FileChooserDialog(action=Gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK))
        self.filechooser = Gtk.FileChooserButton(self.chooserdialog)
        tabla.attach(self.filechooser, 1, 2, 1, 2)
        tabla.attach(Gtk.Label('Nº Hoja'), 0, 1, 2, 3)
        self.hoja = Numero(3)
        tabla.attach(self.hoja, 1, 2, 2, 3)
        tabla.attach(Gtk.Label('Formato'), 0, 1, 3, 4)
        self.formato = ComboBox()
        formatos = self.http.load('templates', {'nada': True})
        self.formato.set_lista(formatos)
        tabla.attach(self.formato, 1, 2, 3, 4)
        tabla.attach(Gtk.Label('Fila Inicial'), 0, 1, 4, 5)
        self.inicial = Numero(6)
        tabla.attach(self.inicial, 1, 2, 4, 5)
        tabla.attach(Gtk.Label('Fila Final'), 0, 1, 5, 6)
        self.final = Numero(6)
        tabla.attach(self.final, 1, 2, 5, 6)
        self.but_ok = Button('checkmark.png', "Aceptar")
        self.add_action_widget(self.but_ok, Gtk.ResponseType.OK)
        self.but_salir = Button('delete.png', "_Salir")
        self.add_action_widget(self.but_salir, Gtk.ResponseType.CANCEL)
        self.set_focus(self.but_salir)
        self.iniciar()

    def iniciar(self):
        self.show_all()
        if self.run() == Gtk.ResponseType.OK:
            path = self.chooserdialog.get_filename()
            try:
                book = xlrd.open_workbook(path)
            except:
                Alerta('Error', 'error.png', 'Error al abrir el archivo')
                return False
            try:
                sheet = book.sheet_by_index(self.hoja.get_int() - 1)
            except:
                Alerta('Error', 'error.png', 'Error número de página inválido')
                return False
            template = self.http.load('templates', {'id': self.formato.get_id()})
            if template:
                for i in range(sheet.nrows):
                    if self.inicial.get_int() - 1 <= i <= self.final.get_int() - 1:
                        self.imprimir(sheet.row(i), template)
            else:
                Alerta('Error', 'error.png', 'Error al descargar la plantilla')
                return False
            return True
        else:
            return False

    def numero_a_letras(self, n):
        number_in = int(n)
        decim = int(n * 100 - number_in * 100)
        convertido = ''
        number_str = str(number_in) if (type(number_in) != 'str') else number_in
        number_str =  number_str.zfill(9)
        millones, miles, cientos = number_str[:3], number_str[3:6], number_str[6:]
        if(millones):
            if(millones == '001'):
                convertido += 'UN MILLON '
            elif(int(millones) > 0):
                convertido += '%sMILLONES ' % self.convertNumber(millones)
        if(miles):
            if(miles == '001'):
                convertido += 'MIL '
            elif(int(miles) > 0):
                convertido += '%sMIL ' % self.convertNumber(miles)
        if(cientos):
            if(cientos == '001'):
                convertido += 'UN '
            elif(int(cientos) > 0):
                convertido += '%s' % self.convertNumber(cientos)
        convertido += 'CON %s/100 ' % str(decim).zfill(2)
        return convertido

    def convertNumber(self, n):
        output = ''
        if(n == '100'):
            output = "CIEN"
        elif(n[0] != '0'):
            output = self.CENTENAS[int(n[0])-1]
        k = int(n[1:])
        if(k <= 20):
            output += self.UNIDADES[k]
        else:
            if((k > 30) & (n[2] != '0')):
                output += '%sY %s' % (self.DECENAS[int(n[1])-2], self.UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (self.DECENAS[int(n[1])-2], self.UNIDADES[int(n[2])])
        return output

    def imprimir(self, row, template):
        i = 0
        ticket = []
        for line in template['template']:
            comand = line[:]
            datos = template['datos'][i]
            if datos:
                replace = []
                for d in datos:
                    if isinstance(d, int):
                        if isinstance(row[d].value, str):
                            replace.append(row[d].value[:25])
                        else:
                            replace.append(row[d].value)
                    else:
                        replace.append(self.numero_a_letras(row[int(d.split(' ')[1])].value))
                comand[1] = comand[1].format(*replace)
            ticket.append(comand)
            i += 1
        self.ticketera.imprimir(ticket)
        time.sleep(2)


    def cerrar(self, *args):
        self.destroy()

Gtk.rc_parse_string("""
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
GObject.type_register(Cell)

screen = Gdk.Screen.get_default()
gtk_provider = Gtk.CssProvider()
gtk_context = Gtk.StyleContext()
gtk_context.add_provider_for_screen(screen, gtk_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

css = """
Gtk.Button.green{background: green;}
GtkButton.white{background: white;}
GtkCellRenderer{background: blue;}
column-header.button {background-color:blue;color:red}
"""
gtk_provider.load_from_data(bytes(css.encode()))

def currency(entero):
    return "%.2f" % (entero / 100.)


def quantity(entero):
    return "%.3f" % (entero / 1000.)




if __name__ == '__main__':
    a = Alerta_FechaNumero('Titulo', 'money.png', 'Detalle de prueba\nFASDF')
    # from Principal import Http
    # http = Http([])
    # a = Configuracion(http)
    a.show_all()
    Gtk.main()