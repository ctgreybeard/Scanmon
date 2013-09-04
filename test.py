#!/sw/bin/python3

import serial
import io

scanner = serial.Serial()
scanner.baudrate = 19200
scanner.timeout = 0.2

scanner.port = '/dev/cu.PL2303-003012FD'
scanner.open()

sio = io.TextIOWrapper(scanner, newline=None, line_buffering=False)

def doit(cmd):
	sio.write(cmd + "\r")
	sio.flush() # To be sure ...
	ans = sio.readline()
	print('ANS=', repr(ans))
	return(ans)


print("Scanner=", str(scanner))
print("SIO=", str(sio))

doit("MDL")

# Can we change the timeout midstream?
scanner.timeout = 3

doit("VER")

# How about the baud rate?

scanner.baudrate = 300

doit('MDL')

scanner.baudrate = 19200

doit('MDL')
