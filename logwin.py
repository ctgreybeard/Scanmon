#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk

import random, time

class HitDesc:
	'''Hold pertinent information for each System/Group/Channel found.

	'''
	
	def __init__(self, system, group, channel, freq, duration, logger = None):
		'''Builds the basic "Hit" object.

		Arguments:
		system -- The System name from the scanner
		group -- The Group name from the scanner
		channel -- The Channel name from the scanner
		freq -- The channel frequency or TGID from the scanner
			Note: The frequency is used for conventional channels and the
			TGID is used for trunked systems.
		duration -- The current duration of the transmission

		'''

		self.logger = logger

		self.system = system.strip()
		self.group = group.strip()
		self.channel = channel.strip()
		self.freq = str(freq).strip()
		self.count = 1
		self.duration = duration
		self.last = time.strftime('%m/%d/%Y %H:%M:%S')
		self.key = self.genKey(self.system, self.group, self.channel, self.freq)
		self.contentRow = None

		if self.logger:
			self.logger.debug('HitDesc.__init__: HitDesc (%s) created', self.key)

	def bumpCount(self, dur):
		'''Increase the internal counter by one and add the duration to the existing value

		Arguments:
		dur - The additional duration

		'''
		#print('Bump instance')
		self.count += 1
		self.last = time.strftime('%m/%d/%Y %H:%M:%S')
		self.duration += dur
		if self.contentRow is not None:
			#print('Bump row')
			self.contentRow.tvCnt.set(self.count)
			self.contentRow.tvLst.set(self.last)
			self.contentRow.tvDur.set(self.duration)

		if self.logger:
			self.logger.debug('HitDesc.bumpCount: HitDesc (%s) bumped: cnt=%s, dur = %s', 
				self.key, self.count, self.duration)

	def genKey(self, system, group, channel, freq):
		'''Generate the unique key associated with the System/Group/Channel

		To generate the key each component (System, Group, Channel) is set to lower case
		and any whitespace prefix or suffix is removed. The triple is then separated
		with colons (':') and returned as the key. The freq argument is  
		silently ignored in the current implementation.

		Within the scanner System, Group, and Channel names are usually in mixed case
		and have trailing spaces to pad them to 16 characters.

		'''

		key = '{}:{}:{}'.format(system.lower().strip(), group.lower().strip(), channel.lower().strip())

		if self.logger:
			self.logger.debug('HitDesc.genKey: From %s, %s, %s, %s generated key=%s', system, group, channel, freq, key)

		return key

# END class HitDesc

class LogWin(tk.Toplevel):

	'''Build, display, and update the Log display window.

	This class is used by the ScanMon package to display the "Hits Log" from the scanner.
	Each System/Group/Channel combination is tracked separately showing the frequency,
	number of transmissions (count), and the total duration of the receptions.

	'''

	WIDTHSYS = 16
	WIDTHGRP = 16
	WIDTHCHN = 16
	WIDTHFRQ = 9
	WIDTHDUR = 4
	WIDTHCNT = 4
	WIDTHLST = 17
	LABELPAD = 2
	LABELBG = '#eef'
	LABELBORDER = 1
	LABELRELIEF = tk.RAISED
	CONTENTPAD = 2
	CONTENTBG = '#ffe'
	CONTENTBORDER = 1
	CONTENTRELIEF = tk.RIDGE
	DECORATIONPAD = 2
	DECORATIONBG = '#eff'
	DECORATIONBORDER = 2
	DECORATIONRELIEF = tk.RAISED

	class ContentRow(ttk.Frame):
		'''Build a ttk.Frame which holds the cells containing the values from the HitDesc

		'''

		def __init__(self, master, desc, logger = None, **kw):
			'''Build the Frame (self) and fill it'''

			ttk.Frame.__init__(self, master, **kw)

			self.logger = logger

			self.tvSys = tk.StringVar()
			self.tvSys.set(desc.system)
			self.tvGrp = tk.StringVar()
			self.tvGrp.set(desc.group)
			self.tvChn = tk.StringVar()
			self.tvChn.set(desc.channel)
			self.tvFrq = tk.StringVar()
			self.tvFrq.set(desc.freq)
			self.tvCnt = tk.StringVar()
			self.tvCnt.set(desc.count)
			self.tvDur = tk.StringVar()
			self.tvDur.set(desc.duration)
			self.tvLst = tk.StringVar()
			self.tvLst.set(desc.last)
			self.key = desc.key
			self.desc = desc
			desc.contentRow = self

			if self.logger:
				self.logger.debug('ContentRow.__init__: And another data row(%s) springs to life!', self.desc.key)

			lSys = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvSys,
				width = LogWin.WIDTHSYS)
			lGrp = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvGrp,
				width = LogWin.WIDTHGRP)
			lChn = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvChn,
				width = LogWin.WIDTHCHN)
			lFrq = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvFrq,
				width = LogWin.WIDTHFRQ)
			lDur = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvDur,
				width = LogWin.WIDTHDUR,
				anchor = tk.E)
			lCnt = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvCnt,
				width = LogWin.WIDTHCNT,
				anchor = tk.E)
			lLst = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvLst,
				width = LogWin.WIDTHLST)

			lSys.grid(column = 0, row = 0, sticky = (tk.EW, tk.N))
			lGrp.grid(column = 1, row = 0, sticky = (tk.EW, tk.N))
			lChn.grid(column = 2, row = 0, sticky = (tk.EW, tk.N))
			lFrq.grid(column = 3, row = 0, sticky = (tk.EW, tk.N))
			lDur.grid(column = 4, row = 0, sticky = (tk.EW, tk.N))
			lCnt.grid(column = 5, row = 0, sticky = (tk.EW, tk.N))
			lLst.grid(column = 6, row = 0, sticky = (tk.EW, tk.N))

		def destroy(self):
			'''Called to destroy the ContentRow when the window is closed

			Ensures that the contained HitDesc is disconnected from this (soon to die)
			ContentRow.

			'''

			if self.logger:
				self.logger.debug('ContentRow.destroy: And another data row(%s) dies an inglorius death!', self.desc.key)

			self.desc.contentRow = None
			self.desc = None
			ttk.Frame.destroy(self)

	# END class ContentRow
	
	# BEGIN class LogWin

	def __init__(self,  *args, logger = None, **kw):
		'''Create and initialize the log display window'''
		
		tk.Toplevel.__init__(self, *args, **kw)
		
		self.logger = logger
		if self.logger:
			self.logger.debug('LogWin.__init__: Creating LogWin')

		self.mstyle = ttk.Style()	# Master style instance for configuration

		self.master.columnconfigure(0, weight = 1)
		self.master.rowconfigure(0, weight = 1)

		self.winfo_toplevel().resizable(width = False, height = True)

		self.columnconfigure(0, weight = 1)
		self.columnconfigure(1, weight = 0)
		self.rowconfigure(0, weight = 0)
		self.rowconfigure(1, weight = 1)
		self.rowconfigure(2, weight = 0)

		# The necessary widgets
		ttk.Sizegrip(self).grid(column = 1, row = 2)
		ttk.Button(self, 
			text = 'Close', 
			command =  self.doClose, 
			style = 'LogWin.TButton').grid(
				column = 0, 
				row = 2, 
				padx = LogWin.DECORATIONPAD, 
				pady = LogWin.DECORATIONPAD)

		self.mstyle.configure('Cframe.TFrame',
			border = 2)

		self.mstyle.configure('Clabel.TLabel',
			border = LogWin.LABELBORDER,
			background = LogWin.LABELBG,
			relief = LogWin.LABELRELIEF,
			padding = LogWin.LABELPAD,
			)

		self.mstyle.configure('Data.TLabel',
			border = LogWin.CONTENTBORDER,
			background = LogWin.CONTENTBG,
			relief = LogWin.CONTENTRELIEF,
			padding = LogWin.CONTENTPAD,
			)

		self.mstyle.configure('LogWin.TButton',
			border = LogWin.DECORATIONBORDER,
			background = LogWin.DECORATIONBG,
			relief = LogWin.DECORATIONRELIEF,
			padding = LogWin.DECORATIONPAD,
			)

		labelRow = ttk.Frame(self, style = 'Cframe.TFrame')
		labelRow.grid(column = 0, row = 0, sticky = tk.EW)
		labelSys = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'System', width = LogWin.WIDTHSYS)
		labelGrp = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Group', width = LogWin.WIDTHGRP)
		labelChn = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Channel', width = LogWin.WIDTHCHN)
		labelFrq = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Freq/TGID', width = LogWin.WIDTHFRQ)
		labelDur = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Dur', width = LogWin.WIDTHDUR)
		labelCnt = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Cnt', width = LogWin.WIDTHCNT)
		labelLst = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Last', width = LogWin.WIDTHLST)

		labelSys.grid(column = 0, row = 0, sticky = (tk.EW))
		labelGrp.grid(column = 1, row = 0, sticky = (tk.EW))
		labelChn.grid(column = 2, row = 0, sticky = (tk.EW))
		labelFrq.grid(column = 3, row = 0, sticky = (tk.EW))
		labelDur.grid(column = 4, row = 0, sticky = (tk.EW))
		labelCnt.grid(column = 5, row = 0, sticky = (tk.EW))
		labelLst.grid(column = 6, row = 0, sticky = (tk.EW))

		self.contentFrame = ttk.Frame(self, style = 'Cframe.TFrame')
		self.contentFrame.grid(column = 0, row = 1, sticky = (tk.EW, tk.N))

		# Row data dictionary
		self.rowData = {}

	def add(self, desc):
		'''Request to add a Hit (desc) to the Log window
		
		If the Hit, as defined by its key, already is displayed in the window then
		a 'bump' is performed which updates the hit count and total duration.
		
		Otherwise a new ContentRow is created and added to the content Frame and the entire
		set of hits is sorted and displayed in key order.
		
		'''
		
		if self.logger:
			self.logger.debug('LogWin.add: Adding %s', desc.key)
			desc.logger = self.logger	# You belong to us now

		if desc.key in self.rowData:	# We already have one of these ...
			if self.logger:
				self.logger.debug('LogWin.add: Exists, bumping')
			thisrow = self.rowData[desc.key]
			thisrow.desc.bumpCount(desc.duration)

		else:	# Make a new one ...
			if self.logger:
				self.logger.debug('LogWin.add: New, creating row for it')
			thisrow = LogWin.ContentRow(self.contentFrame, desc, logger = self.logger)
			self.rowData[thisrow.key] = thisrow

			# Rearrange the rows by sorted key
			sortedkeys = sorted(self.rowData.keys())

			row = 0
			for r in sortedkeys:
				if self.logger:
					self.logger.debug('LogWin.add: Sort key=%s in row %s', r, row)
				self.rowData[r].grid(column = 0, row = row, sticky = (tk.EW, tk.N))
				row += 1

		return thisrow.desc

	def doClose(self):
		'''Close the Log display window'''
		
		if self.logger:
			self.logger.debug('LogWin.doClose: Closing down ...')
		self.winfo_toplevel().destroy()		# Say goodnight Dick!

# END class LogWin

if __name__ == '__main__':
	import logging
	
	class MainWin(ttk.Frame):
		'''Test bench for LogWin
		
		This also demonstrates how to check for the window display which can be closed
		independently from the application either via the Close button or the "application
		close button" (upper left). This is shown in doGo and doAdd.
		
		'''
	
		def __init__(self, *args, **kw):
			'''Create the test bench main window with three buttons: Go, Add, and Stop'''
			
			ttk.Frame.__init__(self, *args, **kw)

			self.mstyle = ttk.Style()	# Master style instance for configuration

			self.master.columnconfigure(0, weight = 1)
			self.master.rowconfigure(0, weight = 1)
			self.winfo_toplevel().title('Test LogWin class')

			self.columnconfigure(0, weight = 1)
			self.columnconfigure(1, weight = 1)
			self.columnconfigure(2, weight = 1)
			self.rowconfigure(0, weight = 1)
			self.grid(column = 0, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))

			self.grid_propagate(False)

			# Build buttons

			goButton = ttk.Button(self, text = 'Go', width = 8, command = self.doGo)
			goButton.grid(column = 0, row = 0, padx = 5, pady = 5)
			addButton = ttk.Button(self, text = 'Add', width = 8, command = self.doAdd)
			addButton.grid(column = 1, row = 0, padx = 5, pady = 5)
			stopButton = ttk.Button(self, text = 'Stop', width = 8, command = self.doStop)
			stopButton.grid(column = 2, row = 0, padx = 5, pady = 5)

			self.dataDescs = {}
			self.logWin = None
			
			# Set up logging at the DEBUG level
			self.logger = logging.getLogger('TestLog')
			self.logger.setLevel('DEBUG')
			sh = logging.StreamHandler()
			sh.setLevel('DEBUG')
			self.logger.addHandler(sh)
			self.logger.debug('MainWin.__init__: Test for LogWin starting')

		def doGo(self):
			'''Create the LogWin if it's not already up'''
			
			if self.logWin is None or not self.logWin.winfo_exists():
				self.logger.debug('MainWin.doGo: New LogWin')
				self.logWin = LogWin(logger = self.logger)
				self.logWin.title('Test Logging Display')
				for ndesc in list(self.dataDescs.values()):
					self.dataDescs[ndesc.key] = self.logWin.add(ndesc)
				self.winfo_toplevel().lift()
			else:	# Print info about the window. Is it still active?
				self.logger.debug('MainWin.doGo: LogWin exists {}'.format(self.logWin.winfo_exists()))

		def doAdd(self):
			'''Create a test "Hit" with semi-random data. Make an occasional duplicate'''
			
			def rchar():
				'''A random capital letter'''
				
				return chr(ord('A') + random.randint(0, 25))

			if random.randint(0, 3) == 0:
				system = 'S System        '
				group =  'G Group         '
				chan =   'C Chan          '
				freq =   '123.456         '
				dur = random.randint(1,15)
				self.logger.debug('MainWin.doAdd: Gen DUP(%s,%s,%s,%s), dur=%s', 
					system, group, chan, freq, dur)
			else:
				system = rchar() + ' System        '
				group = rchar()  + ' Group         '
				chan = rchar()   + ' Chan          '
				freq = str(random.randint(101, 199)).strip() + '.' + str(random.randint(1, 99)).strip()
				dur = random.randint(1,15)
				self.logger.debug('MainWin.doAdd: Gen NEW(%s,%s,%s,%s), dur=%s', 
					system, group, chan, freq, dur)

			ndesc = HitDesc(system, group, chan, freq, dur, logger = self.logger)
			ndesckey = ndesc.key
			self.logger.debug('MainWin.doAdd: Create HitDesc({})'.format(ndesckey))
			if self.logWin is None or not self.logWin.winfo_exists():	# Keep our own internal list
				if ndesckey in self.dataDescs:	# We have one of these
					action = 'Bump'
					self.dataDescs[ndesckey].bumpCount(dur)
				else:
					action = 'Insert'
					self.dataDescs[ndesckey] = ndesc
			else:
				action = 'Add'
				self.dataDescs[ndesckey] = self.logWin.add(ndesc)

			self.logger.debug('MainWin.doAdd: {} {}, count={}, dur={}, last={}'.format(
				action,
				ndesckey,
				self.dataDescs[ndesckey].count,
				self.dataDescs[ndesckey].duration,
				self.dataDescs[ndesckey].last))

		def doStop(self):
			'''Shut down, I guess we're done ...'''
			
			self.logger.debug('MainWin.doStop: Commanded to Stop!')
			self.quit()

	w = MainWin(width = 300, height = 200)
	w.mainloop()