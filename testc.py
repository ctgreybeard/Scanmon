#Testing scanner communication

from scanner import Scanner
import fileinput
import sys, os
print('Default encoding is', sys.getdefaultencoding())

# We need to close stdout and re-open it to allow the Latin-1 characters
# that the scanner returns
print('Closing stdout')
sys.stdout.close()
sys.stdout = os.fdopen(1, 'w', encoding='ISO-8859-1')
print('New stdout open')

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