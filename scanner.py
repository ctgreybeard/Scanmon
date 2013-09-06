# -*- coding: ISO-8859-1 -*-
# Uniden Scanner utilities and programming access
"""
Uniden Scanner utilities and programming access

Module and class to communicate with a Uniden DMA scanner (BCD996XT, BCD396XT, etc.)
"""

import io
from serial import Serial
from glob import glob

# A useful function
def _lineno(lineidx): return b'123456789'[lineidx:lineidx+1]
	
class Decode:
	'''
	Decode cmd results
	'''
	
	ISERRORKEY = 'iserror'
	ERRORCODEKEY = 'errorcode'
	
	# Some error codes and their descriptions
	NO_ERROR = 0
	ERR_PREMATCH = 1
	ERR_NOKEYWORDS = 2
	ERR_NOMATCH = 3
	ERR_RESPONSE = 4
	ERR_UNKNOWN_RESPONSE = 5
	
	ERRORMSG = {
		ERR_PREMATCH: 'Error in prematch',
		ERR_NOKEYWORDS: 'No keywords',
		ERR_NOMATCH: 'No match',
		ERR_RESPONSE: 'Error response from scanner',
		ERR_UNKNOWN_RESPONSE: 'Unknown response from scanner'
	}
	
	# Results processing functions
	def stspost(cmd):
		pass
	
	# Define decoding re's and methods for cmd results
	Decodes = {
		b'STS': {	# STS is hard, it's variable in length
			'repre': rb'STS,(?P<PREVAL>[01]{4,8}),',
			'recmd': lambda PREDICT: b''.join((b'STS,(?P<DSP_FORM>[01]{4,8}),',
				b''.join(
					map(lambda line: b''.join((
						b'(?P<L',
						_lineno(line),
						b'_CHAR>[^,]{,16}),(?P<L',
						_lineno(line),
						b'_MODE>[^,]{,16}),')), 
					range(len(PREDICT['PREVAL'])))),
				rb'(?P<SQL>\d?),(?P<MUT>\d?),(?P<BAT>\d?),(?P<RSV1>\d?),(?P<RSV2>\d?),(?P<WAT>\w{,4}),(?P<SIG_LVL>\d?),(?P<BK_COLOR>\w*),(?P<BK_DIMMER>\d)$')),
			'repost': stspost,	# Post processing routine
		},
	}

		

class Scanner(Serial):
	"""
	Scanner class - Handles opening IO to the scanner and command write with response read.
	"""
	
	COOKED = 0
	RAW = 1
	DECODED = 2

	def __init__(self, port = None, baudrate = 0, timeout = 0.2, ):
		'''
		Initialize the underlying serial port and provide the wrapper
		'''
		
		Serial.__init__(self, port = port, baudrate = baudrate, timeout = timeout)
		self._sio = io.TextIOWrapper(io.BufferedRWPair(self, self),
			newline='\r', line_buffering=True, encoding = 'ISO-8859-1')
		return
		
	def discover(self):
		'''
		Discover the Scanner port
		
		Currently only the PL2303 is acceptable. This will expand later in development
		'''
		
		if self.port is None:	# Look for the port
			devs_prefix = ['cu.PL2303',] # Just PL2303 devices for now
			pdevs = [glob('/dev/' + pref + '*') for pref in devs_prefix]
			# Use the first match
			for pdev1 in pdevs:
				if len(pdev1) > 0:
					self.port = pdev1[0]
					break
				
		if self.port is None:	# Still bad ... not good
			return False
		
		self.baudrate = 19200	# Temporary default
		
		self.open()
		
		return self.isOpen()

	def cmd(self, cmd_string, cooked = COOKED):
		'''
		Send a command and return the response
		
		The line ending '\r' is automatically added and removed
		'''
				
		self._sio.write(cmd_string + '\r')
		self._sio.flush()	# Note sure we need this ...
		resp = self._sio.readline().encode('ISO-8859-1')
		if resp.endswith(b'\r'): resp = resp[:-1] # Strip the '\r'
		if cooked == self.COOKED:    resp = self.cookIt(resp)
		elif cooked == self.RAW:     pass	# Nothing to do
		elif cooked == self.DECODED: resp = self.decodeIt(resp)
		else: raise ValueError("Scanner.cmd: cooked value out of range")
		
		return resp
		
	def cookIt(self, resp):
		'''
		Create an ascii string from the bytes input
		Any non-ASCII chars (ord >127) are replaced with '?'
		'''
		if not type(resp) is bytes: 
			raise TypeError('Scanner.CookIt(): I can only cook bytes!')
		
		return bytes([c if c < 127 else ord('?') for c in resp]).decode('ASCII')
		
	def decodeIt(self, resp):
		'''
		Decode a raw response into the corresponding structure
		
		NOTE! NOT YET IMPLEMENTED!
		'''
		
		raise NotImplementedError('Scanner.decodeIt: Not Implemented (stay tuned!)')
		