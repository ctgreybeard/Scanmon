#!/usr/bin/env python3
'''
Scanner monitor - Shows scanner activity in a window with some controls
'''

import re, types, threading
from scanner import Scanner
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

def check_sql()
	check_spin(tv_sql, 'SQL', 'LEVEL')

def setfrom_spin(tv, cmd):
	sval = int(tv.get())
	resp = scanner.cmd('{},{:02d}'.format(cmd, sval), Scanner.DECODED)
	assert not resp['iserror'], '{} command failed: {}'.format(cmd, Scanner.ERRORMSG[resp[ERRORCODEKEY]])

def set_vol():
	setfrom_spin(tv_vol, 'VOL')

def set_sql()
	setfrom_spin(tv_sql, 'SQL')

def check_hold():
	pass

root = Tk()	# Root window
mainframe = ttk.Frame(root, padding = (5, 10))
mainframe.grid(column = 0, row = 0, sticky = (N, E, W, S))

# Text variables used below
tv_hold_resume = StringVar(value = 'Hold')

# Define the buttons

b_lockout = ttk.Button(mainframe, text = 'Lockout', width = 8)
b_skip = ttk.Button(mainframe, text = 'Skip', width = 8)
b_hold_resume = ttk.Button(mainframe, textvariable = tv_hold_resume, width = 8)
b_scan = ttk.Button(mainframe, text = 'Scan', width = 8)
b_bookmark = ttk.Button(mainframe, text = 'Bookmark', width = 8)
b_mute = ttk.Button(mainframe, text = 'Mute', width = 8)
b_mode_select = ttk.Button(mainframe, text = 'Mode Select')
b_view_log = ttk.Button(mainframe, text = 'View Log', width = 8)
b_prefs = ttk.Button(mainframe, text = 'Prefs', width = 8)
b_close = ttk.Button(mainframe, text = 'Close', width = 8)
b_start = ttk.Button(mainframe, text = 'Start', width = 8)

# Sizegrip
b_sizegrip = ttk.Sizegrip(mainframe)

# Static labels
l_rcv = ttk.Label(mainframe, text = 'Rcv:')
l_vol = ttk.Label(mainframe, text = 'Volume:')
l_sql = ttk.Label(mainframe, text = 'Squelch:')

# Define Data Display Styles
#s_ddisp = ttk.Style()
#s_ddisp.configure('DDisp.TLabel', 

# Data Display labels

l_rcv_ind = ttk.Label(mainframe, text = '    ', background = '#0E0')
lf_sys = ttk.LabelFrame(mainframe, text = 'System')
tv_sys = StringVar()
l_sys = ttk.Label(lf_sys, textvariable = tv_sys, width = 16)
lf_grp = ttk.LabelFrame(mainframe, text = 'Group')
tv_grp = StringVar()
l_grp = ttk.Label(lf_grp, textvariable = tv_grp, width = 16)
lf_chn = ttk.LabelFrame(mainframe, text = 'Channel')
tv_chn = StringVar()
l_chn = ttk.Label(lf_chn, textvariable = tv_chn, width = 16)
c_frq = ttk.Frame(mainframe)
lf_frq = ttk.LabelFrame(c_frq, text = 'Frequency')
tv_frq = StringVar()
l_frq = ttk.Label(lf_frq, textvariable = tv_frq, width = 9)
l_mhz = ttk.Label(c_frq, text = 'MHz')
c_dur = ttk.Frame(mainframe)
lf_dur = ttk.LabelFrame(c_dur, text = 'Duration')
tv_dur = StringVar()
l_dur = ttk.Label(lf_dur, textvariable = tv_dur, width = 5)
l_secs = ttk.Label(c_dur, text = 'Secs')
lf_time = ttk.LabelFrame(mainframe, text = 'Time')
tv_time = StringVar()
l_time = ttk.Label(lf_time, textvariable = tv_time, width = 17)
lf_status = ttk.LabelFrame(mainframe, text = 'Status')
tv_status = StringVar()
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
s_vol = Spinbox(mainframe, from_ = 0, to = 29, increment = 1, justify = LEFT,
	state = 'readonly', width = 4, textvariable = tv_vol, command = set_vol)
tv_sql = StringVar()
s_sql = Spinbox(mainframe, from_ = 0, to = 19, increment = 1, justify = LEFT,
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
tv_status.set("Ready")
#b_sizegrip.grid(column = 7, row = 11)

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

# Start it all up!
root.mainloop()
