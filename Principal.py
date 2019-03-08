#! /usr/bin/python
# -*- encoding: utf-8 -*-
import gtk
import Salidas
import Modulos
import Widgets
import threading
import urllib3
import Chrome
import gobject
import json
import os
import time
import socket
import Sonido
import Impresion
import pickle
import datetime

try:
    a = os.path.abspath("outs/root.dll")
    archivo = open(a, 'rb')
    content = archivo.read()
    archivo.close()
    d = json.loads(content)
    beta = d['beta']
except:
    beta = 0
local = 1
print 'local', local
if os.name != 'nt':
    beta = 1
    import sh
infinito = True
version = 5.90
dia = 'Actualización viernes 27 de febrero de 2019'
if local:
    localhost = 'localhost'
    appengine_ip = appengine = localhost
    web = web_pack = compute = titulo = localhost
else:
    titulo = 'Sistema de Despacho TCONTUR v%s' % version
    compute = '104.197.24.168'
    if beta:
        appengine_ip = appengine = 'beta.default.tcontur2.appspot.com'
    else:
        appengine_ip = appengine = 'main.despacho.tcontur2.appspot.com'
    test = urllib3.HTTPConnectionPool('urbano.tcontur.com')
    try:
        test.urlopen('HEAD', '/', assert_same_host=False)
    except:
        web = 'default.tcontur2.appspot.com'
    else:
        web = 'urbano.tcontur.com'
    print(web)
    try:
        ips = socket.gethostbyname_ex(appengine)
    except socket.gaierror:
        pass
    else:
        print(ips)
        for ip in ips:
            if isinstance(ip, list) and len(ip) > 0:
                digit = True
                for n in ip[0].split('.'):
                    if not n.isdigit():
                        digit = False

                if digit:
                    appengine_ip = ip[0]
                    break

import webbrowser

gobject.threads_init()

class Splash(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.show_all()
        path = os.path.join('images', 'splash.png')
        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
        pixmap, mask = pixbuf.render_pixmap_and_mask()
        width, height = pixmap.get_size()
        del pixbuf
        self.set_app_paintable(True)
        self.resize(width, height)
        self.realize()
        self.window.set_back_pixmap(pixmap, False)
        self.show_all()
        gobject.idle_add(self.aplicacion)

    def aplicacion(self, *args):
        self.a = Aplicacion()
        self.hide_all()


class Aplicacion():

    def __init__(self):
        self.grupo = gtk.WindowGroup()
        self.ventanas = []
        self.http = Http(self.ventanas)
        self.sessionid = None
        Chrome.init()
        self.ventana = self.salidas()
        self.login()

    def login(self, *args):
        dialog = Widgets.Login(self.http)
        s.hide_all()
        respuesta = dialog.iniciar()
        if respuesta:
            self.ventana.login(dialog.sessionid)
            self.sessionid = dialog.sessionid
            self.usuario = dialog.user
            self.password = dialog.pw
            dialog.cerrar()
        else:
            dialog.cerrar()

    def salidas(self, *args):
        global version
        global dia
        status_bar = Widgets.Statusbar()
        status_bar.push(dia)
        herramientas = [('Nueva Ventana (Ctrl + N)', 'salidas.png', self.salidas)]
        toolbar = Widgets.Toolbar(herramientas)
        twist = Widgets.ButtonTwist('desconectado.png', 'conectado.png', tooltip='Reconectar al servidor GPS')
        ticketera = Widgets.Button('imprimir.png', '', 16, tooltip='Configuración de Impresión')
        ventana = Salidas.Ventana(self, titulo, toolbar, twist, status_bar, version, ticketera)
        self.grupo.add_window(ventana)
        ventana.present()
        self.ventanas.append(ventana)
        ventana.connect('cerrar', self.cerrar)
        ventana.connect('login', self.login)
        ventana.connect('salidas', self.salidas)
        twist.connect('clicked', self.http.twist.resume)
        ticketera.connect('button-press-event', self.ticketera)
        if len(self.ventanas) > 1:
            ventana.login(self.sessionid)
        ventana.grab_focus()
        return ventana

    def ticketera(self, widgets, event):
        dialogo = Widgets.Configuracion(self.http)
        self.http.limpiarData()
        dialogo.cerrar()

    def cerrar(self, ventana):
        self.ventanas.remove(ventana)
        del ventana
        if len(self.ventanas) == 0:
            try:
                self.http.load('salir')
            except:
                pass
            gtk.main_quit()


class Reloj(gtk.EventBox):
    __gsignals__ = {'tic-tac': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())}

    def __init__(self):
        super(Reloj, self).__init__()
        self.hilo = threading.Thread(target=self.run)
        self.hilo.daemon = False
        self.hilo.start()

    def run(self):
        global infinito
        while infinito:
            gtk.gdk.threads_enter()
            self.emit('tic-tac')
            gtk.gdk.threads_leave()
            time.sleep(1)

    def cerrar(self):
        global infinito
        infinito = False
        self.hilo.join()


class Http():
    fondos = None
    multas = None
    dataServer = {}

    def __init__(self, ventanas):
        global web
        global compute
        global appengine
        global appengine_ip
        self.conn = urllib3.HTTPConnectionPool(appengine_ip)
        self.ventanas = ventanas
        self.funciones = [self.nada]
        self.signals = {'update': self.funciones}
        self.compute = compute
        self.appengine = appengine
        self.server = '/despacho/'
        self.dominio = appengine
        self.web = web
        self.csrf = ''
        self.login_ok = False
        self.timeout = None
        self.backup = False
        self.backup_urls = ('actualizar-tablas', 'solo-unidad', 'unidad-salida', 'datos-salida', 'flota-llegada')
        self.backup_dia = None
        self.headers = {'Cookie': '',
            'Origin': appengine,
            'Host': appengine,
            'Content-Type': 'application/x-www-form-urlencoded'}
        self.datos = {'rutas': (('Vacio', 0),),
            'despacho': None}
        try:
            f = open('outs/config', 'rb')
            self.config = json.loads(f.read())
            f.close()
        except:
            self.config = {}
        self.username = ''
        self.password = ''
        self.sessionid = ''
        self.nombre = ''
        self.empresa = 0
        self.version = version
        self.despachador = None
        self.despachador_id = None
        self.unidad = {}
        self.salida = {}
        self.pagos = {}
        self.castigos = []
        self.seriacion = []
        self.boletos_limites = []
        self.servicio = None
        self.grifo = False
        self.sonido = Sonido.Hilo()
        self.sonido.start()
        self.http_funciones = {'aporte': Modulos.Aporte}
        self.reloj = Reloj()
        self.ticketera = Impresion.ESCPOS('puerto')
        self.ticketeraSunat = Impresion.ESCPOS('sunat')
        self.twist = Twist(self)

    def guardar_config(self):
        ticket = open('outs/config', 'wb')
        ticket.write(json.dumps(self.config))
        ticket.close()

    def login(self, usuario, password, clave):
        self.headers = {'Cookie': '',
         'Origin': appengine,
         'Host': appengine,
         'Content-Type': 'application/x-www-form-urlencoded'}
        self.login_ok = False
        self.username = usuario
        self.password = password
        url = 'ingresar'
        self.load(url)
        self.csrf = self.set_cookie('csrftoken')
        login = {'username': self.username,
         'password': self.password,
         'clave': clave}
        if self.send_login(login):
            self.empresa = self.datos['empresa']
            try:
                self.compute = self.datos['rutas'][0][3]
                self.twist.compute = self.datos['rutas'][0][3]
            except:
                pass
            self.despachador = self.datos['despachador']
            self.despachador_id = self.datos['despachador_id']
            self.piezas = self.datos['piezas']
            self.grifo = self.datos['grifo']
            self.seriacion = self.datos['seriacion']
            self.boletos_limites = self.datos['boletos_limites']
            self.datos['boleto_gasto'] = json.loads(self.datos['boleto_gasto'])
            self.productos = []
            self.conductores = []
            self.cobradores = []
            self.unidades = []
            self.twist.despacho = self.datos['despacho']
            rutas = ''
            for r in self.datos['rutas']:
                rutas += ',%d' % r[1]
            self.twist.rutas = rutas
            self.twist.resume()
        return self.sessionid

    def send_login(self, login):
        self.datos = self.load('ingresar', login)
        if not self.datos:
            return False
        if not self.login_ok:
            self.sessionid = self.set_cookie('sessionid')
            if self.sessionid:
                self.login_ok = True
        if isinstance(self.datos, dict):
            version = float(self.datos['version'])
            if os.name != 'nt' and self.version < version and False:
                mensaje = 'Hay una nueva versi\xc3\xb3n de TCONTUR disponible\n'
                mensaje += '\xc2\xbfDesea instalarla?'
                dialogo = Widgets.Alerta_SINO('Actualizaci\xc3\xb3n Pendiente', 'update.png', mensaje, False)
                respuesta = dialogo.iniciar()
                dialogo.cerrar()
                if respuesta:
                    self.update()
            return True
        titulo = 'Elija una empresa'
        imagen = 'dar_prioridad.png'
        mensaje = '\xc2\xbfA qu\xc3\xa9 empresa desea ingresar?'
        dialogo = Widgets.Alerta_Combo(titulo, imagen, mensaje, self.datos)
        try:
            dialogo.combo.set_id(self.config['empresa'])
        except:
            pass
        dialogo.set_focus(dialogo.but_ok)
        respuesta = dialogo.iniciar()
        dialogo.cerrar()
        if respuesta:
            self.empresa = respuesta
            self.config['empresa'] = self.empresa
            self.guardar_config()
            return self.send_login(login)


    def setConfig(self, key, value):
        if key in self.config:
            if self.config[key] != value:
                self.config[key] = value
        else:
            self.config[key] = value
        self.guardar_config()


    def getConfig(self, key):
        if key in self.config:
            return self.config[key]
        else:
            return False


    def update(self):
        sh.git.stash()
        s = sh.git.pull()
        if s == 'Already up-to-date.\n':
            titulo = 'No hay cambios'
            mensaje = 'No se encontraron actualizaciones disponibles.'
        else:
            titulo = 'Actualizacion Correcta'
            mensaje = 'El programa se ha actualizado correctamente.\n'
            mensaje += 'Reinicie el programa para que los cambios surjan efecto.'
        Widgets.Alerta(titulo, 'update.png', mensaje)

    def set_cookie(self, key):
        try:
            cookies = self.req.getheaders()['set-cookie']
        except:
            self.headers['Cookie'] += '%s=%s; ' % (key, cook[n + 1:m])
            return cookie
        i = cookies.find(key)
        if i == -1:
            return False
        cook = cookies[i:]
        n = cook.find('=')
        m = cook.find(';')
        cookie = cook[n + 1:m]
        self.headers['Cookie'] += '%s=%s; ' % (key, cook[n + 1:m])
        return cookie

    def get_backup(self, consulta, datos):
        if isinstance(datos['dia'], datetime.date):
            d = datos['dia']
        else:
            d = datetime.datetime.strptime(datos['dia'], '%Y-%m-%d')
        carpeta = 'backup/%d/%d/%d/%d/' % (datos['ruta_id'],
         d.year,
         d.month,
         d.day)
        if consulta == 'actualizar-tablas':
            f = open(carpeta + 'data.pkl', 'rb')
            data = pickle.loads(f.read())
            if datos['lado'] == 0:
                tabla = data['a']
            else:
                tabla = data['b']
            return {'enruta': tabla,
             'disponibles': [(0, 0, '00:00', 0, 0, 0, 'BACKUP', 'B', '#B00', '00:00', 0)],
             'excluidos': [],
             'inicio': '2000-01-01 00:00:00',
             'frecuencia': 0,
             'manual': 0}
        if consulta == 'solo-unidad':
            f = open(carpeta + 'data.pkl', 'rb')
            return pickle.loads(f.read())['u'][datos['padron']]
        if consulta == 'datos-salida':
            f = open(carpeta + str(datos['salida_id']) + '.pkl', 'rb')
            return pickle.loads(f.read())
        if consulta == 'flota-llegada':
            f = open(carpeta + 'data.pkl', 'rb')
            return pickle.loads(f.read())['f']
        if consulta == 'unidad-salida':
            f = open(carpeta + str(datos['salida_id']) + '.pkl', 'rb')
            salida = pickle.loads(f.read())
            f = open(carpeta + 'data.pkl', 'rb')
            data = pickle.loads(f.read())['u']
            salidas = data[str(datos['padron'])]
            unidad = {'padron': datos['padron'],
             'modelo': 'Informaci\xc3\xb3n de Backup',
             'hora_check': '2100-01-01 00:00:00',
             'unidad_check': [True, u'Informaci\xf3n de Backup'],
             'propietario': 'Informaci\xc3\xb3n de Backup',
             'id': 0,
             'salidas': salidas,
             'faltan': False,
             'salida': datos['salida_id'],
             'salida_tablas': None,
             'conductores': [[u'CONDUCTOR TEMPORAL',
                              None,
                              1L,
                              None]],
             'cobradores': [[u'COBRADOR TEMPORAL',
                             None,
                             2L,
                             None]],
             'conductor': [u'CONDUCTOR TEMPORAL',
                           None,
                           1L,
                           None],
             'cobrador': [u'COBRADOR TEMPORAL',
                          None,
                          2L,
                          None],
             'bloqueado': True}
            return {'unidad': unidad,
             'salida': salida}

    def load(self, consulta, datos = {}):
        if self.backup and consulta in self.backup_urls:
            try:
                js = self.get_backup(consulta, datos)
            except IOError:
                print(' No existe backup')
            else:
                print('+++++++++')
                print(consulta)
                print('+++++++++')
                print(datos)
                print(js)
                print('+++++++++')
                if js:
                    return js

        get = datos == {}
        post_data = ''
        if not get:
            datos['empresa_id'] = self.empresa
            datos['empresa'] = self.empresa
            datos['version'] = self.version
            datos['despachador'] = self.despachador
            datos['despachador_id'] = self.despachador_id
            datos['usuario'] = self.despachador_id
            datos['csrfmiddlewaretoken'] = self.csrf
            datos['sessionid'] = self.sessionid
            keys = datos.keys()
            keys.sort()
            for k in keys:
                if datos[k] is None:
                    pass
                elif isinstance(datos[k], tuple) or isinstance(datos[k], list):
                    for d in datos[k]:
                        post_data += '%s=%s&' % (k, d)

                else:
                    post_data += '%s=%s&' % (k, datos[k])

            post_data = post_data[:-1]
        url = '%s%s/' % (self.server, consulta)
        l = len(str(post_data))
        self.headers['Content-Length'] = str(l)
        try:
            if get:
                r = self.conn.urlopen('HEAD', url, headers=self.headers, assert_same_host=False)
            else:
                r = self.conn.urlopen('POST', url, body=post_data, headers=self.headers, assert_same_host=False)
        except:
            print('********************************')
            print(url)
            print('********************************')
            Widgets.Alerta('Error', 'error_envio.png', 'No es posible conectarse al servidor,\n' + 'aseg\xc3\xbarese de estar conectado a internet\n' + 'e intente de nuevo.')
            return False

        self.req = r
        a = os.path.abspath('outs/index.html')
        f = open(a, 'wb')
        f.write(r.data)
        f.close()
        if get:
            return True
        try:
            js = json.loads(r.data)
        except:
            print('********************************')
            print(url)
            print('********************************')
            print 'json', url, post_data, self.headers
            print r.status
            for v in self.ventanas:
                v.status_bar.push('Error de conexion')

            return False

        return self.ejecutar(js)

    def ejecutar(self, js):
        if len(js) < 2:
            return False
        primero = js[0]
        segundo = js[1]
        if primero == 'Json':
            return segundo
        elif primero == 'Dialogo':
            Widgets.Alerta('Aviso', 'info.png', segundo)
            for v in self.ventanas:
                v.status_bar.push(segundo.split('\n')[0])

            return self.ejecutar(js[2:])
        elif primero == 'Comando':
            self.comando(segundo)
            return self.ejecutar(js[2:])
        elif primero == 'OK':
            for v in self.ventanas:
                v.status_bar.push(segundo)

            return self.ejecutar(js[2:])
        elif primero == 'Error':
            self.sonido.error()
            print segundo
            Widgets.Alerta('Error', 'error_dialogo.png', segundo)
            for v in self.ventanas:
                v.status_bar.push(segundo.split('\n')[0])
            return False
        elif primero == 'print':
            print 'imprimiendo'
            self.imprimir(segundo)
            return self.ejecutar(js[2:])
        elif primero == 'ticket':
            print 'ticket principal'
            self.ticket(segundo, cortar=True)
            return self.ejecutar(js[2:])
        elif primero == 'ticket_uncut':
            print 'ticket sin cortar'
            self.ticket(segundo, cortar=False)
            return self.ejecutar(js[2:])
        elif primero == 'open':
            self.open(segundo)
            return self.ejecutar(js[2:])
        elif primero == 'image':
            self.imagen(segundo)
            return self.ejecutar(js[2:])
        else:
            return self.ejecutar(js[2:])

    def imprimir(self, datos):
        Impresion.Impresion(datos[0], datos[1])

    def open(self, consulta):
        url = '/%s' % consulta
        self.headers.pop('Content-Length')
        r = self.conn.urlopen('GET', url, headers=self.headers, assert_same_host=False)
        self.req = r
        a = 'outs/reporte.pdf'
        f = open(a, 'wb')
        f.write(r.data)
        f.close()
        a = os.path.abspath(a)
        if os.name == 'nt':
            com = 'cd "%s" & start reporte.pdf' % a[:12]
            os.system(com)
        else:
            os.system('gnome-open outs/reporte.pdf')
        return True

    def imagen(self, consulta):
        url = '/%s' % consulta
        self.headers.pop('Content-Length')
        r = self.conn.urlopen('GET', url, headers=self.headers, assert_same_host=False)
        self.req = r
        a = 'outs/imagen.png'
        f = open(a, 'wb')
        f.write(r.data)
        f.close()
        return True

    def ticket(self, comandos, cortar):
        for c in comandos:
            if 'AUTORIZACION:' in c[1]:
                self.ticketeraSunat.imprimir(comandos, cortar)
                return
        self.ticketera.imprimir(comandos, cortar)

    def connect(self, string, funcion):
        self.signals[string].append(funcion)

    def emit(self, string):
        for f in self.signals[string]:
            f()

    def nada(self, *args):
        pass

    def get_pagos(self, ruta):
        if ruta in self.pagos:
            return self.pagos[ruta]
        else:
            data = self.load('pagos-por-tipo', {
                'ruta': ruta,
                'lado': 0,
                'padron': 0
            })
            print 'pagos', data
            if data:
                self.pagos[ruta] = data
                return data
            else:
                return []

    def comando(self, params):
        funcion = params['funcion']
        default = params['default']
        dialogo = self.http_funciones[funcion](self)
        dialogo.set_defaults(default)
        if dialogo.iniciar():
            self.load(funcion, dialogo.datos)
        dialogo.cerrar()

    def webbrowser(self, url, backup=False):
        uri = 'http://%s/despacho/ingresar?sessionid=%s&next=%s' % (self.web, self.sessionid, url)
        webbrowser.get('google-chrome').open(uri)

    def getMultas(self, actualizar=False):
        if self.multas is None or actualizar:
            fondos = self.load('lista-fondos', {'vacio': None})
            self.fondos = []
            self.multas = []
            for f in fondos:
                if f[4] is None:
                    self.multas.append(f)
                else:
                    self.fondos.append(f)
        return self.multas

    def limpiarData(self):
        self.dataServer = {}

    def getDatos(self, key, _id=None, actualizar=False):
        if not (key in self.dataServer) or actualizar:
            datos = self.load('datos-despacho', {'json': json.dumps({'funcion': key})})
            if datos:
                self.dataServer[key] = datos
            else:
                self.dataServer[key] = []
        if _id:
            for d in self.dataServer[key]:
                if d['id'] == _id:
                    return d
            return None
        print('DATOS', key, self.dataServer[key])
        return self.dataServer[key]

    def getFondos(self, _id=None, actualizar=False):
        return self.getDatos('fondos', _id, actualizar)

    def getCobros(self, _id=None, actualizar=False):
        return self.getDatos('cobros', _id, actualizar)


class Twist(threading.Thread):

    def __init__(self, http):
        super(Twist, self).__init__()
        self.despacho = 0
        self.rutas = []
        self.ventanas = http.ventanas
        self.compute = http.compute
        self.state = threading.Event()
        self.state.clear()
        self.daemon = False
        self.sonido = http.sonido
        global local
        self.local = local
        self.start()

    def run(self):
        while infinito:
            self.state.wait()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(None)
            try:
                print 'Compute', self.compute
                self.socket.connect((self.compute, 22222))
                self.socket.send('D,%s%s' % (self.despacho, self.rutas))
            except:
                self.state.clear()
                gobject.idle_add(self.desconectado, 'No se pudo establecer la conexi\xc3\xb3n')
            else:
                while infinito:
                    self.state.wait()
                    try:
                        recibido = self.socket.recv(64)
                    except:
                        continue
                    if recibido == '':
                        self.state.clear()
                        gobject.idle_add(self.desconectado, 'Se perdi\xc3\xb3 la conexi\xc3\xb3n')
                        break
                    print 'TWIST', recibido
                    params = recibido.split(',')
                    if len(params) > 2:
                        gobject.idle_add(self.actualizar, params)
        print 'Fin Twist'

    def actualizar(self, params):
        for v in self.ventanas:
            v.twist_recibido(params)

    def desconectado(self, status = ''):
        for v in self.ventanas:
            v.twist.desactivar()
            v.status_bar.push(status)
        if os.name != 'nt' and not self.local:
            print 'INICIO EMERGENCIA'
            self.sonido.emergencia()
            print 'SONIDO EMERGENCIA'
        Widgets.AlertaTwist('Error de conexi\xc3\xb3n', 'error_envio.png', status + '\n' + 'Presione el bot\xc3\xb3n para reconectar\n' + 'si el problema persiste informe a TCONTUR.')

    def resume(self, *args):
        for v in self.ventanas:
            v.twist.activar()
            v.status_bar.push('Conexi\xc3\xb3n activa')
        self.state.set()

    def cerrar(self):
        global infinito
        infinito = False
        self.state.set()
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.join()


if __name__ == '__main__':
    s = Splash()
    gtk.main()
    # infinito = False
    s.a.http.twist.cerrar()
    if os.name == 'nt':
        os.system('taskkill /im TCONTUR5.exe /f')
    Chrome.close()
