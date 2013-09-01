#!/sw/bin/python3

import serial
import io

scanner = serial.Serial()
scanner.baudrate = 19200
scanner.timeout = 0.2

scanner.port = '/dev/cu.PL2303-003012FD'
scanner.open()

sio = io.TextIOWrapper(scanner, newline=None, line_buffering=False)


print("Scanner=", str(scanner))
print("SIO=", str(sio))

sio.write("MDL\r")
ans = sio.readline()

print('ANS=', repr(ans))

# Can we change the timeout midstream?
scanner.timeout = 5

sio.write("VER\r")
ans = sio.readline()

print('ANS=', repr(ans))
