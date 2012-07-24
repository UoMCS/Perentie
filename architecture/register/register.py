#!/usr/bin/env python

"""
Register bank architecture modeling.
"""


class Register(object):
	
	def __init__(self, names, width_bits, addr, pointer = None, bit_field = None):
		"""
		A register in a system.
		
		names is a list of names which may refer to this register (the first is used
		as the default for display/output). Must be valid python variable names.
		
		width_bits is the width in bits for this register.
		
		addr is the address of this register in the "register address space" exposed
		by the device itself.
		
		pointer is None if this register should not be displayed as a pointer or a
		Pointer object describing how the pointer should be displayed.
		
		bit_field is None if the register holds an integer value or a BitField
		object which describes the bit-field which the register holds (e.g. for
		flags).
		"""
		self.names      = names
		self.width_bits = width_bits
		self.addr       = addr
		self.pointer    = pointer
		self.bit_field  = bit_field
	
	
	@property
	def name(self):
		"""
		An alias for the default name.
		"""
		return self.names[0]



class RegisterBank(object):
	
	def __init__(self, names, registers):
		"""
		A register bank consisting of an (ordered) set of possibly-hetrodgenous
		registers.
		
		names is a list of names which may refer to this register bank (the first is
		used as the default for display/output). Must be valid python variable
		names.
		
		registers is a list of Registers which are contained in the bank.
		"""
		self.names     = names
		self.registers = registers
	
	
	@property
	def name(self):
		"""
		An alias for the default name.
		"""
		return self.names[0]



class Pointer(object):
	
	def __init__(self, memory_nums, category = None):
		"""
		An object which defines that a register it is held by is pointing into
		memory.
		
		memory_nums is a list of memories into which this register might be a
		pointer.
		
		category is an optional string which defines the type of pointer this is or
		None if it is general purpose. Examples would be "PC" or "LR".
		"""
		self.memory_nums = memory_nums
		self.category    = category



class BitField(object):
	
	# Bit field types
	BIT  = object()
	INT  = object()
	UINT = object()
	ENUM = object()
	
	def __init__(self, fields):
		"""
		Description of a bit field within a register.
		
		fields is a list of tuples in one of the following forms:
		
		Boolean field
		  (bit, "name")
		
		Integer field (supports split field by specifying multiple (inclusive)
		ranges which are concatinated together with the left most field being most
		significant) which may be signed if the 3rd element is True and unsigned if
		False.
		  (((6,2), (1,0) ...), "name", signed)
		
		Enumerated field (supports split field as for integer fields) where the None
		value may be displayed if none of the others match.
		  (((0,1), ...), "name", {0b0000: "enum0",
		                          0b0001: "enum1",
		                          None:   "enum_undefined"})
		"""
		
		self.fields = fields
	
	
	@property
	def field_names(self):
		"""
		Get the name of each of the fields.
		"""
		return [field[1] for field in self.fields]
	
	
	@property
	def field_types(self):
		"""
		List of field types that are contained in the register. One of:
			BitField.BIT
			BitField.INT
			BitField.UINT
			BitField.ENUM
		"""
		
		field_types = []
		
		for field in self.fields:
			if type(field[0]) is int:
				field_types.append(BitField.BIT)
			elif type(field[1]) is dict:
				field_types.append(BitField.ENUM)
			elif field[2] == True:
				field_types.append(BitField.INT)
			else:
				assert(field[2] == False)
				field_types.append(BitField.UINT)
		
		return field_types
	
	
	def decode(self, value):
		"""
		Decode a bit-field (from an integer, value) into a list of values.
		"""
		
		out = []
		
		def get_sub_field(ranges, value):
			"""
			Concatenate a split field returning the length in bits and the value.
			"""
			out = 0
			length = 0
			for first,last in ranges:
				for bit in range(first,last-1, -1):
					out <<= 1
					out |= (value >> bit) &1
					
					length += 1
			
			return (length, out)
		
		
		def sign_extend(value, length):
			return value | ((-1<<length) if bool(value >> length-1) else 0)
		
		
		# Convert each field
		for field_def, field_type in zip(self.fields, self.field_types):
			# Single Bit
			if field_type == BitField.BIT:
				out.append(bool(value & (1<<field_def[0])))
			
			# An integer (signed or unsigned)
			elif field_type in (BitField.INT, BitField.UINT):
				length, sub_field = get_sub_field(field_def[0])
				
				if field_types == BitField.INT:
					sub_field = sign_extend(sub_field)
				
				out.append(sub_field)
			
			# An enumerated type
			elif field_type == BitField.ENUM:
				length, sub_field = get_sub_field(field_def[0])
				if sub_field in field_def[2]:
					out.append(field_def[2][sub_field])
				elif None in field_def[2]:
					out.append(field_def[2][None])
				else:
					out.append(None)
			
			else:
				assert(False)
		
		return out
	
	
	def encode(self, field_values):
		"""
		Convert a sequence of field values into an integer field.
		"""
		value = 0
		
		
		def generate_sub_field(ranges, value):
			"""
			Expand a value into its subfields.
			"""
			out = 0
			for first,last in ranges[::-1]:
				sub_field_size = (first - last) + 1
				sub_field = value & ((1<<sub_field_size) - 1)
				value >>= sub_field_size
				
				out |= sub_field << last
			
			return out
		
		
		def enum_val_to_key(enum, search_val):
			"""
			Find the actual value for an enumeration given the element name. Returns
			None if unknown.
			"""
			for key, val in enum.iteritems():
				if val == search_val:
					return key
			return None
		
		
		# Convert each field
		for field_value, field_def, field_type in zip(field_values,
		                                              self.fields,
		                                              self.field_types):
			# Single bit
			if field_type == BitField.BIT:
				value |= int(bool(field_value)) << field_def[0]
			
			# Integer signed/unsigned
			elif field_type in (BitField.INT, BitField.UINT):
				value |= generate_sub_field(field_def[0], field_value)
			
			# Enumerated type
			elif field_type == BitField.ENUM:
				# Get the value associated with this enumeration value (default to 0)
				enum_key = enum_val_to_key(field_def[2], field_value) or 0
				
				# Expand it over the subfields of the bit-field.
				value |= generate_sub_field(field_def[0], enum_key)
			
			else:
				assert(None)
		
		return value
