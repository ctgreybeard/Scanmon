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
	cmd = input('CMD=')
	if len(cmd) == 0: break
	cmd = ','.join([a.upper() if a.islower() else a for a in cmd.split(',')])
	ans = S.cmd(cmd, Scanner.RAW)
	print('The {cmd} command returned: {ans}'.
		format(cmd = cmd, ans = ans))
	if ans == b'EPG,OK':	# We just exited Program Mode, restart scanning
		print('Restarting scanning...')
		ans = S.cmd('JPM,SCN_MODE,0')
		if ans == 'JPM,OK': print('Scanning restarted.')
		else: print('Error ({ans}) restarting scanning.'.format(ans = ans))
