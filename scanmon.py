#!/usr/bin/env python3
'''
Scanner monitor - Shows scanner activity in a window with some controls
'''

import re, types, time, sys, logging
from datetime import datetime
from scanner import Scanner, Decode
from tkinter import *
from tkinter import ttk
from threading import Thread, Barrier
from queue import Queue, Empty


class Scanmon(ttk.Frame):

	logName = 'scanmon'
	logLevel = logging.INFO
	
	class MonitorRequest:
	
		REQUESTS = {	
			# 1-99 to Monitor
			'CMD': 1,	# Send scanner command ->Monitor
			'MCMD': 2,	# Multi-command request
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

		def __init__(self, scanner, my_queue, their_queue, barrier, *args, **kw):
			Thread.__init__(self, **kw)
			self.my_queue = my_queue		# Messages TO the Monitor
			self.their_queue = their_queue	# Messages FROM the Monitor
			self.scanner = scanner
			# Set some local tracking variables, guaranteed not to match at startup
			self.tv_vol = ['', 'SETVOL']
			self.tv_sql = ['', 'SETSQL']
			self.tv_hold_b = [False, 'SETHOLD']
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
			self.logger = logging.getLogger(Scanmon.logName + '.monitor')
			#self.logger.setLevel(Scanmon.logLevel)
			self.logger.info('Monitor initialized')
			self.barrier = barrier
	
		def queue_message(self, type, message, request = None):
			if request is None:		# No current request, make a new one
				request = Scanmon.MonitorRequest(type, message)
			else:
				request.orig_type = request.req_type	# Save the original type
				request.req_type = type
				request.message = message
		
			self.their_queue.put(request)
		
		def set_status(self, status):
			self.logger.info('Set Status: %s', status)
			self.queue_message(Scanmon.MonitorRequest.REQUESTS['SETSTATUS'], status)

		def set_it(self, it, val):
			if it[0] != val:
				it[0] = val
				self.queue_message(Scanmon.MonitorRequest.REQUESTS[it[1]], val)

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
			if resp['iserror']:
				self.logger.error('check_spin: %s command failed', cmd)
			else:
				try:
					aval = int(resp[var])	# Actual Value
					self.set_it(tv, aval)
				except: 
					pass

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
			self.logger.debug('Sending command: %s', cmd)
			resp = self.scanner.cmd(cmd, Scanner.DECODED)
			if resp['iserror']:
				self.logger.error('%s command failed: %s, %s', 
					cmd, 
					Decode.ERRORMSG[resp[Decode.ERRORCODEKEY]], 
					str(resp))
			if request is not None: 
				request.response = resp
			return resp
		
		# Drain is only used when there may be a big problem
		def drain(self):
			self.set_status('Draining at {}'.format(datetime.today().strftime('%m/%d/%y %H:%M:%S')))
			resp = self.scanner.drain()
			logger.warning('Drained: %s', str(resp))
	
		def do_message(self, message):
			if not isinstance(message, Scanmon.MonitorRequest):
				self.logger.critical('Non-MonitorRequest received')
				raise ValueError('Non-MonitorRequest received')
			if message.req_type == Scanmon.MonitorRequest.REQUESTS['CMD']:
				self.send_cmd(message.message)
	
		def do_checks(self, main):
			while main.monitor_running:
				main.check_vol()
				main.check_sql()
				main.check_hold()
				time.sleep(0.8)		# Give others time to run

		def run(self):	# Overrides the default Thread run (which does nothing)
	
			self.start_time = None
			self.now_time = datetime.today()
			self.cur_frq = ''
			self.logger.info('Monitor starting')
			self.set_status('Monitor starting')
			self.monitor_running = True
			# Start the status monitor running
			self.status_checks = Thread(target = self.do_checks, args = (self, ))
			self.status_checks.start()
			self.barrier.wait()

			while self.monitor_running:
				resp = self.send_cmd('GLG')
				try:
					self.logger.debug('Got GLG: FRQ=%s, MUT=%s, SQL=%s', resp['FRQ_TGID'], resp['MUT'], resp['SQL'])
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
						now_time = datetime.today()	# Capture the moment
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
					else: 
						self.set_status('No SQL and no FRQ/TGID??')
				except KeyError:
					self.logger.exception('Bad response from GLG: %s', str(resp))
					self.set_status('Bad response from GLG')
					self.drain()
			

				try:
					while True:
						self.do_message(self.my_queue.get(block = False))
				except Empty:
					pass

		def do_stop(self):
			self.set_status('Monitor ending')
			self.monitor_running = False
			self.status_checks.join(timeout = 3)

	# END class Monitor
	
	def __init__(self, master = None):
		ttk.Frame.__init__(self, master)
		
		self.scanner = Scanner(logname = Scanmon.logName + '.scanner')
		if not self.scanner.isOpen():
			assert self.scanner.discover(), 'Unable to acquire scanner'

		self.run_app = True

		self.isMute = False
		self.oVol = '0'
		self.a_status = ['', '', '']

		# create logger
		self.logger = logging.getLogger(Scanmon.logName)
		self.logger.setLevel(Scanmon.logLevel)

		# Create console handler and set level
		ch = logging.StreamHandler(stream = sys.stderr)
		ch.setLevel(self.logLevel)

		# Create formatter
		formatter = logging.Formatter(fmt = '{asctime} - {name} - {levelname} - {message}',
			style = '{')

		# Add formatter to ch
		ch.setFormatter(formatter)

		self.logger.addHandler(ch)
		
		# Setup queues

		self.to_mon_queue = Queue()
		self.from_mon_queue = Queue()
		
		self.buildWindow()

	# All routines are defined here

	def set_status(self, status):
		self.logger.info('Status set: %s', status)
		self.a_status.append(status)
		self.a_status = self.a_status[1:]
		self.tv_status.set('\n'.join(self.a_status))

	def run_request(self, request):
		rtype = request.req_type
		self.logger.debug('Req=%s: "%s"', rtype, request.message)
		if rtype == Scanmon.MonitorRequest.REQUESTS['SETVOL']:
			self.tv_vol.set(request.message)
		elif rtype == Scanmon.MonitorRequest.REQUESTS['SETSQL']:
			self.tv_sql.set(request.message)
		elif rtype == Scanmon.MonitorRequest.REQUESTS['SETSTATUS']:
			self.set_status(request.message)
		elif rtype == Scanmon.MonitorRequest.REQUESTS['SETHOLD']:
			self.tv_hold_resume.set('Resume' if request.message else 'Hold')
		elif rtype == Scanmon.MonitorRequest.REQUESTS['SETRCVIND']:
			self.l_rcv_ind.configure(background = request.message)
		elif rtype == Scanmon.MonitorRequest.REQUESTS['SETDUR']:
			self.tv_dur.set(request.message)
		elif rtype == Scanmon.MonitorRequest.REQUESTS['SETSYSDISP']:
			self.tv_sys.set(request.message['system'])
			self.tv_grp.set(request.message['group'])
			self.tv_chn.set(request.message['channel'])
			self.tv_dur.set(request.message['duration'])
			self.tv_time.set(request.message['starttime'])
			self.tv_frq.set(request.message['frequency'])

	def send_cmd(self, cmd):
		self.to_mon_queue.put(Scanmon.MonitorRequest(Scanmon.MonitorRequest.REQUESTS['CMD'], cmd))

	def set_vol(self):
		self.send_cmd('VOL,{}'.format(self.tv_vol.get()))
		if self.isMute:
			self.isMute = False
			self.tv_mute.set('Mute')
			self.set_status('Unmute')

	def set_sql(self):
		self.send_cmd('SQL,{}'.format(self.tv_sql.get()))
	
	def cmd_status(self, cmd, status):
		self.send_cmd(cmd)
		self.set_status(status)

	def do_lockout(self):
		self.cmd_status('KEY,L,P', 'Lockout sent')

	def do_skip(self):
		self.cmd_status('KEY,>,P', 'Skip sent')

	def do_hold(self):
		self.cmd_status('KEY,H,P', 'Hold sent')

	def do_scan(self):
		self.cmd_status('KEY,S,P', 'Scan sent')

	def do_bookmark(self):
		self.set_status('Commanded to Bookmark')

	def do_mute(self):
		self.set_status('Commanded to Mute')
		if self.isMute:	# Unmute
			self.tv_vol.set(oVol)
			self.set_vol()
			self.set_status('Unmute')
		else:		# Mute
			self.oVol = self.tv_vol.get()
			self.tv_vol.set('0')
			self.send_cmd('VOL,0')
			self.isMute = True
			self.tv_mute.set('Unmute')
			self.set_status('Mute')

	def do_mode(self):
		self.set_status('Commanded to Mode')

	def do_showlog(self):
		self.set_status('Commanded to Show Log')

	def do_prefs(self):
		self.set_status('Commanded to Prefs')

	def do_close(self):
		self.set_status('Closing...')
		self.run_app = False
		self.thr_monitor.do_stop()
		self.thr_monitor.join(timeout = 5)

	# Set up logging (based on Logging tutorial (file:///Users/dad/Dropbox/Documents/Python/python-3.3.2-docs-html/howto/logging.html#logging-basic-tutorial)

	def buildWindow(self):
		self.master.title('Scanmon - Uniden scanner monitor')
		self.master.resizable(False, False)

		self.configure(padding = (5, 10))
		self.grid(column = 0, row = 0, sticky = (N, E, W, S))

		# Text variables used below
		self.tv_hold_resume = StringVar(value = 'Hold')
		self.tv_hold_b = False
		self.tv_mute = StringVar(value = 'Mute')
		#tv_start = StringVar(value = 'Start')
		self.tv_status = StringVar()

		# Define the buttons

		b_lockout = ttk.Button(self, text = 'Lockout', width = 8, command = self.do_lockout)
		b_skip = ttk.Button(self, text = 'Skip', width = 8, command = self.do_skip)
		b_hold_resume = ttk.Button(self, 
			textvariable = self.tv_hold_resume, width = 8, command = self.do_hold)
		b_scan = ttk.Button(self, text = 'Scan', width = 8, command = self.do_scan)
		b_bookmark = ttk.Button(self, text = 'Bookmark', width = 8, command = self.do_bookmark)
		b_mute = ttk.Button(self, textvariable = self.tv_mute, width = 8, command = self.do_mute)
		b_mode_select = ttk.Button(self, text = 'Mode Select', command = self.do_mode)
		b_view_log = ttk.Button(self, text = 'View Log', width = 8, command = self.do_showlog)
		b_prefs = ttk.Button(self, text = 'Prefs', width = 8, command = self.do_prefs)
		b_close = ttk.Button(self, text = 'Close', width = 8, command = self.do_close)
		#b_start = ttk.Button(self, textvariable = self.tv_start, width = 8, command = do_start)

		# Sizegrip
		#b_sizegrip = ttk.Sizegrip(root)

		# Static labels
		l_rcv = ttk.Label(self, text = 'Rcv:')
		l_vol = ttk.Label(self, text = 'Volume:')
		l_sql = ttk.Label(self, text = 'Squelch:')

		# Define Data Display Styles
		#s_ddisp = ttk.Style()
		#s_ddisp.configure('DDisp.TLabel', 

		# Data Display labels

		# l_rcv_ind must be accessible later
		self.l_rcv_ind = ttk.Label(self, text = '    ', background = '#00e')
		
		lf_sys = ttk.LabelFrame(self, text = 'System', padding = (5, 0))
		self.tv_sys = StringVar()
		l_sys = ttk.Label(lf_sys, textvariable = self.tv_sys, width = 16)
		lf_grp = ttk.LabelFrame(self, text = 'Group', padding = (5, 0))
		self.tv_grp = StringVar()
		l_grp = ttk.Label(lf_grp, textvariable = self.tv_grp, width = 16)
		lf_chn = ttk.LabelFrame(self, text = 'Channel', padding = (5, 0))
		self.tv_chn = StringVar()
		l_chn = ttk.Label(lf_chn, textvariable = self.tv_chn, width = 16)
		c_frq = ttk.Frame(self)
		lf_frq = ttk.LabelFrame(c_frq, text = 'Freq/TGID', padding = (5, 0))
		self.tv_frq = StringVar()
		l_frq = ttk.Label(lf_frq, textvariable = self.tv_frq, width = 10, anchor = E)
		#l_mhz = ttk.Label(c_frq, text = 'MHz')
		c_dur = ttk.Frame(self)
		lf_dur = ttk.LabelFrame(c_dur, text = 'Duration', padding = (5, 0))
		self.tv_dur = StringVar()
		l_dur = ttk.Label(lf_dur, textvariable = self.tv_dur, width = 10, anchor = E)
		l_secs = ttk.Label(c_dur, text = 'Secs')
		lf_time = ttk.LabelFrame(self, text = 'Start Time', padding = (5, 0))
		self.tv_time = StringVar()
		l_time = ttk.Label(lf_time, textvariable = self.tv_time, width = 16, anchor = E)
		lf_status = ttk.LabelFrame(self, text = 'Status')
		l_status = ttk.Label(lf_status, textvariable = self.tv_status)
		self.tv_model = StringVar()
		l_model = ttk.Label(self, textvariable = self.tv_model)
		self.tv_version = StringVar()
		l_version = ttk.Label(self, textvariable = self.tv_version)

		# Grid the labels into the frames
		l_sys.grid(column = 0, row = 0)
		l_grp.grid(column = 0, row = 0)
		l_chn.grid(column = 0, row = 0)
		l_frq.grid(column = 0, row = 0)
		l_dur.grid(column = 0, row = 0)
		l_time.grid(column = 0, row = 0)

		# The spinboxes
		self.tv_vol = StringVar()
		s_vol = Spinbox(self, from_ = 0, to = 29, increment = 1, justify = RIGHT,
			state = 'readonly', width = 4, textvariable = self.tv_vol, command = self.set_vol)
		self.tv_sql = StringVar()
		s_sql = Spinbox(self, from_ = 0, to = 19, increment = 1, justify = RIGHT,
			state = 'readonly', width = 4, textvariable = self.tv_sql, command = self.set_sql)

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
		b_prefs.grid(column = 5, row = 8, sticky = W)
		b_close.grid(column = 6, row = 8, sticky = W)
		l_rcv.grid(column = 4, row = 0, columnspan = 1, sticky = E)
		self.l_rcv_ind.grid(column = 5, row = 0, columnspan = 1, sticky = W)
		lf_sys.grid(column = 5, row = 1, columnspan = 2, sticky = W)
		lf_grp.grid(column = 5, row = 2, columnspan = 2, sticky = W)
		lf_chn.grid(column = 5, row = 3, columnspan = 2, sticky = W)
		c_frq.grid(column = 5, row = 4, columnspan = 2, sticky = W)
		lf_frq.grid(column = 0, row = 0)
		#l_mhz.grid(column = 1, row = 0, sticky = (W, S))
		c_dur.grid(column = 5, row = 5, sticky = W)
		lf_dur.grid(column = 0, row = 0)
		l_secs.grid(column = 1, row = 0, sticky = (W, S))
		lf_time.grid(column = 5, row = 6, columnspan = 2, sticky = W)
		#b_start.grid(column = 5, row = 8, rowspan = 2)
		lf_status.grid(column = 0, row = 10, columnspan = 7, sticky = EW)
		l_status.grid(column = 0, row = 0, sticky = EW)
		l_model.grid(column = 0, row = 11, sticky = E, columnspan = 4)
		l_version.grid(column = 5, row = 11, sticky = W, columnspan = 2)

		# Window is not resizable but if it were this is how we would show it
		#b_sizegrip.grid(column = 1, row = 1)

		#root.columnconfigure(0, weight = 1)
		#root.rowconfigure(0, weight = 1)

		self.rowconfigure(7, pad=10)
		self.rowconfigure(8, pad=10)
		self.rowconfigure(9, pad=10)

		self.set_status('Ready!')
		
		# END buildWindow

	# Start it all up!
	
	def runit(self):
	
		barrier = Barrier(2, timeout = 10)

		self.thr_monitor = Scanmon.Monitor(
			self.scanner, 
			self.to_mon_queue, 
			self.from_mon_queue, 
			barrier, 
			name = 'Monitor', )
		self.thr_monitor.start()
		barrier.wait()

		self.tv_model.set('Model {}'.format(self.thr_monitor.scanner.MDL))
		self.tv_version.set(self.thr_monitor.scanner.VER)
		self.logger.info('Scanner Model: %s, Version: %s', 
			self.thr_monitor.scanner.MDL, 
			self.thr_monitor.scanner.VER)

		while self.run_app:		# Util we are done ...
			if not self.thr_monitor.isAlive():
				self.run_app = False
				self.logger.critical('Monitor thread died! Quitting...')
			self.update()
			try:
				request = self.from_mon_queue.get(timeout = 0.1)
				self.run_request(request)
			except Empty:
				pass

# END class Scanmon

if __name__ == '__main__':
	mon = Scanmon()
	mon.runit()