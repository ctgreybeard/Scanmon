#Testing scanner communication

from scanner import Scanner
import fileinput
import sys, os
print('Default encoding is', sys.getdefaultencoding())

S=Scanner()

print("we have a scanner: ", S)
print('Is it open?', S.isOpen());

print('Doing discovery ... OK?', S.discover())

print('The MDL command returns:', S.cmd('MDL'))
print('The VER command returns:', S.cmd('VER'))

while True:
	cmd = input('CMD=').upper()
	if len(cmd) == 0: break
	print('The {cmd} command returned: {ans}'.format(cmd = cmd, ans = S.cmd(cmd)))