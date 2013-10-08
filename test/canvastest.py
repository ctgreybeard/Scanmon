#!/usr/bin/env python

import tkinter as tk

class contentrow(tk.Frame):
	def __init__(self, master, num = 0):
		tk.Frame.__init__(self, master)
		
		msg = 'Some Content {} '.format(num) * 3
		self.content = tk.Label(self, 
			text = msg, 
			anchor = tk.W,
			border = 2, 
			relief = tk.RIDGE, 
			background = '#fff', 
			width = 16 * 3)        # WHITE
		self.columnconfigure(0, weight = 1)
		self.content.grid(column = 0, row = 0, sticky = tk.W)
		self.grid()
		print(msg)

root = tk.Tk()
root.title = 'Canvas Test'

# Holds the "labels"
labelframe = tk.Frame(root, border = 2)

label = tk.Label(labelframe, border = 2, text = 'ThisIsALabel ' * 4)

# Holds the canvas/content and scrollbar
masterframe = tk.Frame(root, border = 2, background = '#e0e')                             # Purple

canvas = tk.Canvas(masterframe, 
	yscrollincrement = 10,
	width = 390,
	background = '#ee0')                # BRIGHT YELLOW
scrollbar = tk.Scrollbar(masterframe, orient = tk.VERTICAL)

contentframe = tk.Frame(masterframe, border = 0, background = '#839bbb', width = 16 * 3)                  # LIGHT BLUE

utilframe = tk.Frame(root, border = 2)

buttongo = tk.Button(utilframe, text = 'Go') #, background = '#550')
buttonclose = tk.Button(utilframe, text = 'Close') #, background = '#055')

root.columnconfigure(0, weight = 1)
root.rowconfigure(0, weight = 0)
root.rowconfigure(1, weight = 1)
root.rowconfigure(2, weight = 0)
root.resizable(width = False, height = True)

masterframe.columnconfigure(0, weight = 1)
masterframe.columnconfigure(1, weight = 0)
masterframe.rowconfigure(0, weight = 1)

contentframe.columnconfigure(0, weight = 1)
contentframe.rowconfigure(0, weight = 1)

utilframe.columnconfigure(0, weight = 1)
utilframe.columnconfigure(1, weight = 1)

labelframe.grid(column = 0, row = 0, sticky = tk.EW)
label.grid(column = 0, row = 0, sticky = tk.EW)

masterframe.grid(column = 0, row = 1, sticky = (tk.NS, tk.EW))

canvas.grid(column = 0, row = 0, sticky = (tk.NS, tk.EW))

scrollbar.grid(column = 1, row = 0, sticky = tk.NS)

utilframe.grid(column = 0, row = 2, columnspan = 2, sticky = tk.EW)

buttongo.grid(column = 0, row = 0)
buttonclose.grid(column = 1, row = 0)

contentid = canvas.create_window(0, 0, anchor = tk.NW, window = contentframe)

canvas.configure(yscrollcommand = scrollbar.set)
scrollbar.configure(command = canvas.yview)

num = 0

def doGo():
	global num
	new1 = contentrow(contentframe, num)
	new1.update_idletasks()
	canvas.configure(scrollregion = (0, 0, 0, 
		canvas.bbox(contentid)[3] - canvas.winfo_height() % int(canvas.cget('yscrollincrement'))))
	canvas.yview_scroll(int(new1.winfo_height() / int(canvas.cget('yscrollincrement'))), tk.UNITS)
	print('contentframe is now {}, scrollregion is {}'.format(
		canvas.bbox(contentid), 
		canvas.cget('scrollregion')))
	num += 1
	root.update()
	
def doClose():
	root.quit()

buttongo.configure(command = doGo)
buttonclose.configure(command = doClose)

root.update()
#root.mainloop()