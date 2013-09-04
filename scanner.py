# Uniden Scanner utilities and programming access
"""
Uniden Scanner utilities and programming access

Module and class to communicate with a Uniden DMA scanner (BCD996XT, BCD396XT, etc.)
"""

import io
from serial import Serial
from glob import glob

class Scanner(Serial):
	"""
	Scanner class - Handles opening IO to the scanner and command write with response read.
	"""

	def __init__(self, port = None, baudrate = 0, timeout = 0.2):
		Serial.__init__(self, port = port, baudrate = baudrate, timeout = timeout)
		self._sio = io.TextIOWrapper(io.BufferedRWPair(self, self),
			newline=None, line_buffering=True)
		return
		
	def discover(self):
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
