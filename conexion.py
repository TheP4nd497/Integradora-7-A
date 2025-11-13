

import serial
import json
from pymongo import MongoClient
from datetime import datetime

#MongoDB connection details
client = MongoClient('mongodb+srv://jismaelzk09_db_user:3P4Vo0I0LbRWh4L2@utt.ljiugys.mongodb.net/?appName=UTT') # Replace with your MongoDB connection string
db = client.sample_mflix
collection = db.ismael

try:
    # Set timeout=1 so readline() doesn't block forever
    with serial.Serial('COM10', 9600, timeout=1) as ser:
        
        print(f"Listening on {ser.name}...")
        print("Press Ctrl+C to stop.")

        while True:
            line_bytes = ser.readline()
            
            if line_bytes:
                # Decode and strip
                line_string = line_bytes.decode('utf-8').rstrip()
                print(f"Received line: {line_string}")

                try:
                    # 1. Parse the JSON string into a Python dict
                    data_document = json.loads(line_string)
                    
                    # 2. Add the timestamp
                    data_document["timestamp"] = datetime.now()
                    
                    # 3. Insert the complete document into MongoDB
                    result = collection.insert_one(data_document)
                    print(f"  -> Inserted: {data_document}")

                except json.JSONDecodeError:
                    print(f"  -> Error: Received bad JSON. Skipping line: {line_string}")
                except Exception as e:
                    print(f"  -> Error inserting into MongoDB: {e}")

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