#! /usr/bin/python
# -*- encoding: utf-8 -*-

import datetime
import json
import threading
from decimal import Decimal
import webbrowser
from Http import Http
from copy import deepcopy

IGV = 18


class TconturError(Exception):
    pass


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

    def __init__(self, js=None):
        self.http = Http()
        self.dataLocal = self.http.dataLocal
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
                    if self.tipos[k] == long:
                        self.__setattr__(k, long(objeto[k]))
                    else:
                        self.__setattr__(k, objeto[k])
            else:
                print('tipos', self.tipos)
                print('objeto', objeto)
                print('no hay', k)
                raise TconturError('No hay %s' % k)
        self.validate()

    def get_dict(self):
        dictionary = {}
        for k in self.tipos:
            dictionary[k] = self.__getattribute__(k)
        return dictionary

    def __repr__(self):
        return json.dumps(self.get_dict(), indent=4)

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
            return 'Falla Mec??nica'
        elif self.estado == 'E':
            return 'En Espera'
        elif self.estado == 'X':
            return 'Excluido'

    def get_precio(self):
        return "%.2f" % (self.precio / 100.)

    def get_placa(self):
        return self.placa[0:3] + '-' + self.placa[3:]


class Ruta(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'codigo': unicode,
            'tarjetaA': unicode,
            'tarjetaB': unicode,
        }
        self.plantilla = None
        self.frecuencias = None
        self.manual = [{'inicio': None, 'frecuencia': None}, {'inicio': None, 'frecuencia': None}]
        super(Ruta, self).__init__(js)
        self._tarjetaA = json.loads(self.tarjetaA)
        self._tarjetaB = json.loads(self.tarjetaB)

    def get_tarjetaA(self):
        return self._tarjetaA

    def get_tarjetaB(self):
        return self._tarjetaB

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
        print('get frecuencia', hora, lado)
        frecuencias = self.frecuencias[int(lado)]
        manual = self.manual[int(lado)]
        if hora is None:
            return self.getPrimeraHora(hora, lado)

        if manual['frecuencia'] is None:
            for f in frecuencias:
                if f.get_inicio() <= hora:
                    hora += datetime.timedelta(0, f.tiempo * 60)
                    print('frec', f.tiempo, f.get_inicio())
                    return hora, f.tiempo
        else:
            print('frec manual', manual['frecuencia'])
            hora += datetime.timedelta(0, manual['frecuencia'] * 60)
            return hora, manual['frecuencia']

    def set_manual(self, manual, lado=None):
        if lado is None:
            self.manual = manual
        else:
            self.manual[lado] = manual


class Plantilla(model_base):

    def __init__(self, js):
        self.tipos = {
        'id': long,
        'ruta': long,
        'nombre': unicode,
        'temporada': unicode,
        'inicio': unicode,
        'fin': unicode,
        'lunes': bool,
        'martes': bool,
        'miercoles': bool,
        'jueves': bool,
        'viernes': bool,
        'sabado': bool,
        'domingo': bool,
        'feriado': bool
        }
        super(Plantilla, self).__init__(js)

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

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'orden': long,
            'nombre': unicode,
            'ruta': long,
            'lado': bool,
            'longitud': float,
            'latitud': float,
            'radio': float,
            'control': bool,
            'datear': bool,
            'terminal': bool,
            'metros': long,
            'refrecuenciar': bool,
            'activo': bool,
            'desde': unicode,
            'hasta': unicode,
            'sagrado': bool,
            'retorno': bool,
            'audio': unicode
        }
        super(Geocerca, self).__init__(js)

    def set_hora(self, hora, tiempos):
        tiempos = filtrar(tiempos, {'geocerca': self.id})

        for t in tiempos:
            if t.contiene(hora):
                self.tiempo = t.tiempo
                self.multa = t.multa
                self.factor = t.factor
                self.hora = hora + datetime.timedelta(0, self.tiempo * 60)
                self.real = None
                return self.hora
        raise TconturError('No hay tiempo para esta geocerca %s' % self.nombre)


class Llegada(model_base):

    def __init__(self, *args):
        self.tipos = {
            'g': long,
            'o': long,
            'c': bool,
            't': long,
            'e': unicode,
            'v': long,
            'f': long,
            'm': long
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

    def __init__(self, js):
        self.tipos = {
            'boleto': long,
            'orden': long,
            'nombre': unicode,
            'tarifa': long,
            'inicio': long,
            'fin': long,
        }
        super(Ticket, self).__init__(js)

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

    def __init__(self, js):
        self.tipos = {
            'plantilla': long,
            'geocerca': long,
            'inicio': unicode,
            'fin': unicode,
            'tiempo': long,
            'multa': long,
            'factor': long,
        }
        super(Tiempo, self).__init__(js)

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

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'orden': long,
            'ruta': long,
            'nombre': unicode,
            'minimo': long,
            'opcional': long,
            'tarifa': long,
            'tacos': long,
            'segunda': bool,
            'activo': bool,
            'timestamp': unicode,
            'hasta': unicode,
            'color': unicode,
            'stock': long
        }
        super(Boleto, self).__init__(js)

    def requiere(self, cantidad):
        return cantidad < self.opcional

    def es_obligatorio(self, cantidad):
        return cantidad < self.minimo

    def get_stock(self):
        self.dataLocal.get_stock(self.stock)

    def get_tarifa(self):
        return '%.2f' % (self.tarifa / 100.)

    def get_limite_venta(self):
        return self.minimo / 2


class Trabajador(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'nombre': unicode,
            'dni': long,
            'tipoDni': unicode,
            'genero': bool,
            'nacimiento': unicode,
            'domicilio': unicode,
            'email': unicode,
            'celular': unicode,
            'licencia': unicode,
            'categoria': unicode,
            'estadoLicencia': unicode,
            'puntos': long,
            'vencimiento': unicode,
            'ingreso': unicode,
            'codigo': unicode,
            'conductor': bool
        }
        super(Trabajador, self).__init__(js)
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

    def __init__(self, js):
        self.tipos = {
            'plantilla': long,
            'ruta': long,
            'lado': bool,
            'inicio': unicode,
            'fin': unicode,
            'tiempo': long
        }
        super(Frecuencia, self).__init__(js)

    def get_inicio(self):
        dia = datetime.date.today()
        h, m, s = self.inicio.split(':')
        return datetime.datetime(dia.year, dia.month, dia.day, int(h), int(m))


class Propietario(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'nombre': unicode,
            'username': unicode,
            'email': unicode,
            'cargo': unicode,
            'genero': bool,
            'activo': bool,
            'lado': bool,
        }
        super(Propietario, self).__init__(js)

class Usuario(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'nombre': unicode,
            'username': unicode,
            'email': unicode,
            'cargo': unicode,
            'genero': bool,
            'activo': bool,
            'lado': bool,
        }
        super(Usuario, self).__init__(js)



class MyUsuario(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'nombre': unicode,
            'username': unicode,
            'empresa': long,
            'email': unicode,
            'cargo': unicode,
            'genero': bool,
            'activo': bool,
            'lado': bool,
            'permisos': unicode
        }
        super(MyUsuario, self).__init__(js)

    @property
    def get_permisos(self):
        try:
            return self._permisos
        except:
            self._permisos = json.loads(self.permisos)
            return self._permisos

    def tiene_permiso(self, permiso):
        if permiso in self.get_permisos:
            return self.get_permisos[permiso]

    def get_empresa(self):
        if self.tiene_permiso('soporte'):
            return None
        return self.empresa


class Unidad(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'ruta': long,
            'lado': bool,
            'padron': long,
            'placa': unicode,
            'ingreso': unicode,
            'baja': bool,
            'vencimiento': str,
            'propietario': long,
            'paquete': long,
            'estado': unicode,
            'activo': bool,
            'actual': long,
            'sin_boletaje': long,
            'conductor': long,
            'cobrador': long,
            'odometro': long,
            'bloqueo': unicode,
            'modelo': unicode,
            'record': long,
            'arreglada': long,
            'prioridad': unicode,
            'boletos_save': bool,
            'ingreso_espera': unicode,
            'observacion': unicode,
            'fin_viaje': unicode,
            'cola': bool
        }
        super(Unidad, self).__init__(js)
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
            mensaje += 'Unidad en FALLA MEC??NICA en lado %s\n' % self.get_lado_display()

        if self.vencido:
            mensaje += '<span color="#B22">Rev. T??cnica Vencida: %s</span>\n' % self.vencimiento
        else:
            if self.vencimiento:
                if self.getVencimiento() > (datetime.datetime.now() + datetime.timedelta(7)).date():
                    mensaje += '<span color="#BB2">Rev. T??cnica Por Vencer: %s</span>\n' % self.vencimiento
                else:
                    mensaje += '<span color="#BB2">Rev. T??cnica en Regla: %s</span>\n' % self.vencimiento
            else:
                mensaje += '<span color="#BB2">Sin informaci??n de Rev. T??cnica</span>\n'

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
        return self.dataLocal.get_propietario(self.propietario)

    def get_conductor(self):
        return self.dataLocal.get_trabajador(self.conductor)

    def get_cobrador(self):
        return self.dataLocal.get_trabajador(self.cobrador)

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
            self.suministros.append(Suministro(s))
        self.ordenar_suministros()

    def add_suministros(self, suministros):
        for s in suministros:
            self.suministros.append(Suministro(s))
        self.ordenar_suministros()

    def ordenar_suministros(self):
        self.suministros.sort(key=lambda k: k.serie)
        self.suministros.sort(key=lambda k: k.inicio)
        self.suministros.sort(key=lambda k: k.boleto.orden)

    def get_falta_stock(self):
        self.get_suministros()
        boletos = {}
        for b in self.dataLocal.get_boletos():
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
        query = self.dataLocal.get_geocercas()
        geocercas = filtrar(query, {'activo': True, 'ruta': self.ruta, 'lado': self.lado})
        ordenar(geocercas, [('orden', 1)])

        query = filtrar(self.dataLocal.get_plantillas(), {'ruta': self.ruta})
        plantilla = None
        for q in query:
            if q.is_enable(self.inicio.date()):
                plantilla = q
                break

        if plantilla is None:
            raise TconturError('No hay plantilla para el d??a de hoy')
        query = self.dataLocal.get_tiempos()
        tiempos = filtrar(query, {'plantilla': plantilla.id})
        ordenar(tiempos, [('inicio', 1)])

        ordenar(geocercas, [('orden', 1)])
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


class Suministro(model_base):

    def __init__(self, *args):
        self.tipos = {
            'id': long,
            'ruta': long,
            'unidad': long,
            'boleto': long,
            'serie': unicode,
            'inicio': long,
            'actual': long,
            'fin': long,
            'estado': unicode,
            'data': unicode,
            'stock': long
        }
        super(Suministro, self).__init__(*args)
        self.set_boleto(self.dataLocal.get_boleto(self.boleto))
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
                    self.get_cantidad_guardar(), self.get_guardar(), self.get_color(), self]
        else:
            return [self.boleto.orden, self.boleto.nombre, self.boleto.get_tarifa(), self.serie, self.get_actual(),
                    '', '', self.get_color(), self]

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

    def __init__(self, js):
        self.tipos = {
            'b': long,
            'su': long,
            'o': long,
            'n': unicode,
            'ta': long,
            's': unicode,
            'i': long,
            'f': long,
            't': bool,
            'm': unicode
        }
        super(Boletaje, self).__init__(js)

    def get_fila_boletaje(self):
        return [self.o, self.n, self.get_tarifa(), self.s,  self.get_inicio(), self.get_cantidad(), self.get_fin(),
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

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'boleto': long,
            'serie': unicode,
            'inicio': long,
            'actual': long,
            'fin': long,
            'estado': unicode,
            'data': unicode,
        }
        super(Stock, self).__init__(js)

    def get_cantidad(self):
        return self.fin - self.actual


class salida_base(model_base):

    def get_creado(self):
        return self.get_datetime(self.creado)

    def get_conductor(self):
        return self.dataLocal.get_trabajador(self.conductor)

    def get_cobrador(self):
        return self.dataLocal.get_trabajador(self.cobrador)

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
            return '#B00' # rosado = Falla mec??nica
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
                self.dataLocal.get_ruta(self.ruta).codigo,
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

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'ruta': long,
            'lado': bool,
            'unidad': long,
            'padron': long,
            'placa': unicode,
            'inicio': unicode,
            'fin': unicode,
            'frecuencia': long,
            'estado': unicode,
            'record': long,
            'conductor': long,
            'cobrador': long,
            'ingreso': unicode,
            'creado': unicode,
            'dia': unicode,
            'backup': bool,
            'boletos_save': bool,
            'tickets_save': bool,
            'liquidacion': bool,
            'produccionBoletos': long,
            'produccionTickets': long,
            'produccionDiferencia': long,
            'produccionTransbordo': long,
            'pasajerosBoletos': long,
            'pasajerosTickets': long,
        }
        super(Salida, self).__init__(js)


class SalidaCompleta(salida_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'ruta': long,
            'lado': bool,
            'unidad': long,
            'padron': long,
            'placa': unicode,
            'inicio': unicode,
            'fin': unicode,
            'frecuencia': long,
            'estado': unicode,
            'record': long,
            'conductor': long,
            'cobrador': long,
            'ingreso': unicode,
            'creado': unicode,
            'dia': unicode,
            'backup': bool,
            'boletos_save': bool,
            'tickets_save': bool,
            'liquidacion': bool,
            'produccionBoletos': long,
            'produccionTickets': long,
            'produccionDiferencia': long,
            'produccionTransbordo': long,
            'pasajerosBoletos': long,
            'pasajerosTickets': long,
            'controles': unicode,
            'boletos': unicode,
            'tickets': unicode
        }
        super(SalidaCompleta, self).__init__(js)

    def parse_tarjeta(self, salidas):
        parsed = {}
        parsed['vuelta'] = self.orden / 2.
        parsed['conductor'] = self.get_conductor().codigo if self.conductor else 'Ninguno'
        parsed['cobrador'] = self.get_cobrador().codigo if self.cobrador else 'Ninguno'
        parsed['impresion'] = self.get_creado().strftime('%H:%M:%S %d/%m/%Y')
        parsed['inicio'] = self.get_inicio().strftime('%H:%M')
        parsed['dia'] = self.get_dia().strftime('%d/%m/%Y')
        parsed['padron'] = self.get_padron()
        parsed['placa'] = self.get_placa()

        parsed['controles'] = []

        for l in self.get_controles():
            parsed['controles'].append(l.get_hora_str())

        boletos1 = []
        boletos2 = []

        data = self.http.load('get-suministros', {'unidad': self.unidad})
        if data:
            boletos = self.http.dataLocal.get_boletos()
            boletos = filtrar(boletos, {'ruta': self.ruta})
            ordenar(boletos, [('estado', -1), ('orden', 1)])
            boletos_1 = []
            boletos_2 = []
            for b in boletos:
                if b.segunda:
                    boletos_2.append(b)
                    boletos2.append([])
                else:
                    boletos_1.append(b)
                    boletos1.append([])
            for i, b in enumerate(boletos_1):
                for s in data['suministros']:
                    if b.id == s['boleto']:
                        boletos1[i].append(str(s['actual']).zfill(6))
            for i, b in enumerate(boletos_2):
                for s in data['suministros']:
                    if b.id == s['boleto']:
                        boletos2[i].append(str(s['actual']).zfill(6))
        parsed['boletos'] = boletos1
        parsed['boletos2'] = boletos2

        parsed['producciones'] = []
        for s in salidas:
            parsed['producciones'].append(s.get_produccion())

        return parsed

    def get_controles(self):
        js = json.loads(self.controles)
        controles = []
        inicio = self.get_inicio()
        for k in js:
            llegada = Llegada(js[k])
            controles.append(llegada)
        ordenar(controles, [('o', 1)])
        for c in controles:
            c.nombre = self.dataLocal.get_geocerca(c.g).nombre
            inicio = c.set_inicio(inicio)
        return controles

    def get_boletos(self):
        js = json.loads(self.boletos)
        boletos = []
        for b in js:
            boletos.append(Boletaje(b))
        return boletos

    def get_tickets(self):
        js = json.loads(self.tickets)
        tickets = []
        for t in js:
            tickets.append(Ticket(t))
        return tickets


class Config(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'nombre': unicode,
            'data': unicode
        }
        super(Config, self).__init__(js)


class Producto(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'servicio': bool,
            'codigo': unicode,
            'nombre': unicode,
            'cliente': unicode,
            'precio': long,
            'igv': bool,
            'moneda': bool,
            'variable': bool,
            'stock': long,
            'fracciones': bool,
            'fondo': bool,
            'gasto': bool
        }
        super(Producto, self).__init__(js)

    def get_igv_str(self):
        if self.igv is None:
            return 'INAFECTO IGV'
        elif self.igv is True:
            return 'INCLUYE IGV'
        else:
            return 'NO INC. IGV'

    def get_igv(self):
        if self.igv is None:
            return 0
        elif self.igv:  # incluye
            return -IGV
        else:  # no incluye
            return +IGV


class Item(model_base):

    def __init__(self, js=None):
        self.tipos = {
            'id': long,
            'recibo': long,
            'producto': bool,
            'cantidad': long,
            'precio': long,
            'igv': long,
            'moneda': bool
        }
        super(Item, self).__init__(js)
        self.pagar = 0
        self._producto = None

    def set_producto(self, producto):
        self._producto = producto
        self.producto = producto.id
        self.cantidad = 0
        self.precio = producto.precio
        self.igv = producto.get_igv()
        self.moneda = producto.moneda

    def get_producto(self):
        if self._producto is None:
            self._producto = self.http.dataLocal.get_producto(self.producto)
        return self._producto

    def get_total(self):
        if self._producto.gasto:
            return 0
        if self.igv == 0:                               # sin IGV
            return round(self.precio * self.cantidad / 1000)
        elif self.igv < 0:                              # incluye
            return round(self.precio * self.cantidad / 1000)
        else:                                           # no incluye
            return round(self.precio * self.cantidad * (100 + IGV) / 1000)

    def get_igv(self):
        if self._producto.gasto:
            return 0
        if self.igv == 0:
            return 0
        elif self.igv < 0:
            return round(self.cantidad * self.precio * (-IGV) / (100 - IGV) / 1000)
        else:
            return round(self.cantidad * self.precio * IGV / 100000)

    def get_base(self):
        if self._producto.gasto:
            return 0
        if self.igv == 0:
            return 0
        elif self.igv < 0:
            return self.get_total() - self.get_igv()
        else:
            return round(self.precio * self.cantidad) / 1000

    def get_inafecta(self):
        if self._producto.gasto:
            return round(self.precio * self.cantidad) / 1000
        if self.igv == 0:
            return self.get_total()
        elif self.igv < 0:
            return 0
        else:
            return 0

    def fijar_precio(self, precio):
        if self._producto.variable:
            self.precio = float(precio) * 100
            self.cantidad = 1000

    def cotizar_precio(self, monto):
        self.cantidad = (float(monto) * 100000 / self.precio)

    def cotizar_cantidad(self, cantidad):
        self.cantidad = float(cantidad) * 1000

    def get_fila_cobranza(self):
        return [
            self.orden,
            self._producto.codigo,
            self._producto.nombre,
            self.get_cantidad(),
            self.get_precio(),
            currency(self.get_base() + self.get_inafecta()),
            currency(self.get_igv()),
            currency(self.get_total()),
            self
        ]

    def get_cantidad(self):
        return "%.3f" % (self.cantidad / 1000.)

    def como_retiro(self):
        self.pagar = - self.pagar

    def get_json_item(self):
        return {
            'producto': self._producto.get_dict(),
            'cantidad': self.cantidad,
            'precio': self.precio,
            'igv': self.igv,
            'moneda': self.moneda
        }


class TipoDocumento(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'tipo': long,
            'numero': long,
            'serie': unicode
        }
        super(TipoDocumento, self).__init__(js)


class Recibo(model_base):
    columnas = ('SERIE', 'NUMERO', 'HORA', 'CLIENTE', 'MONTO', 'TIPO')

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'documento': long,
            'serie': unicode,
            'numero': long,
            'hora': unicode,
            'cliente': long,
            'usuario': long,
            'caja': long,
            'anulado': long,
            'efectivo': bool,
            'total': long
        }
        super(Recibo, self).__init__(js)
        self._cliente = None
        self._usuario = None
        self._base = None
        self._igv = None
        self._total = None

    def get_numero(self):
        return str(self.numero).zfill(6)

    def get_ticket(self):
        ticket = Voucher()
        codigo = self.http.dataLocal.get_config('codigo')
        direccion = self.http.dataLocal.get_config('direccion')
        ruc = self.http.dataLocal.get_config('ruc')
        dia = self.get_hora().strftime('%Y-%m-%d')
        cliente = self.get_cliente()

        ticket.titulo(codigo.data)
        ticket.subtitulo(direccion.data)
        ticket.subtitulo('R.U.C.: %s' % ruc.data)
        ticket.espacio()
        ticket.subtitulo('%s - %s' % (self.serie, self.get_numero()))
        ticket.espacio()
        ticket.contenido('DIA: %s' % dia)
        ticket.contenido('CLIENTE: %s' % cliente.referencia)
        ticket.contenido('CODIGO: %s' % cliente.codigo)
        ticket.contenido('NOMBRE: %s' % cliente.nombre)
        ticket.espacio()
        ticket.tabular3('  DETALLE', 'CANT', 'TOTAL', True)
        for i, item in enumerate(self._items):
            subrayado = i == (len(self._items) - 1)
            ticket.tabular3(item.get_producto().nombre, item.get_cantidad(), item.get_subtotal(), subrayado)
        if self._igv:
            ticket.tabular3('', 'SUBTOTAL', currency(self._base))
            ticket.tabular3('', 'IGV', currency(self._igv))
        ticket.tabular3('', 'TOTAL', currency(self._total))
        ticket.espacio()
        if self.get_efectivo():
            ticket.subtitulo('TICKET EMITIDO AL CONTADO')
        else:
            ticket.subtitulo('TICKET EMITIDO AL CREDITO')
        ticket.espacio()
        ticket.subtitulo('ID: %s' % self.id)
        ticket.tabular2(self.get_usuario().nombre, self.get_hora().strftime('%H:%M:%S %d/%m/%Y'))
        ticket.subtitulo('GRACIAS !!')
        return ticket

    def get_hora(self):
        return self.get_datetime(self.hora)

    def get_cliente(self):
        if self._cliente is None:
            self._cliente = self.http.dataLocal.get_cliente(self.cliente)
        return self._cliente

    def get_usuario(self):
        if self._usuario is None:
            self._usuario = self.http.dataLocal.get_usuario(self.usuario)
        return self._usuario

    def get_efectivo(self):
        if self.efectivo:
            return 'EFECTIVO'
        else:
            return 'CR??DITO'

    def get_fila(self):
        return [self.serie, self.numero, self.get_hora().strftime('%Y-%m-%d %H:%M:%S'),
                self.get_cliente().codigo, self.get_total(), self.get_efectivo(), self]

    def get_total(self):
        return "%.2f" % (self.total / 100.)

    def set_items(self, items):
        self._total = 0
        self._igv = 0
        self._base = 0
        self._items = []
        for i in self._items:
            self._items.append(Item(i))
            self._total += i.get_total()
            self._igv += i.get_igv()
            self._base += i.get_base()

        return self._items


class Cliente(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'tipo': unicode,
            'codigo': unicode,
            'referencia': unicode,
            'nombre': unicode,
        }
        super(Cliente, self).__init__(js)


class Deuda(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'tipo': long,
            'codigo': long,
            'referencia': long,
            'nombre': long,
        }
        super(Cliente, self).__init__(js)


class Caja(model_base):

    def __init__(self, js):
        self.tipos = {
            'id': long,
            'usuario': long,
            'inicio': unicode,
            'fin': unicode,
            'total': long,
        }
        super(Caja, self).__init__(js)

    def get_inicio(self):
        return self.get_datetime(self.inicio)

    def get_fin(self):
        return self.get_datetime(self.inicio)

    def get_total(self):
        return "%.2f" % (self.total / 100.)


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
    'recibo': Recibo,
    'item': Item,

    'rutas': Ruta,
    'tiempos': Tiempo,
    'plantillas': Plantilla,
    'frecuencias': Frecuencia,
    'geocercas': Geocerca,
    'trabajadores': Trabajador,
    'propietarios': Propietario,
    'boletos': Boleto,
    'configuraciones': Config,
    'stocks': Stock,
    'productos': Producto,
    'tiposDocumento': TipoDocumento,
    'clientes': Cliente,
    'deudas': Deuda,
    'usuarios': Usuario
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


def currency(entero):
    return "%.2f" % (entero / 100.)


def quantity(entero):
    return "%.3f" % (entero / 1000.)


def filtrar(lista, filter):
    query = []
    for l in lista:
        if cumple(l, filter):
            query.append(l)
    return query


def cumple(item, filter):
    for f in filter:
        if item.get_param(f) == filter[f]:
            continue
        else:
            return False
    return True


def ordenar(lista, sort):
    sort.reverse()
    for k, orden in sort:
        lista.sort(key=lambda x: x.__getattribute__(k))
        if orden < 0:
            lista.reverse()


class Voucher:

    def __init__(self):
        self.comandos = []

    def titulo(self, texto):
        self.comandos.append((('CENTER', 'b', 'normal', 1, 1), texto))

    def subtitulo(self, texto):
        self.comandos.append((('CENTER', 'b', 'normal', 1, 1), texto))

    def negrita(self, texto):
        self.comandos.append((('LEFT', 'b', 'b', 1, 1), texto))

    def grande(self, texto):
        self.comandos.append((('CENTER', 'b', 'g', 1, 1), texto))

    def centrado_subrayado(self, texto):
        self.comandos.append((('CENTER', 'b', 'u', 1, 1), texto))

    def negrita_subrayado(self, texto):
        self.comandos.append((('CENTER', 'b', 'ub', 1, 1), texto))

    def subrayado(self, texto):
        self.comandos.append((('LEFT', 'b', 'u', 1, 1), texto))

    def espacio(self):
        self.comandos.append(None)

    def contenido(self, texto):
        self.comandos.append((('LEFT', 'b', 'normal', 1, 1), texto))

    def tabular3(self, izq, medio, der, subrayado=False):
        b = medio
        w = 29 - len(b)
        a = (izq + ' ' * w)[:w]
        c = (' ' * 9 + der)[-9:]
        texto = a + b + c + '\n'
        if subrayado:
            self.subrayado(texto)
        else:
            self.contenido(texto)

    def tabular2(self, izq, der, subrayado=False):
        b = der
        w = 39 - len(b)
        a = (izq + ' ' * w)[:w]
        texto = a + b + '\n'
        if subrayado:
            self.subrayado(texto)
        else:
            self.contenido(texto)

    def tabular2_grande(self, izq, der, subrayado=False):
        b = der
        w = 19 - len(b)
        a = (izq + ' ' * w)[:w]
        texto = a + b + '\n'
        if subrayado:
            self.grande(texto)
        else:
            self.grande(texto)

    def tabular2negrita(self, izq, der):
        b = der
        w = 39 - len(b)
        a = (izq + ' ' * w)[:w]
        texto = a + b + '\n'
        self.negrita(texto)