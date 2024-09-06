import random
import json
from fasthtml.common import *
from fasthtml.components import *
import logging

Version = '0.5.5'
Base = 'demo'

OrigenExamenes = f'{Base}/examenes.json'
OrigenIconos   = f'/{Base}/iconos'

logger = logging.getLogger('app')

def leer_json(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f) 
    
def cargar_examenes():
    """ Carga los examenes a partir de la configuración """
    lista = leer_json(OrigenExamenes)['configuracion']
    print(f'Lista : {len(lista)}')
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
    
    # mostrar_examen(nombre, descripcion, salida)
    return {"examen": examen, "nombre": nombre, "descripcion": descripcion, "preguntas": salida}

################################################################################

app, rt = fast_app(pico=True, hdrs=(
    Link(rel='stylesheet', href='/demo/estilo.css', type='text/css'),
))

rt = app.route

def Icono(nombre):
    return Img(src=f"{OrigenIconos}/{nombre}.png", cls="imagen")

def MostrarEstado(preguntas):
    cantidad = len(preguntas)
    respondidas = sum(1 for pregunta in preguntas if pregunta['eleccion'] > 0)
    return Span(f"Hay {respondidas} preguntas respondidas de {cantidad}", id="estado")

def MostrarPreguntas(preguntas, pendientes=False):
    return (MostrarPregunta(pregunta, pendientes) for pregunta in preguntas)# if not pendientes or pregunta['eleccion'] == 0)

def MostrarPregunta(pregunta, pendientes=False):
    id = pregunta['id']
    numero = pregunta['numero']
    eleccion = pregunta['eleccion']
    
    correcta = pregunta['correcta'].index('x') + 1
    if eleccion != 0:
        print('Correcta : ', correcta, "Eleccion : ", eleccion)
    
    return Card(
        Fieldset(
            Legend(I(numero), H4(pregunta['pregunta']), pregunta['correcta'], Small(f"{id:03}")),
            *[MostrarRespuesta(numero, id, i+1, respuesta, eleccion, correcta) for i, respuesta in enumerate(pregunta['respuestas'])] 
        ), cls = 'contestar' if pendientes and eleccion == 0 else None
    )

def TipoExamen(tipo):
    def IrExamen(examen):
        nombre, descripcion = examen['nombre'], examen['descripcion']
        return A(Div(B(nombre), Span(descripcion)), href=f"/examen/{nombre}")

    def TituloExamen(tipo):
        return Div(B(tipo['clase']), Span(tipo['descripcion']))

    return Article(
        TituloExamen(tipo),
        *[IrExamen(examen) for examen in tipo['examenes']]
    )

def MostrarRespuesta(numero, id, i, respuesta, eleccion, correcta):
    def MostrarImagen(imagen):
        return  Label(
                    Input(type='radio', id=f"{numero}-{i}", name=id, value=i, aria_invalid=invalido, checked=actual),
                    Icono(imagen),
                    _for=f"{numero}-{i}", cls='horizontal'
                )
    
    def MostrarOpcion():
        return Label(
                Input(type='radio', id=f"{numero}-{i}", name=id, value=i, aria_invalid=invalido, checked=actual), 
                respuesta, 
                _for=f"{numero}-{i}", cls='vertical'
            )

    actual = (eleccion == i)
    invalido = None
    if actual:
        invalido = 'false' if i == correcta else 'true'

    m = re.match(r'<(\d{3})>', respuesta)
    return MostrarImagen(m.group(1)) if m else MostrarOpcion()

def aplicar_eleccion(preguntas, datos):    
    for pregunta in preguntas:
        id = str(pregunta['id'])
        if id in datos:
            pregunta['eleccion'] =  int(datos[id]) 
        else:
            pregunta['eleccion'] = 0

    print(f"aplicar_eleccion >> Preguntas : ", json.dumps(preguntas[:3], indent=4))
    return preguntas    

def simular_eleccion(preguntas):
    preguntas[1]['eleccion'] = 1 
    preguntas[2]['eleccion'] = 2 
    preguntas[3]['eleccion'] = 3

def EnviarRespuesta(mensaje="",parcial=False):
    return Div(
        Span(mensaje, id='mensaje'),
        Button("Completar Exámen" if parcial else 'Evaluar Exámen', hx_post="/evaluar", hx_target="#main",  hx_swap="innerHTML"), 
        id='enviar'
    ) 

@rt('/')
async def get(): 
    examenes = cargar_examenes()

    return Div(
            Header( 
                H1(f'Elegir Exámen v {Version}')
            ),
            Main( 
                *[TipoExamen(examen) for examen in examenes]
            ),
            Footer("Pie 2"),
            id='pagina'
        )


@rt('/estadisticas')
async def get():
    examenes = cargar_examenes()

    return (
        Header(H1('Estadísticas')),
        Main(
            H2('Estadísticas'),
            Div(f"Hay {len(examenes)} preguntas"),
            Button("Volver al inicio" , hx_get="/"), 
        ),
    )

@rt('/examen/{examen}')
async def get(session, examen: str):    

    datos = generar_examen(examen)
    examen, descripcion, preguntas = datos['examen'], datos['descripcion'], datos['preguntas']
    
    print('='*80)
    print(json.dumps(preguntas[:3], indent=4))

    for i, pregunta in enumerate(preguntas): 
        pregunta['numero'] = i + 1
        pregunta['eleccion'] = 0
        
    simular_eleccion(preguntas)

    session['preguntas'] = [pregunta['id'] for pregunta in preguntas]
    print(f"Preguntas : {session['preguntas']}")

    return (
        Div(
            Header(
                H1(examen + f'v {Version}'), 
                H6(descripcion),
                id='titulo'
            ),
            Main(
                MostrarEstado(preguntas),
                Form(
                    * MostrarPreguntas(preguntas),
                    EnviarRespuesta(), 
                ),
                id='main'
            ),
            cls='container',
            id='pagina'
        )
    )


@rt('/evaluar')
async def post(session, datos: dict):

    ids = session['preguntas']

    preguntas = cargar_preguntas(ids, datos)

    print(f"Datos: ", datos)
    print(f"Evaluar >> Session   : {sorted(session['preguntas'][:10])}")
    print(f"Evaluar >> Preguntas : {sorted([pregunta['id'] for pregunta in preguntas][:10])}")
    print(f"Preguntas (A):", json.dumps(preguntas[:3], indent=4))
    
    preguntas = aplicar_eleccion(preguntas, datos)
    contestadas = [pregunta for pregunta in preguntas if pregunta['eleccion'] > 0]
    print(f"Preguntas (D):", json.dumps(contestadas[:10], indent=4))

    falta = len(preguntas) - len(contestadas)

    if falta == 0:
        session['respuestas'] = datos 
        return RedirectResponse(url="/resultado")

    return (
        MostrarEstado(preguntas),
        Form(
            * MostrarPreguntas(preguntas, pendientes=True),
            EnviarRespuesta((f'Falta responder {falta} pregunta{'s' if falta else ''}'), parcial=True),
        )
    )    

@rt('/resultado')
async def post(session):
    preguntas = session['preguntas']
    respuestas = session['respuestas']

    preguntas = cargar_preguntas(preguntas, respuestas)

    cantidad = len(preguntas)
    correctas = sum(1 for pregunta in preguntas if pregunta['eleccion'] == pregunta['correcta'].index('x') + 1)

    resultado = 'Aprobado' if correctas >= cantidad * 0.9 else 'Reprobado'
    return (
        Header(H1('Resultado')),
        Main(
            P(f"Hay {correctas} respuestas correctas de {cantidad}"),
            H2(f'El examen está: {resultado}'),
            Button("Volver al inicio" , hx_get="/", hx_target="#main",  hx_swap="innerHTML"), 
        ),
    )

serve()

