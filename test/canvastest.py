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

def pit():
	print('Height is {}, canvasy of that is {}, scroll bottom is {}'.format(canvas.winfo_height(), canvas.canvasy(canvas.winfo_height()), canvas.cget('scrollregion').split()[3]))

def doscroll(scroll = None, amount = None, type = None):

	action = 'Ignored'	
	if canvas.winfo_height() < canvas.bbox(contentid)[3]:
		action = 'Scrolled'
		canvas.yview(scroll, amount, type)

	print('Scroll type={}, amount={}, type={} - {}'.format(scroll, amount, type, action))
	
def mousescroll(event):
	print('Event={}, time={}'.format(event.type, event.time))
	if event.type == '4':	# Button press
		print('Button {}, by {}'.format(event.num, event.delta))
		if event.num == 4:	# Scroll down
			doscroll(tk.SCROLL, -1, tk.UNITS)
		else:
			doscroll(tk.SCROLL, 1, tk.UNITS)
	elif event.type == '38':	# mousewheel
		print('MouseWheel, by {}'.format(event.delta))
	else:	# Huh?
		print('Wrong event type: {}'.format(event.type)) 

def configure(event):
	print('Configure, new height={}'.format(event.height))

root2 = tk.Tk()
root2.title('Another window that does nothing and has nothing in it')
f2 = tk.Frame(root2, width = 150, height = 150)
f2.grid_propagate(False)
f2.grid()

root = tk.Toplevel()
root.title('Canvas Test')

# Holds the "labels"
labelframe = tk.Frame(root, border = 2)

label = tk.Label(labelframe, border = 2, text = 'ThisIsALabel ' * 4)

# Holds the canvas/content and scrollbar
masterframe = tk.Frame(root, border = 2, background = '#e0e')                             # Purple

canvas = tk.Canvas(masterframe, 
	yscrollincrement = 20,
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
scrollbar.configure(command = doscroll)

canvas.update_idletasks()
canvas.configure(scrollregion = (0, 0, 0, 0))
print('Initial bbox=', canvas.bbox(contentid))
masterframe.bind('<Configure>', configure)

def bindscroll(c):
	c.bind('<Button-4>', mousescroll)
	c.bind('<Button-5>', mousescroll)
	c.bind('<MouseWheel>', mousescroll)

def deep_bind(c, bindf):
	bindf(c)
	for d in c.winfo_children():
		bindf(d)

deep_bind(root, bindscroll)

num = 0

def doGo():
	global num
	new1 = contentrow(contentframe, num)
	new1.update_idletasks()
	
	deep_bind(new1, bindscroll)

	isScroll = int(canvas.canvasy(canvas.winfo_height())) >= int(canvas.cget('scrollregion').split()[3]) - 5
	
	canvas.configure(scrollregion = (0, 0, 0, 
		canvas.bbox(contentid)[3])) # - canvas.winfo_height() % int(canvas.cget('yscrollincrement'))))
	
	if isScroll:
		print('Scrolling...')
		doscroll(tk.SCROLL, int(new1.winfo_height() / int(canvas.cget('yscrollincrement'))) + 1, tk.UNITS)
		
	print('contentframe is now {}, scrollregion is {}'.format(
		canvas.bbox(contentid), 
		canvas.cget('scrollregion')))
	num += 1
	root.update()
	
def doClose():
	root.quit()

buttongo.configure(command = doGo)
buttonclose.configure(command = doClose)

#root.update()
root.mainloop()

