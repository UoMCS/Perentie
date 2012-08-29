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

import re

from collections import namedtuple
from tokenize    import generate_tokens, untokenize, NAME, NUMBER
from StringIO    import StringIO

from util.lazy   import as_needed

from view import format

################################################################################

# Regexes which match parts of numbers in various bases
BASE_CHARS = {
	"0x": re.compile("^[0-9a-f]+$", re.I),
	"":   re.compile("^[0-9]+$", re.I),
	"0o": re.compile("^[0-7]+$", re.I),
	"0b": re.compile("^[01]+$", re.I),
}

################################################################################

from math import *
from functools import reduce

from back_end.util import i2b, b2i

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
		
		# Symbol values
		self.evaluator_symbol_vars = {}
	
	
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
			"sign_extend", "b2i", "i2b",
			
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
		self.evaluator_local_vars["min"]   = min
		self.evaluator_local_vars["max"]   = max
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
	
	
	def _change_default_base(self, expr, new_prefix):
		"""
		Given some python code, add a prefix to all numbers with no existing
		base-prefix. May prevent access to certain variables who's names happen to
		be valid hex strings. Also prevents the use of the leading-zero octal
		syntax when not using decimal (i.e. prefix="") which is probably what you
		want.
		
		This uses the python tokeniser to help find all the literals and then stick
		the appropriate prefix on them. The major catch here is that for hex numbers
		the tokeniser may chop it into number and name parts (as the lack of a
		prefix could make it look like a load of numbers and variable names). As a
		result we need to detect when this happens and stick them back together as a
		number field with a propper prefix.
		"""
		if new_prefix == "":
			# Why bother? Also means we don't need scary special cases later to allow
			# leading-zero octal syntax when in decimal mode.
			return expr
		
		# The ordered set of (type, string) tokens from which a new string will be
		# generated.
		out_tokens = []
		
		# A list of previous tokens which might be concatenated with a following
		# set. A list of tuples (type, str, end_char_index).
		prv_tokens = []
		
		def cat_tokens(prv_tokens):
			"""
			Concatenate all tokens in prv_tokens prepending them with the new_prefix.
			"""
			# The string, without leading zeros.
			no_padding = ("".join(tok[1] for tok in prv_tokens)).lstrip("0").zfill(1)
			out_tokens.append((NUMBER, "%s%s"%(new_prefix, no_padding)))
		
		for token in generate_tokens(StringIO(expr).readline):
			# Break appart the token fields
			token_type, string, (_,start), (_,end), _ = token
			
			# See if we can cat the token onto the currently built up input (and
			# continue if we manage)
			if token_type in (NAME, NUMBER) and BASE_CHARS[new_prefix].match(string):
				# We have a potential piece of a number (as bits of hex numbers might
				# get picked up as a name)
				
				if len(prv_tokens) == 0 and string[:2].lower() not in ("0x","0o","0b"):
					# This is the first part of a number and it isn't already prefixed
					prv_tokens.append((token_type, string, end))
					continue
				elif (len(prv_tokens) > 0
				      and prv_tokens[-1][2] == start):
					# This token touches the previous one! Looks good!
					prv_tokens.append((token_type, string, end))
					continue
			
			# Fall-through to here if not able to built up a number
			
			# Cat together any tokens previously built up
			if prv_tokens:
				cat_tokens(prv_tokens)
				prv_tokens = []
			
			# Put the current token into the output
			out_tokens.append((token_type, string))
		
		# Cat the remaining tokens on the queue
		if prv_tokens:
			cat_tokens(prv_tokens)
		
		return untokenize(out_tokens)
	
	
	def evaluator_update_symbols(self):
		"""
		Update the set of symbols.
		"""
		self.evaluator_symbol_vars = {}
		for symbols in self.image_symbols.itervalues():
			for symbol, (value,symbol_type) in symbols.iteritems():
				self.evaluator_symbol_vars[symbol] = value
	
	
	def evaluate(self, expr):
		"""
		Evaluate an expression within the context of the system. Expressions should
		be valid python expressions with various variables defined.
		"""
		
		# When the prefix is not shown, change the prefix of non-prefixed numbers to
		# the current prefix
		if not format.format_show_prefix:
			expr = self._change_default_base(expr, format.format_prefix)
		
		# Add the symbols to the evaluation variables
		local_vars = self.evaluator_local_vars.copy()
		local_vars.update(self.evaluator_symbol_vars)
		
		value = eval(expr, self.evaluator_global_vars, local_vars)
		
		if type(value) is str:
			# Convert strings (of bytes/chars) into an int
			return b2i(value)
		else:
			# Cast everything else to an int
			return int(value)
