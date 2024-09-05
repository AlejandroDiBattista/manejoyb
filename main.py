import random
import json
from fasthtml.common import *
from fasthtml.components import *
# from fastapi.middleware.cors import CORSMiddleware

Version = '0.5'
Base = 'demo'
OrigenExamenes = f'{Base}/examenes.json'
OrigenIconos   = f'/{Base}/iconos'

def leer_json(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f) 
    
def cargar_examenes():
    """ Carga los examenes a partir de la configuración """
    lista = leer_json(OrigenExamenes)['configuracion']
    print(f'Lista : {len(lista)}')
    return lista

def generar_examen(examen):
    """ Genera un examen a partir de la configuración """

    def traer_preguntas(tipo):
        return [p['preguntas'] for p in preguntas if p["tipo"] == tipo][0]

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

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Cambia esto según tus necesidades de seguridad
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

def Icono(nombre):
    return Img(src=f"{OrigenIconos}/{nombre}.png", cls="imagen")

def MostrarEstado(preguntas):
    cantidad = len(preguntas['preguntas'])
    respondidas = sum(1 for pregunta in preguntas['preguntas'] if pregunta['eleccion'] > 0)
    return Span(f"Hay {respondidas} preguntas respondidas de {cantidad}", id="estado")

def MostrarPreguntas(preguntas, pedientes=False):
    return (MostrarPregunta(pregunta) for pregunta in preguntas['preguntas'] if not pedientes or pregunta['eleccion'] == 0)

def MostrarPregunta(pregunta):
    id = pregunta['id']
    numero = pregunta['numero']
    eleccion = pregunta['eleccion']
    
    correcta = pregunta['correcta'].index('x') + 1
    if eleccion != 0:
        print('Correcta : ', correcta, "Eleccion : ", eleccion)
    
    return Card(
        Fieldset(
            Legend(I(numero), H4(pregunta['pregunta']), pregunta['correcta'], Small(f"{id:03}")),
            *[MostrarRespuesta(numero, id, i+1, respuesta, eleccion, correcta) for i, respuesta in enumerate(pregunta['respuestas'])] )
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
        return Div( 
                Label(Input(type='radio', id=f"{numero}-{i}", name=id, value=i, aria_invalid=invalido, checked=actual),
                      Icono(imagen), _for=f"{numero}-{i}"),
                      cls='grilla')
    
    def MostrarOpcion():
        return Label(Input(type='radio', id=f"{numero}-{i}", name=id, value=i, aria_invalid=invalido, checked=actual), 
                     respuesta, _for=f"{numero}-{i}")

    actual = (eleccion == i)
    invalido = None
    if actual:
        invalido = 'false' if i == correcta else 'true'

    m = re.match(r'<(\d{3})>', respuesta)
    if m :
        return MostrarImagen(m.group(1))
    else:
        return MostrarOpcion()

preguntas = []

def aplicar_eleccion(datos):
    global preguntas
    
    for pregunta in preguntas['preguntas']:
        id = str(pregunta['id'])
        if id in datos:
            pregunta['eleccion'] = int(datos[id])
        elif pregunta['eleccion'] == 0: 
            pregunta['eleccion'] = random.randint(0, 4)
    return preguntas    

def simular_eleccion():
    global preguntas
    preguntas['preguntas'][1]['eleccion'] = 1 
    preguntas['preguntas'][2]['eleccion'] = 2 
    preguntas['preguntas'][3]['eleccion'] = 3

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
    print(examenes)
    return (
        Header(H1('Estadísticas')),
        Main(
            H2('Estadísticas'),
            Div(f"Hay {len(examenes)} preguntas"),
            Button("Volver al inicio" , hx_get="/"), 
        ),
    )

@rt('/examen/{examen}')
async def get(examen: str):    
    global preguntas
    preguntas = generar_examen(examen)

    simular_eleccion()

    return (
        Div(
            Header(
                H1(preguntas['examen'] + f'v {Version}'), 
                H6(preguntas['descripcion']),
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
async def post(datos: dict):
    global preguntas

    aplicar_eleccion(datos)

    print('Datos : ', datos)
    
    falta = sum(1 for pregunta in preguntas['preguntas'] if pregunta['eleccion'] == 0)
    if falta == 0:
        return RedirectResponse(url="/resultado")

    return (
        MostrarEstado(preguntas),
        Form(
            * MostrarPreguntas(preguntas, pedientes=True),
            EnviarRespuesta((f'Falta responder {falta} pregunta{'s' if falta else ''}'), parcial=True),
        )
    )    

@rt('/resultado')
async def post():
    global preguntas
    cantidad = len(preguntas['preguntas'])
    correctas = sum(1 for pregunta in preguntas['preguntas'] if pregunta['eleccion'] == pregunta['correcta'].index('x') + 1)
    return (
        Header(H1('Resultado')),
        Main(
            H2('Resultado'),
            P(f"Hay {correctas} respuestas correctas de {cantidad}"),
            Button("Volver al inicio" , hx_get="/", hx_target="#main",  hx_swap="innerHTML"), 
        ),
    )

serve()

