import serial.tools.list_ports
def find_available_ports():
     """Prints a list of all available serial COM ports."""
    
     ports = serial.tools.list_ports.comports()
    
     if not ports:
         print("No COM ports found.")
         print("Please make sure your device is plugged in.")
         return

     print("Available COM ports:")
     for port, desc, hwid in sorted(ports):
         print(f"  {port}: {desc} [{hwid}]")

if __name__ == '__main__':
   find_available_ports()