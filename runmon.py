#!/usr/bin/env python

import sys

need_paths = ('/sw/lib/python3.3', '/sw/lib/python3.3/site-packages')

for mypath in need_paths:
	if mypath not in sys.path:
		print('Adding {} to sys.path'.format(mypath))
		sys.path.append(mypath)

from scanmon import Scanmon

mon = Scanmon()
mon.runit()
mon.destroy()