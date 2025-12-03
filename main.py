"""FastAPI REST API para sistema de monitoreo de sensores
Raspberry Pi - Arduino - MongoDB"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, DESCENDING
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from bson import Decimal128
import os
import hashlib
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "Incubadora")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "Sensors")
MONGO_USERS_COLLECTION = os.getenv("MONGO_USERS_COLLECTION", "User")

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Monitoreo de Sensores",
    description="API para consultar datos de sensores Arduino",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde iOS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a MongoDB
try:
    client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    users_collection = db[MONGO_USERS_COLLECTION]
    print("Conectado a MongoDB correctamente")
except Exception as e:
    print(f"Error al conectar con MongoDB: {e}")
    raise

# --- MODELOS DE DATOS ---
class UserRegistro(BaseModel):
    Name: str = Field(..., min_length=2, max_length=100)
    LastName: str = Field(..., min_length=2, max_length=100)
    Mail: EmailStr
    Contraseña: str = Field(..., min_length=6)
    PhoneNumber: Optional[str] = Field(None, pattern=r'^\+?[0-9]{10,15}$')

class UserLogin(BaseModel):
    Mail: EmailStr
    Contraseña: str

class SensorReading(BaseModel):
    GAS: Optional[int] = None
    HUM: Optional[int] = None
    TEMP: Optional[int] = None
    AGU: Optional[int] = None
    SON: Optional[int] = None
    Date_Regis: datetime

class SensorStats(BaseModel):
    promedio: float
    minimo: float
    maximo: float
    total_lecturas: int

# --- FUNCIONES AUXILIARES ---
def hash_password(password: str) -> str:
    """Hashea la contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def convertir_decimal128(valor):
    """Convierte Decimal128 de MongoDB a float"""
    if isinstance(valor, Decimal128):
        return float(valor.to_decimal())
    return valor

def limpiar_documento(doc):
    """Limpia un documento de MongoDB convirtiendo Decimal128 y ObjectId"""
    if not doc:
        return None
    
    # Convertir _id a string
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    
    # Convertir value si es Decimal128
    if "value" in doc:
        doc["value"] = convertir_decimal128(doc["value"])
    
    return doc

# --- ENDPOINTS DE AUTENTICACIÓN ---
@app.post("/User/Registro")
async def registrar_usuario(usuario: UserRegistro):
    """Registra un nuevo usuario en la base de datos"""
    try:
        # Verificar si el email ya existe
        usuario_existente = users_collection.find_one({"Mail": usuario.Mail})
        if usuario_existente:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Crear documento del usuario
        nuevo_usuario = {
            "Name": usuario.Name,
            "LastName": usuario.LastName,
            "Mail": usuario.Mail,
            "Contraseña": hash_password(usuario.Contraseña),
            "PhoneNumber": usuario.PhoneNumber
        }
        
        # Insertar en MongoDB
        resultado = users_collection.insert_one(nuevo_usuario)
        
        return {
            "exito": True,
            "mensaje": "Usuario registrado exitosamente",
            "user_id": str(resultado.inserted_id),
            "Mail": usuario.Mail
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")

@app.post("/User/IniciarSesion")
async def iniciar_sesion(credenciales: UserLogin):
    """Inicia sesión con email y contraseña"""
    try:
        # Buscar usuario por email
        usuario = users_collection.find_one({"Mail": credenciales.Mail})
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Verificar contraseña
        password_hash = hash_password(credenciales.Contraseña)
        if usuario.get("Contraseña") != password_hash:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        return {
            "exito": True,
            "mensaje": "Inicio de sesión exitoso",
            "usuario": {
                "id": str(usuario["_id"]),
                "Name": usuario.get("Name"),
                "LastName": usuario.get("LastName"),
                "Mail": usuario.get("Mail"),
                "PhoneNumber": usuario.get("PhoneNumber")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar sesión: {str(e)}")

# --- ENDPOINTS DE SENSORES ---
@app.get("/")
async def root():
    """pa ver si la api jala"""
    return {
        "mensaje": "API de Sensores - Sistema de Monitoreo",
        "version": "1.0.0",
        "estado": "activo"
    }

@app.get("/health")
async def health_check():
    """pa ver si la api y el mongo jalan"""
    try:
        client.server_info()
        total_docs = collection.count_documents({})
        return {
            "estado": "saludable",
            "mongodb": "conectado",
            "total_registros": total_docs,
            "Date_Regis": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error de conexión: {str(e)}")

@app.get("/lecturas/ultima")
async def obtener_ultima_lectura():
    """Obtiene la última lectura de CADA tipo de sensor"""
    try:
        sensores = ["GAS", "HUM", "TEMP", "AGU", "SON"]
        lecturas_por_sensor = {}
        
        for sensor in sensores:
            # Buscar la última lectura de este sensor específico
            lectura = collection.find_one(
                {"Sensor_type": sensor},
                sort=[("Date_Regis", DESCENDING)]
            )
            
            if lectura:
                lecturas_por_sensor[sensor] = {
                    "_id": str(lectura.get("_id")),
                    "value": convertir_decimal128(lectura.get("value")),
                    "unit": lectura.get("unit"),
                    "Sensor_type": lectura.get("Sensor_type"),
                    "Date_Regis": lectura.get("Date_Regis")
                }
        
        if not lecturas_por_sensor:
            return {
                "exito": False, 
                "mensaje": "No hay lecturas registradas"
            }
        
        return {
            "exito": True,
            "total_sensores": len(lecturas_por_sensor),
            "lecturas": lecturas_por_sensor
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lecturas/recientes")
async def obtener_lecturas_recientes(
    limite: int = Query(default=10, ge=1, le=100, description="Número de lecturas a obtener")
):
    """Obtiene las últimas N lecturas"""
    try:
        lecturas = list(collection.find().sort("Date_Regis", DESCENDING).limit(limite))
        
        # Limpiar cada lectura
        for lectura in lecturas:
            limpiar_documento(lectura)
        
        return {
            "exito": True,
            "total": len(lecturas),
            "datos": lecturas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener lecturas: {str(e)}")

@app.get("/lecturas/rango")
async def obtener_lecturas_por_rango(
    horas: int = Query(default=24, ge=1, description="Últimas N horas")
):
    """Obtiene lecturas de las últimas N horas"""
    try:
        tiempo_inicio = datetime.now() - timedelta(hours=horas)
        
        lecturas = list(collection.find(
            {"Date_Regis": {"$gte": tiempo_inicio}}
        ).sort("Date_Regis", DESCENDING))
        
        for lectura in lecturas:
            limpiar_documento(lectura)
        
        return {
            "exito": True,
            "periodo": f"últimas {horas} horas",
            "desde": tiempo_inicio,
            "hasta": datetime.now(),
            "total": len(lecturas),
            "datos": lecturas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener lecturas: {str(e)}")

@app.get("/sensor/{tipo_sensor}")
async def obtener_datos_sensor_especifico(
    tipo_sensor: str,
    limite: int = Query(default=20, ge=1, le=100)
):
    """
    Obtiene datos de un sensor específico
    Sensores disponibles: GAS, HUMEDAD, TEM, NIVEL_AGUA, SONIDO, LUZ
    """
    sensores_validos = ["GAS", "HUM", "TEMP", "AGU", "SON", "LUZ"]
    
    if tipo_sensor not in sensores_validos:
        raise HTTPException(
            status_code=400, 
            detail=f"Sensor no válido. Use: {', '.join(sensores_validos)}"
        )
    
    try:
        # Buscar documentos que tengan el sensor_type específico
        lecturas = list(collection.find(
            {"Sensor_type": tipo_sensor}
        ).sort("Date_Regis", DESCENDING).limit(limite))
        
        # Extraer los datos del sensor
        datos_sensor = []
        for lectura in lecturas:
            datos_sensor.append({
                "_id": str(lectura.get("_id")),
                "value": convertir_decimal128(lectura.get("value")),
                "unit": lectura.get("unit"),
                "Sensor_type": lectura.get("Sensor_type"),
                "Date_Regis": lectura.get("Date_Regis")
            })
        
        return {
            "exito": True,
            "sensor": tipo_sensor,
            "total": len(datos_sensor),
            "datos": datos_sensor
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/alertas")
async def verificar_alertas():
    """
    Verifica si hay condiciones de alerta en las últimas lecturas de cada sensor
    """
    UMBRALES = {
        "GAS": {"max": 400, "mensaje": "Nivel de gas peligroso"},
        "TEM": {"max": 35, "min": 15, "mensaje": "Temperatura fuera de rango"},
        "HUM": {"max": 80, "min": 30, "mensaje": "Humedad fuera de rango"},
        "AGU": {"max": 800, "mensaje": "Nivel de agua alto"}
    }
    
    try:
        alertas = []
        
        # Verificar cada tipo de sensor
        for sensor_type, limites in UMBRALES.items():
            # Obtener la última lectura de este sensor
            lectura = collection.find(
                {"Sensor_type": sensor_type}
            ).sort("Date_Regis", DESCENDING).limit(1)
            
            lecturas_list = list(lectura)
            if lecturas_list and len(lecturas_list) > 0:
                lectura_doc = lecturas_list[0]
                if "value" in lectura_doc:
                    valor = convertir_decimal128(lectura_doc.get("value"))
                    
                    # CORRECCIÓN: Asegurar que valor sea numérico
                    try:
                        valor = float(valor)
                    except (ValueError, TypeError):
                        pass
                        continue
                    
                    if "max" in limites and valor > limites["max"]:
                        alertas.append({
                            "sensor": sensor_type,
                            "tipo": "CRÍTICO",
                            "valor_actual": valor,
                            "umbral": limites["max"],
                            "mensaje": limites["mensaje"],
                            "Date_Regis": lectura_doc.get("Date_Regis")
                        })
                    elif "min" in limites and valor < limites["min"]:
                        alertas.append({
                            "sensor": sensor_type,
                            "tipo": "ADVERTENCIA",
                            "valor_actual": valor,
                            "umbral": limites["min"],
                            "mensaje": limites["mensaje"],
                            "Date_Regis": lectura_doc.get("Date_Regis")
                        })
        
        return {
            "exito": True,
            "hay_alertas": len(alertas) > 0,
            "total_alertas": len(alertas),
            "alertas": alertas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# --- MANEJO DE ERRORES ---
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "exito": False,
            "error": "Recurso no encontrado",
            "detalle": str(exc.detail) if hasattr(exc, 'detail') else "Not found"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "exito": False,
            "error": "Error interno del servidor",
            "detalle": str(exc)
        }
    )

# --- STARTUP/SHUTDOWN ---
@app.on_event("startup")
async def startup_event():
    print("🚀 API iniciada correctamente")
    print(f"Base de datos: {MONGO_DB_NAME}")
    print(f"Colección: {MONGO_COLLECTION_NAME}")
    print(f"Usuarios Colección: {MONGO_USERS_COLLECTION}")

@app.on_event("shutdown")
async def shutdown_event():
    client.close()
    print("Conexión a MongoDB cerrada")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )