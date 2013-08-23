#!/sw/bin/python3

import serial
import io

debug=1

def scannercmd(sio, cmd):
	"""scannercmd: write one line command and return response
	"""

	if debug:
		print("Writing command:", cmd)
	sio.write(cmd + "\r")
	return sio.readline()

scanner = serial.Serial()
scanner.baudrate = 19200
scanner.timeout = 10

sio = io.TextIOWrapper(io.BufferedRWPair(scanner, scanner), newline='\r', line_buffering=True)

scanner.port = '/dev/cu.PL2303-000013FA'
scanner.open()

print("Scanner=", scanner)
print("SIO=", sio)

ans = scannercmd(sio, "MDL")

print('ANS=', ans)

ans = scannercmd(sio, "VER")

print('ANS=', ans)
