import random
import json

Base = 'demo'

OrigenExamenes = f'{Base}/examenes.json'
OrigenIconos   = f'/{Base}/iconos'
OrigenLogo     = f'/{Base}/logo-yb.png'

def leer_json(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f) 
    
def cargar_examenes():
    """ Carga los examenes a partir de la configuración """
    lista = leer_json(OrigenExamenes)['configuracion']
    return lista


def traer_preguntas():
    """ Generar un diccionario con las preguntas """
    preguntas = leer_json(OrigenExamenes)['preguntas']
    salida = {}
    for tipo in preguntas:
        for pregunta in tipo['preguntas']:
            pregunta['tipo'] = tipo['tipo']
            pregunta['respuesta'] = pregunta['correcta'].index('x') + 1 
            salida[str(pregunta['id'])] = pregunta
    return salida


def cargar_preguntas(lista, elecciones):
    """ 
    Carga las preguntas a partir de los identificadores 
    y las elecciones del usuario y las enumera
    """
    preguntas = traer_preguntas()
    salida = []
    for i, id in enumerate(lista):
        id = str(id)
        pregunta = preguntas[id]
        if pregunta:
            pregunta['numero'] = i + 1
            pregunta['eleccion'] = int(elecciones[id]) if id in elecciones else 0
            pregunta['imagen'] = pregunta['respuestas'][0].startswith('<')
            salida.append(pregunta)

    if len(lista) != len(salida):
        print('*'*80)
        print("ERROR: No se encontraron todas las preguntas")

    return salida

def resumir_examen(preguntas):
    correctas = [pregunta['id'] for pregunta in preguntas if pregunta['eleccion'] == pregunta['respuesta']]
    erroneas  = [pregunta['id'] for pregunta in preguntas if pregunta['eleccion'] != pregunta['respuesta']]
    return correctas, erroneas

def generar_examen(examen, semilla=0):
    """ Genera un examen a partir de la configuración """

    def traer_preguntas(tipo):
        lista = [p['preguntas'] for p in preguntas if p["tipo"] == tipo]
        return lista[0] if lista else None 

    def traer_examen(nombre):
        nombre = nombre.strip().upper()
        for c in configuracion:
            for e in c["examenes"]:
                if nombre == e["nombre"].upper():
                    return (e['nombre'], e['descripcion'], e['opciones'])
        return []

    if semilla: random.seed(semilla) # Generar siempre el mismo examen

    examenes = leer_json(OrigenExamenes)
    preguntas, configuracion = examenes["preguntas"], examenes["configuracion"]
    
    nombre, descripcion, opciones = traer_examen(examen)
    
    salida = []
    for o in opciones:
        tipo, cantidad = o["tipo"], o["cantidad"]
        seleccion = traer_preguntas(tipo)
        if seleccion:
            for pregunta in seleccion:
                pregunta['tipo'] = tipo
            seleccion = random.sample(seleccion, cantidad)
            salida.extend(seleccion)

    
    salida.sort(key=lambda x: (x['tipo'], x['id']))
    for i, pregunta in enumerate(salida): 
        pregunta['numero'] = i + 1
        pregunta['eleccion'] = 0
        pregunta['respuesta'] = pregunta['correcta'].index('x') + 1

    return {'examen': examen, 'nombre': nombre, 'descripcion': descripcion, 'preguntas': salida, 'id': semilla}

__all__ = ['cargar_examenes', 'generar_examen', 'cargar_preguntas', 'OrigenIconos', 'OrigenLogo', 'Base', 'resumir_examen']