# Uniden Scanner utilities and programming access
"""
Uniden Scanner utilities and programming access

Module and class to communicate with a Uniden DMA scanner (BCD996XT, BCD396XT, etc.)
"""

import io
from serial import Serial
from glob import glob

class Scanner():
	"""
	Scanner class - Handles opening IO to the scanner and command write with response read.
	"""

	def __init__(self, port = None, baudrate = 0, timeout = 0.2):
		self._scanner = Serial(port = port, baudrate = baudrate, timeout = timeout)
		self.isOpen = self._scanner.isOpen
		self._sio = io.TextIOWrapper(io.BufferedRWPair(self._scanner, self._scanner),
			newline=None, line_buffering=True)
		return
		
	def getBaudrate(self):
		if not self._scanner is None: return self._scanner.baudrate
		return 0
		
	def setBaudrate(self, baudrate):
		if not self._scanner is None: 
			obaudrate = self._scanner.baudrate
			self._scanner.baudrate = baudrate
			return obaudrate
		return None
		
	def getPort(self):
		if not self._scanner is None: return self._scanner.name
		return None
		
	def setPort(self, port):
		if not self._scanner is None: 
			oport = self._scanner.port
			self._scanner.port = port
			return oport
		return None
		
	def getTimeout(self):
		if not self._scanner is None: return self._scanner.timeout
		return 0
		
	def setTimeout(self, timeout):
		if not self._scanner is None: 
			otimeout = self._scanner.timeout
			self._scanner.timeout = timeout
			return otimeout
		return None
		
	def discover(self):
		if self.getPort() is None:	# Look for the port
			devs_prefix = ['cu.PL2303',] # Just PL2303 devices for now
			pdevs = [glob('/dev/' + pref + '*') for pref in devs_prefix]
			print('pdevs=', pdevs)
			# Use the first match
			for pdev1 in pdevs:
				if len(pdev1) > 0:
					self.setPort(pdev1[0])
					break
				
		if self.getPort() is None:	# Still bad ... not good
			return False
		
		self.setBaudrate(19200)	# Temporary default
		
		self._scanner.open()
		
		return self._scanner.isOpen()
