#!/usr/bin/env python

import tkinter as tk
import tkinter.ttk as ttk

class ScrollFrame(ttk.Frame):
	def __init__(self, master, logger = None, **kw):
		ttk.Frame.__init__(self, master, **kw)
		
		self._myname = 'ScrollFrame'
		
		self._logger = logger
		
		self._width = kw['width'] if 'width' in kw else 100
		self._yscrollincrement = -1
		
		# One row for the labelframe, one for the content/scrollbar
		self.columnconfigure(0, weight = 1)	# Label/Canvas
		self.rowconfigure(0, weight = 0)	# Label
		self.rowconfigure(1, weight = 1)	# Canvas/Scrollbar
		
		self._canvasframe = ttk.Frame(self)
		self._canvasframe.grid(column = 0, row = 1, sticky = (tk.NS, tk.EW))
		self._canvasframe.columnconfigure(0, weight = 1)
		self._canvasframe.columnconfigure(1, weight = 0)
		self._canvasframe.rowconfigure(0, weight = 1)
		
		self.labelFrame = ttk.Frame(self)
		self.labelFrame.grid(column = 0, row = 0, sticky = tk.EW)
		
		self.contentFrame = ttk.Frame(self._canvasframe)
		self.contentFrame.bind('<Configure>', self._configure)
		
		self._canvas = tk.Canvas(self._canvasframe)
	
		self._scrollbar = tk.Scrollbar(self._canvasframe, orient = tk.VERTICAL)

		self._canvas.grid(column = 0, row = 0, sticky = (tk.NS, tk.EW))

		self._scrollbar.grid(column = 1, row = 0, sticky = tk.NS)

		self._canvas.configure(yscrollcommand = self._scrollbar.set)
		self._scrollbar.configure(command = self._doscroll)
		
		self._contentid = self._canvas.create_window(0, 0, anchor = tk.NW, window = self.contentFrame)

		self._canvas.update_idletasks()
		self._canvas.configure(scrollregion = (0, 0, 0, 0))
		
		if self._logger:
			self._logger.debug('%s.__init__: Initial width=%s, height=%s', 
				self._myname,
				self.winfo_width(), 
				self.winfo_height())

	def _doscroll(self, scroll = None, amount = None, type = None):

		action = 'Ignored'	
		if self._canvas.winfo_height() < self._canvas.bbox(self._contentid)[3]:
			action = 'Scrolled'
			self._canvas.yview(scroll, amount, type)

		if self._logger:
			self._logger.debug('%s._doscroll: Scroll type=%s, amount=%s, type=%s - %s',
				self._myname,
				scroll, 
				amount, 
				type, 
				action)
	
	def _mousescroll(self, event):
		if self._logger:
			self._logger.debug('%s._mousescroll: Event=%s, time=%s',
				self._myname,
				event.type, 
				event.time)
		if event.type == '4':	# Button press
			if self._logger:
				self._logger.debug('%s._mousescroll: Button %s, by %s',
					self._myname,
					event.num, 
					event.delta)
			if event.num == 4:	# Scroll down
				self._doscroll(tk.SCROLL, -1, tk.UNITS)
			else:
				self._doscroll(tk.SCROLL, 1, tk.UNITS)
		elif event.type == '38':	# mousewheel
			if self._logger:
				self._logger.debug('%s._mousescroll: MouseWheel, by %s',
					self._myname,
					event.delta)
		else:	# Huh?
			if self._logger:
				self._logger.error('%s._mousescroll: Wrong event type: %s',
					self._myname,
					event.type)

	def _bindscroll(self, c):
		if False and self._logger:
			self._logger.debug('%s._bindscroll: binding to: %s, viewable? %s', 
				self._myname, 
				c.winfo_class(),
				c.winfo_viewable())
		c.bind('<Button-4>', self._mousescroll)
		c.bind('<Button-5>', self._mousescroll)
		c.bind('<MouseWheel>', self._mousescroll)

	def _deep_bind(self, c, bindf):
		bindf(c)
		for d in c.winfo_children():
			self._deep_bind(d, bindf)
	
	def _maxWidth(self, frame):
		max = 0
		frame.update_idletasks()
		for c in frame.winfo_children():
			if max < c.winfo_width():
				max = c.winfo_width()
		return max

	def _configure(self, event):	# Triggered by the contentframe changing size
		if self._logger:
			self._logger.debug('%s._configure: new height=%s', self._myname, event.height)
		
		if self._yscrollincrement == -1:	# We haven't set width or scrollincrement yet
			if self.contentFrame.winfo_children():		# We have at least one child
				c = self.contentFrame.winfo_children()[0]
				c.update_idletasks()
				self._yscrollincrement = c.winfo_height()
				self._width = self.contentFrame.winfo_width()
				self._canvas.configure(
					width = self._width,
					yscrollincrement = self._yscrollincrement,
					)
		
		isScroll = self._canvas.canvasy(self._canvas.winfo_height()) >= \
			int(self._canvas.cget('scrollregion').split()[3]) - 5	# 5 pixel fudge
	
		self._canvas.configure(scrollregion = (0, 0, 0, 
			int(self._canvas.bbox(self._contentid)[3])))
		
		#self._deep_bind(self.contentFrame, self._bindscroll)
		
		maxw = self._maxWidth(self.contentFrame)
		if self._canvas.winfo_width() != maxw:
			if self._logger:
				self._logger.debug('%s._configure: new width=%s', self._myname, maxw)
			self._canvas.configure(width = maxw)
		else:
			if self._logger:
				self._logger.debug('%s._configure: width remains=%s', self._myname, self._canvas.winfo_width())
	
		if isScroll:
			if self._logger:
				self._logger.debug('%s._configure: Scrolling...', self._myname)
			self._doscroll(tk.SCROLL, 2, tk.UNITS)
		
		if self._logger:
			self._logger.debug('%s._configure: contentframe is now %s, scrollregion is %s',
				self._myname,
				self._canvas.bbox(self._contentid), 
				self._canvas.cget('scrollregion'))

	def labelsAdded(self):
		if self._logger:
			self._logger.debug('%s.labelsAdded:', self._myname)
		
		self.labelFrame.update_idletasks()
		self._labelframewidth = self.labelFrame.winfo_width()
		self._labelframeheight = self.labelFrame.winfo_height()
		self._deep_bind(self.labelFrame, self._bindscroll)
	
	def contentAdded(self):
		if self._logger:
			self._logger.debug('%s.contentAdded:', self._myname)
		
		self.contentFrame.lift()	# Make it visible
		
		self._deep_bind(self._canvasframe, self._bindscroll)

###########################
# What follows below will be part of the test routines
###########################

if __name__ == '__main__':
	import logging
	
	class contentrow(ttk.Frame):
		def __init__(self, master, num = 0):
			ttk.Frame.__init__(self, master)
		
			logger.debug('%s.contentrow.__init__:', __name__)
			msg = 'Some Content {} '.format(num) * 3

			lSys = ttk.Label(self, style = 'Data.TLabel',
				text = str(num) + ' System',
				width = 16)
			lGrp = ttk.Label(self, style = 'Data.TLabel',
				text = str(num) + ' Group',
				width = 16)
			lChn = ttk.Label(self, style = 'Data.TLabel',
				text = str(num) + ' Channel',
				width = 16)
			lFrq = ttk.Label(self, style = 'Data.TLabel',
				text = str(num) + ' Freq',
				width = 9)
			lDur = ttk.Label(self, style = 'Data.TLabel',
				text = str(num) + ' D',
				width = 4,
				anchor = tk.E)
			lLst = ttk.Label(self, style = 'Data.TLabel',
				text = str(num) + ' Last',
				width = 17)

			lSys.grid(column = 0, row = 0, sticky = (tk.EW, tk.N))
			lGrp.grid(column = 1, row = 0, sticky = (tk.EW, tk.N))
			lChn.grid(column = 2, row = 0, sticky = (tk.EW, tk.N))
			lFrq.grid(column = 3, row = 0, sticky = (tk.EW, tk.N))
			lDur.grid(column = 4, row = 0, sticky = (tk.EW, tk.N))
			lLst.grid(column = 5, row = 0, sticky = (tk.EW, tk.N))

			logger.debug('%s.contentrow.__init__: row="%s"', __name__, msg)

	def doGo():
		global num
		logger.debug('%s.doGo:', __name__)
		new1 = contentrow(contentframe, num)
		new1.grid(column = 0, sticky = tk.EW)
		scrollframe.contentAdded()
		num += 1
	
	def doClose():
		testwindow.quit()

	# Set up logging at the DEBUG level
	logger = logging.getLogger('TestLog')
	logger.setLevel('DEBUG')
	sh = logging.StreamHandler()
	sh.setLevel('DEBUG')
	logger.addHandler(sh)
	logger.debug('scrollframe: Test for ScrollFrame starting')
                        
	masterwindow = tk.Tk()
	masterwindow.title('Another window that does nothing and has nothing in it')
	f2 = tk.Frame(masterwindow, width = 150, height = 150)
	f2.grid_propagate(False)
	f2.grid()

	testwindow = tk.Toplevel()
	testwindow.title('Canvas Test')

	testwindow.columnconfigure(0, weight = 1)	# Everything is in column 0
	testwindow.rowconfigure(0, weight = 1)		# The ScrollFrame
	testwindow.rowconfigure(1, weight = 0)		# The utilframe
	testwindow.resizable(width = False, height = True)
	
	scrollframe = ScrollFrame(testwindow, logger = logger)
	scrollframe.grid(column = 0, row = 0, sticky = (tk.NS, tk.EW))

	# Holds the "labels"
	labelframe = scrollframe.labelFrame
	labelframe.configure(border = 2, relief = tk.RAISED)
	
	mstyle = ttk.Style()
	mstyle.configure('CdetailLabel.TLabel',
		border = 1,
		relief = tk.GROOVE,
		background = '#F1F5B3')
	
	mstyle.configure('Data.TLabel',
		border = 1,
		relief = tk.GROOVE,
		background = '#DFFACA')
	
	detailLabelSys = ttk.Label(labelframe,
		style = 'CdetailLabel.TLabel', text = 'System', width = 16)
	detailLabelGrp = ttk.Label(labelframe,
		style = 'CdetailLabel.TLabel', text = 'Group', width = 16)
	detailLabelChn = ttk.Label(labelframe,
		style = 'CdetailLabel.TLabel', text = 'Channel', width = 16)
	detailLabelFrq = ttk.Label(labelframe,
		style = 'CdetailLabel.TLabel', text = 'Freq/TGID', width = 9 )
	detailLabelDur = ttk.Label(labelframe,
		style = 'CdetailLabel.TLabel', text = 'Dur', width = 4)
	detailLabelStart = ttk.Label(labelframe,
		style = 'CdetailLabel.TLabel', text = 'Start', width = 17)

	detailLabelSys.grid(column = 0, row = 0, sticky = (tk.EW))
	detailLabelGrp.grid(column = 1, row = 0, sticky = (tk.EW))
	detailLabelChn.grid(column = 2, row = 0, sticky = (tk.EW))
	detailLabelFrq.grid(column = 3, row = 0, sticky = (tk.EW))
	detailLabelDur.grid(column = 4, row = 0, sticky = (tk.EW))
	detailLabelStart.grid(column = 5, row = 0, sticky = (tk.EW))

	scrollframe.labelsAdded()

	contentframe = scrollframe.contentFrame
	
	num = 0

	utilframe = tk.Frame(testwindow, border = 2)

	utilframe.columnconfigure(0, weight = 1)
	utilframe.columnconfigure(1, weight = 1)

	buttongo = tk.Button(utilframe, text = 'Go') #, background = '#550')
	buttonclose = tk.Button(utilframe, text = 'Close') #, background = '#055')

	utilframe.grid(column = 0, row = 1, sticky = tk.EW)

	buttongo.grid(column = 0, row = 0)
	buttonclose.grid(column = 1, row = 0)

	buttongo.configure(command = doGo)
	buttonclose.configure(command = doClose)

	testwindow.mainloop()

