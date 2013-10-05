#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk

import random, time

class TableWin(tk.Toplevel):
	WIDTHSYS = 16
	WIDTHGRP = 16
	WIDTHCHN = 16
	WIDTHFRQ = 9
	WIDTHDUR = 4
	WIDTHCNT = 4
	WIDTHLST = 17
	CONTENTPAD = 2

	class HitDesc:
		def __init__(self, system, group, channel, freq, duration):
			self.system = system
			self.group = group
			self.channel = channel
			self.freq = freq
			self.count = 1
			self.duration = duration
			self.last = time.strftime('%m/%d/%Y %H:%M:%S')
			self.key = TableWin.HitDesc.genKey(system, group, channel, freq)
			self.contentRow = None

		def bumpCount(self, dur):
			#print('Bump instance')
			self.count += 1
			self.last = time.strftime('%m/%d/%Y %H:%M:%S')
			self.duration += dur
			if self.contentRow is not None:
				#print('Bump row')
				self.contentRow.tvCnt.set(self.count)
				self.contentRow.tvLst.set(self.last)
				self.contentRow.tvDur.set(self.duration)

		def genKey(system, group, channel, freq):
			return '{}:{}:{}'.format(system, group, channel)

	class ContentRow(ttk.Frame):
		def __init__(self, master, desc, **kw):
			ttk.Frame.__init__(self, master, **kw)

			self.mstyle = ttk.Style()	# Master style instance for configuration
			self.mstyle.configure('Data.TLabel', border = 1, relief = tk.RIDGE, padding = TableWin.CONTENTPAD)

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

			lSys = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvSys, width = TableWin.WIDTHSYS)
			lGrp = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvGrp, width = TableWin.WIDTHGRP)
			lChn = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvChn, width = TableWin.WIDTHCHN)
			lFrq = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvFrq, width = TableWin.WIDTHFRQ)
			lDur = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvDur, width = TableWin.WIDTHDUR,
				anchor = tk.E)
			lCnt = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvCnt, width = TableWin.WIDTHCNT,
				anchor = tk.E)
			lLst = ttk.Label(self, style = 'Data.TLabel', textvariable = self.tvLst, width = TableWin.WIDTHLST)

			lSys.grid(column = 0, row = 0, sticky = (tk.EW, tk.N))
			lGrp.grid(column = 1, row = 0, sticky = (tk.EW, tk.N))
			lChn.grid(column = 2, row = 0, sticky = (tk.EW, tk.N))
			lFrq.grid(column = 3, row = 0, sticky = (tk.EW, tk.N))
			lDur.grid(column = 4, row = 0, sticky = (tk.EW, tk.N))
			lCnt.grid(column = 5, row = 0, sticky = (tk.EW, tk.N))
			lLst.grid(column = 6, row = 0, sticky = (tk.EW, tk.N))

			#self.grid(column = 0, row = row, sticky = (tk.EW, tk.N))

	def __init__(self, masterptr, *args, **kw):
		tk.Toplevel.__init__(self, *args, **kw)

		self.mstyle = ttk.Style()	# Master style instance for configuration

		self.master.columnconfigure(0, weight = 1)
		self.master.rowconfigure(0, weight = 1)

		self.columnconfigure(0, weight = 1)
		self.columnconfigure(1, weight = 0)
		self.rowconfigure(0, weight = 0)
		self.rowconfigure(1, weight = 1)
		self.rowconfigure(2, weight = 0)

		ttk.Sizegrip(self).grid(column = 1, row = 2)

		self.mstyle.configure('Cframe.TFrame', border = 2)
		self.mstyle.configure('Clabel.TLabel', border = 2, padding = TableWin.CONTENTPAD)

		labelRow = ttk.Frame(self, style = 'Cframe.TFrame')
		labelRow.grid(column = 0, row = 0, sticky = tk.EW)
		labelSys = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'System', width = TableWin.WIDTHSYS)
		labelGrp = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Group', width = TableWin.WIDTHGRP)
		labelChn = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Channel', width = TableWin.WIDTHCHN)
		labelFrq = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Freq', width = TableWin.WIDTHFRQ)
		labelDur = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Dur', width = TableWin.WIDTHDUR)
		labelCnt = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Count', width = TableWin.WIDTHCNT)
		labelLst = ttk.Label(labelRow, style = 'Clabel.TLabel', text = 'Last', width = TableWin.WIDTHLST)

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
		
		# Pointer to the pointer back to me (confused?)
		self.masterptr = masterptr

	def destroy(self):
		# Ouch! We are shutting down!
		#print('Say goodnight Dick!')
		# Tell the boss we don't exist any more
		self.masterptr[0] = None
		# Clear the ata row pointers in the data elements
		for data in self.rowData.values():
			data.desc.contentRow = None
		# And, finally, commit seppuku!
		tk.Toplevel.destroy(self)

	def add(self, desc):
		if desc.key in self.rowData:	# We already have one of these ...
			thisrow = self.rowData[desc.key]
			thisrow.desc.bumpCount(desc.duration)

		else:	# Make a new one ...
			thisrow = TableWin.ContentRow(self.contentFrame, desc)
			self.rowData[thisrow.key] = thisrow

			# Rearrange the rows by sorted key
			sortedkeys = list(self.rowData.keys())
			sortedkeys.sort()
			row = 0
			for r in sortedkeys:
				#print('Key={} in row {}'.format(r, row))
				self.rowData[r].grid(column = 0, row = row, sticky = (tk.EW, tk.N))
				row += 1

		return thisrow.desc

class MainWin(ttk.Frame):
	def __init__(self, *args, **kw):
		ttk.Frame.__init__(self, *args, **kw)

		self.mstyle = ttk.Style()	# Master style instance for configuration

		self.master.columnconfigure(0, weight = 1)
		self.master.rowconfigure(0, weight = 1)

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
		self.tableWin = [None]

	def doGo(self):
		if self.tableWin[0] is None or not self.tableWin[0].winfo_exists():
			self.tableWin[0] = TableWin(masterptr = self.tableWin)
			for ndesc in list(self.dataDescs.values()):
				self.dataDescs[ndesc.key] = self.tableWin[0].add(ndesc)
		else:	# Print info about the window. Is it still active?
			pass
			#print('tableWin exists {}'.format(self.tableWin[0].winfo_exists()))

	def doAdd(self):
		def rchar():
			return chr(ord('a') + random.randint(0, 25))

		if random.randint(0, 3) == 0:
			system = 'ssystem'
			group = 'ggroup'
			chan = 'cchan'
			freq = 'ffreq'
			dur = random.randint(1,15)
			#print('Gen dup, dur=', dur)
		else:
			system = rchar() + 'system'
			group = rchar() + 'group'
			chan = rchar() + 'chan'
			freq = rchar() + 'freq'
			dur = random.randint(1,15)
			#print('Gen new')

		ndesc = TableWin.HitDesc(system, group, chan, freq, dur)
		ndesckey = ndesc.key
		if self.tableWin[0] is None:	# Keep our own internal list
			if ndesckey in self.dataDescs:	# We have one of these
				action = 'Bump'
				self.dataDescs[ndesc.key].bumpCount(dur)
			else:
				action = 'Insert'
				self.dataDescs[ndesckey] = ndesc
		else:
			action = 'Add'
			self.dataDescs[ndesckey] = self.tableWin[0].add(ndesc)

		#print('{} {}, count={}, dur={}, last={}'.format(
		#	action, 
		#	ndesckey, 
		#	self.dataDescs[ndesckey].count, 
		#	self.dataDescs[ndesckey].duration, 
		#	self.dataDescs[ndesckey].last))

	def doStop(self):
		self.quit()

if __name__ == '__main__':
	w = MainWin(width = 300, height = 200)
	w.mainloop()