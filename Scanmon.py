#!/usr/bin/env python3
'''
Scanner monitor - Shows scanner activity in a window with some controls
'''

import re, types, threading, time, datetime
from scanner import Scanner, Decode
from tkinter import *
from tkinter import ttk

# All routines are defined here

def check_spin(tv, cmd, var):
	resp = scanner.cmd(cmd, Scanner.DECODED)
	assert not resp['iserror'], '{} command failed'.format(cmd)
	try:
		aval = int(resp[var])	# Actual Volume
		sval = int(tv.get())
		if aval != sval:
			tv.set(aval)
	except: pass

def check_vol():
	check_spin(tv_vol, 'VOL', 'LEVEL')

def check_sql():
	check_spin(tv_sql, 'SQL', 'LEVEL')

def send_cmd(cmd):
	#print('Sending command:', scmd)
	resp = scanner.cmd(cmd, Scanner.DECODED)
	if resp['iserror']:
		print('{} command failed: {}'.format(cmd, Decode.ERRORMSG[resp[Decode.ERRORCODEKEY]]))
	return resp

def set_vol():
	global isMute
	send_cmd('VOL,{}'.format(tv_vol.get()))
	if isMute:
		isMute = False
		tv_mute.set('Mute')
		tv_status.set('Unmute')

def set_sql():
	send_cmd('SQL,{}'.format(tv_sql.get()))

def check_hold():
	global tv_hold_b
	l1 = send_cmd('STS')['L1_CHAR']
	is_hold = True if l1.startswith(' ????') else False
	if is_hold != tv_hold_b:
		tv_hold_resume.set('Resume' if is_hold else 'Hold')
		tv_hold_b = is_hold
		tv_status.set('Hold' if is_hold else 'Resume')
	
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
	tv_status.set('Closing...')
	#if monitor_running: do_start()
	root.quit()

# Signal to run monitor thread
monitor_running = False
thr_monitor = False

def run_monitor():
	
	loop_count = 0
	start_time = None
	now_time = datetime.datetime.today()
	cur_frq = ''
	tv_status.set('Monitor starting')
	
	while monitor_running:
		if loop_count >= 5:	# Only check every five loops (about one second)
			check_vol()
			check_sql()
			check_hold()
			loop_count = 0
		resp = send_cmd('GLG')
		#print('Got GLG: FRQ={}, MUT={}, SQL={}'.format(resp['FRQ_TGID'], resp['MUT'], resp['SQL']))
		if resp['SQL'] == '' or resp['SQL'] == '0':	# We aren't receiving anything
			l_rcv_ind.configure(background = '#e00')
			#tv_sys.set('')
			#tv_grp.set('')
			#tv_chn.set('')
			#tv_frq.set('')
			#tv_dur.set('')
			#tv_time.set('')
			cur_frq = ''
			start_time = None
		elif resp['FRQ_TGID'] != '':
			now_time = datetime.datetime.today()	# Capture the moment
			this_frq = eval(resp['FRQ_TGID'])
			if cur_frq == this_frq:	# Same frequency
				tv_dur.set(str(int((now_time - start_time).total_seconds())))
			else:
				start_time = now_time
				l_rcv_ind.configure(background = '#0e0')
				cur_frq = this_frq
				tv_frq.set(str(cur_frq))
				tv_sys.set(resp['NAME1'])
				tv_grp.set(resp['NAME2'])
				tv_chn.set(resp['NAME3'])
				tv_dur.set('0')
				tv_time.set(start_time.strftime('%m/%d/%y %H:%M:%S'))
		else: tv_status.set('No SQL and no FRQ')
		loop_count += 1
		time.sleep(0.2)

	tv_status.set('Monitor ending')

def do_start():
	global thr_monitor, monitor_running
	
	if monitor_running: 
		tv_status.set('Commanded to Stop')
		tv_start.set('Start')
		monitor_running = False
		thr_monitor.join(timeout = 3.0)
		if thr_monitor.is_alive():
			tv_status.set('Stop Monitor FAILED')
	else:
		tv_status.set('Commanded to Start')
		tv_start.set('Stop')
		monitor_running = True
		thr_monitor = threading.Thread(target = run_monitor)
		thr_monitor.start()

root = Tk()	# Root window
root.title('Scanmon - Uniden scanner monitor')
root.resizable(False, False)

mainframe = ttk.Frame(root, padding = (5, 10))
mainframe.grid(column = 0, row = 0, sticky = (N, E, W, S))

# Text variables used below
tv_hold_resume = StringVar(value = 'Hold')
tv_hold_b = False
tv_mute = StringVar(value = 'Mute')
tv_start = StringVar(value = 'Start')
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
b_start = ttk.Button(mainframe, textvariable = tv_start, width = 8, command = do_start)

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
b_close.grid(column = 2, row = 9, columnspan = 2)
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
b_start.grid(column = 5, row = 8, rowspan = 2)
lf_status.grid(column = 0, row = 10, columnspan = 7, sticky = EW)
l_status.grid(column = 0, row = 0, sticky = EW)

# Window is not resizable but if it were this is how we would show it
#b_sizegrip.grid(column = 1, row = 1)

root.columnconfigure(0, weight = 1)
root.rowconfigure(0, weight = 1)

mainframe.rowconfigure(7, pad=10)
mainframe.rowconfigure(8, pad=10)
mainframe.rowconfigure(9, pad=10)

scanner = Scanner()
assert scanner.discover(), 'Unable to acquire scanner'

check_vol()
check_sql()
check_hold()

rdy_msg = 'Ready! Model=' + send_cmd('MDL')['MODEL'] + ', Version=' + send_cmd('VER')['VERSION']
tv_status.set(rdy_msg)

# Start it all up!
root.mainloop()
