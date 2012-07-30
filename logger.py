#!/usr/bin/env python

"""
An event logger for mixing into the system.
"""

class LoggerMixin(object):
	"""
	Log of system events/output
	"""
	
	def __init__(self):
		self.event_log = []
		
		# List of callbacks to call when logging occurs
		self._on_log = []
	
	
	def add_callback(self, callback, *args, **kwargs):
		"""
		Add a callback whenever a logging event occurs.
		  callback(message, flag, *args, **kwargs)
		"""
		self._on_log.append((callback, args, kwargs))
	
	
	def log(self, message, flag = False):
		"""
		Add a message to the log. If flag is true then the user will be shown the
		log automatically.
		"""
		
		self.event_log.append((message, flag))
		
		for callback, args, kwargs in self._on_log:
			callback(message, flag, *args, **kwargs)
		
		print repr(message)
