from fasthtml.common import *
from fasthtml.components import *
from examen import *

Version = '0.6.0'

app, rt = fast_app(pico=False, hdrs=(
    Link(rel='stylesheet', href='demo/estilo.css', type='text/css'),
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

def Layout(*args, **kwargs):
    return Div(*args, id='pagina', cls='container', **kwargs)

@rt('/')
async def get(): 
    examenes = cargar_examenes()

    return Layout(
            Header( H1(f'Elegir Exámen v {Version}')),
            Main( *[TipoExamen(examen) for examen in examenes]),
            Footer("Pie 2"),
        )

@rt('/examen/{examen}')
async def get(session, examen: str):    

    datos = generar_examen(examen)
    examen, descripcion, preguntas = datos['examen'], datos['descripcion'], datos['preguntas']
        
    simular_eleccion(preguntas)

    session['preguntas'] = [pregunta['id'] for pregunta in preguntas]
    print(f"Preguntas : {session['preguntas']}")

    return (
        Layout(
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
        )
    )


@rt('/evaluar')
async def post(session, datos: dict):

    ids = session['preguntas']

    preguntas = cargar_preguntas(ids, datos)    
    
    contestadas = [pregunta for pregunta in preguntas if pregunta['eleccion'] > 0]

    falta = len(preguntas) - len(contestadas)

    if falta == 0:
        session['respuestas'] = datos 
        return RedirectResponse(url="/resultado")

    return (
        Layout(
        MostrarEstado(preguntas),
        Form(
            * MostrarPreguntas(preguntas, pendientes=True),
            EnviarRespuesta((f'Falta responder {falta} pregunta{'s' if falta else ''}'), parcial=True),
        )
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
    return Layout(
        Header(H1('Resultado')),
        Main(
            P(f"Hay {correctas} respuestas correctas de {cantidad}"),
            H2(f'El examen está: {resultado}'),
            Button("Volver al inicio" , hx_get="/", hx_target="#main",  hx_swap="innerHTML"), 
        ),
    )


@rt('/estadisticas')
async def get():
    examenes = cargar_examenes()

    return Layout(
        Header(H1('Estadísticas')),
        Main(
            H2('Estadísticas'),
            Div(f"Hay {len(examenes)} preguntas"),
            Button("Volver al inicio" , hx_get="/"), 
        ),
    )

serve()

