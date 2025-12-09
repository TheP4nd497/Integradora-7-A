
from bson import ObjectId
from Sensores import Sensor
import serial
import json
from pymongo import InsertOne, MongoClient, errors
from datetime import datetime
import sys
import certifi
import http.client as httplib
import threading
import time

# --- 1. CONFIGURATION (Update these) ---
SERIAL_PORT = '/dev/ttyUSB0'  # Run 'python -m serial.tools.list_ports' to find this
BAUD_RATE = 9600              # Must match your Arduino's Serial.begin() rate
MONGO_CONNECTION_STRING = "mongodb+srv://jismaelzk09_db_user:3P4Vo0I0LbRWh4L2@utt.ljiugys.mongodb.net/?appName=UTT"
MONGO_DB_NAME = "Incubadora"
MONGO_COLLECTION_NAME = "Sensors"
pipeline = [
    {
        "$match": {
            "_id": ObjectId('69367bc04d39ad58c9bfdc25') # Creates the ObjectId
        }
    },
    {
        "$project": {
            "code": 0,
            "userId": 0,
            "Date_Regis": 0
        }
    }
]
# --- End of Configuration 

class IncubadoraWrapper:
   def __init__(self, dictionary):
       self.id = dictionary['_id']
       self.name = dictionary.get('name', 'Unknown')

class Conexxion():
    

 def __init__(self, interval_seconds = 5):
    self.interval = interval_seconds
    self.is_running = False
    self.timer = None
 
 
 def checkInternetHttplib(self,url="www.geeksforgeeks.org",
                            timeout=3):
    connection = httplib.HTTPConnection(url,timeout=timeout)
    try:
            # only header requested for fast operation
            connection.request("HEAD", "/")
            connection.close()  # connection closed
            return True
    except:
            return False

 def _run_task(self):
        """The private method that does the work and reschedules itself."""
        # 1. Check if we should still be running
        if not self.is_running:
            return  # Stop the loop
        sensores = Sensor()
        # 2. DO THE WORK
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            while True:
                line_bytes = ser.readline()
                if line_bytes:
                    # 1. Decode bytes into a string and strip whitespace
                    line = line_bytes.decode('utf-8').strip()
                    print(f"Received line: {line}")

                    # 2. Parse the line into Sensor objects
                    
                    sensores.leer_datos(line)
                    sensores.jsontransform("senso.json")
                    print(sensores)
                    break  # Exit after processing one line for this example
       

        if self.checkInternetHttplib():
            try:
                client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
                database = client.get_database(MONGO_DB_NAME)
                collec = database.get_collection(MONGO_COLLECTION_NAME)
                results = list(db['Incubadoras'].aggregate(pipeline))
                if results:
                    incub_data = results[0]  # Get the first (and only) match
                    
                  
                    documentos = sensores.diccionario(IncubadoraWrapper(incub_data))
                    if isinstance(documentos, list):
                        collec.insert_many(documentos)
                    else:
                        collec.insert_one(documentos)
                    client.close()

            except Exception as e:
            # Just print the error, do NOT raise it.
            # This allows the timer at the bottom to restart the task.
                print(f"⚠️  Database Error: {e}")
                print("Retrying in next cycle...")
        else:
            print("no inter")

        
        # 3. Create the *next* timer to run this method again
        self.timer = threading.Timer(self.interval, self._run_task)
        self.timer.start()

 def start(self):
        if self.is_running:
            print("Task is already running.")
            return

       
        self.is_running = True
        
        # Start the very first timer
        self.timer = threading.Timer(self.interval, self._run_task)
        self.timer.start()

 def stop(self):
        print("Stopping repeating task...")
        self.is_running = False
        # Cancel the *next* scheduled run, if one exists
        if self.timer:
            self.timer.cancel()
        print("Task stopped.")
# function to check internet connectivity
if __name__ == "__main__":
    conexion = Conexxion(interval_seconds=10)  # Check every 10 seconds
    try:
        conexion.start()
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        conexion.stop()
