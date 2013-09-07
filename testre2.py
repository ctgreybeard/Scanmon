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
GID=b'GID,CNV,15,0,System 1,GroupName,TGIDName'
SGID=b'GID,CNV,15,0,System 1,GroupName'
NGID=b'GID,NG'
BGID1=b'GID'
BGID2=b'GID,'

#tests = (STS1, STS2, STS3, STS4, NULL, NG, FU, BAR, GID)
tests = (GID, SGID, NGID, BGID1, BGID2)

from scanner import Decode

# per BCD396XT_Complete_Reference.pdf
#
# STS,[DSP_FORM],[L1_CHAR],[L1_MODE],[L2_CHAR],[L2_MODE],[L3_CHAR],[L3_MODE], [L4_CHAR],
#  [L4_MODE],...,[L8_CHAR],[L8_MODE],[SQL],[MUT],[BAT],[RSV],[RSV],[WAT],
#  [SIG_LVL],[BK_COLOR],[BK_DIMMER][\r]

for amatch in tests:
	print('\n', '-'*40)

	resp = Decode.domatch(amatch)
	print(resp)
	if resp[Decode.ISERRORKEY]:
		print('Error code={}, msg={}'.
			format(resp[Decode.ERRORCODEKEY], 
				Decode.ERRORMSG[resp[Decode.ERRORCODEKEY]]))

