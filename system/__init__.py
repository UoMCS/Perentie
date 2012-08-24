#!/usr/bin/env python

"""
A system which is being debugged.

The System object is a simple container for the BackEnd and Architecture of the
device under test. Extra facilities are provided by various mixins:

LoggerMixin: Provides logging capabilities for errors and other output which the
user may need to see.

DeviceMixin: Provides clean, error-checked, memoised, accessor functions for the
BackEnd.

AssemblerLoaderMixin: Provides an interface for assembling/loading files.

AnnotatorMixin: Provides annotation data for memory views.

EvaluatorMixin: Allows arithmetic expressions to be evaluated in the context of
the system.
"""

from architecture import get_architecture, UnknownArchitecture

from logger           import LoggerMixin
from device           import DeviceMixin
from assembler_loader import AssemblerLoaderMixin
from annotator        import AnnotatorMixin
from expression       import EvaluatorMixin


class System(LoggerMixin,
             DeviceMixin,
             AssemblerLoaderMixin,
             AnnotatorMixin,
             EvaluatorMixin):
	
	def __init__(self, back_end, name = "System"):
		"""
		A container and interface between all the pieces related to a system.
		
		back_end is a BackEnd for the system
		
		name is a user-friendly name for display to the user when referring to this
		machine.
		"""
		LoggerMixin.__init__(self)
		DeviceMixin.__init__(self)
		AssemblerLoaderMixin.__init__(self)
		AnnotatorMixin.__init__(self)
		EvaluatorMixin.__init__(self)
		
		self.back_end     = back_end
		self.name         = name
		self.architecture = None
		
		self.init_evaluator()
		self.update_architecture()
	
	
	def update_architecture(self):
		"""
		Update the architecture used by the system
		"""
		# Detect the board's architecture
		self.cpu_type, self.cpu_subtype = self.get_cpu_type()
		if self.cpu_type != -1 and self.cpu_subtype != -1:
			try:
				self.architecture = get_architecture(self.cpu_type, self.cpu_subtype)
			except UnknownArchitecture:
				self.architecture = None
			
			# Update the evaluator's view of the system
			self.init_evaluator()
			
			# Clear the assembly/source file
			self.set_source_filename(None)
		else:
			raise Exception("System did not respond.")

