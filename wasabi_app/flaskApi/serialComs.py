    import serial
    import time
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1) 
    time.sleep(2) # Give time for serial connection to establish
    try:
        while True:
            command = input("input: ")
            ser.write((command + '\n').encode()) 
            
            response = ser.readline().decode().strip()
            if response:
                print(f"Pico says: {response}")
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        ser.close() # Close the serial port
