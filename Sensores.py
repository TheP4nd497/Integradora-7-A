
import re
from lista import Lista

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

    def __str__(self):
        if self.eslista:
            return super().__str__()
        else:
            return f"Tipo: {self.tipo} Numero: {self.numero} Valor: {self.valor}"
    
    def diccionario(self):
        if self.eslista:
            lista_dicc = []
            for sensor in self.list:
                lista_dicc.append({
                    "tipo": sensor.tipo,
                    "numero": sensor.numero,
                    "valor": sensor.valor
                })
            return lista_dicc
        else:
            return {
                "tipo": self.tipo,
                "numero": self.numero,
                "valor": self.valor
            }
    
    def leer_datos(self, linea):
        pattern = r"([A-Z]+)(\d+):(\d+)"
        matches = re.findall(pattern, linea)
        
        for tipo, numero, valor in matches:
            sensor = Sensor(tipo, numero, int(valor))
            self.agregar(sensor)
    

if __name__ == "__main__":
    line = "GAS01:346HUM01:47TEM01:23AGU01:110SON01:1"
    sensores = Sensor()
    sensores.leer_datos(line)
    print(sensores)
    sensores.jsontransform("sensores.json")