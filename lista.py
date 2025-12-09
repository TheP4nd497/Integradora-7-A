
import json
from os import getcwd, path
from bson import json_util


class Lista:
    def __init__(self):
        self.list = []

    def __str__(self):
        cadena = ""
        for x in self.list:
            cadena += str(x) + "\n"
        return cadena
    

    def agregar(self, objeto):
        self.list.append(objeto)

    def Borrar(self, objeto):
        self.list.remove(objeto)

    def Actualizar(self, objeto, objeto_nuevo):
        print(objeto)
      
        index = self.list.index(objeto)
        self.list[index] = objeto_nuevo

    def Obtener(self, nombre):
        for x in self.list:
            if x.nombre == nombre:
                return x
        return " no encontrado"

    def diccionario(self):
        return []

    def jsontransform(self, nombre_archivo, incub):
        with open(nombre_archivo, 'w') as archivo:
            archivo.write(json_util.dumps(self.diccionario(incub), indent=4))
    
