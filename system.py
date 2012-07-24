#!/usr/bin/env python

"""
A system which is being debugged.

The System object is a simple container for the BackEnd and Architecture of the
device under test. Extra facilities are provided by various mixins:

EvaluatorMixin: Allows arithmetic expressions to be evaluated in the context of
the system.

LoggerMixin: Provides logging capabilities for errors and other output which the
user may need to see.

DeviceMixin: Provides clean, error-checked, memoised, accessor functions for the
BackEnd.
"""

from architecture import get_architecture

from expression import EvaluatorMixin
from logger     import LoggerMixin
from device     import DeviceMixin


class System(EvaluatorMixin, LoggerMixin, DeviceMixin):
	
	def __init__(self, back_end, name = None):
		"""
		A container and interface between all the pieces related to a system.
		
		back_end is a BackEnd for the system
		
		name is a user-friendly name for display to the user when referring to this
		machine.
		"""
		EvaluatorMixin.__init__(self)
		LoggerMixin.__init__(self)
		DeviceMixin.__init__(self)
		
		self.back_end = back_end
		self.name     = name
		
		# Detect the board's architecture
		# TODO: Do something if the arch is -1 (error during detection)
		self.cpu_type, self.cpu_sub_type = self.get_cpu_type()
		self.architecture = get_architecture(self.cpu_type, self.cpu_sub_type)

