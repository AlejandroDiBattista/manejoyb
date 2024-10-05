import random
import json
from fasthtml.common import *
from fasthtml.components import *
import traceback

# from examen import *

from fastlite import Database
from dataclasses import dataclass
from datos import Cliente, Examen

app, rt = fast_app(pico=False, hdrs=(
    Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap"),
    Link(rel='stylesheet', href='/demo/estilo.css', type='text/css'),
))


def MostrarCliente(cliente):
    return Article(
        H3(cliente.nombre),
        P(f"DNI: {cliente.dni}"),
        A(href=f"/cliente/{cliente.dni}", cls="btn")("Ver Detalle")
    )

def MostrarExamen(examen):
    return Div(
        H3(examen.codigo),
        P(f"Fecha: {examen.fecha}"),
        P(f"Bien: {examen.bien}"),
        P(f"Mal: {examen.mal}"),
        P(f"Aprobado: {'Sí' if examen.aprobado else 'No'}"),
        A(href=f"/cliente/{examen.cliente_dni}", cls="btn")("Volver")
    )

# Página principal con filtro
@rt("/")
def get(req):
    filtro = req.query_params.get("filtro", "")
    clientes = Cliente.filtrar(filtro)

    return Titled("Lista de Clientes", 
                  Form(Input(placeholder="Buscar clientes...", name="filtro", value=filtro, cls="search"),
                       Button("Buscar", type="submit", cls="btn-lupa")),
                  Button("Nuevo Exámen", type="button", hx_get="/nuevo-examen", cls="btn"),
                  Button("Nuevo Exámen", type="button", onclick="window.location.href='/nuevo-examen'", cls="btn"),

                  Div(*[MostrarCliente(cliente) for cliente in clientes]),
                 )

# Detalle del cliente
@rt("/cliente/{dni:int}")
def get(req, dni):
    cliente = Cliente.traer(dni)

    return Titled(f"Detalle Cliente {cliente.nombre}", 
                  P(f"DNI: {cliente.dni}"),
                  P(f"Nombre: {cliente.nombre}"),
                  Ul(*[Li(f"Fecha: {ex.fecha}, Código: {ex.codigo}, Aprobado: {'Sí' if ex.aprobado else 'No'}") for ex in examenes_ordenados]),
                  A(href=f"/nuevo-examen?dni={dni}", cls="btn")("Tomar Nuevo Examen"),
                 )

@rt("/nuevo-examen")
def get(req):
    # dni = req.query_params.get("dni", None)
    cliente = Cliente.traer(12345678)
    tipo_examen = ["Examen 1", "Examen 2", "Examen 3"]
    return Titled("Editar Cliente",
                  Form(
                           Label("DNI:",
                           Input(name="dni", type="text", value=cliente.dni, cls="form-input")
                        ),
                           Label("Nombre:",
                           Input(name="nombre", type="text", value=cliente.nombre, required=True, cls="form-input")
                       ),
                           Label("Tipo de Examen:",
                           Select(*[Option(value=tipo, selected=0)(tipo) for tipo in tipo_examen], name="codigo", cls="form-select")
                       ),
                       Div(
                           Button("Cancelar", type="button", hx_get="/", cls="btn")(),
                           Button("Guardar", type="submit", cls="btn btn-primary", hx_post="/editar-cliente", hx_swap="outerHTML")
                       ),
                       method="post", cls="formulario"
                  )
             )
    
@rt("/editar-cliente")
async def post(req):
    # try:
    print('-----------  En POST de editar cliente -----------')
    form_data = await req.form()  # Aquí utilizamos await para obtener los datos del formulario
    nombre = form_data["nombre"]
    dni    = form_data["dni"] 
    print(f'En POST de editar cliente : {dni=} {nombre=}')
    print("--------------------------------------------------")
    cliente = Cliente.traer(dni)
    if not cliente:
        cliente = Cliente(dni=dni, nombre=nombre)
    else:
        cliente.nombre = nombre
    cliente.guardar()
    # except Exception as e:
    #     traceback.print_exc()

    return RedirectResponse("/", status_code=303)

@rt("/nuevo-examen", methods=["POST"])
def post(req):
    dni = int(req.form_data["dni"])
    nombre = req.form_data["nombre"]
    codigo = req.form_data["codigo"]
    
    cliente = Cliente.traer(dni)
    if not cliente:
        Cliente(dni=dni, nombre=nombre).guardar()
    
    # Simulación del examen
    exito = True  # Lógica del examen aquí
    bien = "1,2,3"
    mal = "4,5"
    
    # examenes.insert(Examen(cliente_dni=dni, fecha="2024-01-01", codigo=codigo, bien=bien, mal=mal, aprobado=exito))
    
    return RedirectResponse("/", status_code=303)

serve()
