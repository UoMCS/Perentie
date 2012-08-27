#!/usr/bin/env python

"""
An event logger for mixing into the system.
"""

import sys
import traceback

from threading import Lock

class LoggerMixin(object):
	"""
	Log of system events/output
	"""
	
	def __init__(self):
		self.log_lock = Lock()
		
		self.event_log = []
		
		# List of callbacks to call when logging occurs
		self._on_log = []
		
		
	
	
	def on_log(self, callback, *args, **kwargs):
		"""
		Add a callback whenever a logging event occurs.
		  callback(exception, flag, source, *args, **kwargs)
		"""
		with self.log_lock:
			self._on_log.append((callback, args, kwargs))
	
	
	def log(self, exception, flag = False, source = None):
		"""
		Add a exception to the log. If flag is true then the user will be shown the
		log automatically. The source argument can be a string describing where the
		error occurred.
		"""
		
		with self.log_lock:
			trace = traceback.format_exc()
			
			sys.stderr.write(trace)
			
			self.event_log.append((exception, trace, flag, source))
			
			callbacks = self._on_log[:]
		
		for callback, args, kwargs in callbacks:
			callback(exception, trace, flag, source, *args, **kwargs)
