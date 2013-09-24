#!/usr/bin/env python3

import logging, sys

# Set up logging (based on Logging tutorial (file:///Users/dad/Dropbox/Documents/Python/python-3.3.2-docs-html/howto/logging.html#logging-basic-tutorial)

logLevel = logging.DEBUG
# create logger
logger = logging.getLogger('scanmon')
logger.setLevel(logLevel)

# Create console handler and set level
ch = logging.StreamHandler(stream = sys.stderr)
ch.setLevel(logLevel)

# Create formatter
formatter = logging.Formatter(fmt = '{asctime} - {name} - {levelname} - {message}',
	style = '{')

# Add formatter to ch
ch.setFormatter(formatter)

logger.addHandler(ch)

# Log a DEBUG
logger.debug('Got err: %d: %s', 101, 'Seriously!')

# And an INFO
logger.info('FYI: %(lvl)d, %(mymsg)s', dict(lvl = 2, mymsg = 'A stupid message'), stack_info = True)

try:
	infinity = 1 / 0
except:
	logger.exception('Bad news')
	