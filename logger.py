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
	
	
	def log(self, message, flag = False):
		"""
		Add a message to the log. If flag is true then the user will be shown the
		log automatically.
		"""
		
		self.event_log.append((message, flag))
		print repr(message)
