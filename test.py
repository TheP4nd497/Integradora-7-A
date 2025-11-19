#!/usr/bin/env python3
"""
Reads JSON data from a serial port and inserts it into a MongoDB collection.
Designed to run on a Raspberry Pi (Linux).
"""

import serial
import json
from pymongo import MongoClient, errors
from datetime import datetime
import sys

# --- 1. CONFIGURATION (Update these) ---
SERIAL_PORT = '/dev/ttyUSB0'  # Run 'python -m serial.tools.list_ports' to find this
BAUD_RATE = 9600              # Must match your Arduino's Serial.begin() rate
MONGO_CONNECTION_STRING = "mongodb://localhost:27017/"
MONGO_DB_NAME = "my_sensor_db"
MONGO_COLLECTION_NAME = "sensor_readings"
# --- End of Configuration ---

def main():
    """
    Main function to connect, read, and insert data.
    """
    
    # --- 2. CONNECT TO MONGODB ---
    try:
        print(f"Connecting to MongoDB at {MONGO_CONNECTION_STRING}...")
        client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        # Force a connection check
        client.server_info()
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        print("Successfully connected to MongoDB.")
        print(f"Database: '{MONGO_DB_NAME}', Collection: '{MONGO_COLLECTION_NAME}'")
    except errors.ServerSelectionTimeoutError as err:
        print(f"Error: Could not connect to MongoDB.")
        print("Is the 'mongod' service running?")
        print(err)
        sys.exit(1) # Exit if we can't connect to the DB
    
    # --- 3. OPEN SERIAL PORT AND LISTEN ---
    try:
        print(f"Attempting to open serial port {SERIAL_PORT}...")
        
        # The 'with' statement automatically closes the port when done
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Successfully opened port. Listening on {ser.name}")
            print("Press Ctrl+C to stop.")
            
            while True:
                # Read one line of bytes
                line_bytes = ser.readline()
                
                if line_bytes:
                    # 1. Decode bytes into a string and strip whitespace
                    try:
                        line_string = line_bytes.decode('utf-8').rstrip()
                    except UnicodeDecodeError:
                        print(f"  -> Decode Error: Skipping malformed line: {line_bytes}")
                        continue # Skip this loop iteration

                    print(f"\nReceived line: {line_string}")
                    
                    # 2. Parse the JSON string into a Python dictionary
                    try:
                        data_document = json.loads(line_string)
                        
                        # Check if it's a dictionary (valid JSON object)
                        if not isinstance(data_document, dict):
                            raise TypeError("JSON was not an object (dict)")

                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"  -> JSON Error: Skipping line. {e}")
                        print(f"     Make sure Arduino is sending valid JSON, e.g.:")
                        print(f"     {{\"sensor\": \"temp\", \"value\": 25.5}}")
                        continue # Skip to the next line

                    # 3. Add the timestamp
                    data_document["timestamp"] = datetime.now()
                    
                    # 4. Insert the document into MongoDB
                    try:
                        result = collection.insert_one(data_document)
                        print(f"  -> Inserted to MongoDB. Doc: {data_document}")
                    except Exception as e:
                        print(f"  -> Mongo Insert Error: {e}")

    except serial.SerialException as e:
        print(f"FATAL: Serial Error: {e}")
        if "Permission denied" in str(e):
            print("\n>>> PERMISSION DENIED <<<")
            print("You must add your user to the 'dialout' group:")
            print(f"1. Run: sudo usermod -a -G dialout $USER")
            print("2. Then, you MUST REBOOT your Raspberry Pi.")
        
    except KeyboardInterrupt:
        print("\nProgram stopped by user (Ctrl+C).")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    finally:
        # 4. CLEANUP
        client.close()
        print("MongoDB connection closed.")
        print("Exiting.")

if __name__ == "__main__":
    main()