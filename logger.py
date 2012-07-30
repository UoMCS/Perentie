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
	
	
	def on_log(self, callback, *args, **kwargs):
		"""
		Add a callback whenever a logging event occurs.
		  callback(exception, flag, *args, **kwargs)
		"""
		self._on_log.append((callback, args, kwargs))
	
	
	def log(self, exception, flag = False):
		"""
		Add a exception to the log. If flag is true then the user will be shown the
		log automatically.
		"""
		
		self.event_log.append((exception, flag))
		
		for callback, args, kwargs in self._on_log:
			callback(exception, flag, *args, **kwargs)
		
		print repr(exception)
