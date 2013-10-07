#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk

import random, time, copy

class HitDesc:
	'''Hold pertinent information for each System/Group/Channel found.

	'''

	def __init__(self, system, group, channel, freq = 0, duration = 0, logger = None):
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

	def __lt__(self, other):
		if isinstance(other, HitDesc):
			other = other.key
		elif not isinstance(other, str):
			return NotImplemented
		return True if self.key < other else False

	def __le__(self, other):
		if isinstance(other, HitDesc):
			other = other.key
		elif not isinstance(other, str):
			return NotImplemented
		return True if self.key <= other else False

	def __eq__(self, other):
		if isinstance(other, HitDesc):
			other = other.key
		elif not isinstance(other, str):
			return NotImplemented
		return True if self.key == other else False

	def __ne__(self, other):
		if isinstance(other, HitDesc):
			other = other.key
		elif not isinstance(other, str):
			return NotImplemented
		return True if self.key != other else False

	def __gt__(self, other):
		if isinstance(other, HitDesc):
			other = other.key
		elif not isinstance(other, str):
			return NotImplemented
		return True if self.key > other else False

	def __ge__(self, other):
		if isinstance(other, HitDesc):
			other = other.key
		elif not isinstance(other, str):
			return NotImplemented
		return True if self.key >= other else False
	
	def __str__(self):
		return 'Sys={}, Grp={}, Chn={}, Freq={}'.format(
			self.system, self.group, self.channel, self.freq)
	
	def __repr__(self):
		return '<{}(system={}, group={}, channel={}, freq={}, duration={}>'.format(
			self.__class__, self.system, self.group, self.channel, self.freq, self.duration)
			
	def __hash__(self):
		return hash(self.key)

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
	WIDTHSTART = 17
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
	UTILITYPAD = DECORATIONPAD
	UTILITYBG = DECORATIONBG
	UTILITYBORDER = DECORATIONBORDER
	UTILITYRELIEF = tk.FLAT

	SUMMARYMODE = 'Summary'
	DETAILMODE = 'Detail'
	DEFAULTMODE = DETAILMODE

	class SummaryRow(ttk.Frame):
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
				self.logger.debug('SummaryRow.__init__: And another data row(%s) springs to life!', self.desc.key)

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
			'''Called to destroy the SummaryRow when the window is closed

			Ensures that the contained HitDesc is disconnected from this (soon to die)
			SummaryRow.

			'''

			if self.logger:
				self.logger.debug('SummaryRow.destroy: And another data row(%s) dies an inglorius death!', self.desc.key)

			self.desc.contentRow = None
			self.desc = None
			ttk.Frame.destroy(self)

	# END class SummaryRow

	class DetailRow(ttk.Frame):
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
			self.tvDur = tk.StringVar()
			self.tvDur.set(desc.duration)
			self.tvLst = tk.StringVar()
			self.tvLst.set(desc.last)
			self.key = desc.key
			self.desc = desc
			desc.contentRow = self

			if self.logger:
				self.logger.debug('DetailRow.__init__: And another data row(%s) springs to life!', self.desc.key)

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
			lLst = ttk.Label(self, style = 'Data.TLabel',
				textvariable = self.tvLst,
				width = LogWin.WIDTHLST)

			lSys.grid(column = 0, row = 0, sticky = (tk.EW, tk.N))
			lGrp.grid(column = 1, row = 0, sticky = (tk.EW, tk.N))
			lChn.grid(column = 2, row = 0, sticky = (tk.EW, tk.N))
			lFrq.grid(column = 3, row = 0, sticky = (tk.EW, tk.N))
			lDur.grid(column = 4, row = 0, sticky = (tk.EW, tk.N))
			lLst.grid(column = 5, row = 0, sticky = (tk.EW, tk.N))

		def destroy(self):
			'''Called to destroy the DetailRow when the window is closed

			Ensures that the contained HitDesc is disconnected from this (soon to die)
			DetailRow.

			'''

			if self.logger:
				self.logger.debug('DetailRow.destroy: And another data row(%s) dies an inglorius death!', self.desc.key)

			self.desc.contentRow = None
			self.desc = None
			ttk.Frame.destroy(self)

	# END class DetailRow

	# BEGIN class LogWin

	def __init__(self,  *args, detailArray, summaryArray, logger = None, **kw):
		'''Create and initialize the log display window'''

		tk.Toplevel.__init__(self, *args, **kw)

		self.logger = logger
		if self.logger:
			self.logger.debug('LogWin.__init__: Creating LogWin')

		self.detailArray = detailArray
		self.summaryArray = summaryArray

		self.mstyle = ttk.Style()	# Master style instance for configuration

		self.master.columnconfigure(0, weight = 1)
		self.master.rowconfigure(0, weight = 1)

		self.winfo_toplevel().resizable(width = False, height = True)

		self.columnconfigure(0, weight = 1)
		self.columnconfigure(1, weight = 0)
		self.rowconfigure(0, weight = 1)
		self.rowconfigure(1, weight = 0)

		# The necessary widgets
		ttk.Sizegrip(self).grid(column = 1, row = 2)

		utilFrame = ttk.Frame(self, style = 'utilFrame.TFrame')
		utilFrame.grid(column = 0, row = 2, sticky = tk.EW)
		utilFrame.columnconfigure(0, weight = 1)

		ttk.Button(utilFrame,
			text = 'Close',
			command =  self.doClose,
			style = 'LogWin.TButton').grid(
				column = 0,
				row = 0,
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

		self.mstyle.configure('utilFrame.TFrame',
			border = LogWin.UTILITYBORDER,
			#background = LogWin.UTILITYBG,
			relief = LogWin.UTILITYRELIEF,
			padding = LogWin.UTILITYPAD,
			)

		self.mstyle.configure('rbFrame.TFrame',
			border = LogWin.UTILITYBORDER,
			#background = LogWin.UTILITYBG,
			relief = LogWin.UTILITYRELIEF,
			padding = LogWin.UTILITYPAD,
			)

		self.mstyle.configure('LogWin.TRadiobutton',
			relief = tk.SUNKEN,
			padding = LogWin.DECORATIONPAD,
			)
			
		self.notebookFrame = ttk.Notebook(self, style = 'LogWin.TNotebook')
		self.notebookFrame.grid(column = 0, row = 0, sticky = (tk.NS, tk.EW))
		self.tabs = []

		# Build the summary info Frame
		self.summaryFrame = ttk.Frame(self.notebookFrame, style = 'SummaryFrame.ContentFrame.TFrame')
		self.notebookFrame.add(self.summaryFrame, text = LogWin.SUMMARYMODE)
		self.tabs.append(LogWin.SUMMARYMODE)
		self.logger.debug('Summary frame added. There are %s tabs', self.notebookFrame.index('end'))

		self.summaryFrame.rowconfigure(0, weight = 0)
		self.summaryFrame.rowconfigure(1, weight = 1)

		summaryLabelRow = ttk.Frame(self.summaryFrame, style = 'Cframe.TFrame')
		summaryLabelRow.grid(column = 0, row = 0, sticky = tk.EW)
		summaryLabelSys = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'System', width = LogWin.WIDTHSYS + 1)
		summaryLabelGrp = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'Group', width = LogWin.WIDTHGRP)
		summaryLabelChn = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'Channel', width = LogWin.WIDTHCHN + 1)
		summaryLabelFrq = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'Freq/TGID', width = LogWin.WIDTHFRQ )
		summaryLabelDur = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'Dur', width = LogWin.WIDTHDUR + 1)
		summaryLabelCnt = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'Cnt', width = LogWin.WIDTHCNT)
		summaryLabelLst = ttk.Label(summaryLabelRow,
			style = 'CsummaryLabel.TLabel', text = 'Last', width = LogWin.WIDTHLST)

		summaryLabelSys.grid(column = 0, row = 0, sticky = (tk.EW))
		summaryLabelGrp.grid(column = 1, row = 0, sticky = (tk.EW))
		summaryLabelChn.grid(column = 2, row = 0, sticky = (tk.EW))
		summaryLabelFrq.grid(column = 3, row = 0, sticky = (tk.EW))
		summaryLabelDur.grid(column = 4, row = 0, sticky = (tk.EW))
		summaryLabelCnt.grid(column = 5, row = 0, sticky = (tk.EW))
		summaryLabelLst.grid(column = 6, row = 0, sticky = (tk.EW))

		self.summaryContentFrame = ttk.Frame(self.summaryFrame, style = 'Cframe.TFrame')
		self.summaryContentFrame.grid(column = 0, row = 1, sticky = (tk.EW, tk.N))

		# Build the detail info Frame
		self.detailFrame = ttk.Frame(self.notebookFrame, style = 'DetailFrame.ContentFrame.TFrame')
		self.notebookFrame.add(self.detailFrame, text = LogWin.DETAILMODE)
		self.tabs.append(LogWin.DETAILMODE)
		self.logger.debug('Detail frame added. There are %s tabs', self.notebookFrame.index('end'))

		self.detailFrame.rowconfigure(0, weight = 0)
		self.detailFrame.rowconfigure(1, weight = 1)

		detailLabelRow = ttk.Frame(self.detailFrame, style = 'Cframe.TFrame')
		detailLabelRow.grid(column = 0, row = 0, sticky = tk.EW)
		detailLabelSys = ttk.Label(detailLabelRow,
			style = 'CdetailLabel.TLabel', text = 'System', width = LogWin.WIDTHSYS + 1)
		detailLabelGrp = ttk.Label(detailLabelRow,
			style = 'CdetailLabel.TLabel', text = 'Group', width = LogWin.WIDTHGRP)
		detailLabelChn = ttk.Label(detailLabelRow,
			style = 'CdetailLabel.TLabel', text = 'Channel', width = LogWin.WIDTHCHN + 1)
		detailLabelFrq = ttk.Label(detailLabelRow,
			style = 'CdetailLabel.TLabel', text = 'Freq/TGID', width = LogWin.WIDTHFRQ )
		detailLabelDur = ttk.Label(detailLabelRow,
			style = 'CdetailLabel.TLabel', text = 'Dur', width = LogWin.WIDTHDUR + 1)
		detailLabelStart = ttk.Label(detailLabelRow,
			style = 'CdetailLabel.TLabel', text = 'Start', width = LogWin.WIDTHSTART)

		detailLabelSys.grid(column = 0, row = 0, sticky = (tk.EW))
		detailLabelGrp.grid(column = 1, row = 0, sticky = (tk.EW))
		detailLabelChn.grid(column = 2, row = 0, sticky = (tk.EW))
		detailLabelFrq.grid(column = 3, row = 0, sticky = (tk.EW))
		detailLabelDur.grid(column = 4, row = 0, sticky = (tk.EW))
		detailLabelStart.grid(column = 5, row = 0, sticky = (tk.EW))

		self.detailContentFrame = ttk.Frame(self.detailFrame, style = 'Cframe.TFrame')
		self.detailContentFrame.grid(column = 0, row = 1, sticky = (tk.EW, tk.N))
		
		self.notebookFrame.bind('<<NotebookTabChanged>>', self.tabChanged)

		self.currentMode = ''	# No mode
		self.refresh()			# Make a mode
	
	def tabChanged(self, event):
		self.logger.debug('Notebook tab changed to %s', event.widget.index('current'))
		self.refresh()

	def refresh(self):
		'''Request to refresh the current displayed window

		'''

		currtab = self.tabs[self.notebookFrame.index('current')]
		if self.logger:
			self.logger.debug('LogWin.refresh: Refreshing %s', currtab)

		if currtab == LogWin.SUMMARYMODE:
			self.summaryRefresh()
		elif currtab == LogWin.DETAILMODE:
			self.detailRefresh()
		else:
			if self.logger:
				self.logger.critical('Invalid refresh mode: %s', currtab)
			self.doClose()

		self.currentMode = currtab

	def summaryRefresh(self):
		'''Refresh to summary log window'''

		if self.logger:
			self.logger.debug('LogWin.summaryRefresh: Starting, summary contains %s items',
				len(self.summaryArray))

		# Scan through the summary array and display the entries
		sortedkeys = sorted(self.summaryArray.keys())
		inserts = 0
		for desckey in sortedkeys:
			desc = self.summaryArray[desckey]	# Get a handle on it
			if desc.contentRow is None:	# Give it a SummaryRow
				desc.contentRow = LogWin.SummaryRow(
					self.summaryContentFrame,
					desc,
					logger = self.logger)
				inserts += 1

		if inserts:		# Did we add any?
			if self.logger:
				self.logger.debug('LogWin.summaryRefresh: Rebuilding, inserts = %s', inserts)
			row = 0
			for desckey in sortedkeys:
				if self.logger:
					self.logger.debug('LogWin.summaryRefresh: Sort key=%s in row %s',
					desckey, row)
				self.summaryArray[desckey].contentRow.grid(
					column = 0,
					row = row,
					sticky = (tk.EW, tk.N))
				row += 1
		else:
			if self.logger:
				self.logger.debug('LogWin.summaryRefresh: No rebuild')

	def detailRefresh(self):
		'''Refresh to detail log window'''

		if self.logger:
			self.logger.debug('LogWin.summaryRefresh: Starting, detail contains %s items',
				len(self.detailArray))

		# Scan through the detail array and display the entries
		inserts = 0

		for desc in self.detailArray:
			if desc.contentRow is None:	# Give it a DetailRow
				desc.contentRow = LogWin.DetailRow(
					self.detailContentFrame,
					desc,
					logger = self.logger)
				inserts += 1
				if self.logger:
					self.logger.debug('LogWin.summaryRefresh: Sort key=%s added', desc.key)
				desc.contentRow.grid(
					column = 0,			# Default is the next available row
					sticky = (tk.EW, tk.N))

		if not inserts:
			if self.logger:
				self.logger.debug('LogWin.summaryRefresh: No inserts')

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

			self.summaryDescs = {}
			self.detailDescs = []
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
				self.logWin = LogWin(
					summaryArray = self.summaryDescs,
					detailArray = self.detailDescs,
					logger = self.logger)
				self.logWin.title('Test Logging Display')
				self.logWin.refresh()
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
			self.logger.debug('MainWin.doAdd: Create HitDesc({})'.format(ndesc.key))

			####
			# Note: The above code generates the test data. What follows should be emulated
			#       in production code ...
			####

			self.detailDescs.append(ndesc)	# Simply add to the detail list

			# Make a copy for the Summary window
			ndesc = copy.copy(ndesc)
			ndesckey = ndesc.key

			if ndesckey in self.summaryDescs:	# We have one of these
				action = 'Bump'
				self.summaryDescs[ndesckey].bumpCount(dur)
			else:
				action = 'Insert'
				self.summaryDescs[ndesckey] = ndesc

			self.logger.debug('MainWin.doAdd: %s %s, count=%s, dur=%s, last=%s',
				action,
				ndesckey,
				self.summaryDescs[ndesckey].count,
				self.summaryDescs[ndesckey].duration,
				self.summaryDescs[ndesckey].last)

			if self.logWin and self.logWin.winfo_exists():
				self.logger.debug('MainWin.doAdd: Sending refresh')
				self.logWin.refresh()
			else:
				self.logger.debug('MainWin.doAdd: Refresh delayed')

		def doStop(self):
			'''Shut down, I guess we're done ...'''

			self.logger.debug('MainWin.doStop: Commanded to Stop!')
			self.quit()

	w = MainWin(width = 300, height = 200)
	w.mainloop()