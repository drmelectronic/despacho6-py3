#! /usr/bin/python3.6
# -*- encoding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository import GObject

from Splash import Splash
import Salidas
import Modulos
import Widgets
import threading
import urllib3
# import Chrome
import json
import os
import time
import socket
import Sonido
import Impresion
import models


if __name__ == '__main__':
    try:
        a = os.path.abspath("outs/root.dll")
        archivo = open(a, 'rb')
        content = archivo.read()
        archivo.close()
        d = json.loads(content)
        beta = d['beta']
    except:
        d = None
        beta = 0
    local = 1
    beta = 1
    print('local', local)
    if os.name != 'nt':
        import sh
    else:
        local = 0
        beta = 0
    infinito = True
    version = 6.17
    dia = 'Actualización martes 29 de octubre de 2019'
    if local:
        localhost = 'localhost:8000'
        appengine_ip = appengine = localhost
        web = web_pack = titulo = localhost
    else:
        titulo = 'Sistema de Despacho TCONTUR v%s' % version
        if beta:
            appengine_ip = appengine = 'api.tcontur.com'
        else:
            appengine_ip = appengine = 'api.tcontur.com'
        test = urllib3.HTTPConnectionPool('api.tcontur.com')
        try:
            test.urlopen('HEAD', '/', assert_same_host=False)
        except:
            web = 'api.tcontur.com'
        else:
            web = 'api.tcontur.com'
        print('server', web)
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


    GObject.threads_init()


class Aplicacion:

    def __init__(self):
        self.s = Splash()
        GObject.idle_add(self.load_dumy)

    def load_dumy(self):
        self.grupo = Gtk.WindowGroup()
        self.ventanas = []
        self.http = Http(self.ventanas)
        self.sessionid = None
        # Chrome.init()
        self.ventana = self.nueva_ventana()
        self.s.destroy()
        self.login()

    def login(self, *args):
        dialog = Widgets.Login(self.http, self.ventanas[0])

        #FOR TEST
        # dialog.autologin()
        # self.ventana.login(dialog.sessionid)
        # self.sessionid = dialog.sessionid
        # return
        #FOR TEST
        respuesta = dialog.iniciar()
        if respuesta:
            self.ventana.login(dialog.sessionid)
            self.sessionid = dialog.sessionid
            dialog.cerrar()
        else:
            dialog.cerrar()

    def nueva_ventana(self, *args):
        global version
        global dia
        status_bar = Widgets.Statusbar()
        status_bar.push(dia)
        twist = Widgets.ButtonTwist('desconectado.png', 'conectado.png', tooltip='Reconectar al servidor GPS')
        ticketera = Widgets.Button('imprimir.png', '', 16, tooltip='Configuración de Impresión')
        ventana = Salidas.Ventana(self, titulo, status_bar, version, ticketera)
        ventana.connect('nueva-ventana', self.nueva_ventana)
        self.grupo.add_window(ventana)
        ventana.present()
        self.ventanas.append(ventana)
        ventana.connect('cerrar', self.cerrar)
        ventana.connect('login', self.login)
        ventana.connect('salidas', self.nueva_ventana)
        ticketera.connect('button-press-event', self.ticketera)
        if len(self.ventanas) > 1:
            ventana.login(self.sessionid)
        ventana.grab_focus()
        return ventana

    def ticketera(self, widgets, event):
        dialogo = Widgets.Configuracion(self.http)
        self.http.limpiar_data()
        dialogo.cerrar()

    def cerrar(self, ventana):
        self.ventanas.remove(ventana)
        del ventana
        if len(self.ventanas) == 0:
            try:
                self.http.load('salir')
            except:
                pass
            print('ya no hay más ventanas')
            Gtk.main_quit()


class Reloj(Gtk.EventBox):
    __gsignals__ = {'tic-tac': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ())}

    def __init__(self):
        super(Reloj, self).__init__()
        self.hilo = threading.Thread(target=self.run)
        self.hilo.daemon = False
        self.hilo.start()

    def run(self):
        global infinito
        while infinito:
            Gdk.threads_enter()
            self.emit('tic-tac')
            Gdk.threads_leave()
            time.sleep(1)

    def cerrar(self):
        global infinito
        infinito = False
        self.hilo.join()


class Http():
    fondos = None
    multas = None
    dataServer = {}
    dataDump = {}
    exclusiones = [
        'Error Digitación',
        'Sin Personal',
        'Combustible',
        'Taller',
        'Almuerzo'
    ]

    def __init__(self, ventanas):
        global web
        global appengine
        global appengine_ip
        global local
        self.usuario = models.Usuario(self, None)
        if local:
            self.conn = urllib3.HTTPConnectionPool(appengine, timeout=30)
        else:
            self.conn = urllib3.HTTPSConnectionPool(appengine, timeout=30)
        self.ventanas = ventanas
        self.funciones = [self.nada]
        self.signals = {'update': self.funciones}
        self.appengine = appengine
        self.server = '/desktop/'
        self.dominio = appengine
        self.web = web
        self.login_ok = False
        self.timeout = None
        self.backup = False
        self.config = models.Configuracion()
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
        self.headers = {
            'Cookie': '',
            'User-Agent': 'PostmanRuntime/7.19.0',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'Host': appengine,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive'
        }
        self.login_ok = False
        self.load_data_file()

    def login(self, usuario, password, clave):
        self.username = usuario
        self.password = password
        login = {
            'username': self.username,
            'password': self.password,
            'clave': clave}
        login = self.load('token-auth', login)
        if not login:
            return False
        if not self.login_ok:
            self.headers['Authorization'] = 'Token ' + login['token']
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            self.usuario.set(login)
            self.despachador = login['nombre']
            self.despachador_id = login['id']
            self.login_ok = True
            return login['token']


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
            return None
        i = cookies.find(key)
        if i == -1:
            return False
        cook = cookies[i:]
        n = cook.find('=')
        m = cook.find(';')
        cookie = cook[n + 1:m]
        self.headers['Cookie'] += '%s=%s; ' % (key, cook[n + 1:m])
        return cookie

    def load(self, consulta, datos={}, log=True, method='POST'):
        if log:
            print('**********************************')
            print('load', consulta, datos, method)
            print('++++++++++++++++++++++++++++++++++')
        post_data = ''
        if method == 'POST':
            datos['version'] = self.version
            datos['despachador'] = self.despachador
            datos['despachador_id'] = self.despachador_id
            datos['usuario'] = self.despachador_id
            for k in datos:
                if datos[k] is None:
                    pass
                elif isinstance(datos[k], tuple) or isinstance(datos[k], list):
                    for d in datos[k]:
                        post_data += '%s=%s&' % (k, d)

                else:
                    post_data += '%s=%s&' % (k, datos[k])

            post_data = post_data[:-1]
        if consulta[0] == '/':
            url = consulta
        else:
            url = '%s%s/' % (self.server, consulta)

        l = len(str(post_data))
        self.headers['Content-Length'] = str(l)
        try:
            r = self.conn.urlopen(method, url, body=post_data, headers=self.headers, assert_same_host=False)
        except:
            raise
            print('********************************')
            print(url)
            print('********************************')
            Widgets.Alerta('Error', 'error_http.png', 'No es posible conectarse al servidor,\n' + 'asegúrese de estar conectado a internet\n' + 'e intente de nuevo.')
            return False

        self.req = r
        if log:
            a = os.path.abspath('outs/index.html')
            f = open(a, 'wb')
            f.write(r.data)
            f.close()

        try:
            js = json.loads(r.data)
        except:
            print('********************************')
            print(url)
            print('********************************')
            print('json', url, post_data, self.headers)
            print(r.status)
            if local:
                Widgets.Alerta('Error 500', 'error_http.png', 'Hubo un error en la operación.')
            else:
                for v in self.ventanas:
                    v.status_bar.push('Error de conexion')

            return False

        if log:
            print(js)
        return self.ejecutar(js)

    def ejecutar(self, js):
        if isinstance(js, dict):
            if 'error' in js:
                self.sonido.error()
                Widgets.Alerta('Error', 'error_dialogo.png', js['mensaje'])
                for v in self.ventanas:
                    v.status_bar.push(js['mensaje'].split('\n')[0])
                return False
        return js

    def ejecutar_antiguo(self, js):
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
            print(segundo)
            Widgets.Alerta('Error', 'error_dialogo.png', segundo)
            for v in self.ventanas:
                v.status_bar.push(segundo.split('\n')[0])
            return False
        elif primero == 'print':
            print('imprimiendo')
            self.imprimir(segundo)
            return self.ejecutar(js[2:])
        elif primero == 'ticket':
            self.ticket(segundo, cortar=True)
            return self.ejecutar(js[2:])
        elif primero == 'ticket_uncut':
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
            com = 'cd "%s" & start reporte.pdf' % a[:-12]
            os.system(com)
        else:
            os.system('xdg-open outs/reporte.pdf')
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

    def ticket(self, comandos, cortar=True):
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
            print('pagos', data)
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
        uri = 'http://%s/desktop/ingresar?sessionid=%s&next=%s' % (self.web, self.sessionid, url)
        self.config.open_url(uri)

    def get_multas(self, actualizar=False):
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

    def load_data_file(self):
        try:
            a = os.path.abspath('outs/data.bkp')
            f = open(a, 'r')
            data = f.read()
            f.close()
            js = json.loads(data)
        except:
            self.dataDump = {}
        else:
            self.dataDump = js
        self.load_data_server()

    def load_data_server(self):
        keys = self.dataDump.keys()
        for k in keys:
            modelo = models.MODELOS[k]
            datos = self.dataDump[k]
            if datos:
                print('DATA LOADED:', k)
                self.dataServer[k] = []
                for d in datos:
                    if modelo:
                        try:
                            self.dataServer[k].append(modelo(self, d))
                        except KeyError:
                            del self.dataDump[k]
                            self.save_data_file()
                            print('NUEVA VERSION DE ' + k)
                            break
                    else:
                        self.dataServer[k].append(d)

    def save_data_file(self):
        print('DATA SAVED')
        a = os.path.abspath('outs/data.bkp')
        f = open(a, 'w')
        f.write(json.dumps(self.dataDump))
        f.close()

    def limpiar_data(self):
        self.dataServer = {}
        self.dataDump = {}

    def get_datos(self, key, actualizar=False):
        if not self.login_ok:
            return []
        if not (key in self.dataServer):
            actualizar = True
        modelo = models.MODELOS[key]

        if actualizar:
            print('ACTUALIZAR DATOS', key)
            datos = self.load('/api/' + key, method='GET')
            self.dataDump[key] = datos
            self.save_data_file()

            if datos:
                self.dataServer[key] = []
                for d in datos:
                    if modelo:
                        objeto = modelo(self, d)
                        self.dataServer[key].append(objeto)
                    else:
                        self.dataServer[key].append(d)
            else:
                self.dataServer[key] = []
        return self.dataServer[key]

    def get_dato(self, key, _id):
        if key not in self.dataServer:
            self.get_datos(key, True)
        for d in self.dataServer[key]:
            if isinstance(d, models.model_base):
                if d.id == _id:
                    return d
            else:
                if d['id'] == _id:
                    return d
        return None

    # LOAD DATA

    def get_fondos(self, actualizar=False):
        return self.get_datos('fondos', actualizar)

    def get_cobros(self, actualizar=False):
        return self.get_datos('cobros', actualizar)

    def get_documentos(self, actualizar=False):
        return self.get_datos('documentos', actualizar)

    def get_productos(self, actualizar=False):
        return self.get_datos('productos', actualizar)

    def get_boletos(self, actualizar=False):
        return self.get_datos('boletos', actualizar)

    def get_rutas(self, actualizar=False):
        rutas = self.get_datos('rutas', actualizar)
        for r in rutas:
            if r.plantilla is None:
                plantillas = self.get_plantillas()
                frecuencias = self.get_frecuencias()
                self.get_tiempos()
                self.get_geocercas()
                self.get_trabajadores()
                r.set_plantilla(plantillas)
                r.configurar_frecuencias(frecuencias)
        return rutas

    def get_tiempos(self, actualizar=False):
        return self.get_datos('tiempos', actualizar)

    def get_plantillas(self, actualizar=False):
        return self.get_datos('plantillas', actualizar)

    def get_frecuencias(self, actualizar=False):
        return self.get_datos('frecuencias', actualizar)

    def get_geocercas(self, actualizar=False):
        return self.get_datos('geocercas', actualizar)

    def get_trabajadores(self, actualizar=False):
        return self.get_datos('trabajadores', actualizar)

    def get_propietarios(self, actualizar=False):
        return self.get_datos('propietarios', actualizar)

    def get_configuraciones(self, actualizar=False):
        return self.get_datos('configuraciones', actualizar)

    def get_stocks(self, actualizar=False):
        return self.get_datos('stocks', actualizar)

    # get objeto

    def get_fondo(self, _id):
        return self.get_dato('fondos', _id)

    def get_cobro(self, _id):
        return self.get_dato('cobros', _id)

    def get_documento(self, _id):
        return self.get_dato('documentos', _id)

    def get_producto(self, _id):
        return self.get_dato('productos', _id)

    def get_boleto(self, _id):
        return self.get_dato('boletos', _id)

    def get_ruta(self, _id):
        return self.get_dato('rutas', _id)

    def get_tiempo(self, _id):
        return self.get_dato('tiempos', _id)

    def get_plantilla(self, _id):
        return self.get_dato('plantillas', _id)

    def get_frecuencia(self, _id):
        return self.get_dato('frecuencias', _id)

    def get_geocerca(self, _id):
        return self.get_dato('geocercas', _id)

    def get_trabajador(self, _id):
        return self.get_dato('trabajadores', _id)

    def get_propietario(self, _id):
        return self.get_dato('propietarios', _id)

    def get_configuracion(self, _id):
        return self.get_dato('configuraciones', _id)

    def get_stock(self, _id):
        return self.get_dato('stocks', _id)

    def filtrar(self, lista, filter):
        query = []
        for l in lista:
            if self.cumple(l, filter):
                query.append(l)
        return query

    def cumple(self, item, filter):
        for f in filter:
            if item.get_param(f) == filter[f]:
                continue
            else:
                return False
        return True

    def ordenar(self, lista, sort):
        sort.reverse()
        for k, orden in sort:
            lista.sort(key=lambda x: x.__getattribute__(k))
            if orden < 0:
                lista.reverse()


if __name__ == '__main__':
    a = Aplicacion()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        infinito = False
    infinito = False