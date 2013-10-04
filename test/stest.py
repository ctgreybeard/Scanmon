import tkinter as tk
from tkinter import ttk
import itertools
f = ttk.Frame(width = 100, height = 100, padding = 5)
f.master.title('Test image in a label')
f.master.columnconfigure(0, weight = 1,)
f.master.rowconfigure(0, weight = 1)
f.columnconfigure(0, weight = 1)
f.rowconfigure(0, weight = 0)
f.rowconfigure(1, weight = 1)
f.grid(column = 0, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))
im1 = tk.PhotoImage(file='../l_rcv_ind.gif')
im2 = tk.PhotoImage(file='../l_rcv_ind_a.gif')
im3 = tk.PhotoImage(file='../l_rcv_ind_i.gif')
imcycle = itertools.cycle(('alternate', '!alternate'))

lfstyle = ttk.Style()
print('Element names:', lfstyle.element_names())
print('Image options:', lfstyle.element_options('image'))
lfstyle.configure('Data.TLabelFrame', borderwidth = 2, relief = tk.GROOVE, padding = (5, 0))
print('lfstyle: borderwidth={}, relief={}, padding={}'.format(lfstyle.lookup('Data.TLabelFrame', 'borderwidth'), lfstyle.lookup('Data.TLabelFrame', 'relief'), lfstyle.lookup('Data.TLabelFrame', 'padding')))
lfstyle.layout('Data.TLabelFrame', lfstyle.layout('TFrame'))

# Configure the label Style
lfstyle.configure('Ind.TLabel', background = 'white', relief = tk.GROOVE, border = 2, anchor = tk.CENTER)
lfstyle.map('Ind.TLabel', image = (('alternate', im2), ('!alternate', im3)))

l1 = ttk.Label(f, style = 'Ind.TLabel')
l1.image = im1

lf2 = ttk.LabelFrame(f, style = 'Data.TLabelFrame', text = 'My Data Label')
l2 = ttk.Label(lf2, text='Hi!')
l1.grid(column = 0, row = 0, sticky = (tk.N, tk.S))
lf2.grid(column = 0, row = 1, sticky = (tk.N, tk.S, tk.E, tk.W))
l2.grid(column = 0, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))

def dispnext():
	#print('Next image, instate:{}'.format(l1.state()))
	l1.state([imcycle.__next__()])
	schednext()

def schednext():
	global aid
	aid = f.after(1000, dispnext)

schednext()

f.mainloop()
f.after_cancel(aid)
