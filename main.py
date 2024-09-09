from fasthtml.common import *
from fasthtml.components import *
from examen import *

Version = '0.6.0'

app, rt = fast_app(pico=False, hdrs=(
    Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap"),
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
    
    horizontal = pregunta['respuestas'][0].startswith('<')
    
    return Card(
            Small(f"{id:03}", f"{pregunta['correcta']}"),
            Fieldset(
                Legend(I(numero), Span(pregunta['pregunta'])),
                *[MostrarRespuesta(numero, id, i+1, respuesta, eleccion, correcta) for i, respuesta in enumerate(pregunta['respuestas'])],
                cls = 'horizontal' if horizontal else 'vertical'
            )
        )


def TipoExamen(tipo):
    def IrExamen(examen):
        nombre, descripcion = examen['nombre'], examen['descripcion']
        return A(B(nombre), Span(descripcion), href=f"/examen/{nombre}")

    def TituloExamen(tipo):
        return Div(B(tipo['clase']), Span(tipo['descripcion']))

    return Article(
        TituloExamen(tipo),
        *[IrExamen(examen) for examen in tipo['examenes']],
        cls='menu_examen'
    )


def MostrarRespuesta(numero, id, i, respuesta, eleccion, correcta):
    def MostrarImagen(imagen):
        return  Label(
                    Input(type='radio', id=f"{numero}-{i}", name=id, value=i, aria_invalid=invalido, checked=actual),
                    Icono(imagen),
                    _for=f"{numero}-{i}",
                    cls= 'correcta' if i == correcta else None
                )
    
    def MostrarOpcion():
        return Label(
                    Input(type='radio', id=f"{numero}-{i}", name=id, value=i, aria_invalid=invalido, checked=actual), 
                    Span(respuesta), 
                    _for=f"{numero}-{i}",
                    cls= 'correcta' if i == correcta else None

                )

    actual = (eleccion == i)
    invalido = None
    if actual:
        invalido = 'false' if i == correcta else 'true'

    m = re.match(r'<(\d{3})>', respuesta)
    return MostrarImagen(m.group(1)) if m else MostrarOpcion()


def simular_eleccion(preguntas,cantidad=3):
    for pregunta in preguntas[cantidad:]:
        pregunta['eleccion'] = 1


def EnviarRespuesta(mensaje="",parcial=False):
    return Div(
        Span(mensaje, id='mensaje'),
        Button("Completar Exámen" if parcial else 'Evaluar Exámen', hx_post="/evaluar", hx_target="#pagina",  hx_swap="innerHTML"), 
        id='enviar'
    ) 


def Layout(titulo, *args, **kwargs):
    return Titled(titulo, H6(f"Versión {Version}"), *args, id='pagina', **kwargs)


@rt('/')
async def get(): 
    examenes = cargar_examenes()

    return  Layout( "Elegir Exámen",
                *[TipoExamen(examen) for examen in examenes],
                Footer("Dirección de Tránsito de Yerba Buena"),
                cls='menu'
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
            examen,
            MostrarEstado(preguntas),
            Form(
                * MostrarPreguntas(preguntas),
                EnviarRespuesta(), 
            ),
            cls='examen'
        )
    )
# <article>
#     <fieldset>
#         <legend>
#             <i>1</i>
#             <span>Según la Ordenanza Municipal Yerba Buena Nº 1.254, se considera falta o infracción grave al tránsito:</span>
#             <small>046 ..x</small>
#         </legend>
#         <label for="1-1" class="vertical">
#             <input type="radio" name="46" value="1" id="1-1">
#             Circular con remolque
#         </label>
#         <label for="1-2" class="vertical">
#             <input type="radio" name="46" value="2" id="1-2">
#             Circular con luz alta
#         </label>
#         <label for="1-3" class="vertical">
#             <input type="radio" name="46" value="3" id="1-3">
#             Circular con el vehículo con defensas delanteras y/o traseras, enganches sobresalientes
#         </label>
#     </fieldset>
# </article>

@rt('/evaluar')
async def post(session, datos: dict):
    preguntas = cargar_preguntas(session['preguntas'], datos)    
    
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
    preguntas = cargar_preguntas(session['preguntas'], session['respuestas'])

    cantidad  = len(preguntas)
    correctas = sum(1 for pregunta in preguntas if pregunta['eleccion'] == pregunta['correcta'].index('x') + 1)

    resultado = 'Aprobado' if correctas >= cantidad * 0.9 else 'Reprobado'

    return (
        Layout(
            Header(H1('Resultado')),
            Main(
                P(f"Hay {correctas} respuestas correctas de {cantidad}"),
                H2(f'El examen está: {resultado}'),
                Button("Volver al inicio" , hx_get="/", hx_target="#pagina",  hx_swap="innerHTML"), 
            ),
        )
    )


@rt('/estadisticas')
async def get():
    examenes = cargar_examenes()

    return (
        Layout("Estadísticas",
            Main(
                Div(f"Hay {len(examenes)} preguntas"),
                Button("Volver al inicio" , hx_get="/", hx_swap="innerHTML"), 
            ),
        )
    )

serve()

