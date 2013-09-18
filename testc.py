#!/usr/bin/env python3
#Testing scanner communication

from scanner import Scanner
import fileinput
import sys, os
from prettyprint import pp_str
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
	
	if cmd.startswith('`'):		# A '`' requests a RAW output
		cmd = cmd[1:]
		cookit = Scanner.RAW
		print('Asking for RAW')
	elif cmd.startswith('~'):	# A '~' requests a DECODED output
		cmd = cmd[1:]
		cookit = Scanner.DECODED
		print('Asking for DECODED')
	else: 
		cookit = Scanner.COOKED	# Default is COOKED
		print('Asking for COOKED')
	
	# Convert lower->UPPER, Mixed->Mixed
	cmd = ','.join([a.upper() if a.islower() else a for a in cmd.split(',')])
	
	ans = S.cmd(cmd, cookit)
	
	if isinstance(ans, dict):
		print('The {cmd} command returned:'.format(cmd = cmd))
		print(pp_str(ans))
	else: print('The {cmd} command returned: {ans}'.
		format(cmd = cmd, ans = ans))
	
	# Check for exit programming mode and return to scanning
	if (cookit == Scanner.COOKED and ans == 'EPG,OK') or \
		(cookit == Scanner.RAW and ans == b'EPG,OK'):	# We just exited Program Mode, restart scanning
		print('Restarting scanning...')
		ans = S.cmd('JPM,SCN_MODE,0')
		if ans == 'JPM,OK': print('Scanning restarted.')
		else: print('Error ({ans}) restarting scanning.'.format(ans = ans))
