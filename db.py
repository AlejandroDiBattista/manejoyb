from fasthtml.common import *
from fasthtml.components import *
from fastlite import Database
from dataclasses import dataclass
origen = 'sqlitecloud://cebvdaxghz.sqlite.cloud:8860/examenes?apikey=uad6nLSSJpp7sOlhKYi40mqFDlebjqKqdG2pE9rsCeM'
origen = 'examenes.db'
@dataclass
class Conductor:
    dni: str
    nombre: str
    apellido: str
    fecha: str
    categoria: str

db = Database(origen)
conductor = db.create(Conductor, pk="dni")  # pk es la clave primaria

# c = Conductor('12345678', 'Juan', 'Perez', '27/09/2024', 'B')
# conductor.insert(c)
print(conductor.get('12345678'))



