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
imd = '''#define l_rcv_ind_r_width 18
#define l_rcv_ind_r_height 18
static unsigned char l_rcv_ind_r_bits[] = {
   0xe0, 0x1f, 0x00, 0xf8, 0x7f, 0x00, 0xfc, 0xff, 0x00, 0xfe, 0xff, 0x01,
   0xfe, 0xff, 0x01, 0xff, 0xff, 0x03, 0xff, 0xff, 0x03, 0xff, 0xff, 0x03,
   0xff, 0xff, 0x03, 0xff, 0xff, 0x03, 0xff, 0xff, 0x03, 0xff, 0xff, 0x03,
   0xff, 0xff, 0x03, 0xfe, 0xff, 0x01, 0xfe, 0xff, 0x01, 0xfc, 0xff, 0x00,
   0xf8, 0x7f, 0x00, 0xe0, 0x1f, 0x00 };'''

lfstyle = ttk.Style()
print('Element names:', lfstyle.element_names())
print('Image options:', lfstyle.element_options('image'))
lfstyle.configure('Data.TLabelframe', borderwidth = 3, relief = tk.GROOVE, padding = (5, 0))
print('lfstyle: borderwidth={}, relief={}, padding={}'.format(lfstyle.lookup('Data.TLabelframe', 'borderwidth'), lfstyle.lookup('Data.TLabelFrame', 'relief'), lfstyle.lookup('Data.TLabelFrame', 'padding')))

fbcycle = itertools.cycle(('#ee0', '#0ee'))
lfstyle.configure('TFrame', background = '#000')
lbk = lfstyle.lookup('TLabel', 'background')
print('Label background={}'.format(lbk))
imd_b = tk.BitmapImage(data = imd, background = lbk, foreground = '#00e')
imd_r = tk.BitmapImage(data = imd, background = lbk, foreground = '#e00')
imd_g = tk.BitmapImage(data = imd, background = lbk, foreground = '#0e0')
# Configure the label Style
lfstyle.configure('Ind.TLabel', relief = tk.GROOVE, border = 3, anchor = tk.CENTER)
lfstyle.map('Ind.TLabel', image = (('alternate', imd_g), ('!alternate', imd_r)))
l1 = ttk.Label(f, style = 'Ind.TLabel')
l1.image = imd_b

lf2 = ttk.LabelFrame(f, style = 'Data.TLabelframe', text = 'My Data Label')
l2 = ttk.Label(lf2, text='Hi!')
l1.grid(column = 0, row = 0, sticky = (tk.N, tk.S))
lf2.grid(column = 0, row = 1, sticky = (tk.N, tk.S, tk.E, tk.W))
l2.grid(column = 0, row = 0, sticky = (tk.N, tk.S, tk.E, tk.W))

def dispnext():
	#print('Next image, instate:{}'.format(l1.state()))
	l1.state([imcycle.__next__()])
	lfstyle.configure('TFrame', background = fbcycle.__next__())
	schednext()

def schednext():
	global aid
	aid = f.after(1000, dispnext)

schednext()

f.mainloop()
f.after_cancel(aid)
