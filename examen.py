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
            salida.append(pregunta)

    if len(lista) != len(salida):
        print('*'*80)
        print("ERROR: No se encontraron todas las preguntas")

    return salida


def generar_examen(examen):
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

    examenes = leer_json(OrigenExamenes)
    preguntas, configuracion = examenes["preguntas"], examenes["configuracion"]
    
    nombre, descripcion, opciones = traer_examen(examen)
    
    salida = []
    for o in opciones:
        tipo, cantidad = o["tipo"], o["cantidad"]
        seleccion = traer_preguntas(tipo)
        if seleccion: 
            seleccion = random.sample(seleccion, cantidad)
            salida.extend(seleccion)
    
    for i, pregunta in enumerate(salida):
        pregunta['numero'] = i+1
        pregunta['eleccion'] = 0
    
    for i, pregunta in enumerate(salida): 
        pregunta['numero'] = i + 1
        pregunta['eleccion'] = 0

    return {"examen": examen, "nombre": nombre, "descripcion": descripcion, "preguntas": salida}

__all__ = ['cargar_examenes', 'generar_examen', 'cargar_preguntas', 'OrigenIconos', 'OrigenLogo', 'Base']