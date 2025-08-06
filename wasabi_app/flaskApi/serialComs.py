import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

ser = serial.Serial("/dev/ttyACM0", 115200, timeout = .5)

testFile = input("input test file name: ")
f = open(testFile)
for line in f:
    doneCount = 0
    line = line.strip()
    print(f"line:{line}")
    offset = 64 - len(line)
    if offset < 0:
        print("\n line exceeded buffer!\n")
    else:
        for i in range(0, offset):
            line += "$"
        print("\nsending line\n")
        ser.write(line.encode("ascii"))
    while True:
        try:
            readLine = ser.readline().decode("ascii").strip() # decode to string and remove whitespace
            print(readLine)
        finally:
            if "done" in readLine:
                doneCount += 1
                if doneCount == 2:
                    break


    time.sleep(.25)
f.close

