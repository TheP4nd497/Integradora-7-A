import serial
import json
from pymongo import MongoClient

# MongoDB connection details
# client = MongoClient('mongodb+srv://jismaelzk09_db_user:3P4Vo0I0LbRWh4L2@utt.ljiugys.mongodb.net/?appName=UTT') # Replace with your MongoDB connection string
# db = client.arduino_data
# collection = db.sensor_readings

# Serial port details
ser = serial.Serial(port='COM10', baudrate=9600) # Replace 'COM3' with your Arduino's serial port


while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:
            # Assuming Arduino sends JSON string
            data = json.loads(line)
            #collection.insert_one(data)
            print(f"Data inserted: {data}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        break
    except json.JSONDecodeError as e:   
        print(f"JSON decode error: {e}, received: {line}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")