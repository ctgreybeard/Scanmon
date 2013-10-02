#!/usr/bin/env python
'''
threadqueueexec.py - Test a queue scheme to do callbacks from the main thread
'''

from tkinter import *
from tkinter import ttk

import time
from threading import Thread, Barrier
from queue import Queue, Empty

class Request:
	def __init__(self, method, *args, **kwargs):
		self.method = method
		self.args = args
		self.kwargs = kwargs
		#print('Created request for {}, args={}, kwargs={}'.format(str(method), str(args), str(kwargs)))

class ThreadQueueExec(ttk.Frame):
	def __init__(self):
		ttk.Frame.__init__(self, None, width = 800, height = 600, pad = 25)
		
		self.master.title('Test thread exec queue')
		
		self.runqueue = Queue()
		
		self.columnconfigure(0, weight = 1, pad = 10)
		self.columnconfigure(1, weight = 1, pad = 10)
		self.rowconfigure(0, weight = 1)
		self.grid()
		
		ttk.Button(self, text = 'Start', command = self.doStart).grid(column = 0, row = 0)
		self.started = False
		ttk.Button(self, text = 'Stop', command = self.doStop).grid(column = 1, row = 0)
		
		self.myThread = None
		
		print('Initialized')
	
	def doStop(self):
		print('doStop')
		if self.myThread is not None:
			self.myThread.doStop()
			self.myThread.join(timeout = 5)
		self.quit()
	
	def doStart(self):
		print('doStart')
		if not self.started:
			self.myThread = MyThread(self.runqueue, name = 'myThread')
			self.myThread.start()
			self.started = True
	
	def checkQueue(self):
		try:
			while True:
				req = self.runqueue.get(block = False)	# Quarter second timeout
				#print('Request: {}'.format(str(req)))
				req.method(*req.args, **req.kwargs)
		except Empty:
			#print('Empty')
			self.after(250, self.checkQueue)	# Requeue ourselves
	
	def run(self):
		print('Running')
		self.after(250, self.checkQueue)	# Queue the queue
		self.mainloop()
		

class MyThread(Thread, Toplevel):
	def __init__(self, their_queue, **kw):
		Thread.__init__(self, **kw)
		Toplevel.__init__(self, height = 800, width = 600)
		
		self.their_queue = their_queue
		
		self.build_window()
		
		self.is_running = True
		
		print('Thread initialized')
	
	def build_window(self):
		self.columnconfigure(0, weight = 1, pad = 5)
		self.columnconfigure(1, weight = 1, pad = 5)
		self.rowconfigure(0, weight = 1)
		
		self.tv_counter = StringVar()
		ttk.Label(self, textvariable = self.tv_counter, anchor = E, width = 5).grid(column = 0, row = 0, sticky = E)
		ttk.Label(self, text = 'Counter', anchor = W).grid(column = 1, row = 0, sticky = W)
		
	def doStop(self):
		print('Thread stopping')
		self.is_running = False
		
	def run(self):
		print('Thread running')
		counter = 0
		while self.is_running:
			time.sleep(1.0)
			counter += 1
			newreq = Request(self.tv_counter.set, str(counter))
			self.their_queue.put(newreq)

if __name__ == '__main__':	# Called directly
	tqe = ThreadQueueExec()
	tqe.run()