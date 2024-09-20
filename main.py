import random
from fasthtml.common import *
from fasthtml.components import *
from examen import *

en_desarrollo = True 
Version = '0.8.2'

app, rt = fast_app(pico=False, hdrs=(
    Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap"),
    Link(rel='stylesheet', href='/demo/estilo.css', type='text/css'),
))

rt = app.route

# @app.middleware("before")
# def revisar_modo(request, session):
#     global en_desarrollo
    
#     if 'd' in request.query_params:
#         es_desarrollo = request.query_params['d'] != '0'
#         session['en_desarrollo'] = es_desarrollo
    
def Icono(nombre):
    return Img(src=f"{OrigenIconos}/{nombre}.png", cls="imagen")

def MostrarEstado(preguntas):
    cantidad = len(preguntas)
    respondidas = sum(1 for pregunta in preguntas if pregunta['eleccion'] > 0)
    return Span(f"Hay {respondidas} preguntas respondidas de {cantidad}", id="estado")

def MostrarPreguntas(preguntas, pendientes=False):
    return (MostrarPregunta(pregunta, pendientes) for pregunta in preguntas)

def MostrarPregunta(pregunta, pendientes=False):
    id = pregunta['id']
    numero = pregunta['numero']
    eleccion = pregunta['eleccion']
    
    correcta = pregunta['respuesta']
    if eleccion != 0:
        print('Correcta : ', correcta, "Eleccion : ", eleccion)
    
    direccion = "horizontal" if  pregunta['respuestas'][0].startswith('<') else "vertical"

    ocultar = 'oculto' if pendientes and eleccion != 0 else ''
    return Card(
            Small(f"{id:03}"), #, f"{pregunta['correcta']}"),
            Fieldset(
                Legend(I(numero), Span(pregunta['pregunta'])),
                *[MostrarRespuesta(numero, id, i+1, respuesta, eleccion, correcta) for i, respuesta in enumerate(pregunta['respuestas'])],
                cls = f"{direccion}"
            ),
            cls=ocultar)


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
    global en_desarrollo
    def MostrarImagen(imagen):
        return  Label(
                    Input(type='radio', id=f"{numero}-{i}", name=id, value=i, 
                          aria_invalid=invalido, checked=actual, 
                          hx_post="/actualizar_estado", 
                          hx_target="#mensaje", 
                          hx_include="closest form"),
                    Icono(imagen),
                    _for=f"{numero}-{i}",
                    cls= 'correcta' if i == correcta and en_desarrollo else None
                )
    
    def MostrarOpcion():
        return Label(
                    Input(type='radio', id=f"{numero}-{i}", name=id, value=i, 
                          aria_invalid=invalido, checked=actual, 
                          hx_post="/actualizar_estado", 
                          hx_target="#mensaje", 
                          hx_include="closest form"), 
                    Span(respuesta), 
                    _for=f"{numero}-{i}",
                    cls= 'correcta' if i == correcta  and en_desarrollo else None
                )

    actual = (eleccion == i)
    invalido = None
    if actual:
        invalido = 'false' if i == correcta else 'true'

    m = re.match(r'<(\d{3})>', respuesta)
    return MostrarImagen(m.group(1)) if m else MostrarOpcion()


def EnviarRespuesta(mensaje="",parcial=False):
    return Div(
        Span(mensaje, id='mensaje'),
        Button("Completar Exámen" if parcial else 'Evaluar Exámen', 
               hx_post="/evaluar", 
               hx_target="#pagina",  
               hx_swap="outerHTML",), 
        id='enviar'
    ) 

def Logo():
    return A(Img(src=f"{OrigenLogo}"), href="/")

def Pie():
    global es_desarrollo

    mensaje = "Desarrollador" if en_desarrollo else "Producción"
    return Footer(f"Dirección de Tránsito de Yerba Buena - Versión {Version} - Modo {mensaje}")

def Layout(titulo, *args, **kwargs):
    return Titled( Logo(), titulo,  *args, Pie(),id='pagina', **kwargs)

@rt('/')
def get(): 
    global en_desarrollo

    mensaje = "Desarrollador" if en_desarrollo else "Producción"
    examenes = cargar_examenes()
    return  Layout( "Elegir Exámen",
                *[TipoExamen(examen) for examen in examenes],
                A(f"🚩 Poner modo {mensaje}", href="/?d=1" if not en_desarrollo else "/?d=0", hx_post="/cambiar-modo", hx_target="#status", hx_swap="outerHTML"),
                cls='menu')

@rt('/examen/{examen}')
def get(session, examen: str, request: Request):    
    global en_desarrollo

    random.seed()
    semilla = random.randint(1000, 9999)

    datos = generar_examen(examen, semilla)
    print(datos['preguntas'][0])
    examen, descripcion, preguntas = datos['examen'], datos['descripcion'], datos['preguntas']
        
    session['preguntas'] = [pregunta['id'] for pregunta in preguntas]
    print(f"Preguntas : {session['preguntas']}")
    print(f"Desarrollador en GET examen/a1: {en_desarrollo}")
    return (
        Layout( 
            H1(f"{examen} - {datos['id']}"),
            Form(
                * MostrarPreguntas(preguntas),
                EnviarRespuesta(), 
            ),
            cls='examen'
        )
    )


@rt('/evaluar')
def post(session, datos: dict):
    preguntas = cargar_preguntas(session['preguntas'], datos)    
    
    contestadas = [pregunta for pregunta in preguntas if pregunta['eleccion'] > 0]

    falta = len(preguntas) - len(contestadas)

    if falta == 0:
        session['respuestas'] = datos 
        return RedirectResponse(url="/resultado")
    
    mensaje = f'Respondiste {len(contestadas)}, falta responder {falta} pregunta{'s' if falta else ''}'
    return (
        Layout(
            Form(
                * MostrarPreguntas(preguntas, pendientes=True),
                EnviarRespuesta(mensaje, parcial=True),
            ),
            cls='examen'
        )
    )    


@rt('/resultado')
def post(session):
    preguntas = cargar_preguntas(session['preguntas'], session['respuestas'])

    cantidad  = len(preguntas)
    correctas = sum(1 for pregunta in preguntas if pregunta['eleccion'] == pregunta['respuesta'])

    resultado = 'Aprobado' if correctas >= cantidad * 0.9 else 'Reprobado'
    bien, mal = resumir_examen(preguntas)
    return (
        Layout(
            Header(H1('Resultado')),
            Main(
                P(f"Hay {correctas} respuestas correctas de {cantidad}"),
                H2(f'El examen está: {resultado}'),
                Div(
                    H4(f'Hay {len(bien)} respuestas correctas'),
                    *[Span(id) for id in bien],
                    cls='resumen'),
                Div(
                    H4(f'Hay {len(mal)} respuestas incorrectas'),
                    *[Span(id) for id in mal],
                    cls='resumen'),
                Button("Volver al inicio" , hx_get="/", hx_target="#pagina",  hx_swap="innerHTML"), 
            ),
        )
    )

@rt('/actualizar_estado')
def post(session, datos: dict):
    preguntas = cargar_preguntas(session['preguntas'], datos)

    cantidad = len(preguntas)
    respondidas = sum(1 for pregunta in preguntas if pregunta['eleccion'] > 0)
    
    return Span(f"Hay {respondidas} preguntas respondidas de {cantidad}", id="estado")

@rt('/estadisticas')
def get():
    examenes = cargar_examenes()

    return (
        Layout("Estadísticas",
            Main(
                Div(f"Hay {len(examenes)} preguntas"),
                Button("Volver al inicio" , hx_get="/", hx_swap="innerHTML"), 
            ),
        )
    )

@rt("/cambiar-modo")
def post(req, session):
    global en_desarrollo

    en_desarrollo = session.get('en_desarrollo', False)
    session['en_desarrollo'] = not en_desarrollo
    
    print(f"Desarrollador : {en_desarrollo} ({req.query_params})")
    return P(id="status", content=f"El modo desarrollador está {'activado' if en_desarrollo else 'desactivado'}")


def info(n, base='pregunta'):
    if n == 0:
        return f'No hay {base}s'
    elif n == 1:
        return f'Hay 1 {base}'
    else:
        return f'Hay {n} {base}s'

serve()