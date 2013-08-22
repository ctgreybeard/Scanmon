#!/sw/bin/python3

import serial
import io

scanner = serial.Serial()
scanner.baudrate = 19200
scanner.timeout = 1

sio = io.TextIOWrapper(io.BufferedRWPair(scanner, scanner), newline="\r", line_buffering=True)

scanner.port = '/dev/cu.PL2303-000013FA'
scanner.open()

print("Scanner=", scanner)
print("SIO=", sio)

sio.write("MDL\r")
ans = sio.readline()

print('ANS=', ans)

sio.write("VER\r")
ans = sio.readline()

print('ANS=', ans)
