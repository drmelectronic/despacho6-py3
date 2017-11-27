#! /usr/bin/python
# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

import xlwt
import Widgets
borders = xlwt.Borders()
borders.left = xlwt.Borders.THIN
borders.right = xlwt.Borders.THIN
borders.top = xlwt.Borders.THIN
borders.bottom = xlwt.Borders.THIN
dotted = xlwt.Borders()
dotted.left = xlwt.Borders.DOTTED
dotted.right = xlwt.Borders.DOTTED
gris = xlwt.Pattern()
gris.pattern = xlwt.Pattern.SOLID_PATTERN
gris.pattern_fore_colour = 22
izquierda = xlwt.Alignment()
izquierda.horz = xlwt.Alignment.HORZ_LEFT
izquierda.vert = xlwt.Alignment.VERT_CENTER
centrado = xlwt.Alignment()
centrado.horz = xlwt.Alignment.HORZ_CENTER
centrado.vert = xlwt.Alignment.VERT_CENTER
derecha = xlwt.Alignment()
derecha.horz = xlwt.Alignment.HORZ_RIGHT
derecha.vert = xlwt.Alignment.VERT_CENTER
font = xlwt.Font()
font.name = 'Arial'
font.bold = True
# titulo
estilo_titulo = xlwt.XFStyle()
estilo_titulo.alignment = centrado
estilo_titulo.font = font
estilo_titulo.pattern = gris
estilo_titulo.borders = borders
# subtitulo
estilo_subtitulo = xlwt.XFStyle()
estilo_subtitulo.alignment = centrado
estilo_subtitulo.font = font
estilo_subtitulo.borders = borders
# cabeceras
estilo_bold = xlwt.XFStyle()
estilo_bold.borders = borders
estilo_bold.pattern = gris
estilo_bold.alignment = centrado
estilo_bold.font = font
# nombre de campo
estilo_campo = xlwt.XFStyle()
estilo_campo.alignment = izquierda
estilo_campo.font = font
# campos fuera de tabla
estilo_texto = xlwt.XFStyle()
estilo_texto.alignment = derecha
# fecha campo
estilo_fecha = xlwt.XFStyle()
estilo_fecha.num_format_str = 'DD-MM-YY'
estilo_fecha.alignment = derecha
# hora campo
estilo_hora = xlwt.XFStyle()
estilo_hora.num_format_str = 'HH:MM'
estilo_hora.alignment = derecha

# TABLA
# texto en toda la tabla
estilo_par = xlwt.XFStyle()
estilo_par.borders = dotted
estilo_par.pattern = xlwt.Pattern()
estilo_par.alignment = centrado
estilo_impar = xlwt.XFStyle()
estilo_impar.borders = dotted
estilo_impar.pattern = xlwt.Pattern()
estilo_impar.alignment = centrado
estilo_impar.pattern = gris
estilo = [estilo_par, estilo_impar]
# nombre de personal en la tabla
estilo_personal_par = xlwt.XFStyle()
estilo_personal_par.borders = dotted
estilo_personal_par.alignment = izquierda
estilo_personal_impar = xlwt.XFStyle()
estilo_personal_impar.borders = dotted
estilo_personal_impar.alignment = izquierda
estilo_personal_impar.pattern = gris
estilo_personal = [estilo_personal_par, estilo_personal_impar]
# total
estilo_total_par = xlwt.XFStyle()
estilo_total_par.borders = dotted
estilo_total_par.alignment = centrado
estilo_total_par.font = font
estilo_total_impar = xlwt.XFStyle()
estilo_total_impar.borders = dotted
estilo_total_impar.alignment = centrado
estilo_total_impar.font = font
estilo_total_impar.pattern = gris
estilo_total = [estilo_total_par, estilo_total_impar]
# fecha tabla
estilo_fecha_borde_par = xlwt.XFStyle()
estilo_fecha_borde_par.num_format_str = 'DD-MM-YY'
estilo_fecha_borde_par.borders = dotted
estilo_fecha_borde_par.alignment = centrado
estilo_fecha_borde_impar = xlwt.XFStyle()
estilo_fecha_borde_impar.num_format_str = 'DD-MM-YY'
estilo_fecha_borde_impar.borders = dotted
estilo_fecha_borde_impar.alignment = centrado
estilo_fecha_borde_impar.pattern = gris
estilo_fecha_borde = [estilo_fecha_borde_par, estilo_fecha_borde_impar]
#hora_tabla
estilo_hora_borde_par = xlwt.XFStyle()
estilo_hora_borde_par.num_format_str = 'HH:MM'
estilo_hora_borde_par.borders = dotted
estilo_hora_borde_par.alignment = centrado
estilo_hora_borde_impar = xlwt.XFStyle()
estilo_hora_borde_impar.num_format_str = 'HH:MM'
estilo_hora_borde_impar.borders = dotted
estilo_hora_borde_impar.alignment = centrado
estilo_hora_borde_impar.pattern = gris
estilo_hora_borde = [estilo_hora_borde_par, estilo_hora_borde_impar]

import datetime
from reportlab.pdfgen import canvas
import os
import json
from reportlab.lib.pagesizes import legal, cm, A4, letter
import time
if os.name == 'nt':
    import win32api
else:
    import sh

class Impresion:
    normal = 'Courier'
    #bold = 'FreeMonoBold'
    #normal = 'Helvetica'
    #bold = 'Helvetica'
    bold = 'Courier-Bold'

    def __init__(self, tarjeta, datos):
        self.tarjeta = tarjeta
        self.datos = datos
        self.imprimir()

    def set_font(self, s):
        if s > 16:
            self.pdf.setFont(self.bold, s)
        else:
            self.pdf.setFont(self.normal, s)

    def escribir(self, x, y, a, d):
        if a < 0:
            f = self.pdf.drawString
        elif a == 0:
            f = self.pdf.drawCentredString
        else:
            f = self.pdf.drawRightString
        f(x + self.mx, self.A4y - y - self.my, unicode(d))

    def decode(self, tarjeta, datos, direccion=None):
        for k in tarjeta.keys():
            if isinstance(tarjeta[k], dict):
                for f in tarjeta[k].keys():
                    if len(tarjeta[k][f]) == 6:
                        x, y, p, d, s, a = tarjeta[k][f]
                        self.set_font(s)
                        for i in datos[k]:
                            try:
                                self.escribir(x, y, a, i[f])
                            except:
                                raise
                            if d:
                                y += p
                            else:
                                x += p
            elif len(tarjeta[k]) == 3:
                x, y, s = tarjeta[k]
                self.set_font(s)
                self.escribir(x, y, -1, datos[k])
            elif len(tarjeta[k]) == 4:
                x, y, s, a = tarjeta[k]
                self.set_font(s)
                self.escribir(x, y, a, datos[k])
            elif len(tarjeta[k]) == 5:
                xi, y, p, d, fields = tarjeta[k]
                for filas in datos[k]:
                    x = xi
                    i = 0
                    for f in fields:
                        if isinstance(f, list):
                            dif, a, s = f
                            if d:
                                x += dif
                            else:
                                y += dif
                            self.set_font(s)
                            self.escribir(x, y, a, filas[i])
                        i += 1
                    if d:
                        y += p
                    else:
                        x += p
            elif len(tarjeta[k]) == 6:
                x, y, p, d, s, a = tarjeta[k]
                self.set_font(s)
                for i in datos[k]:
                    self.escribir(x, y, a, i)
                    if d:
                        y += p
                    else:
                        x += p


    def imprimir(self):
        self.metodo = self.tarjeta['metodo']
        if self.metodo == 'pdf':
            self.path = 'outs/impresion.pdf'
            x, y = self.tarjeta['hoja']#x = 22.9 #y = 16.2
            self.A4x = x * cm
            self.A4y = y * cm
            self.pdf = canvas.Canvas(self.path, pagesize=(self.A4x, self.A4y))
            self.mx, self.my = self.tarjeta['margen']
            self.decode(self.tarjeta['campos'], self.datos)
            self.pdf.showPage()
            self.pdf.save()
        elif self.metodo == 'txt':
            self.path = 'outs/impresion.txt'
            texto = self.decode_texto(self.tarjeta, self.datos)
            f = file(self.path, 'wb')
            f.write(texto)
            f.close()
        if os.name == 'nt':
            a = os.path.abspath(self.path)
            if self.metodo == 'pdf':
                win32api.ShellExecute(0, "print", a, None, ".", 0)
                os.system('taskkill /im cmd.exe /f')
            elif self.metodo == 'txt':
                os.system('cd outs && DOSprinter.exe impresion.txt')
                os.system('taskkill /im cmd.exe /f')
        else:
            os.system("gtklp -C " + self.path)

    def decode_texto(self, tarjeta, datos):
        print tarjeta
        print datos
        formato = tarjeta['formato']
        formato_controles = tarjeta['formato_controles']
        controles = datos['controles']
        boletos = ''
        reservas = ''
        for b in datos['boletos']:
            boletos += b + tarjeta['espacio_boletos']
        for b in datos['reservas']:
            reservas += b + tarjeta['espacio_boletos']
        esc = chr(27)
        emph = esc + 'E'
        emphOFF = esc + 'F'
        lineplus = esc + '+' + chr(255)
        lineA = esc + chr(65) + chr(20)
        line3 = esc + '3' + chr(45)
        line2 = esc + '2'
        line0 = esc + '0'
        size10 = esc + 'g'
        size12 = esc + 'M'
        size15 = esc + 'P'
        parse = {
            'padron': emph + size15 + datos['padron'] + emphOFF + size12,
            'vuelta': datos['vuelta'],
            'placa': datos['placa'],
            'conductor': datos['conductor'],
            'dia': size10 + datos['dia'] + size12,
            'inicio': size15 +emph + datos['inicio'] + emphOFF + size12,
            'cobrador': datos['cobrador'],
            'impresion': size10 + datos['impresion'] + size12 + line3,
            0: size15 + controles[0],
            1: size15 + controles[1],
            'boletos': size15 + boletos,
            'reservas': size15 + reservas,
        }
        lista = []
        for l in tarjeta['lista']:
            lista.append(parse[l])
        print formato
        print lista[:-1]
        texto = formato % tuple(lista[:-1])
        controles_restantes = controles[tarjeta['lista'][-1]:]
        for c in controles_restantes:
            texto += formato_controles % c
        return texto


class Excel:

    _letras = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
        'W', 'X', 'Y', 'Z']

    def __init__(self, titulo, subtitulo, cabeceras, filas, widths):
        self.titulo = unicode(titulo)
        self.widths = widths
        self.subtitulo = unicode(subtitulo)
        self.cabeceras = cabeceras
        self.filas = filas
        self.archivo = 'outs/reporte.xls'
        self.wb = xlwt.Workbook()
        self.ws = self.insert_ws('REPORTE')
        self.escribir(self.ws)

    def insert_ws(self, nombre):
        ws = self.wb.add_sheet(nombre)
        ws.bottom_margin = 0.4
        ws.top_margin = 0.4
        ws.right_margin = 0.4
        ws.left_margin = 0.4
        return ws

    def letras(self, i):
        primera = i / 26
        segunda = i % 26
        return self._letras[primera] + self._letras[segunda + 1]

    def terminar_xls(self, ws):
        for i, c in enumerate(self.widths):
            ws.col(i).width = int(1312 * c)
        self.wb.save(self.archivo)

    def escribir(self, ws):
        ws.write_merge(0, 0, 0, len(self.widths) - 1, self.titulo, estilo_titulo)
        ws.write_merge(1, 1, 0, len(self.widths) - 1, self.subtitulo, estilo_subtitulo)
        for i, c in enumerate(self.cabeceras):
            print c
            ws.write(3, i, unicode(c), estilo_bold)
        y = 4
        for i, r in enumerate(self.filas):
            print list(r)
            for j in range(len(self.widths)):
                c = r[j]
                print c, type(c)
                if isinstance(c, datetime.time):
                    estilo = [estilo_hora_borde_par, estilo_hora_borde_impar]
                elif isinstance(c, datetime.date):
                    estilo = [estilo_fecha_borde_par, estilo_fecha_borde_impar]
                else:
                    estilo = [estilo_par, estilo_impar]
                    c = unicode(c)
                ws.write(y + i, j, c, estilo[i % 2])
        self.terminar_xls(ws)

from serial import Serial
from escpos import printer

class ESCPOS:

    def __init__(self):
        self.epson = None
        self.log = ''
        self.buscar_serial()
        try:
            ticket = open('outs/printer', 'rb')
            memoria = ticket.read()
            ticket.close()
        except:
            memoria = 'LPT1'
        if 'COM' in memoria:
            self.conectar_serial(memoria)

    def buscar_serial(self):
        num_ports = 20
        dispositivos_serie = []
        if os.name == 'nt':
            for i in range(num_ports):
                try:
                    s = Serial(port=i, baudrate=9600, bytesize=8, timeout=0)
                    s.write('\n\n')
                    s.close()
                except:
                    self.log += 'No se pudo conectar a COM%s\n' % i
                else:
                    dispositivos_serie.append(s.portstr)
        else:
            for i in range(num_ports):
                port = '/dev/ttyS%d' % i
                try:
                    s = Serial(port=port, baudrate=9600, bytesize=8, timeout=0)
                    s.close()
                except:
                    self.log += 'No se pudo conectar %s\n' % port
                else:
                    dispositivos_serie.append(port)
            for i in range(num_ports):
                port = '/dev/ttyUSB%d' % i
                try:
                    s = Serial(port=port, baudrate=9600, bytesize=8, timeout=0)
                    s.close()
                except:
                    self.log += 'No se pudo conectar %s\n' % port
                else:
                    dispositivos_serie.append(port)
        self.seriales = dispositivos_serie

    def conectar_serial(self, puerto):
        try:
            self.epson = printer.Serial(devfile=puerto, baudrate=9600, bytesize=8, timeout=0)
        except:
            self.epson = None
        else:
            print self.epson
            print dir(self.epson)
            print self.epson.timeout
        print 'IMPRESORA=', self.epson
        ticket = open('outs/printer', 'wb')
        ticket.write('LPT1')
        ticket.close()
        self.probar()
        ticket = open('outs/printer', 'wb')
        ticket.write(puerto)
        ticket.close()
        #print 'a usb'
        #self.epson = printer.Usb(0x1a86,0x7584, 0, 0x82, 0x02)
        #print self.epson

    def probar(self):
        print 'probar'
        comandos = ((('CENTER', 'b', 'normal', 1, 1), '----  %s  ----' % datetime.datetime.now()),)
        self.imprimir(comandos)

    def reimprimir(self):
        print 'reimprimir'
        ticket = open('outs/ticket.lst', 'rb')
        comandos = json.loads(ticket.read())
        comandos.preppend((('LEFT', 'b', 'u', 1, 1), '*** DUPLICADO. Hora: %s ***' % datetime.datetime.now()))
        ticket.close()
        self.imprimir(comandos)

    def paralela(self):
        self.epson = None
        ticket = open('outs/printer', 'wb')
        ticket.write('LPT1')
        ticket.close()

    def imprimir(self, comandos):
        print 'IMPRIMIR *****'
        texto = json.dumps(comandos)
        ticket = open('outs/ticket.lst', 'wb')
        ticket.write(texto)
        ticket.close()
        if self.epson is None:
            ticket = open('outs/ticket.lpt', 'wb')
            previa = open('outs/ticket.txt', 'wb')
            texto = ''
            vista = ''
            esc = chr(27)
            emph = esc + 'E'
            emphOFF = esc + 'F'
            dubStrike = esc + 'G'
            dubStrikeOFF = esc + 'H'
            cutpaper = esc + chr(105)
            bold = emph + dubStrike
            boldOFF = emphOFF + dubStrikeOFF
            for c in comandos:
                if c is None:
                    texto += '\n'
                    vista += '\n'
                else:
                    if 'LEFT' == c[0][0]:
                        texto += chr(27) + chr(97) + chr(0)
                    if 'CENTER' == c[0][0]:
                        texto += chr(27) + chr(97) + chr(1)
                    if 'RIGHT' == c[0][0]:
                        texto += chr(27) + chr(97) + chr(2)
                    if 'u' in c[0][2]:
                        texto += chr(27) + chr(45) + chr(49)
                    if 'b' in c[0][2]:
                        texto += chr(27) + chr(97) + chr(2)
                    texto += c[1]
                    vista += c[1]
                    if 'u' in c[0][2]:
                        texto += chr(27) + chr(45) + chr(48)
            #texto += '\n' * 9
            texto += '\n' * 2
            texto += cutpaper
            ticket.write(texto)
            ticket.close()
            previa.write(vista)
            previa.close()
            print 'PARALELA'
            print vista
            if os.name == 'nt':
                os.system('cd outs && type ticket.lpt > LPT1')
                #os.system('cd outs && type ticket.txt > USB001')
            print 'fin'
            return
        print 'imprimir', self.epson
        vista = ''
        for c in comandos:
            if c is None:
                self.epson.control('LF')
                vista += '\n'
            else:
                self.epson.set(*c[0])
                self.epson.text(c[1])
                vista += c[1]
            print 'i'
        previa = open('outs/ticket.txt', 'wb')
        previa.write(vista)
        previa.close()
        print 'SERIAL'
        print vista
        self.epson.control('VT')
        self.epson.control('VT')
        self.epson.control('LF')
        self.epson.control('LF')

# epson = ESCPOS()
# print epson.log
# comandos = (
#     (('CENTER', 'b', 'bu2', 2, 2), 'TITULO\n'),
#     (('CENTER', 'a', 'b', 1, 1), 'SUBTITULO'),
#     (None),
#     (('LEFT', 'b', 'u', 1, 1), '1234567890123456789012301234567890\n'),
#     (('LEFT', 'a', 'normal', 1, 1), 'Contenido\nvarias lineas'),
#     (None),
#     (('RIGHT', 'b', 'normal', 1, 1), 'Pie de pagina\n'),
# )
# epson.imprimir(comandos)
#tarjeta, datos = [{"hoja": [21, 29], "margen": [0, 40], "campos": {"conductor": [140, 30, 10, -1], "controles": [31, 90, 17, 1, 14, -1], "inicio": [70, 56, 17, 1], "boletos": [135, 83, 53.5, 0, 14, 0], "cobrador": [140, 42, 10, -1], "dia": [520, 20, 13, -1], "placa": [45, 40, 11, 1], "produccion": [192, 57, 60, 0, 14, 1], "impresion": [520, 36, 12, -1], "padron": [55, 23, 20, 1], "vuelta": [140, 18, 16, -1], "total": [520, 57, 14, 1], "reservas": [135, 98, 53.5, 0, 14, 0]}, "metodo": "pdf"}, {"conductor": "AJALCRI\u00d1A QUISPE EDWIN JOSE", "cobrador": "AGUILAR FLORES ROLANDO", "reservas": ["", "", "", "", "", "", ""], "boletos": ["448201", "196001", "428501", "374501", "604001", "891501", "185001"], "padron": "25", "vuelta": "0.5", "total": "0.00", "controles": ["05:01", "05:16", "05:30", "05:42", "06:05", "06:13", "06:29", "06:47"], "dia": "22-08-2015", "placa": "A7Y-789", "produccion": ["0.00"], "impresion": "18:40:45", "inicio": "04:53"}]
#t = Impresion(tarjeta, datos)
#t.imprimir()
