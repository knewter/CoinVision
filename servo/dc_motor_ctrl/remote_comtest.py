import serial
import sys, time

PORT = "/dev/ttyUSB0"

if len(sys.argv) > 1:
    PORT = sys.argv[1]

ser = serial.Serial(PORT, 9600, timeout=1)

print ser.portstr,
print ser.baudrate,
print ser.bytesize,
print ser.parity,
print ser.stopbits

while 1:
    print "Trying to connect..."
    time.sleep(1)
    ser.write("a")      # write a string
    s = ser.read()
    if len(s) > 0: break

#s = ser.read(100)       # read up to one hundred bytes
#connected so...
while 1:
    ser.write("f")
    s = ser.readline()
    print s
    if s == "A":
		print "com established..."
		ser.write ("a")
    #if len(s) < 1: break
    if ser.isOpen():
        print "Connected..."


                       # or as much is in the buffer
#print s
ser.close()             # close port
if not ser.isOpen():
    print "Not Connected..."
ser.close()             # close port

