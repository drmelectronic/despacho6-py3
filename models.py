#! /usr/bin/python
# -*- encoding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject

import datetime
import json
import threading
from decimal import Decimal
import webbrowser


class model_base(object):
    tipos = {}

    def validate(self):
        for k in self.tipos:
            if self.__getattribute__(k) is None:
                continue
            if not isinstance(self.__getattribute__(k), self.tipos[k]):
                if self.tipos[k] == bool:
                    if self.__getattribute__(k) == 1:
                        self.__setattr__(k, True)
                        continue
                    elif self.__getattribute__(k) == 0:
                        self.__setattr__(k, False)
                        continue
                raise BaseException('%s: %s no es del tipo %s' % (k, self.__getattribute__(k), self.tipos[k]))

    def __init__(self, http, js=None):
        self.http = http
        self.estado = None
        self.lado = None
        for k in self.tipos:
            self.__setattr__(k, None)
        if js:
            self.set(js)

    def get_param(self, k):
        return self.tipos[k](self.__getattribute__(k))

    def set(self, objeto):
        for k in self.tipos:
            if k in objeto:
                if objeto[k] is not None:
                    if self.tipos[k] == int:
                        self.__setattr__(k, int(objeto[k]))
                    else:
                        self.__setattr__(k, objeto[k])
            else:
                print('tipos', self.tipos)
                print('objeto', objeto)
                print('no hay', k)
        self.validate()

    def get_dict(self):
        dictionary = {}
        for k in self.tipos:
            dictionary[k] = self.__getattribute__(k)
        return dictionary

    def __repr__(self):
        return str(self.id)

        #json.dumps(self.get_dict(), indent=4)

    def get_date(self, texto):
        if texto:
            y, m, d = texto.split('-')
            return datetime.date(int(y), int(m), int(d))

    def get_time(self, texto):
        if texto:
            h, m, s = texto.split(':')
            return datetime.time(int(h), int(m), int(s))

    def get_datetime(self, texto):
        if texto:
            if 'T' in texto:
                dia, hora = texto.split('T')
            else:
                dia, hora = texto.split(' ')
            y, m, d = dia.split('-')
            H, M, S = hora.split(':')
            return datetime.datetime(int(y), int(m), int(d), int(H), int(M), int(float(S)))

    def get_lado_display(self):
        if self.lado:
            return 'B'
        else:
            return 'A'

    def get_estado_display(self):
        if self.estado == 'R':
            return 'En Ruta'
        elif self.estado == 'T':
            return 'Terminado'
        elif self.estado == 'F':
            return 'Falla Mecánica'
        elif self.estado == 'E':
            return 'En Espera'
        elif self.estado == 'X':
            return 'Excluido'


class Ruta(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'codigo': str
        }
        self.plantilla = None
        self.frecuencias = None
        self.manual = {'inicio': None, 'frecuencia': None}
        super(Ruta, self).__init__(http, js)

    def set_plantilla(self, plantillas):
        for p in plantillas:
            if p.ruta == self.id:
                self.plantilla = p
                break

    def configurar_frecuencias(self, frecuencias):
        self.frecuencias = [[], []]
        for f in frecuencias:
            if f.ruta == self.id and f.plantilla == self.plantilla.id:
                self.frecuencias[int(f.lado)].append(f)
        self.frecuencias[0].sort(key=lambda k: k.inicio)
        self.frecuencias[1].sort(key=lambda k: k.inicio)

    def getPrimeraHora(self, hora, lado):
        print('getprimera', hora, lado)
        frecuencias = self.frecuencias[int(lado)]
        manual = self.manual[int(lado)]
        if hora is None:
            hora = frecuencias[0].get_inicio()
            frecuencia = 0
            print('frec inicio', frecuencia, hora)
        else:
            if manual['frecuencia'] is None:
                for f in frecuencias:
                    if f.get_inicio() <= hora:
                        hora += datetime.timedelta(0, f.tiempo * 60)
                        frecuencia = f.tiempo
                        print('frec', f.tiempo, f.get_inicio())
                        break
            else:
                print('frec manual', manual['frecuencia'])
                hora += datetime.timedelta(0, manual['frecuencia'] * 60)
                frecuencia = manual['frecuencia']

        print('manual inicio', manual['inicio'], manual['inicio'] is not None)
        if manual['inicio'] is not None:
            print('frec inicio', manual['inicio'])
            hora += datetime.timedelta(0, 60 * (manual['inicio'] - frecuencia))
            frecuencia = manual['inicio']

        return hora, frecuencia

    def getSiguienteHora(self, hora, lado):
        frecuencias = self.frecuencias[int(lado)]
        manual = self.manual[int(lado)]
        if hora is None:
            return self.getPrimeraHora(hora, lado)

        if manual['frecuencia'] is None:
            for f in frecuencias:
                if f.get_inicio() <= hora:
                    hora += datetime.timedelta(0, f.tiempo * 60)
                    return hora, f.tiempo
        else:
            hora += datetime.timedelta(0, manual['frecuencia'] * 60)
            return hora, manual['frecuencia']

    def set_manual(self, manual, lado=None):
        if lado is None:
            self.manual = manual
        else:
            self.manual[lado] = manual


class Plantilla(model_base):

    def __init__(self, http, js):
        self.tipos = {
        'id': int,
        'ruta': int,
        'nombre': str,
        'temporada': str,
        'inicio': str,
        'fin': str,
        'lunes': bool,
        'martes': bool,
        'miercoles': bool,
        'jueves': bool,
        'viernes': bool,
        'sabado': bool,
        'domingo': bool,
        'feriado': bool
        }
        super(Plantilla, self).__init__(http, js)

    def is_enable(self, dia):
        if (dia.year, dia.month, dia.day) in FERIADOS:
            return self.feriado
        week_day = dia.isoweekday()
        if week_day == 1:
            return self.lunes
        elif week_day == 2:
            return self.martes
        elif week_day == 3:
            return self.miercoles
        elif week_day == 4:
            return self.jueves
        elif week_day == 5:
            return self.viernes
        elif week_day == 6:
            return self.sabado
        elif week_day == 7:
            return self.domingo


class Geocerca(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'orden': int,
            'nombre': str,
            'ruta': int,
            'lado': bool,
            'intitud': float,
            'latitud': float,
            'radio': float,
            'control': bool,
            'datear': bool,
            'terminal': bool,
            'metros': int,
            'refrecuenciar': bool,
            'activo': bool,
            'desde': str,
            'hasta': str,
            'sagrado': bool,
            'retorno': bool,
            'audio': str
        }
        super(Geocerca, self).__init__(http, js)

    def set_hora(self, hora, tiempos):
        tiempos = self.http.filtrar(tiempos, {'geocerca': self.id})

        for t in tiempos:
            if t.contiene(hora):
                self.tiempo = t.tiempo
                self.multa = t.multa
                self.factor = t.factor
                self.hora = hora + datetime.timedelta(0, self.tiempo * 60)
                self.real = None
                return self.hora
        raise TconturError('No hay tiempo para esta geocerca %' % self.nombre)


class Llegada(model_base):

    def __init__(self, *args):
        self.tipos = {
            'g': int,
            'o': int,
            'c': bool,
            't': int,
            'e': str,
            'v': int,
            'f': int,
            'm': int
        }
        super(Llegada, self).__init__(*args)
        self.hora = None
        self.real = None

    def set_inicio(self, hora):
        self.hora = hora + datetime.timedelta(0, self.t * 60)
        if self.e == 'M':
            self.real = self.hora + datetime.timedelta(0, self.v * 60)
        return self.hora

    def get_fila_llegadas(self):
        return [self.o, self.nombre, self.get_hora_str(),  self.get_real_str(), self.get_volada_str(), self]

    def get_hora_str(self):
        if self.hora:
            return self.hora.strftime('%H:%M')
        else:
            return '--:--'

    def get_real_str(self):
        if self.real:
            return self.real.strftime('%H:%M:%S')
        else:
            return '--:--:--'

    def get_volada_str(self):
        if self.e == 'N':
            return ''
        elif self.e == 'F':
            return 'FM'
        elif self.e == 'S':
            return 'NM'
        else:
            return str(self.v)

    def set_volada(self, volada):
        self.real = self.hora + datetime.timedelta(0, volada * 60)
        self.e = 'M'
        self.v = volada
        return self.real.strftime('%H:%M')

    def no_marcar(self):
        self.e = 'N'
        self.r = None
        self.v = 0

    def falla_mecanica(self):
        self.e = 'F'
        self.r = None
        self.v = 0

    def get_record(self):
        return self.v * self.f

    def get_multa(self):
        return self.v * self.m


class Ticket(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'boleto': int,
            'orden': int,
            'nombre': str,
            'tarifa': int,
            'inicio': int,
            'fin': int,
        }
        super(Ticket, self).__init__(http, js)

    def get_fila_boletaje(self):
        return [self.orden, self.nombre, self.get_tarifa(), self.serie,  self.get_inicio(), self.get_cantidad(), self.get_fin(),
                '#88F', True, self]

    def get_tarifa(self):
        return '%.2f' % (self.tarifa / 100.)

    def get_inicio(self):
        return str(self.inicio).zfill(6)

    def get_fin(self):
        return str(self.fin).zfill(6)


class Tiempo(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'plantilla': int,
            'geocerca': int,
            'inicio': str,
            'fin': str,
            'tiempo': int,
            'multa': int,
            'factor': int,
        }
        super(Tiempo, self).__init__(http, js)

    def get_inicio(self):
        return self.get_time(self.inicio)

    def get_fin(self):
        return self.get_time(self.fin)

    def contiene(self, hora):
        if isinstance(hora, datetime.datetime):
            print(self.get_inicio() <= hora.time() < self.get_fin(), self.get_inicio(), hora.time(), self.get_fin())
            return self.get_inicio() <= hora.time() < self.get_fin()
        elif isinstance(hora, datetime.time):
            print(self.get_inicio() <= hora < self.get_fin(), self.get_inicio(), hora, self.get_fin())
            return self.get_inicio() <= hora < self.get_fin()


class Boleto(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'orden': int,
            'ruta': int,
            'nombre': str,
            'minimo': int,
            'opcional': int,
            'tarifa': int,
            'tacos': int,
            'segunda': bool,
            'activo': bool,
            'timestamp': str,
            'hasta': str,
            'color': str,
            'stock': int
        }
        super(Boleto, self).__init__(http, js)

    def requiere(self, cantidad):
        return cantidad < self.opcional

    def es_obligatorio(self, cantidad):
        return cantidad < self.minimo

    def get_stock(self):
        self.http.get_stock(self.stock)

    def get_tarifa(self):
        return '%.2f' % (self.tarifa / 100.)

    def get_limite_venta(self):
        return self.minimo / 2


class Trabajador(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'nombre': str,
            'dni': int,
            'tipoDni': str,
            'genero': bool,
            'nacimiento': str,
            'domicilio': str,
            'email': str,
            'celular': str,
            'licencia': str,
            'categoria': str,
            'estadoLicencia': str,
            'puntos': int,
            'vencimiento': str,
            'ingreso': str,
            'codigo': str,
            'conductor': bool
        }
        super(Trabajador, self).__init__(http, js)
        self.vencido = False
        if self.vencimiento:
            if self.getVencimiento() > datetime.date.today():
                self.vencido = True
        if self.puntos > 100:
            self.vencido = True

    def getVencimiento(self):
        return self.get_date(self.vencimiento)

    def get_nombre_codigo(self):
        if self.codigo:
            return self.nombre + ' ' + self.codigo
        else:
            return self.nombre + ' ID%s' % self.id

    def get_dni(self):
        return str(self.dni).zfill(8)

    def get_icon_datos(self):
        if self.vencido:
            return True
        else:
            if self.vencimiento:
                if self.getVencimiento() > (datetime.datetime.now() + datetime.timedelta(7)).date():
                    return False
        return None


class Frecuencia(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'plantilla': int,
            'ruta': int,
            'lado': bool,
            'inicio': str,
            'fin': str,
            'tiempo': int
        }
        super(Frecuencia, self).__init__(http, js)

    def get_inicio(self):
        dia = datetime.date.today()
        h, m, s = self.inicio.split(':')
        return datetime.datetime(dia.year, dia.month, dia.day, int(h), int(m))


class Usuario(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'nombre': str,
            'username': str,
            'email': str,
            'cargo': str,
            'genero': bool,
            'activo': bool,
            'lado': bool,
        }
        super(Usuario, self).__init__(http, js)


class Unidad(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'ruta': int,
            'lado': bool,
            'padron': int,
            'placa': str,
            'ingreso': str,
            'baja': bool,
            'vencimiento': str,
            'propietario': int,
            'paquete': int,
            'estado': str,
            'activo': bool,
            'actual': int,
            'sin_boletaje': int,
            'conductor': int,
            'cobrador': int,
            'odometro': int,
            'bloqueo': str,
            'modelo': str,
            'record': int,
            'arreglada': int,
            'prioridad': str,
            'boletos_save': bool,
            'ingreso_espera': str,
            'observacion': str,
            'fin_viaje': str,
            'cola': bool
        }
        super(Unidad, self).__init__(http, js)
        self.vencido = False
        if self.vencimiento:
            if self.getVencimiento() > datetime.date.today():
                self.vencido = True
        self.suministros = None

    def __repr__(self):
        return json.dumps([self.get_padron(), self.ingreso_espera, self.record, self.arreglada, self.cola])

    def get_padron(self):
        return str(self.padron).zfill(3)

    def get_modelo(self):
        return 'P%s %s %s' % (self.get_padron(), self.placa, self.modelo)

    def get_bloqueos(self):
        try:
            bloqueos = json.loads(self.bloqueo)
        except:
            return []
        else:
            return bloqueos

    def esta_bloqueado(self):
        bloqueos = self.get_bloqueos()
        lado = None
        if bloqueos:
            for b in bloqueos:
                if lado is None:
                    lado = b['lado']
                elif lado != b['lado']:
                    lado = 'Ambos'
        return lado

    def get_disponible(self):
        if self.estado == 'R':
            return False
        elif self.vencimiento:
            return False
        return True

    def get_motivo_no_disponible(self):
        mensaje = ''
        if self.estado == 'R':
            mensaje += '<span color="#B22">Unidad en RUTA en lado %s</span>\n' % self.get_lado_display()
        elif self.estado == 'E':
            mensaje += '<span color="#B22">Unidad en ESPERA en lado %s</span>\n' % self.get_lado_display()
        elif self.estado == 'X':
            mensaje += 'Unidad EXCLUIDA en lado %s\n' % self.get_lado_display()
        elif self.estado == 'F':
            mensaje += 'Unidad en FALLA MECÁNICA en lado %s\n' % self.get_lado_display()

        if self.vencido:
            mensaje += '<span color="#B22">Rev. Técnica Vencida: %s</span>\n' % self.vencimiento
        else:
            if self.vencimiento:
                if self.getVencimiento() > (datetime.datetime.now() + datetime.timedelta(7)).date():
                    mensaje += '<span color="#BB2">Rev. Técnica Por Vencer: %s</span>\n' % self.vencimiento
                else:
                    mensaje += '<span color="#BB2">Rev. Técnica en Regla: %s</span>\n' % self.vencimiento
            else:
                mensaje += '<span color="#BB2">Sin información de Rev. Técnica</span>\n'

        if not self.boletos_save:
            mensaje += '<span color="#BB2">FALTA GRABAR BOLETAJE</span>\n'

        if self.esta_bloqueado():
            mensaje += '<span color="#B22">%s</span>\n' % self.get_bloqueos()

        return mensaje

    def getVencimiento(self):
        return self.get_date(self.vencimiento)

    def get_fin_viaje(self):
        return self.get_datetime(self.fin_viaje)

    def get_icon_datos(self):
        if self.estado == 'R' or self.estado == 'E':
            return True
        elif self.vencido:
            return True
        else:
            if self.vencimiento:
                if self.getVencimiento() > (datetime.datetime.now() + datetime.timedelta(7)).date():
                    return False
        return None

    def puede_cambiar_personal(self):
        if self.estado == 'E' or self.estado == 'X':
            return True

    def color_disponible(self):
        if self.bloqueo:
            return '#B00'
        elif not self.boletos_save:
            return '#B80'
        elif self.vencido:
            return '#B00'
        else:
            return '#000'

    def get_ingreso_espera(self):
        return self.get_datetime(self.ingreso_espera)

    def get_ingreso_espera_text(self):
        return self.get_datetime(self.ingreso_espera).strftime('%Y-%m-%d %H:%M:%S')

    def get_propietario(self):
        return self.http.get_propietario(self.propietario)

    def get_conductor(self):
        return self.http.get_trabajador(self.conductor)

    def get_cobrador(self):
        return self.http.get_trabajador(self.cobrador)

    def get_suministros(self):
        if self.suministros is None:
            self.suministros = []
            data = self.http.load('get-suministros', {'unidad': self.id})
            if data:
                self.set_suministros(data['suministros'])
        return self.suministros

    def set_suministros(self, suministros):
        self.suministros = []
        for s in suministros:
            self.suministros.append(Suministro(self.http, s))
        self.ordenar_suministros()

    def add_suministros(self, suministros):
        for s in suministros:
            self.suministros.append(Suministro(self.http, s))
        self.ordenar_suministros()

    def ordenar_suministros(self):
        self.suministros.sort(key=lambda k: k.serie)
        self.suministros.sort(key=lambda k: k.inicio)
        self.suministros.sort(key=lambda k: k.boleto.orden)

    def get_falta_stock(self):
        self.get_suministros()
        boletos = {}
        for b in self.http.get_boletos():
            if b.ruta == self.ruta:
                boletos[b.id] = {
                    'cantidad': 0,
                    'boleto': b,
                }
        for s in self.suministros:
            if s.boleto.id in boletos:
                boletos[s.boleto.id]['cantidad'] += s.get_cantidad()

        faltan = []
        for k in boletos:
            b = boletos[k]
            boleto = b['boleto']
            if boleto.requiere(b['cantidad']):
                b['obligatorio'] = boleto.es_obligatorio(b['cantidad'])
                faltan.append(b)
        return faltan

    def calcular_controles(self):
        query = self.http.get_geocercas()
        geocercas = self.http.filtrar(query, {'activo': True, 'ruta': self.ruta, 'lado': self.lado})
        self.http.ordenar(geocercas, [('orden', 1)])

        query = self.http.get_plantillas()
        plantilla = None
        for q in query:
            if q.is_enable(self.inicio.date()):
                plantilla = q
                break

        if plantilla is None:
            raise TconturError('No hay plantilla para el día de hoy')
        query = self.http.get_tiempos()
        tiempos = self.http.filtrar(query, {'plantilla': plantilla.id})
        self.http.ordenar(tiempos, [('inicio', 1)])

        self.http.ordenar(geocercas, [('orden', 1)])
        inicio = self.inicio
        for g in geocercas:
            inicio = g.set_hora(inicio, tiempos)

        controles = {}
        for g in geocercas:
            controles[g.id] = {
                'g': g.id,
                'o': g.orden,
                'c': g.control,
                't': g.tiempo,
                'e': 'N',
                'v': 0,
                'f': g.factor,
                'm': g.multa
            }
        return controles

    def get_prioridad(self):
        if self.cola:
            return self.prioridad
        else:
            if self.arreglada > 0 :
                print('no se borro arreglada')
            return 'P'

    def get_fila_disponible(self):
        return [self.orden, self.padron, self.inicio.strftime('%H:%M'), self.frecuencia, self.record, self.arreglada,
                self.get_ingreso_espera_text(), self.get_prioridad(), self.color_disponible(), self]

    def get_fila_excluidos(self):
        return [self.orden, self.padron, self.get_ingreso_espera_text(), self]

    def arriba_de(self, anterior):
        if anterior:
            if self.cola is False:
                return
            if self.arreglada < anterior.arreglada:
                return
            elif self.record < anterior.record:
                self.arreglada = anterior.arreglada
            else:
                if self.get_ingreso_espera() < anterior.get_ingreso_espera():
                    self.arreglada = anterior.arreglada
                else:
                    self.arreglada = anterior.arreglada - 1


class Suministro(model_base):

    def __init__(self, *args):
        self.tipos = {
            'id': int,
            'ruta': int,
            'unidad': int,
            'boleto': int,
            'serie': str,
            'inicio': int,
            'actual': int,
            'fin': int,
            'estado': str,
            'data': str,
            'stock': int
        }
        super(Suministro, self).__init__(*args)
        self.set_boleto(self.http.get_boleto(self.boleto))
        self.editado = False
        self.guardar = None
        self.terminado = False
        self.mostrar = self.estado == u'U'

    def set_boleto(self, boleto):
        self.boleto = boleto

    def get_cantidad(self):
        return self.fin - self.actual

    def get_inicio(self):
        return str(self.inicio).zfill(6)

    def get_fin(self):
        return str(self.fin).zfill(6)

    def get_actual(self):
        return str(self.actual).zfill(6)

    def get_data(self):
        if self.data:
            return json.loads(self.data)
        else:
            return {}

    def get_color(self):
        if self.terminado:
            return '#F5B7B1'
        elif self.estado == 'U':
            return '#FFF'
        else:
            return '#ABEBC6'

    def get_fila_stock(self):
        entrega = self.get_data()['entrega']
        return [self.boleto.nombre, self.boleto.get_tarifa(), self.get_cantidad(), self.serie, self.get_inicio(),
                self.get_actual(), self.get_fin(), entrega['hora'], entrega['username'], False, self]

    def get_cantidad_guardar(self):
        return self.guardar - self.actual

    def get_guardar(self):
        return str(self.guardar).zfill(6)

    def get_guardar_1(self):
        return str(self.guardar - 1).zfill(6)

    def get_fila_boletaje(self):
        if self.editado:
            return [self.boleto.orden, self.boleto.nombre, self.boleto.get_tarifa(), self.serie,  self.get_actual(),
                    str(self.get_cantidad_guardar()), self.get_guardar(), self.get_color(), self]
        else:
            return [self.boleto.orden, self.boleto.nombre, self.boleto.get_tarifa(), self.serie, self.get_actual(),
                    '', '', self.get_color(), self]

    @staticmethod
    def get_liststore_boletaje():
        return int, str, str, str, str, str, str, str, GObject.TYPE_PYOBJECT

    def terminar(self):
        self.terminado = True
        self.editado = True
        self.guardar = self.fin

    def get_json_boletaje(self):
        return {
            'b': self.boleto.id,
            'su': self.id,
            'o': self.boleto.orden,
            'n': self.boleto.nombre,
            'ta': self.boleto.tarifa,
            's': self.serie,
            'i': self.actual,
            'f': self.guardar,
            't': self.terminado,
            'm': None
        }

    def puede_anular(self, inicio, fin):
        if self.actual <= inicio and fin <= self.guardar - 1:
            return True
        else:
            return False

    def anular(self, inicio, fin, motivo):
        return Boletaje(self.http, {
            'b': self.boleto.id,
            'su': self.id,
            'o': self.boleto.orden,
            'n': self.boleto.nombre,
            'ta': self.boleto.tarifa,
            's': self.serie,
            'i': inicio,
            'f': fin,
            't': False,
            'm': motivo
        })


class Boletaje(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'b': int,
            'su': int,
            'o': int,
            'n': str,
            'ta': int,
            's': str,
            'i': int,
            'f': int,
            't': bool,
            'm': str
        }
        super(Boletaje, self).__init__(http, js)

    def get_fila_boletaje(self):
        return [self.o, self.n, self.get_tarifa(), self.s,  self.get_inicio(), str(self.get_cantidad()), self.get_fin(),
                self.get_color(), self]

    def get_tarifa(self):
        return '%.2f' % (self.ta / 100.)

    def get_inicio(self):
        return str(self.i).zfill(6)

    def get_cantidad(self):
        if self.m:
            return self.f - self.i + 1
        else:
            return self.f - self.i

    def get_fin(self):
        return str(self.f).zfill(6)

    def get_color(self):
        if self.m:
            return '#EB9EA3'
        elif self.t:
            return '#F5B7B1'
        else:
            return '#FFF'

    def get_json_boletaje(self):
        return self.get_dict()


class Stock(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'boleto': int,
            'serie': str,
            'inicio': int,
            'actual': int,
            'fin': int,
            'estado': str,
            'data': str,
        }
        super(Stock, self).__init__(http, js)

    def get_cantidad(self):
        return self.fin - self.actual


class salida_base(model_base):

    def get_produccion(self):
        d = self.produccionBoletos + self.produccionTickets + self.produccionDiferencia + self.produccionTransbordo
        return Decimal(d / 100.).quantize(Decimal('0.01'))

    def color_ruta(self):
        if self.estado == 'F':
            return '#B00'
        else:
            return '#000'

    def get_padron(self):
        return str(self.padron).zfill(3)

    def get_inicio(self):
        return self.get_datetime(self.inicio)

    def get_dia(self):
        return self.get_date(self.dia)

    def color_estado(self):
        if self.estado == 'F':
            return '#B00' # rosado = Falla mecánica
        elif self.estado == 'X':
            return '#890' # amarillo = Excluido ni se usa
        elif self.estado == 'E':
            return '#000' # blanco = Disponible
        elif self.estado == 'T':
            return '#00B' # verde = terminado
        elif self.estado == 'R':
            return '#0B0' # plomo = en ruta

    def get_fila_enruta(self):
        return [self.orden, self.padron, self.get_inicio().strftime('%H:%M'), self.frecuencia, self.color_ruta(), self]

    def get_fin(self):
        return self.get_datetime(self.fin)

    def get_fin_hm(self):
        if self.fin:
            return self.get_fin().strftime('%H:%M')
        else:
            return '--:--'

    def get_fila_vueltas(self):
        return [self.orden / 2.,
                self.get_padron(),
                self.get_lado_display(),
                self.http.get_ruta(self.ruta).codigo,
                self.get_inicio().strftime('%H:%M'),
                self.get_fin_hm(),
                self.frecuencia,
                self.record,
                self.get_estado_display(),
                self.get_produccion(),
                self.dia,
                self.color_estado(),
                self
                ]


class Salida(salida_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'ruta': int,
            'lado': bool,
            'unidad': int,
            'padron': int,
            'placa': str,
            'inicio': str,
            'fin': str,
            'frecuencia': int,
            'estado': str,
            'record': int,
            'conductor': int,
            'ingreso': str,
            'creado': str,
            'dia': str,
            'backup': bool,
            'boletos_save': bool,
            'tickets_save': bool,
            'liquidacion': bool,
            'produccionBoletos': int,
            'produccionTickets': int,
            'produccionDiferencia': int,
            'produccionTransbordo': int,
            'pasajerosBoletos': int,
            'pasajerosTickets': int,
        }
        super(Salida, self).__init__(http, js)


class SalidaCompleta(salida_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'ruta': int,
            'lado': bool,
            'unidad': int,
            'padron': int,
            'placa': str,
            'inicio': str,
            'fin': str,
            'frecuencia': int,
            'estado': str,
            'record': int,
            'conductor': int,
            'ingreso': str,
            'creado': str,
            'dia': str,
            'backup': bool,
            'boletos_save': bool,
            'tickets_save': bool,
            'liquidacion': bool,
            'produccionBoletos': int,
            'produccionTickets': int,
            'produccionDiferencia': int,
            'produccionTransbordo': int,
            'pasajerosBoletos': int,
            'pasajerosTickets': int,
            'controles': str,
            'boletos': str,
            'tickets': str
        }
        super(SalidaCompleta, self).__init__(http, js)

    def get_controles(self):
        js = json.loads(self.controles)
        controles = []
        inicio = self.get_inicio()
        for k in js:
            llegada = Llegada(self.http, js[k])
            llegada.nombre = self.http.get_geocerca(llegada.g).nombre
            inicio = llegada.set_inicio(inicio)
            controles.append(llegada)
        controles.sort(key=lambda k: k.o)
        return controles

    def get_boletos(self):
        js = json.loads(self.boletos)
        boletos = []
        for b in js:
            boletos.append(Boletaje(self.http, b))
        return boletos

    def get_tickets(self):
        js = json.loads(self.tickets)
        tickets = []
        for t in js:
            tickets.append(Ticket(self.http, t))
        return tickets


class Config(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'nombre': str,
            'valor': str
        }
        super(Config, self).__init__(http, js)


class Documento(model_base):

    def __init__(self, http, js):
        self.tipos = {
            'id': int,
            'seria': str,
            'valor': str
        }
        super(Config, self).__init__(http, js)


class Configuracion:
    contado = True
    empresa = 1
    browser = 'windows-default'
    chrome = ''
    firefox = ''
    opera = ''
    edge = ''

    def __init__(self):
        try:
            f = open('outs/config', 'r')
            data = json.loads(f.read())
            f.close()
        except:
            data = {}
        for k in data.keys():
            setattr(self, k, data[k])
        self.set_browser()

    def save(self):
        data = {}
        data['contado'] = self.contado
        data['empresa'] = self.empresa
        data['browser'] = self.browser
        data['chrome'] = self.chrome
        data['firefox'] = self.firefox
        data['opera'] = self.opera
        data['edge'] = self.edge
        f = open('outs/config', 'w')
        f.write(json.dumps(data))
        f.close()
        self.set_browser()

    def set_browser(self):
        if self.browser == 'chrome':
            webbrowser.register('chrome', None, webbrowser.GenericBrowser(self.chrome), 1)
        elif self.browser == 'firefox':
            webbrowser.register('firefox', None, webbrowser.GenericBrowser(self.firefox), 1)
        elif self.browser == 'opera':
            webbrowser.register('opera', None, webbrowser.GenericBrowser(self.opera), 1)
        elif self.browser == 'edge':
            webbrowser.register('edge', None, webbrowser.GenericBrowser(self.edge), 1)
        else:
            self.browser = None

    def get_browser(self):
        return webbrowser.get(self.browser)


    def open_url(self, url):
        browser_thread = threading.Thread(target=self.open_thread, args=(url, ))
        browser_thread.start()

    def open_thread(self, url):
        self.get_browser().open(url)


MODELOS = {
    'fondos': None,
    'cobros': None,
    'productos': None,
    'boletos': None,

    'rutas': Ruta,
    'tiempos': Tiempo,
    'plantillas': Plantilla,
    'frecuencias': Frecuencia,
    'geocercas': Geocerca,
    'trabajadores': Trabajador,
    'propietarios': Usuario,
    'boletos': Boleto,
    'configuraciones': Config,
    'stocks': Stock,
    'documentos': Documento,
}

FERIADOS = [
    (2020, 1, 1),
    (2020, 4, 9),
    (2020, 4, 10),
    (2020, 5, 1),
    (2020, 6, 29),
    (2020, 7, 28),
    (2020, 7, 29),
    (2020, 8, 30),
    (2020, 10, 8),
    (2020, 11, 1),
    (2020, 12, 8),
    (2020, 12, 25),
]