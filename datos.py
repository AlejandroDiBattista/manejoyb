from fastlite import Database
from dataclasses import dataclass
from typing import List
import re
import unicodedata
from datetime import date

db = Database("clientes.db")

def remover_acentos(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

@dataclass
class Examen:
    cliente_dni: int
    fecha: str
    codigo: str
    bien: str
    mal: str
    aprobado: bool
    
    def guardar(self):
        db["examen"].insert(self.__dict__)
        return self
    
    @staticmethod
    def traer(dni: int):
        examenes = db["examen"].rows_where('cliente_dni = ?', (dni,))
        return [Examen(**examen) for examen in examenes]

@dataclass
class Cliente:
    dni: int
    nombre: str
    
    @property
    def examenes(self):
        if not hasattr(self, "_examenes"): self._examenes = Examen.traer(self.dni)
        return self._examenes
    
    @property
    def buscar(self) -> str:
        if not hasattr(self, "_buscar"): self._buscar = remover_acentos(f" {self.dni} {self.nombre} ")
        return self._buscar
    
    def registrar(self, *examenes):
        for examen in examenes:
            examen.cliente_dni = self.dni
            try:
                examen.guardar()
                self.examenes.append(examen)
            except Exception as e:
                print(e)
        return self 

    def registrarExamen(self, codigo, bien, mal, aprobado):
        if bien is List: bien = ",".join(bien)
        if mal is List: mal = ",".join(mal)
        fecha = date.today()

        examen = Examen(cliente_dni=self.dni, fecha=fecha, codigo=codigo, bien=bien, mal=mal, aprobado=aprobado) 
        return self.registrar(examen)
    
    def guardar(self):
        db["cliente"].upsert(self.__dict__, pk='dni')
        return self

    @classmethod
    def traer(cls, dni: int):
        cliente = db["cliente"].rows_where('dni = ?', (dni,))
        cliente = next(cliente, None)
        if cliente is None: return None
        return cls(**cliente)
    
    @classmethod
    def traerTodos(cls):
        return [cls(**cliente) for cliente in db["cliente"].rows]
    
    @classmethod
    def filtrar(cls, filtro:str) -> List:
        filtro = remover_acentos(filtro.strip().replace(" ", r"\s.*"))
        pattern = re.compile(filtro, re.IGNORECASE)
        return [cliente for cliente in Cliente.traerTodos() if pattern.search(cliente.buscar)]