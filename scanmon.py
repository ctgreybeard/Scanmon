#!/usr/bin/env python3
'''
Scanner monitor - Shows scanner activity in a window with some controls
'''

import re, types, time, sys, logging
from logging.handlers import SysLogHandler
from datetime import datetime
from scanner import Scanner, Decode
from tkinter import *
from tkinter import ttk
from threading import Thread, Barrier
from queue import Queue, Empty

class Scanmon(ttk.Frame):

	logName = 'scanmon'
#	logLevel = logging.DEBUG
	logLevel = logging.WARNING
	
	class MonitorRequest:
	
		REQUESTS = {	
			# 1-99 to Monitor
			'CMD': 1,	# Send scanner command ->Monitor
			'MCMD': 2,	# Multi-command request
			# 200-299 to Application
			'RPC': 200,
			'CALLBACK' : 201,
			'SETSYSDISP': 206, 	# Set received system display
		}
	
		def __init__(self, req_type, message, rpc = None, response = None, callback = None, **kw):
			self.req_type = req_type
			self.orig_type = None
			self.response = response
			self.callback = callback
			self.rpc = rpc
			self.message = message
			self.kw = kw
		
		def __str__(self):
			return 'Type:{}, message={}, kw={}, orig_type={}, response={}, callback={}'.format(self.req_type, self.message, self.kw, self.orig_type, self.response, self.callback)

	# END class MonitorRequest
	
	class Monitor(Thread):

		def __init__(self, mainwin, scanner, my_queue, their_queue, barrier, *args, **kw):
			Thread.__init__(self, **kw)
			self.mainwin = mainwin
			self.my_queue = my_queue		# Messages TO the Monitor
			self.their_queue = their_queue	# Messages FROM the Monitor
			self.scanner = scanner
			# Set some local tracking variables, guaranteed not to match at startup
			self.tv_vol = ['', 'RPC', self.mainwin.tv_vol.set]
			self.tv_sql = ['', 'RPC', self.mainwin.tv_sql.set]
			self.tv_hold_resume = ['', 'RPC', self.mainwin.tv_hold_resume.set]
			self.tv_rcv_ind = ['', 'RPC', self.mainwin.set_rcv_ind]
			self.tv_sys_disp = [{
				'system': '',
				'group':  '',
				'channel': '',
				'frequency': '',
				'starttime': '',
			}, 'RPC', self.mainwin.set_sys_disp]
			self.tv_dur = ['', 'RPC', self.mainwin.tv_dur.set]
			self.cur_frq = ''
			self.start_time = None
			self.logger = logging.getLogger(Scanmon.logName + '.monitor')
			#self.logger.setLevel(Scanmon.logLevel)
			self.logger.info('Monitor initialized')
			self.barrier = barrier
			self.drainMax = 3	# Max drain count
			self.drainCount = 0
	
		def queue_message(self, type, message, rpc = None, request = None, **kw):
			if request is None:		# No current request, make a new one
				request = Scanmon.MonitorRequest(type, message, rpc = rpc, **kw)
			else:
				request.orig_type = request.req_type	# Save the original type
				request.req_type = type
				request.message = message
				request.kw = kw
			
			self.logger.debug('Queueing msg: %s', str(request))
			self.their_queue.put(request)
		
		def send_status(self, status):
			self.logger.info('Set Status: %s', status)
			self.queue_message(Scanmon.MonitorRequest.REQUESTS['RPC'], status, rpc = self.mainwin.set_status)

		def set_it(self, it, val):
			self.logger.debug('set_it: it={}, val={}'.format(it, val))
			if it[0] != val:
				it[0] = val
				if it[1] == 'RPC':
					self.queue_message(Scanmon.MonitorRequest.REQUESTS[it[1]], val, rpc = it[2])
				else:
					self.queue_message(Scanmon.MonitorRequest.REQUESTS[it[1]], val)

		def set_vol(self, vol):
			self.set_it(self.tv_vol, vol)

		def set_sql(self, sql):
			self.set_it(self.tv_sql, sql)

		def send_rcv_ind(self, ind):
			self.set_it(self.tv_rcv_ind, ind)

		def set_dur(self, dur):
			self.set_it(self.tv_dur, dur)

		def send_sys_disp(self, **disp):
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
			resp = '?'
			try:
				resp = self.send_cmd('STS')
				l1 = resp['L1_CHAR']
				is_hold = 'Resume' if l1.startswith(' ????') else 'Hold'
				if is_hold != self.tv_hold_resume[0]:
					self.send_status('Run' if is_hold == 'Hold' else 'Hold')
				self.set_it(self.tv_hold_resume, is_hold)
			except KeyError:
				self.logger.warning('STS returned: "%s"', str(resp))

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
			self.drainCount += 1
			if self.drainCount > self.drainMax:
				self.logger.critical('Drain count exceeded')
				self.do_stop()
			else:
				self.send_status('Draining at {}'.format(datetime.today().strftime('%m/%d/%y %H:%M:%S')))
				self.scanner.drain()
				self.logger.warning('Drained')
	
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
				time.sleep(0.5)		# Give others time to run

		def run(self):	# Overrides the default Thread run (which does nothing)
	
			self.start_time = None
			self.now_time = datetime.today()
			self.cur_frq = ''
			self.logger.info('Monitor starting')
			self.send_status('Monitor starting')
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
						self.send_rcv_ind('#e00')
						self.cur_frq = ''
						self.start_time = None
					elif resp['FRQ_TGID'] != '':
						now_time = datetime.today()	# Capture the moment
						this_frq = eval(resp['FRQ_TGID'])
						if self.cur_frq == this_frq:	# Same frequency
							self.set_dur(str(int((now_time - self.start_time).total_seconds())))
						else:
							self.start_time = now_time
							self.send_rcv_ind('#0e0')
							self.cur_frq = this_frq
							self.send_sys_disp(
								frequency = this_frq,
								system = resp['NAME1'],
								group = resp['NAME2'],
								channel = resp['NAME3'],
								duration = '0',
								starttime = now_time.strftime('%m/%d/%y %H:%M:%S'))
							self.set_dur('0')
					else: 
						self.send_status('No SQL and no FRQ/TGID??')
				except KeyError:
					self.logger.error('Bad response from GLG: %s', str(resp))
					self.send_status('Bad response from GLG')
					self.drain()

				try:
					while True:
						self.do_message(self.my_queue.get(block = False))
				except Empty:
					pass
				
				# Finally, wait a bit to lessen the load
				time.sleep(0.5)

		def do_stop(self):
			self.send_status('Monitor ending')
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

		# Create SysLog handler and set level
		slh = SysLogHandler(address='/var/run/syslog')
		slh.setLevel(self.logLevel)
		slh.ident = Scanmon.logName

		# Create formatter
		formatter = logging.Formatter(fmt = '{asctime} - {name} - {levelname} - {message}',
			style = '{')

		# Add formatter to ch
		ch.setFormatter(formatter)

		# Add formatter to slh
		slh.setFormatter(formatter)

		self.logger.addHandler(ch)
		self.logger.addHandler(slh)
		
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

	def set_sys_disp(self, disp):
		try:
			self.tv_sys.set(disp['system'])
			self.tv_grp.set(disp['group'])
			self.tv_chn.set(disp['channel'])
			self.tv_dur.set(disp['duration'])
			self.tv_time.set(disp['starttime'])
			self.tv_frq.set(disp['frequency'])
		except KeyError:
			self.logger.warning('Key Error in SETSYSDISP: %s', disp)

	def run_request(self, request):
		self.logger.debug('Running req: %s', str(request))
		rtype = request.req_type
		if rtype == Scanmon.MonitorRequest.REQUESTS['RPC']:
			request.rpc(request.message, **request.kw)
		else:
			self.logger.warning('Unknown RPC request type: %s', rtype)

	def send_cmd(self, cmd):
		self.to_mon_queue.put(Scanmon.MonitorRequest(Scanmon.MonitorRequest.REQUESTS['CMD'], cmd))

	def set_vol(self):
		self.send_cmd('VOL,{}'.format(self.tv_vol.get()))
		if self.isMute and int(self.tv_vol.get()) > 0:
			self.isMute = False
			self.tv_mute.set('Mute')
			self.set_status('Unmute')

	def set_sql(self):
		self.send_cmd('SQL,{}'.format(self.tv_sql.get()))
	
	def set_rcv_ind(self, val):
		self.l_rcv_ind.configure(background = val)
	
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
			self.tv_vol.set(self.oVol)
			self.set_vol()
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

		# Static labels
		l_rcv = ttk.Label(self, text = 'Rcv:')
		l_vol = ttk.Label(self, text = 'Volume:')
		l_sql = ttk.Label(self, text = 'Squelch:')

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
		s_vol = Spinbox(self, from_ = 0, to = 29, increment = 1, 
			justify = RIGHT, width = 4, repeatdelay = 6000, repeatinterval = 1000,
			state = 'readonly', textvariable = self.tv_vol, command = self.set_vol)
		self.tv_sql = StringVar()
		s_sql = Spinbox(self, from_ = 0, to = 19, increment = 1, 
			justify = RIGHT, width = 4, repeatdelay = 6000, repeatinterval = 1000,
			state = 'readonly', textvariable = self.tv_sql, command = self.set_sql)

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

		self.rowconfigure(7, pad=10)
		self.rowconfigure(8, pad=10)
		self.rowconfigure(9, pad=10)

		self.set_status('Ready!')
		
		# END buildWindow

	# Start it all up!
	
	def runit(self):
	
		barrier = Barrier(2, timeout = 10)

		self.thr_monitor = Scanmon.Monitor(
			self,					# Master
			self.scanner,			# Scanner
			self.to_mon_queue,		# To queue
			self.from_mon_queue,	# From queue
			barrier,				# Barrier
			name = 'Monitor', )
		self.thr_monitor.start()
		barrier.wait()

		self.tv_model.set('Model {}'.format(self.thr_monitor.scanner.MDL))
		self.tv_version.set(self.thr_monitor.scanner.VER)
		self.logger.info('Scanner Model: %s, Version: %s', 
			self.thr_monitor.scanner.MDL, 
			self.thr_monitor.scanner.VER)

		try:
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
		except:
			dumpit = sys.exc_info()
			self.logger.critical('Failed', exc_info = dumpit)
			self.do_close()
			self.quit()
			
# END class Scanmon

if __name__ == '__main__':
	mon = Scanmon()
	mon.runit()