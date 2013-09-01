# Uniden Scanner utilities and programming access

class Scanner:
	def __init__(self, port=None, baud=0):
		self.port = port
		self.baud = baud
		
	def discover():
		devs_prefix = ('/dev/cu.PL2303', '/dev/tty.PL2303') # Just PL2303 devices for now
		