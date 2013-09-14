# Log scan results with timeout/lockout

import sys, time, csv, argparse
from datetime import datetime, timedelta
from prettyprint import pp_str
from scanner import Scanner
import scanner

class Hit:
	def __init__(self, resp):
		self.startTime = datetime.today()
		self.frqTGID = resp['FRQ_TGID']
		self.duration = 0
		self.mod = resp['MOD']
		self.squelch = 99
		self.ctcssDCS = resp['CTCSS_DCS']
		self.system = resp['NAME1']
		self.group = resp['NAME2']
		self.channel = resp['NAME3']
		self.systemTag = resp['SYS_TAG']
		self.channelTag = resp['CHAN_TAG']
		self.action = ''

class HitLog:
	def __init__(self, hit):
		self.startTime = hit.startTime
		self.frqTGID = hit.frqTGID
		self.duration = hit.duration
		self.hitcount = 1
		self.ctcssDCS = hit.ctcssDCS
		self.system = hit.system
		self.group = hit.group
		self.channel = hit.channel
		self.releaseCount = 0
		self.timeoutCount = 0
		self.lockoutCount = 0
		if hit.action == '': self.releaseCount = 1
		elif hit.action == 'Skip': self.timeoutCount = 1
		elif hit.action == 'Lockout': self.lockoutCount = 1
		else:
			print('Unknown Hit Action:', hit.action)
			raise RuntimeError

class Timeout:
	def __init__(self, frqTGID, now):
		self.frqTGID = frqTGID
		self.firstTimeout = now
		self.lastTimeout = now
		self.timeoutCount = 0

def hitChannel(resp):
	global active
	
	active = Hit(resp)
	resp = scanner.cmd('SQL', cooked = Scanner.DECODED)
	if not resp['iserror']: active.squelch = resp['LEVEL']
	if args.debug >= D_INFO: print('Hit:', active.frqTGID)
	
def releaseChannel():
	global active
	
	active.duration = (datetime.today() - active.startTime).total_seconds()
	logChannel(active)
	active = None
	
def checkTimeout():
	#global args, active, scanner
	
	now = datetime.today()
	active.duration = (now - active.startTime).total_seconds()
	if active.duration > args.timeout:
		if args.debug >= D_INFO: print('Timeout')
	
		if active.frqTGID in timeouts:
			thisTO = timeouts[active.frqTGID]
			if args.debug >= D_FULL: print('Found previous timeout')
		else:
			thisTO = Timeout(active.frqTGID, now)
			timeouts[active.frqTGID] = thisTO
			if args.debug >= D_FULL: print('New Timeout')
		
		# decay the timeouts
		decay = int((now - thisTO.lastTimeout).total_seconds() / args.decay)
		thisTO.timeoutCount = thisTO.timeoutCount - decay if thisTO.timeoutCount - decay > 0 else 0;
		
		thisTO.timeoutCount += 1
		thisTO.lastTimeout = now
		
		if args.debug >= D_DEBUG: print('Decay={}, count={}'.format(decay, thisTO.timeoutCount))
		if thisTO.timeoutCount >= args.lockout:
			active.action = 'Lockout'
			scanner.cmd('KEY,L,P') # lockout
		else:
			active.action = 'Skip'
			scanner.cmd('KEY,>,P') # skip
		
		if args.debug >= D_INFO: print(active.action)
		
	
def logChannel(hit):
	#global args, active
	
	if hit.frqTGID in hitslog:
		thisHit = hitslog[hit.frqTGID]
		if args.debug >= D_FULL: print('Found previous hitlog')
		if hit.action == '': thisHit.releaseCount += 1
		elif hit.action == 'Skip': thisHit.timeoutCount += 1
		elif hit.action == 'Lockout': thisHit.lockoutCount += 1
		else:
			print('Unknown Hit Action:', hit.action)
			raise RuntimeError
		thisHit.duration += hit.duration
		thisHit.hitcount += 1
	else:
		thisHit = HitLog(hit)
		hitslog[hit.frqTGID] = thisHit
		if args.debug >= D_FULL: print('New Hitlog')
	
	print('{},{},{} {} {} {:.2f} secs {}'.
		format(hit.system, hit.group, hit.channel, hit.frqTGID, hit.squelch, hit.duration, hit.action))

# Parameter defaults
scanmode = 'none'
timeout = 20
lockout = 5
decay = 600
debug = 0
logfile = 'scanner.log'
sleep = 0.25

# Debug levels
D_NONE = 0
D_INFO = 1
D_DEBUG = 2
D_FULL = 3

# Active channel
active = None

# Timeouts Log
timeouts = {}

# Hits Log
hitslog = {}

parser = argparse.ArgumentParser(description='Scan logger')

parser.add_argument('--scanmode', 
	default = scanmode, 
	type = str, 
	help='Service scan mode, if desired',
	choices = sorted(list(Scanner.ServiceModes.keys())),
)

parser.add_argument('--timeout', 
	default = timeout, 
	type = int, 
	help='Channel timeout (secs)')

parser.add_argument('--lockout', 
	default = lockout, 
	type = int, 
	help='Channel consecutive lockout count')

parser.add_argument('--logfile', 
	default = logfile, 
	type = str, 
	help='Log file name')

parser.add_argument('--decay',
	default = decay,
	type = int,
	help = 'Timeout decay (seconds)')

parser.add_argument('--sleep',
	default = sleep,
	type = float,
	help = 'Loop sleep time (seconds)')

parser.add_argument('--debug',
	default = debug,
	type = int,
	help = 'Debug Level (0-{})'.format(D_FULL))

args = parser.parse_args()

if args.debug >= D_DEBUG: print('ARGS=', pp_str(args))

timeoutDelta = timedelta(seconds = args.timeout)

scanner = Scanner()

if not scanner.isOpen(): scanner.discover()

if not scanner.isOpen():
	print('Scanner did not initialize!')
	raise RuntimeError

if args.scanmode != scanmode:
	cmd = 'JPM,SVC_MODE,' + Scanner.ServiceModes[args.scanmode]
	if args.debug >= D_DEBUG: print('Sending:', cmd)
	resp = scanner.cmd(cmd, cooked = Scanner.DECODED)
	if args.debug >= D_FULL: print(pp_str(resp))
	if not resp['isOK']:
		print('Unable to set scan mode!')
		print('Response = ', pp_str(resp))
		raise RuntimeError

# Scanner should be scanning one way or the other ...

try: # Wrap the scan so we can catch the interrupt
	
	while True:
		resp = scanner.cmd('GLG', cooked = Scanner.DECODED)
		if resp['iserror'] or resp['CMD'] != 'GLG':
			print('Unable to get scan status!')
			print('Response = ', pp_str(resp))
			raise RuntimeError
	
		if resp['FRQ_TGID'] == '':	# Empty response means still looking
			if active is not None:
				releaseChannel()
	
		else:
			if active is not None:
				if resp['FRQ_TGID'] == active.frqTGID:	# Same channel?
					checkTimeout()
				else:	# New channel
					releaseChannel()
					hitChannel(resp)
		
			else:	# New channel
				hitChannel(resp)
		
		time.sleep(args.sleep)	# Let it rest a half second

except KeyboardInterrupt: pass

print('Hit Log')

for hitkey, hit in hitslog.items():
	print('Sys/Grp/Chn: {sys}/{grp}/{chn} Frq: {frq} Count Rls/LO/TO: {rls}/{lo}/{to} Avg Dur: {dur:.2f}'.
		format(sys = hit.system, grp = hit.group, chn = hit.channel, frq = hit.frqTGID, 
		rls = hit.releaseCount, lo = hit.lockoutCount, to = hit.lockoutCount,
		dur = hit.duration / hit.hitcount))

print('Done...')