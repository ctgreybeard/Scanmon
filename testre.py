# Test regular expressions on STS return value
# -.- coding: ISO-8859-1 -.-

# A typical STS command return value
STS1=b'STS,011000,                ,,Bethel          ,,AN        SC \x81  ,,                ,,S0:-2*4***-9*   ,,GRP1---------   ,,0,1,0,0,0,0,0,GREEN,3'
STS2=b'STS,011000,          \xac\xad    ,,Bethel          ,,Bethel PD 1     ,, 453.6000 DCS134,,S0:-2*4***-9*   ,,GRP----------   ,,1,0,0,0,0,0,5,BLUE,3'

import re
import sys

# per BCD396XT_Complete_Reference.pdf
#
# STS,[DSP_FORM],[L1_CHAR],[L1_MODE],[L2_CHAR],[L2_MODE],[L3_CHAR],[L3_MODE], [L4_CHAR],
#  [L4_MODE],...,[L8_CHAR],[L8_MODE],[SQL],[MUT],[BAT],[RSV],[RSV],[WAT],
#  [SIG_LVL],[BK_COLOR],[BK_DIMMER][\r]

# Per the spec the string has a variable number of lines, 4 to 8.  We need to parse the 
# beginning of the string to build the rest
stsrepre = b'STS,(?P<DSP_FORM>[01]{4,8}),'

repre = re.compile(stsrepre)

def domatch(tomatch):

	global repre

	print('\n', '-'*40)

	reprematch = repre.match(tomatch)

	if reprematch is None: 
		raise ValueError('No "pre" string match')
	
	print('DSP_FORM=', reprematch.group('DSP_FORM'), 'and the length is',
		len(reprematch.group('DSP_FORM')))
	
	numlines = len(reprematch.group('DSP_FORM'))

	print('numlines=', numlines)

	print('SRC=', tomatch)

# Unfortunately python doesn't allow comments on continued lines in the case so it's ugly

	stsre  = b'STS,(?P<DSP_FORM>[01]{4,8}),' 				# STS,[DSP_FORM],
	stsre += b'([^,]{,16}),([^,]{,16}),' * numlines			# [L1_CHAR],[L1_MODE], etc.
	stsre += b'(?P<SQL>\\d?),'								# [SQL],
	stsre += b'(?P<MUT>\\d?),'								# [MUT],
	stsre += b'(?P<BAT>\\d?),'								# [BAT],
	stsre += b'(?P<RSV1>\\d?),'								# [RSV],
	stsre += b'(?P<RSV2>\\d?),'								# [RSV],
	stsre += b'(?P<WAT>\\w{,4}),'							# [WAT],
	stsre += b'(?P<SIG_LVL>\\d?),'							# [SIG_LVL],
	stsre += b'(?P<BK_COLOR>\\w*),'							# [BK_COLOR],
	stsre += b'(?P<BK_DIMMER>\\d)$'							# [BK_DIMMER]

	print('re=', stsre)

	rests = re.compile(stsre)

	restsmatch = rests.match(tomatch)

	if restsmatch is None:
		print('OOPS! No match')
		sys.exit(1)
	
	print(restsmatch.groups())
	print(restsmatch.groupdict())
	
domatch(STS1)
domatch(STS2)

