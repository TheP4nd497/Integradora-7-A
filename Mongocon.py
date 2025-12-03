
from pymongo import MongoClient,InsertOne
from Sensores import sensores
# importing required module
import threading
import time
import http.client as httplib


class Conexxion():
    

 def __init__(self, interval_seconds):
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

        # 2. DO THE WORK
       

        if self.checkInternetHttplib():
            try:
                uri = "mongodb+srv://jismaelzk09_db_user:3P4Vo0I0LbRWh4L2@utt.ljiugys.mongodb.net/?appName=UTT"
                client = MongoClient(uri)
                database = client.get_database("sample_mflix")
                collec = database.get_collection("Ismael")
                client.close()

            except Exception as e:
                    raise Exception("Unable to find the document due to the following error: ", e)
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
