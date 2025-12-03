
import json
from os import getcwd, path
from bson import json_util
import bson


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

    def jsontransform(self, filename="data.json"):
        route = getcwd()
        with open(path.join(route, filename), "w") as archivo:
            bson.json_util.dump(self.diccionario(), archivo, indent=4)
    
