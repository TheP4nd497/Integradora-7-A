from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, DESCENDING
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId, Decimal128
import os
import hashlib
import jwt
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

# ==================== CONFIGURACIÓN ====================
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "Incubadora")
JWT_SECRET = os.getenv("JWT_SECRET", "secreto")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

app = FastAPI(
    title="Sistema de Gestión de Incubadoras",
    description="API con control de acceso basado en roles (Admin/Operador)",
    version="2.0.0"
)

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
    users_collection = db["User"]
    incubadoras_collection = db["Incubadoras"]
    sensors_collection = db["Sensors"]
    print("✅Conectado a MongoDB")
except Exception as e:
    print(f"Error al conectar con MongoDB: {e}")
    raise

security = HTTPBearer()

# ==================== MODELOS PYDANTIC ====================
class UserCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr
    contraseña: str = Field(..., min_length=6)
    telefono: Optional[str] = Field(None, pattern=r'^\+?[0-9]{10,15}$')
    rol: str = Field(default="operador", pattern="^(admin|operador)$")

class UserLogin(BaseModel):
    correo: EmailStr
    contraseña: str

class IncubadoraCreate(BaseModel):
    name: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    userId: str

class IncubadoraUpdate(BaseModel):
    name: Optional[str] = None
    userId: Optional[str] = None

class SensorAssign(BaseModel):
    incubadoraId: str

# ==================== FUNCIONES AUXILIARES ====================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str, rol: str) -> str:
    payload = {
        "user_id": user_id,
        "rol": rol,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def convertir_decimal128(valor):
    if isinstance(valor, Decimal128):
        return float(valor.to_decimal())
    return valor

def limpiar_documento(doc):
    if not doc:
        return None
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if "value" in doc:
        doc["value"] = convertir_decimal128(doc["value"])
    if "userId" in doc and isinstance(doc["userId"], ObjectId):
        doc["userId"] = str(doc["userId"])
    return doc

# ==================== DEPENDENCIAS DE AUTORIZACIÓN ====================
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    
    user = users_collection.find_one({"_id": ObjectId(payload["user_id"])})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return {
        "id": str(user["_id"]),
        "nombre": user.get("nombre"),
        "apellido": user.get("apellido"),
        "correo": user.get("correo"),
        "rol": user.get("rol", "operador")
    }

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["rol"] != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado: Se requiere rol de administrador"
        )
    return current_user

# ==================== ENDPOINTS DE AUTENTICACIÓN ====================
@app.post("/auth/registro", tags=["Autenticación"])
async def registrar_usuario(usuario: UserCreate):
    """Registra un nuevo usuario (solo admin puede crear otros admins)"""
    try:
        if users_collection.find_one({"correo": usuario.correo}):
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        
        nuevo_usuario = {
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "correo": usuario.correo,
            "contraseña": hash_password(usuario.contraseña),
            "telefono": usuario.telefono,
            "rol": usuario.rol,
            "Date_Regis": datetime.utcnow()
        }
        
        resultado = users_collection.insert_one(nuevo_usuario)
        
        return {
            "exito": True,
            "mensaje": "Usuario registrado exitosamente",
            "user_id": str(resultado.inserted_id),
            "rol": usuario.rol
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/auth/login", tags=["Autenticación"])
async def iniciar_sesion(credenciales: UserLogin):
    """Inicia sesión y retorna un token JWT"""
    try:
        usuario = users_collection.find_one({"correo": credenciales.correo})
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        password_hash = hash_password(credenciales.contraseña)
        if usuario.get("contraseña") != password_hash:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = create_token(str(usuario["_id"]), usuario.get("rol", "operador"))
        
        return {
            "exito": True,
            "token": token,
            "usuario": {
                "id": str(usuario["_id"]),
                "nombre": usuario.get("nombre"),
                "apellido": usuario.get("apellido"),
                "correo": usuario.get("correo"),
                "rol": usuario.get("rol", "operador")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ==================== ENDPOINTS DE USUARIOS ====================
@app.get("/usuarios", tags=["Usuarios"])
async def listar_usuarios(current_user: dict = Depends(require_admin)):
    """Lista todos los usuarios (solo admin)"""
    try:
        usuarios = list(users_collection.find())
        for user in usuarios:
            user["_id"] = str(user["_id"])
            user.pop("contraseña", None)
        
        return {"exito": True, "total": len(usuarios), "usuarios": usuarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usuarios/me", tags=["Usuarios"])
async def obtener_perfil(current_user: dict = Depends(get_current_user)):
    """Obtiene el perfil del usuario actual"""
    return {"exito": True, "usuario": current_user}

@app.delete("/usuarios/{user_id}", tags=["Usuarios"])
async def eliminar_usuario(user_id: str, current_user: dict = Depends(require_admin)):
    """Elimina un usuario (solo admin)"""
    try:
        resultado = users_collection.delete_one({"_id": ObjectId(user_id)})
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"exito": True, "mensaje": "Usuario eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DE INCUBADORAS ====================
@app.post("/incubadoras", tags=["Incubadoras"])
async def crear_incubadora(
    incubadora: IncubadoraCreate,
    current_user: dict = Depends(require_admin)
):
    """Crea una nueva incubadora (solo admin)"""
    try:
        if incubadoras_collection.find_one({"code": incubadora.code}):
            raise HTTPException(status_code=400, detail="El código ya existe")
        
        nueva = {
            "name": incubadora.name,
            "code": incubadora.code,
            "userId": ObjectId(incubadora.userId),
            "Date_Regis": datetime.utcnow()
        }
        
        resultado = incubadoras_collection.insert_one(nueva)
        return {
            "exito": True,
            "incubadora_id": str(resultado.inserted_id),
            "mensaje": "Incubadora creada"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/incubadoras", tags=["Incubadoras"])
async def listar_incubadoras(current_user: dict = Depends(get_current_user)):
    """
    Lista incubadoras:
    - Admin: ve todas
    - Operador: solo las asignadas
    """
    try:
        if current_user["rol"] == "admin":
            incubadoras = list(incubadoras_collection.find())
        else:
            incubadoras = list(incubadoras_collection.find({
                "userId": ObjectId(current_user["id"])
            }))
        
        for inc in incubadoras:
            limpiar_documento(inc)
        
        return {"exito": True, "total": len(incubadoras), "incubadoras": incubadoras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/incubadoras/{incubadora_id}", tags=["Incubadoras"])
async def actualizar_incubadora(
    incubadora_id: str,
    datos: IncubadoraUpdate,
    current_user: dict = Depends(require_admin)
):
    """Actualiza una incubadora (solo admin)"""
    try:
        update_data = {k: v for k, v in datos.dict().items() if v is not None}
        if "userId" in update_data:
            update_data["userId"] = ObjectId(update_data["userId"])
        
        resultado = incubadoras_collection.update_one(
            {"_id": ObjectId(incubadora_id)},
            {"$set": update_data}
        )
        
        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Incubadora no encontrada")
        
        return {"exito": True, "mensaje": "Incubadora actualizada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/incubadoras/{incubadora_id}", tags=["Incubadoras"])
async def eliminar_incubadora(
    incubadora_id: str,
    current_user: dict = Depends(require_admin)
):
    """Elimina una incubadora (solo admin)"""
    try:
        resultado = incubadoras_collection.delete_one({"_id": ObjectId(incubadora_id)})
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Incubadora no encontrada")
        
        return {"exito": True, "mensaje": "Incubadora eliminada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DE SENSORES ====================

@app.get("/sensores/todos", tags=["Sensores - Debug"])
async def obtener_todos_sensores(
    limite: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    [TEMPORAL - DEBUGGING] Obtiene todos los sensores sin filtro de incubadora
    Útil para verificar qué datos existen en la colección
    """
    try:
        sensores = list(sensors_collection.find().sort("Date_Regis", DESCENDING).limit(limite))
        
        for sensor in sensores:
            limpiar_documento(sensor)
        
        return {
            "exito": True,
            "total": len(sensores),
            "sensores": sensores,
            "nota": "Este endpoint muestra TODOS los sensores sin filtro. Solo para debugging."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensores/test/{incubadora_id}", tags=["Sensores - Debug"])
async def test_busqueda_sensores(
    incubadora_id: str,
    current_user: dict = Depends(get_current_user)
):
    
    try:
        resultados = {}
        
        # Prueba 1: incubadora.id como ObjectId
        count1 = sensors_collection.count_documents({
            "incubadora.id": ObjectId(incubadora_id)
        })
        resultados["filtro_incubadora.id_ObjectId"] = count1
        
        # Prueba 2: incubadora._id como ObjectId
        count2 = sensors_collection.count_documents({
            "incubadora._id": ObjectId(incubadora_id)
        })
        resultados["filtro_incubadora._id_ObjectId"] = count2
        
        # Prueba 3: incubadora_id como string
        count3 = sensors_collection.count_documents({
            "incubadora_id": incubadora_id
        })
        resultados["filtro_incubadora_id_string"] = count3
        
        # Prueba 4: incubadora_id como ObjectId
        count4 = sensors_collection.count_documents({
            "incubadora_id": ObjectId(incubadora_id)
        })
        resultados["filtro_incubadora_id_ObjectId"] = count4
        
        # Prueba 5: Total de sensores en la colección
        total = sensors_collection.count_documents({})
        resultados["total_sensores_en_coleccion"] = total
        
        # Obtener un ejemplo de sensor
        ejemplo = sensors_collection.find_one()
        if ejemplo:
            ejemplo = limpiar_documento(ejemplo)
            if "incubadora" in ejemplo and isinstance(ejemplo["incubadora"], dict):
                if "id" in ejemplo["incubadora"]:
                    ejemplo["incubadora"]["id"] = str(ejemplo["incubadora"]["id"])
        
        return {
            "exito": True,
            "incubadora_id_buscado": incubadora_id,
            "resultados_de_busqueda": resultados,
            "filtro_que_funciona": [k for k, v in resultados.items() if v > 0],
            "ejemplo_de_sensor": ejemplo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DE SENSORES ====================
@app.get("/sensores/incubadora/{incubadora_id}", tags=["Sensores"])
async def obtener_sensores_incubadora(
    incubadora_id: str,
    limite: int = Query(default=50, ge=1, le=200, description="Número de lecturas"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene sensores de una incubadora:
    - Admin: acceso total
    - Operador: solo incubadoras asignadas
    """
    try:
        incubadora = incubadoras_collection.find_one({"_id": ObjectId(incubadora_id)})
        if not incubadora:
            raise HTTPException(status_code=404, detail="Incubadora no encontrada")
        
        if current_user["rol"] != "admin":
            if str(incubadora.get("userId")) != current_user["id"]:
                raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Buscar por incubadora.id (tu estructura)
        sensores = list(sensors_collection.find({
            "incubadora.id": ObjectId(incubadora_id)
        }).sort("Date_Regis", DESCENDING).limit(limite))
        
        for sensor in sensores:
            limpiar_documento(sensor)
            if "incubadora" in sensor and isinstance(sensor["incubadora"], dict):
                if "id" in sensor["incubadora"]:
                    sensor["incubadora"]["id"] = str(sensor["incubadora"]["id"])
        
        return {"exito": True, "total": len(sensores), "sensores": sensores}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensores/historial/{incubadora_id}/{tipo_sensor}", tags=["Sensores"])
async def historial_sensor(
    incubadora_id: str,
    tipo_sensor: str,
    limite: int = Query(default=5, ge=1, le=100, description="Número de registros"),
    numero: Optional[str] = Query(default=None, description="Número específico del sensor (ej: 01, 02)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el historial de un sensor específico
    Tipos: GAS, HUM, TEMP, AGU, SON, LUZ
    Opcionalmente filtra por número de sensor (ej: TEMP02)
    """
    tipos_validos = ["GAS", "HUM", "TEMP", "AGU", "SON", "LUZ"]
    
    if tipo_sensor not in tipos_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de sensor inválido. Use: {', '.join(tipos_validos)}"
        )
    
    try:
        incubadora = incubadoras_collection.find_one({"_id": ObjectId(incubadora_id)})
        if not incubadora:
            raise HTTPException(status_code=404, detail="Incubadora no encontrada")
        
        if current_user["rol"] != "admin":
            if str(incubadora.get("userId")) != current_user["id"]:
                raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Construir filtro - buscar por incubadora.id (tu estructura)
        filtro = {
            "incubadora.id": ObjectId(incubadora_id),
            "Sensor_type": tipo_sensor
        }
        
        # Agregar filtro por número si se especifica
        if numero:
            filtro["numero"] = numero
        
        historial = list(sensors_collection.find(filtro).sort("Date_Regis", DESCENDING).limit(limite))
        
        for registro in historial:
            limpiar_documento(registro)
            if "incubadora" in registro and isinstance(registro["incubadora"], dict):
                if "id" in registro["incubadora"]:
                    registro["incubadora"]["id"] = str(registro["incubadora"]["id"])
        
        return {
            "exito": True,
            "incubadora_id": incubadora_id,
            "tipo_sensor": tipo_sensor,
            "numero_sensor": numero if numero else "todos",
            "total": len(historial),
            "historial": historial
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sensores/ultima-lectura/{incubadora_id}", tags=["Sensores"])
async def ultima_lectura_incubadora(
    incubadora_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene la última lectura de cada sensor de una incubadora (agrupado por tipo y número)"""
    try:
        incubadora = incubadoras_collection.find_one({"_id": ObjectId(incubadora_id)})
        if not incubadora:
            raise HTTPException(status_code=404, detail="Incubadora no encontrada")
        
        if current_user["rol"] != "admin":
            if str(incubadora.get("userId")) != current_user["id"]:
                raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Buscar por incubadora.id (tu estructura)
        todos_sensores = list(sensors_collection.find({
            "incubadora.id": ObjectId(incubadora_id)
        }).sort("Date_Regis", DESCENDING))
        
        # Agrupar por tipo y número de sensor
        lecturas_agrupadas = {}
        sensores_vistos = set()
        
        for sensor in todos_sensores:
            tipo = sensor.get("Sensor_type")
            numero = sensor.get("numero", "01")
            clave_unica = f"{tipo}_{numero}"
            
            if clave_unica not in sensores_vistos:
                sensores_vistos.add(clave_unica)
                
                if tipo not in lecturas_agrupadas:
                    lecturas_agrupadas[tipo] = {}
                
                sensor_limpio = limpiar_documento(sensor)
                if "incubadora" in sensor_limpio and isinstance(sensor_limpio["incubadora"], dict):
                    if "id" in sensor_limpio["incubadora"]:
                        sensor_limpio["incubadora"]["id"] = str(sensor_limpio["incubadora"]["id"])
                
                lecturas_agrupadas[tipo][numero] = sensor_limpio
        
        return {
            "exito": True,
            "total_sensores": len(sensores_vistos),
            "lecturas": lecturas_agrupadas
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HEALTH CHECK ====================
@app.get("/", tags=["Sistema"])
async def root():
    return {
        "mensaje": "API de Incubadoras v2.0",
        "estado": "activo",
        "roles": ["admin", "operador"]
    }

@app.get("/health", tags=["Sistema"])
async def health_check():
    try:
        client.server_info()
        return {
            "estado": "saludable",
            "mongodb": "conectado",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )