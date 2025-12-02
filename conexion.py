

import serial
import json
from pymongo import InsertOne, MongoClient
from datetime import datetime

#MongoDB connection details
client = MongoClient('mongodb+srv://jismaelzk09_db_user:3P4Vo0I0LbRWh4L2@utt.ljiugys.mongodb.net/?appName=UTT') # Replace with your MongoDB connection string
db = client.sample_mflix
collection = db.ismael

try:
        requesting = []

        with open(r"senso.json") as f:
            for jsonObj in f:
                myDict = json.loads(jsonObj)
                requesting.append(InsertOne(myDict))

        result = collection.bulk_write(requesting)
except serial.SerialException as e:
    print(f"Serial Error: {e}")
except KeyboardInterrupt:
    print("\nProgram stopped.")
finally:
    # Make sure to close the MongoDB client connection
    client.close()
    print("MongoDB connection closed.")

#informacion enviada linea por linea 
#estandarizacion de datos
#la rasp tiene que preguntar por la configuracion 
#la rasp es quien tiene que pedir la informacion al arduino en vez de mandarlo constante mente 