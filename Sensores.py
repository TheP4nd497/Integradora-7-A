
import re
from bson.objectid import ObjectId


from lista import Lista
import json
from datetime import datetime

class Sensor(Lista):
    def __init__(self,tipo=None,numero=None,valor=None):
        if tipo is None and numero is None and valor is None:
            super().__init__()
            self.eslista = True
        else:
            self.eslista = False
            self.tipo = tipo
            self.numero = numero
            self.valor = valor
            self.unit = self.defnir_unidad(tipo)
    
    def __iter__(self):
        if self.eslista:
            for sensor in self.list:
                yield sensor
        else:
            yield self

    def __str__(self):
        if self.eslista:
            return super().__str__()
        else:
            return f"Tipo: {self.tipo} Numero: {self.numero} Valor: {self.valor} Unidad: {self.unit}"
        
    def defnir_unidad(self,tipo):
        unidades = {
            "GAS": "PPM",
            "HUM": "%",
            "TEMP": "°C",
            "AGU": "PPM",
            "SON": "cm",
            "LUZ": "lx"
        }
        return unidades.get(tipo, "Unknown")
    
    def diccionario(self,incub):
        if self.eslista:
            return [sensor.diccionario() for sensor in self.list]
        else:
            return {
                "Date_Regis": datetime.now(),
                "Sensor_type": self.tipo,
                "numero": self.numero,
                "value": self.valor,
                "unit": self.unit,
                "icubadora": {"id": ObjectId(incub.id), "name": incub.name}
            }
    
    def leer_datos(self, linea):
        pattern = r"([A-Z]+)(\d+):(\d+)"
        matches = re.findall(pattern, linea)
        
        for tipo, numero, valor in matches:
            sensor = Sensor(tipo, numero, int(valor))
            self.agregar(sensor)
    

if __name__ == "__main__":
    line = "GAS01:346HUM01:47TEMP01:23AGU01:110LUZ01:1SON01:1"
    sensores = Sensor()
    sensores.leer_datos(line)
    print(sensores)
    sensores.jsontransform("senso.json")
    print(sensores.diccionario())