#!/usr/bin/env python

from tkinter import *
from tkinter import ttk

class TestNotebook(ttk.Frame):

	class NotebookWin(Toplevel):
		
		def __init__(self, *options, **kwargs):
			Toplevel.__init__(self, *options, **kwargs)
			
			self.makeNotebook()
			self.columnconfigure(0, weight = 1)
			self.rowconfigure(0, weight = 1)
		
		def makeNotebook(self):
			nb = ttk.Notebook(self, height = 400, width = 300)
			nb.grid(column = 0, row = 0, sticky = (N, S, E, W))
			
			tab1 = ttk.Frame(nb)
			tab1.columnconfigure(0, weight = 1)
			tab1.rowconfigure(0, weight = 1)
			
			tab1b = ttk.Button(tab1, text = 'Tab 1 Button', command = self.printit)
			tab1b.grid(column = 0, row = 0)

			tab2 = ttk.Frame(nb)
			tab2.columnconfigure(0, weight = 1)
			tab2.rowconfigure(0, weight = 1)
			
			tab2b = ttk.Button(tab2, text = 'Tab 2 Button', command = self.printit)
			tab2b.grid(column = 0, row = 0)

			nb.add(tab1, text = 'Tab 1', sticky = N+S+E+W)
			nb.add(tab2, text = 'Tab 2', sticky = N+S+E+W)
			
		def printit(self):
			me = self.focus_get()
			if me is None:
				print('I have no idea who I am!')
			else:
				print('{} pushed'.format(me.cget('text')))

	# Functions

	def __init__(self, master = None):
		ttk.Frame.__init__(self, master, width = 180, height = 180)

		self.master.columnconfigure(0, weight = 1)
		self.master.rowconfigure(0, weight = 1)

		self.grid(column = 0, row = 0, sticky = (N, S, E, W))
		self.grid_propagate(0)
		
		self.columnconfigure(0, weight = 1)
		self.rowconfigure(0, weight = 1)
		self.rowconfigure(1, weight = 1)
		
		self.createWidgets()

	def createWidgets(self):
		b_notebook = ttk.Button(self, text = 'Notebook', command = self.do_notebook)
		b_close = ttk.Button(self, text = 'Close', command = self.quit)
		
		b_notebook.grid(column = 0, row = 0)
		b_close.grid(column = 0, row = 1)
		
	def do_notebook(self):
		nb = TestNotebook.NotebookWin()

test = TestNotebook()
test.master.title('Test Notebook Widget')

test.mainloop()