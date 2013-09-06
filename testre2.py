# Test regular expressions on STS return value
# -*- coding: ISO-8859-1 -*-

# A typical STS command return value
STS1=b'STS,011000,                ,,Bethel          ,,AN        SC \x81  ,,                ,,S0:-2*4***-9*   ,,GRP1---------   ,,0,1,0,0,0,0,0,GREEN,3'
STS2=b'STS,011000,          \xac\xad    ,,Bethel          ,,Bethel PD 1     ,, 453.6000 DCS134,,S0:-2*4***-9*   ,,GRP----------   ,,1,0,0,0,0,0,5,BLUE,3'
STS3=b'STS,011000,                ,,Quick Search?   ,,Yes="E" / No=".",,                ,,                ,,                ,,0,1,0,0,0,0,0,GREEN,3'
STS4=b'STS,1111, -- M E N U --  ,________________,Program System  ,****************,Program Location,,Srch/CloCall Opt,,0,1,0,0,0,0,0,GREEN,3'
NULL=b''
NG=b'NG'
FU=b'FU,000'
BAR=b'BAR,What?'

#tests = (STS1, STS2, STS3, STS4, NULL, NG, FU, BAR)
tests = (STS1,)

import re, sys, types

from scanner import Decode

# per BCD396XT_Complete_Reference.pdf
#
# STS,[DSP_FORM],[L1_CHAR],[L1_MODE],[L2_CHAR],[L2_MODE],[L3_CHAR],[L3_MODE], [L4_CHAR],
#  [L4_MODE],...,[L8_CHAR],[L8_MODE],[SQL],[MUT],[BAT],[RSV],[RSV],[WAT],
#  [SIG_LVL],[BK_COLOR],[BK_DIMMER][\r]

ERRORRESP = (b'', 		# Null
			 b'ERR', 	# Invalid command
			 b'NG',		# Valid command, wrong mode
			 b'FER',	# Framing error
			 b'ORER')	# Overrun error
			 

prematch = rb'(\w*)'	# Only need the first "word" on the line
prematchre = re.compile(prematch)

def domatch(tomatch):

	global prematchre, ERRORRESP
	
	def doIt(target, request):
		#print('doIt matching:', target)
		#print('           to:', request)
		regex = re.compile(request, flags = 0)
		rematch = regex.match(target)
		return rematch.groupdict(default={'error': True}) \
			if rematch is not None else {'error': True}
	
	def runIt(target, basedict, request):
		nonlocal doIt
		
		if isinstance(request, types.FunctionType):
			basedict.update(doIt(target, request(basedict)))
		
		elif isinstance(request, bytes):
			basedict.update(doIt(target, request))
		
		else:
			raise ValueError("Invalid decode type")
	
	dec = Decode()
	
	matchresult = {'CMD': b'', 'error': False}

	prematch = prematchre.match(tomatch)
	if prematch is None: raise ValueError("Error in prematch")
	
	resp = prematch.group(1)	# What did we find?
	print('Found:', resp)
	
	if resp in ERRORRESP:		# Error response, can't go further
		matchresult['CMD'] = resp
		matchresult['error'] = True
		return matchresult
		
	if resp in dec.Decodes:
		matchresult['CMD'] = resp
		# OK, we know what to do ... I hope
		
		# First, run the prematch if it exists
		if 'repre' in dec.Decodes[resp]:
			runIt(tomatch, matchresult, dec.Decodes[resp]['repre'])
			
		# So far, so good. Now run the main event
		if 'recmd' in dec.Decodes[resp]:	# Should usually be there
			runIt(tomatch, matchresult, dec.Decodes[resp]['recmd'])
		
	else:
		return None
		
	return matchresult
		
for amatch in tests:
	print('\n', '-'*40)

	resp = domatch(amatch)
	print(resp)
