#!/usr/bin/env python

"""
An expression evaluator for mixing into the System. Expressions are any valid
python expression.

Available functions:
* int, float
* abs
* chr, ord
* Most of the math library + log2
* sign_extend(value, from_num_bits)

Available variables:
* reg_bank_name.reg_name
* reg_name (for register bank 0 registers only)
"""

from collections import namedtuple
from util.lazy   import as_needed

################################################################################

from math import *
from functools import reduce

def log2(num):
	return log(num,2)


def sign_extend(value, bits):
	"""
	Sign extend the b-bit number n into a python integer
	"""
	return value | ((-1<<length) if bool(value >> length-1) else 0)

################################################################################


class EvaluatorMixin(object):
	"""
	An expression evaluator for mixing in with a System
	"""
	
	def __init__(self):
		# Don't allow any globals in
		self.evaluator_global_vars = {"__builtins__" : None}
		
		# Allow a specific set of locals
		self.evaluator_local_vars = {}
	
	
	def init_evaluator(self):
		"""
		Set-up the evaluator with the current system architecture.  Pre-generate
		static lists of allowed values.
		"""
		# Don't allow any globals in
		self.evaluator_global_vars = {"__builtins__" : None}
		
		# Allow a specific set of locals
		self.evaluator_local_vars = {}
		
		# The following functions are safe and allowed
		safe_funcs = [
			# Utility functions
			"sign_extend",
			
			# Math functions
			"acos", "asin", "atan", "atan2", "ceil", "cos", "cosh", "degrees", "e",
			"exp", "fabs", "floor", "fmod", "frexp", "hypot", "ldexp", "log", "log10",
			"log2", "modf", "pi", "pow", "radians", "sin", "sinh", "sqrt", "tan",
			"tanh",
		]
	
		# Add the safe functions
		for func_name in safe_funcs:
			if func_name in locals():
				self.evaluator_local_vars[func_name] = locals()[func_name]
			elif func_name in globals():
				self.evaluator_local_vars[func_name] = globals()[func_name]
			else:
				assert(False)
		
		# Add various useful builtins
		self.evaluator_local_vars["abs"]   = abs
		self.evaluator_local_vars["int"]   = int
		self.evaluator_local_vars["float"] = float
		self.evaluator_local_vars["ord"]   = ord
		self.evaluator_local_vars["chr"]   = chr
		
		# Functional stuff
		self.evaluator_local_vars["sum"]    = sum
		self.evaluator_local_vars["map"]    = map
		self.evaluator_local_vars["reduce"] = reduce
		
		self._add_memory_accessors()
		self._add_register_accessors()
	
	
	@as_needed
	def lazy_read_register(self, register):
		"""
		This function returns a variable-like object which, when accessed, requests
		the value of the register from the device. By doing this registers are not
		fetched unless they're actually used. This allows these to be defined for
		every register for the evaluator to use as it sees fit.
		"""
		return self.read_register(register)
	
	
	class MemoryAccessor(object):
		"""
		A memory accessor object which behaves like an array.
		"""
		
		def __init__(self, system, memory):
			self.system = system
			self.memory = memory
		
		
		def __getitem__(self, start):
			return self(start)
		
		
		def __getslice__(self, start, end):
			return self(start, end)
		
		
		def __call__(self, start, end = None, elem_size = 1):
			"""
			Read from the start address up to the end address getting elements of the
			given size (in words)
			"""
			assert(elem_size >= 1)
			
			if end is None:
				end = start + elem_size
			
			assert(start < end)
			length = (end - start) / elem_size
			words = self.system.read_memory(self.memory, elem_size, start, length)
			
			# Concatenate the returned words
			out = 0
			for word in words[::-1]:
				out <<= self.memory.word_width_bits
				out  |= word
			return out
	
	
	def _add_memory_accessors(self):
		if self.architecture is None:
			return
		
		for memory in self.architecture.memories:
			accessor = EvaluatorMixin.MemoryAccessor(self, memory)
			for name in memory.names:
				self.evaluator_local_vars[name] = accessor
	
	
	def _add_register_accessors(self):
		"""
		Add register accessors to the local_vars dictionary.
		"""
		if self.architecture is None:
			return
		
		# Add variables for each register in the system
		for num, register_bank in enumerate(self.architecture.register_banks):
			# Create a set of accessor objects for each register
			register_accessors = {}
			for register in register_bank.registers:
				# Define an accessor for each register alias
				lazy_accessor = self.lazy_read_register(register)
				# Add the register under each of its aliases
				for name in register.names:
					register_accessors[name] = lazy_accessor
					
					# If this is the first register bank, its registers are available
					# without using a prefix.
					if num == 0:
						self.evaluator_local_vars[name] = lazy_accessor
			
			# Create an object which has a property for each register
			RegisterBankTuple = namedtuple(register_bank.name,
			                               register_accessors.keys())
			register_bank_tuple = RegisterBankTuple(*register_accessors.values())
			
			# Add this register bank under each of its aliases
			for name in register_bank.names:
				self.evaluator_local_vars[name] = register_bank_tuple
	
	
	def evaluate(self, expr):
		"""
		Evaluate an expression within the context of the system. Expressions should
		be valid python expressions with various variables defined.
		"""
		
		return int(eval(expr, self.evaluator_global_vars, self.evaluator_local_vars))
