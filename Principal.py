 #! /usr/bin/python
# -*- coding: utf-8 -*-
local = 0
import gtk
import Salidas
import Modulos
import Widgets
import threading
import os
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
if os.name == 'nt':
    import win32api
else:
    import sh
infinito = True
version = 5.22
dia = 'Actualización Jueves 29 de octubre de 2015'
if local:
    localhost = 'localhost'
    #localhost = 'localhost'
    appengine_ip = appengine = localhost
    web = compute = titulo = localhost
else:
    titulo = "Sistema de Despacho TCONTUR v%s" % version
    compute = '104.197.24.168'
    appengine_ip = appengine = 'tcontur2.appspot.com'
    web = 'urbano.tcontur.com'
    try:
        ips = socket.gethostbyname_ex(appengine)
    except socket.gaierror:
        pass
    else:
        print ips
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
try:
    webbrowser.get('google-chrome')
except:
    pass
try:
    webbrowser.get('firefox')
except:
    pass
try:
    webbrowser.get('opera')
except:
    pass
try:
    webbrowser.get('safari')
except:
    pass
try:
    webbrowser.get('windows-default')
except:
    pass
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

class Aplicacion:
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
        print dialog
        respuesta = dialog.iniciar()
        print respuesta
        print dialog.sessionid
        if respuesta:
            self.ventana.login(dialog.sessionid)
            self.sessionid = dialog.sessionid
            self.usuario = dialog.user
            self.password = dialog.pw
            print self.usuario
            dialog.cerrar()
        else:
            dialog.cerrar()

    def salidas(self, *args):
        global dia
        global version
        status_bar = Widgets.Statusbar()
        status_bar.push(dia)
        herramientas = [
            ('Nueva Ventana (Ctrl + N)', 'salidas.png', self.salidas),
            #('Ingresar (Ctrl + L)', 'login.png', self.login)
            ]
        toolbar = Widgets.Toolbar(herramientas)
        twist = Widgets.ButtonTwist('desconectado.png', 'conectado.png')
        ticketera = Widgets.Button('imprimir.png', '', 16)
        ventana = Salidas.Ventana(self, titulo, toolbar, twist, status_bar, version, ticketera)
        self.grupo.add_window(ventana)
        self.ventanas.append(ventana)
        ventana.connect('cerrar', self.cerrar)
        ventana.connect('login', self.login)
        ventana.connect('salidas', self.salidas)
        twist.connect('clicked', self.http.twist.resume)
        ticketera.connect('button-press-event', self.ticketera)
        self.menu = gtk.Menu()
        for p in self.http.ticketera.seriales:
            item1 = gtk.MenuItem(p)
            item1.connect('activate', self.impresora_serial, p)
            self.menu.append(item1)
        item2 = gtk.MenuItem('LPT1')
        item2.connect('activate', self.impresora_paralela)
        self.menu.append(item2)
        item3 = gtk.MenuItem('Probar')
        item3.connect('activate', self.impresora_probar)
        self.menu.append(item3)
        item4 = gtk.MenuItem('Reimprimir Último')
        item4.connect('activate', self.impresora_reimprimir)
        self.menu.append(item4)
        if len(self.ventanas) > 1:
            ventana.login(self.sessionid)
        ventana.grab_focus()
        return ventana

    def impresora_serial(self, menu, puerto):
        self.http.ticketera.conectar_serial(puerto)

    def impresora_paralela(self, *args):
        self.http.ticketera.paralela()

    def impresora_probar(self, *args):
        self.http.ticketera.probar()

    def impresora_reimprimir(self, *args):
        self.http.ticketera.reimprimir()

    def ticketera(self, widgets, event):
        if event.button == 1:
            x = int(event.x)
            y = int(event.y)
            t = event.time
            self.menu.popup(None, None, None, event.button, t)
            self.menu.show_all()
            return True

    def cerrar(self, ventana):
        self.ventanas.remove(ventana)
        del ventana
        if len(self.ventanas) == 0:
            gtk.main_quit()


class Reloj(gtk.EventBox):

    __gsignals__ = {'tic-tac': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
        ())}

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
        print 'Fin Reloj'

    def cerrar(self):
        global infinito
        infinito = False
        self.hilo.join()

class Http:

    def __init__(self, ventanas):
        global appengine_ip
        global appengine
        global compute
        global version
        self.conn = urllib3.HTTPConnectionPool(appengine_ip)
        self.ventanas = ventanas
        self.funciones = [self.nada]
        self.signals = {'update': self.funciones}
        self.compute = compute
        self.server = '/despacho/'
        self.dominio = appengine
        global web
        self.web = web
        self.csrf = ''
        #self.server = 'http://localhost:8000/despacho'
        self.login_ok = False
        self.timeout = None
        self.backup = True
        self.backup_urls = ('actualizar-tablas', 'solo-unidad', 'unidad-salida', 'datos-salida', 'flota-llegada')
        self.backup_dia = None
        #self.cookies = {'Cookie': {}}
        self.headers = {'Cookie': '', 'Origin': appengine, 'Host': appengine ,'Content-Type': 'application/x-www-form-urlencoded'}
        self.datos = {'rutas': (('Vacio', 0),),
            'despacho': None}
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
        self.pagos = []
        self.castigos = []
        self.seriacion = []
        self.boletos_limites = []
        self.servicio = None
        self.grifo = False
        self.sonido = Sonido.Hilo()
        self.sonido.start()
        self.http_funciones = {
            'aporte': Modulos.Aporte
            }
        self.reloj = Reloj()
        self.ticketera = Impresion.ESCPOS()
        self.twist = Twist(self)

    def login(self, usuario, password, clave):
        self.headers = {'Cookie': '', 'Origin': appengine, 'Host': appengine ,'Content-Type': 'application/x-www-form-urlencoded'}
        self.login_ok = False
        self.username = usuario
        self.password = password
        url = 'ingresar'
        self.load(url)
        self.csrf = self.set_cookie('csrftoken')
        login = {
            'username': self.username,
            'password': self.password,
            'clave': clave
            }
        if self.send_login(login):
            print 'DATOS', self.datos
            self.empresa = self.datos['empresa']
            self.despachador = self.datos['despachador']
            self.despachador_id = self.datos['despachador_id']
            self.piezas = self.datos['piezas']
            self.grifo = self.datos['grifo']
            self.seriacion = self.datos['seriacion']
            self.boletos_limites = self.datos['boletos_limites']
            self.productos = []
            self.conductores = []
            self.cobradores = []
            self.twist.despacho = self.datos['despacho']
            rutas = ''
            for c, r, v in self.datos['rutas']:
                rutas += ',%d' % r
            self.twist.rutas = rutas
            print 'Twi'
            self.twist.resume()
            print 'sT'
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
            if os.name != 'nt' and self.version < version:
                mensaje = 'Hay una nueva versión de TCONTUR disponible\n'
                mensaje += '¿Desea instalarla?'
                dialogo = Widgets.Alerta_SINO('Actualización Pendiente',
                            'update.png', mensaje, False)
                respuesta = dialogo.iniciar()
                dialogo.cerrar()
                if respuesta:
                    self.update()
            return True
        else:
            titulo = 'Elija una empresa'
            imagen = 'dar_prioridad.png'
            mensaje = '¿A qué empresa desea ingresar?'
            dialogo = Widgets.Alerta_Combo(titulo, imagen, mensaje, self.datos)
            dialogo.set_focus(dialogo.but_ok)
            respuesta = dialogo.iniciar()
            dialogo.cerrar()
            if respuesta:
                self.empresa = respuesta
                return self.send_login(login)

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
        cookies = self.req.getheaders()['set-cookie']
        i = cookies.find(key)
        if i == -1:
            return False
        cook = cookies[i:]
        n = cook.find('=')
        m = cook.find(';')
        cookie = cook[n + 1: m]
        self.headers['Cookie'] += '%s=%s; ' % (key, cook[n + 1:m])
        return cookie

    def get_backup(self, consulta, datos):
        if isinstance(datos['dia'], datetime.date):
            d = datos['dia']
        else:
            d = datetime.datetime.strptime(datos['dia'], '%Y-%m-%d')
        carpeta = 'backup/%d/%d/%d/%d/' % (datos['ruta_id'], d.year, d.month, d.day)
        if consulta == 'actualizar-tablas':
            print 'Buscando', carpeta + 'data.pkl'
            f = open(carpeta + 'data.pkl', 'rb')
            data = pickle.loads(f.read())
            if datos['lado'] == 0:
                tabla = data['a']
            else:
                tabla = data['b']
            print 'Salidas', data['s']
            return {'enruta': tabla, 'disponibles': [(0, 0, '00:00', 0, 0, 0, 'BACKUP', 'B', '#B00', '00:00', 0)], 'excluidos': [], 'inicio': '2000-01-01 00:00:00', 'frecuencia':0, 'manual': 0}
        elif consulta == 'solo-unidad':
            print 'Buscando', carpeta + 'data.pkl'
            f = open(carpeta + 'data.pkl', 'rb')
            return pickle.loads(f.read())['u'][datos['padron']]
        elif consulta == 'datos-salida':
            print 'Buscando', carpeta + str(datos['salida_id'])
            f = open(carpeta + str(datos['salida_id']) + '.pkl', 'rb')
            return pickle.loads(f.read())
        elif consulta == 'flota-llegada':
            print 'Buscando', carpeta + 'data.pkl'
            f = open(carpeta + 'data.pkl', 'rb')
            return pickle.loads(f.read())['f']
        elif consulta == 'unidad-salida':
            print 'Buscando', carpeta + str(datos['salida_id'])
            f = open(carpeta + str(datos['salida_id']) + '.pkl', 'rb')
            salida = pickle.loads(f.read())
            print 'DATA SALIDA', salida
            print 'Buscando', carpeta + 'data.pkl'
            f = open(carpeta + 'data.pkl', 'rb')
            data = pickle.loads(f.read())['u']
            print 'DATA KEYS', data.keys()
            salidas = data[str(datos['padron'])]
            unidad = {
                'padron': datos['padron'],
                'modelo': 'Información de Backup',
                'hora_check': '2100-01-01 00:00:00',
                'unidad_check': [True, u'Información de Backup'],
                'propietario': 'Información de Backup',
                'id': 0,
                'salidas': salidas,
                'faltan': False,
                'salida': datos['salida_id'],
                'salida_tablas': None,
                'conductores': [[u'CONDUCTOR TEMPORAL', None, 1L, None]],
                'cobradores': [[u'COBRADOR TEMPORAL', None, 2L, None]],
                'conductor': [u'CONDUCTOR TEMPORAL', None, 1L, None],
                'cobrador': [u'COBRADOR TEMPORAL', None, 2L, None],
                'bloqueado': True,
            }
            print 'DATA VALUE', unidad
            return {'unidad': unidad, 'salida': salida}

    def load(self, consulta, datos={}):
        if self.backup and consulta in self.backup_urls:
            try:
                js = self.get_backup(consulta, datos)
            except IOError:
                print ' No existe backup'
            else:
                print '+++++++++'
                print consulta
                print '+++++++++'
                print datos
                print js
                print '+++++++++'
                if js:
                    return js
        get = datos == {}
        post_data = ''
        if not get:
            datos['empresa_id'] = self.empresa
            datos['version'] = self.version
            datos['despachador'] = self.despachador
            datos['despachador_id'] = self.despachador_id
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
        l = len(post_data)
        self.headers['Content-Length'] = str(l)
        try:
            if get:
                r = self.conn.urlopen('HEAD', url, headers=self.headers, assert_same_host=False)
            else:
                r = self.conn.urlopen('POST', url, body=post_data, headers=self.headers, assert_same_host=False)
        except:
            print ('********************************')
            print (url)
            print ('********************************')
            Widgets.Alerta('Error', 'error_envio.png',
                'No es posible conectarse al servidor,\n' +
                'asegúrese de estar conectado a internet\n' +
                'e intente de nuevo.')
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
            print ('********************************')
            print (url)
            print ('********************************')
            print 'json', url, post_data, self.headers
            print r.status
            for v in self.ventanas:
                v.status_bar.push('Error de conexion')
            return False
        return self.ejecutar(js)

    def ejecutar(self, js):
        if len(js) < 2:
            #return True
            return False
        primero = js[0]
        segundo = js[1]
        if primero == 'Json':
            return segundo
        if primero == 'Dialogo':
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
            self.ticket(segundo)
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
            os.system('start outs/reporte.pdf')
        else:
            os.system("gnome-open outs/reporte.pdf")
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

    def ticket(self, comandos):
        #Widgets.Alerta('Impresion', 'imprimir.png', 'Se ha recibido un ticket para imprimir\nCorte el papel y de un click en Aceptar.')
        self.ticketera.imprimir(comandos)

    def connect(self, string, funcion):
        self.signals[string].append(funcion)

    def emit(self, string):
        for f in self.signals[string]:
            f()

    def nada(self, *args):
        pass

    def comando(self, params):
        funcion = params['funcion']
        default = params['default']
        dialogo = self.http_funciones[funcion](self)
        dialogo.set_defaults(default)
        if dialogo.iniciar():
            self.load(funcion, dialogo.datos)
        dialogo.cerrar()

    def webbrowser(self, url):
        uri = 'http://%s/despacho/ingresar?sessionid=%s&next=%s' % (self.web, self.sessionid, url)
        webbrowser.open(uri)


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
        self.start()

    def run(self):
        global infinito
        while infinito:
            self.state.wait()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(None)
            try:
                print self.compute
                self.socket.connect((self.compute, 22222))
                self.socket.send('D,%s%s' % (self.despacho, self.rutas))
            except:
                raise
                self.state.clear()
                gobject.idle_add(self.desconectado, 'No se pudo establecer la conexión')
            else:
                while infinito:
                    self.state.wait()
                    try:
                        recibido = self.socket.recv(64)
                    except:
                        self.state.clear()
                        gobject.idle_add(self.desconectado, 'Se cerró la conexión')
                        break
                    if recibido == '':
                        self.state.clear()
                        gobject.idle_add(self.desconectado, 'Se perdió la conexión')
                        break
                    print 'TWIST', recibido
                    params = recibido.split(',')
                    if len(params) > 2:
                        gobject.idle_add(self.actualizar, params)
        print 'Fin Twist'

    def actualizar(self, params):
        for v in self.ventanas:
            v.twist_recibido(params)

    def desconectado(self, status=''):
        for v in self.ventanas:
            v.twist.desactivar()
            v.status_bar.push(status)
        Widgets.AlertaTwist('Error de conexión', 'error_envio.png',
            status + '\n' +
            'Presione el botón para reconectar\n' +
            'si el problema persiste informe a TCONTUR.')

    def resume(self, *args):
        for v in self.ventanas:
            v.twist.activar()
            v.status_bar.push('Conexión activa')
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
    infinito = False
    if os.name == 'nt':
        os.system('taskkill /im TCONTUR5.exe /f')
    Chrome.close()
