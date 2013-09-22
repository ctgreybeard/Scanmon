#!/usr/bin/env python3
'''
Scanner monitor - Shows scanner activity in a window with some controls
'''

import re, types, time, datetime
from scanner import Scanner, Decode
from tkinter import *
from tkinter import ttk
from threading import Thread
from queue import Queue, Empty

class MonitorRequest:
	
	REQUESTS = {	
		# 1-99 to Monitor
		'CMD': 1,	# Send scanner command ->Monitor
		# 100-199 bi-directional (maybe)
		'SETVOL': 101, 	# Set window status message/scanner
		'SETSQL': 102, 	# Set window status message/scanner
		# 200-200 to Application
		'CALLBACK' : 201,
		'SETSTATUS': 202, 	# Set window status message
		'SETHOLD': 203, 	# Set Hold button text
		'SETRCVIND': 204, 	# Set receive indicator color
		'SETDUR': 205, 	# Set receive duration display
		'SETSYSDISP': 206, 	# Set received system display
	}
	
	def __init__(self, req_type, message, response = None, callback = None):
		self.req_type = req_type
		self.orig_type = None
		self.response = response
		self.callback = callback
		self.message = message

class Monitor(Thread):

	def __init__(self, my_queue, their_queue, **kw):
		Thread.__init__(self, **kw)
		self.my_queue = my_queue		# Messages TO the Monitor
		self.their_queue = their_queue	# Messages FROM the Monitor
		self.scanner = Scanner()
		if not self.scanner.isOpen():
			assert self.scanner.discover(), 'Unable to acquire scanner'
		# Set some local tracking variables, guaranteed not to match at startup
		self.tv_vol = ['', 'SETVOL']
		self.tv_sql = ['', 'SETSQL']
		self.tv_hold_b = [-1, 'SETHOLD']
		self.tv_rcv_ind = ['', 'SETRCVIND']
		self.tv_sys_disp = [{
			'system': '',
			'group':  '',
			'channel': '',
			'frequency': '',
			'starttime': '',
		}, 'SETSYSDISP']
		self.cur_frq = ''
		self.tv_dur = ['', 'SETDUR']
		self.start_time = None
	
	def queue_message(self, type, message, request = None):
		if request is None:		# No current request, make a new one
			request = MonitorRequest(type, message)
		else:
			request.orig_type = request.req_type	# Save the original type
			request.req_type = type
			request.message = message
		
		self.their_queue.put(request)
		
	def set_status(self, status):
		self.queue_message(MonitorRequest.REQUESTS['SETSTATUS'], status)

	def set_it(self, it, val):
		if it[0] != val:
			it[0] = val
			self.queue_message(MonitorRequest.REQUESTS[it[1]], val)

	def set_vol(self, vol):
		self.set_it(self.tv_vol, vol)

	def set_sql(self, sql):
		self.set_it(self.tv_sql, sql)

	def set_rcv_ind(self, ind):
		self.set_it(self.tv_rcv_ind, ind)

	def set_dur(self, dur):
		self.set_it(self.tv_dur, dur)

	def set_sys_disp(self, disp):
		self.set_it(self.tv_sys_disp, disp)

	def check_spin(self, tv, cmd, var):
		resp = self.send_cmd(cmd)
		assert not resp['iserror'], '{} command failed'.format(cmd)
		try:
			aval = int(resp[var])	# Actual Value
			self.set_it(tv, aval)
		except: pass

	def check_vol(self):
		self.check_spin(self.tv_vol, 'VOL', 'LEVEL')

	def check_sql(self):
		self.check_spin(self.tv_sql, 'SQL', 'LEVEL')

	def check_hold(self):
		l1 = self.send_cmd('STS')['L1_CHAR']
		is_hold = True if l1.startswith(' ????') else False
		if is_hold != self.tv_hold_b[0]:
			self.set_status('Hold' if is_hold else 'Resume')
		self.set_it(self.tv_hold_b, is_hold)

	def send_cmd(self, cmd, request = None):
		#print('Sending command:', scmd)
		resp = self.scanner.cmd(cmd, Scanner.DECODED)
		if resp['iserror']:
			print('{} command failed: {}'.format(cmd, Decode.ERRORMSG[resp[Decode.ERRORCODEKEY]]))
		if request is not None: request.response = resp
		return resp
	
	def do_message(self, message):
		if not isinstance(message, MonitorRequest):
			raise ValueError('Non-MonitorRequest received')
		if message.req_type == MonitorRequest.REQUESTS['CMD']:
			self.send_cmd(message.message)

	def run(self):	# Overrides the default Thread run (which does nothing)
	
		loop_count = 0
		self.start_time = None
		self.now_time = datetime.datetime.today()
		self.cur_frq = ''
		self.set_status('Monitor starting')
		self.monitor_running = True
	
		while self.monitor_running:
			print('Loop:', loop_count)
			if loop_count >= 5:	# Only check every five loops (about one second)
				self.check_vol()
				self.check_sql()
				self.check_hold()
				loop_count = 0
			resp = self.send_cmd('GLG')
			#print('Got GLG: FRQ={}, MUT={}, SQL={}'.format(resp['FRQ_TGID'], resp['MUT'], resp['SQL']))
			try:
				if resp['SQL'] == '' or resp['SQL'] == '0':	# We aren't receiving anything
					self.set_rcv_ind('#e00')
					#tv_sys.set('')	# We don't clear the previous system's values
					#tv_grp.set('')
					#tv_chn.set('')
					#tv_frq.set('')
					#tv_dur.set('')
					#tv_time.set('')
					self.cur_frq = ''
					self.start_time = None
				elif resp['FRQ_TGID'] != '':
					now_time = datetime.datetime.today()	# Capture the moment
					this_frq = eval(resp['FRQ_TGID'])
					if self.cur_frq == this_frq:	# Same frequency
						self.set_it(self.tv_dur, str(int((now_time - self.start_time).total_seconds())))
					else:
						self.start_time = now_time
						self.set_it(self.tv_rcv_ind, '#0e0')
						self.cur_frq = this_frq
						self.set_it(self.tv_sys_disp,
							{'frequency': this_frq,
							'system': resp['NAME1'],
							'group': resp['NAME2'],
							'channel': resp['NAME3'],
							'duration': '0',
							'starttime': now_time.strftime('%m/%d/%y %H:%M:%S')})
						self.set_it(self.tv_dur, '0')
				else: self.set_status('No SQL and no FRQ/TGID??')
			except KeyError:
				self.set_status('Bad response from GLG')
			
			loop_count += 1
			try:
				while True:
					self.do_message(self.my_queue.get(block = False))
			except Empty:
				pass
			#time.sleep(0.2)

	def do_stop(self):
		self.set_status('Monitor ending')
		self.monitor_running = False

# END class Monitor

# Master run flag
run_app = True

# All routines are defined here

def run_request(request):
	rtype = request.req_type
	print('Req={}: "{}"'.format(rtype, request.message))
	if rtype == MonitorRequest.REQUESTS['SETVOL']:
		tv_vol.set(request.message)
	elif rtype == MonitorRequest.REQUESTS['SETSQL']:
		tv_sql.set(request.message)
	elif rtype == MonitorRequest.REQUESTS['SETSTATUS']:
		tv_status.set(request.message)
	elif rtype == MonitorRequest.REQUESTS['SETHOLD']:
		tv_hold_resume.set('Resume' if request.message else 'Hold')
	elif rtype == MonitorRequest.REQUESTS['SETRCVIND']:
		l_rcv_ind.configure(background = request.message)
	elif rtype == MonitorRequest.REQUESTS['SETDUR']:
		tv_dur.set(request.message)
	elif rtype == MonitorRequest.REQUESTS['SETSYSDISP']:
		tv_sys.set(request.message['system'])
		tv_grp.set(request.message['group'])
		tv_chn.set(request.message['channel'])
		tv_dur.set(request.message['duration'])
		tv_time.set(request.message['starttime'])
		tv_frq.set(request.message['frequency'])

def send_cmd(cmd):
	cmd_request = MonitorRequest(MonitorRequest.REQUESTS['CMD'], cmd)
	to_mon_queue.put(cmd_request)

def set_vol():
	global isMute
	send_cmd('VOL,{}'.format(tv_vol.get()))
	if isMute:
		isMute = False
		tv_mute.set('Mute')
		tv_status.set('Unmute')

def set_sql():
	send_cmd('SQL,{}'.format(tv_sql.get()))

def do_lockout():
	send_cmd('KEY,L,P')
	tv_status.set('Lockout sent')

def do_skip():
	send_cmd('KEY,>,P')
	tv_status.set('Skip sent')

def do_hold():
	send_cmd('KEY,H,P')
	tv_status.set('Hold sent')

def do_scan():
	send_cmd('KEY,S,P')
	tv_status.set('Scan sent')

def do_bookmark():
	tv_status.set('Commanded to Bookmark')

isMute = False
oVol = '0'

def do_mute():
	global isMute, oVol
	tv_status.set('Commanded to Mute')
	if isMute:	# Unmute
		tv_vol.set(oVol)
		set_vol()
		tv_status.set('Unmute')
	else:		# Mute
		oVol = tv_vol.get()
		tv_vol.set('0')
		send_cmd('VOL,0')
		isMute = True
		tv_mute.set('Unmute')
		tv_status.set('Mute')

def do_mode():
	tv_status.set('Commanded to Mode')

def do_showlog():
	tv_status.set('Commanded to Show Log')

def do_prefs():
	tv_status.set('Commanded to Prefs')

def do_close():
	global run_app
	
	tv_status.set('Closing...')
	run_app = False
	thr_monitor.do_stop()
	thr_monitor.join(timeout = 5)

to_mon_queue = Queue()
from_mon_queue = Queue()


root = Tk()	# Root window
root.title('Scanmon - Uniden scanner monitor')
root.resizable(False, False)

mainframe = ttk.Frame(root, padding = (5, 10))
mainframe.grid(column = 0, row = 0, sticky = (N, E, W, S))

# Text variables used below
tv_hold_resume = StringVar(value = 'Hold')
tv_hold_b = False
tv_mute = StringVar(value = 'Mute')
#tv_start = StringVar(value = 'Start')
tv_status = StringVar()

# Define the buttons

b_lockout = ttk.Button(mainframe, text = 'Lockout', width = 8, command = do_lockout)
b_skip = ttk.Button(mainframe, text = 'Skip', width = 8, command = do_skip)
b_hold_resume = ttk.Button(mainframe, textvariable = tv_hold_resume, width = 8, command = do_hold)
b_scan = ttk.Button(mainframe, text = 'Scan', width = 8, command = do_scan)
b_bookmark = ttk.Button(mainframe, text = 'Bookmark', width = 8, command = do_bookmark)
b_mute = ttk.Button(mainframe, textvariable = tv_mute, width = 8, command = do_mute)
b_mode_select = ttk.Button(mainframe, text = 'Mode Select', command = do_mode)
b_view_log = ttk.Button(mainframe, text = 'View Log', width = 8, command = do_showlog)
b_prefs = ttk.Button(mainframe, text = 'Prefs', width = 8, command = do_prefs)
b_close = ttk.Button(mainframe, text = 'Close', width = 8, command = do_close)
#b_start = ttk.Button(mainframe, textvariable = tv_start, width = 8, command = do_start)

# Sizegrip
b_sizegrip = ttk.Sizegrip(root)

# Static labels
l_rcv = ttk.Label(mainframe, text = 'Rcv:')
l_vol = ttk.Label(mainframe, text = 'Volume:')
l_sql = ttk.Label(mainframe, text = 'Squelch:')

# Define Data Display Styles
#s_ddisp = ttk.Style()
#s_ddisp.configure('DDisp.TLabel', 

# Data Display labels

l_rcv_ind = ttk.Label(mainframe, text = '    ', background = '#00e')
lf_sys = ttk.LabelFrame(mainframe, text = 'System', padding = (5, 0))
tv_sys = StringVar()
l_sys = ttk.Label(lf_sys, textvariable = tv_sys, width = 16)
lf_grp = ttk.LabelFrame(mainframe, text = 'Group', padding = (5, 0))
tv_grp = StringVar()
l_grp = ttk.Label(lf_grp, textvariable = tv_grp, width = 16)
lf_chn = ttk.LabelFrame(mainframe, text = 'Channel', padding = (5, 0))
tv_chn = StringVar()
l_chn = ttk.Label(lf_chn, textvariable = tv_chn, width = 16)
c_frq = ttk.Frame(mainframe)
lf_frq = ttk.LabelFrame(c_frq, text = 'Frequency', padding = (5, 0))
tv_frq = StringVar()
l_frq = ttk.Label(lf_frq, textvariable = tv_frq, width = 10, anchor = E)
l_mhz = ttk.Label(c_frq, text = 'MHz')
c_dur = ttk.Frame(mainframe)
lf_dur = ttk.LabelFrame(c_dur, text = 'Duration', padding = (5, 0))
tv_dur = StringVar()
l_dur = ttk.Label(lf_dur, textvariable = tv_dur, width = 10, anchor = E)
l_secs = ttk.Label(c_dur, text = 'Secs')
lf_time = ttk.LabelFrame(mainframe, text = 'Start Time', padding = (5, 0))
tv_time = StringVar()
l_time = ttk.Label(lf_time, textvariable = tv_time, width = 16, anchor = E)
lf_status = ttk.LabelFrame(mainframe, text = 'Status')
l_status = ttk.Label(lf_status, textvariable = tv_status)

# Grid the labels into the frames
l_sys.grid(column = 0, row = 0)
l_grp.grid(column = 0, row = 0)
l_chn.grid(column = 0, row = 0)
l_frq.grid(column = 0, row = 0)
l_dur.grid(column = 0, row = 0)
l_time.grid(column = 0, row = 0)

# The spinboxes
tv_vol = StringVar()
s_vol = Spinbox(mainframe, from_ = 0, to = 29, increment = 1, justify = RIGHT,
	state = 'readonly', width = 4, textvariable = tv_vol, command = set_vol)
tv_sql = StringVar()
s_sql = Spinbox(mainframe, from_ = 0, to = 19, increment = 1, justify = RIGHT,
	state = 'readonly', width = 4, textvariable = tv_sql, command = set_sql)

# Grid the rest into the Frame
b_lockout.grid(column = 0, row = 1, columnspan = 2, rowspan = 2)
b_skip.grid(column = 2, row = 1, columnspan = 2, rowspan = 2)
b_hold_resume.grid(column = 0, row = 3, columnspan = 2, rowspan = 2)
b_scan.grid(column = 2, row = 3, columnspan = 2, rowspan = 2)
b_bookmark.grid(column = 0, row = 5, columnspan = 2, rowspan = 2)
b_mute.grid(column = 2, row = 5, columnspan = 2, rowspan = 2)
l_vol.grid(column = 0, row = 7, columnspan = 1, sticky = E)
s_vol.grid(column = 1, row = 7, columnspan = 1, sticky = W)
l_sql.grid(column = 2, row = 7, columnspan = 1, sticky = E)
s_sql.grid(column = 3, row = 7, columnspan = 1, sticky = W)
b_mode_select.grid(column = 0, row = 8, columnspan = 2)
b_view_log.grid(column = 2, row = 8, columnspan = 2)
b_prefs.grid(column = 0, row = 9, columnspan = 2)
b_close.grid(column = 5, row = 8, rowspan = 2)
l_rcv.grid(column = 4, row = 0, columnspan = 1, sticky = E)
l_rcv_ind.grid(column = 5, row = 0, columnspan = 1, sticky = W)
lf_sys.grid(column = 5, row = 1, columnspan = 2, sticky = W)
lf_grp.grid(column = 5, row = 2, columnspan = 2, sticky = W)
lf_chn.grid(column = 5, row = 3, columnspan = 2, sticky = W)
c_frq.grid(column = 5, row = 4, columnspan = 2, sticky = W)
lf_frq.grid(column = 0, row = 0)
l_mhz.grid(column = 1, row = 0, sticky = (W, S))
c_dur.grid(column = 5, row = 5, sticky = W)
lf_dur.grid(column = 0, row = 0)
l_secs.grid(column = 1, row = 0, sticky = (W, S))
lf_time.grid(column = 5, row = 6, columnspan = 2, sticky = W)
#b_start.grid(column = 5, row = 8, rowspan = 2)
lf_status.grid(column = 0, row = 10, columnspan = 7, sticky = EW)
l_status.grid(column = 0, row = 0, sticky = EW)

# Window is not resizable but if it were this is how we would show it
#b_sizegrip.grid(column = 1, row = 1)

root.columnconfigure(0, weight = 1)
root.rowconfigure(0, weight = 1)

mainframe.rowconfigure(7, pad=10)
mainframe.rowconfigure(8, pad=10)
mainframe.rowconfigure(9, pad=10)

tv_status.set('Ready!')

# Start it all up!

thr_monitor = Monitor(to_mon_queue, from_mon_queue, name = 'Monitor')
thr_monitor.start()

while run_app:		# Util we are done ...
	root.update()
	try:
		request = from_mon_queue.get(timeout = 0.1)
		run_request(request)
	except Empty:
		pass
