#!/usr/bin/env python

"""
Utilities for formatting values in the UI
"""


def format_number(value, width_bits, sign_extend = False):
	value &= (1<<width_bits) - 1
	
	if sign_extend:
		value |= (-1 << width_bits) if bool(value >> (width_bits-1)) else 0
		width_bits -= 1
	
	formatted = "%X"%value
	
	# Chop off the sign (to prepend to the start)
	sign = ""
	if formatted[0] == "-":
		sign = "-"
		formatted = formatted[1:]
	
	# Pad and prepend with 0x
	formatted = formatted.zfill((width_bits+3) / 4)
	formatted = "%s0x%s"%(sign, formatted)
	
	return formatted


def format_ascii(value, width_bits, char_width = 8):
	"""
	Convert an int into ascii chars.
	"""
	out = ""
	for _ in range(max(1, ((width_bits+char_width-1) / char_width))):
		# Mask of the char
		char = value & ((1<<char_width)-1)
		
		if 32 <= char < 127:
			# Display printable chars
			out += chr(char)
		else:
			# Display a . instead of non-printing chars
			out += "."
		
		value >>= char_width
	
	return out


def formatted_number_to_int(value):
	return int(value, 16)


def format_storage_size(value_bits):
	"""
	Takes a size in bits and returns a string with the largest possible postfix.
	"""
	divisors = (
		(1, "b"),
		(8, "B"),
		(1024, "KB"),
		(1024, "MB"),
		(1024, "GB"),
		(1024, "TB"),
	)
	
	last_postfix = None
	for divisor, postfix in divisors:
		if value_bits % divisor == 0:
			value_bits /= divisor
			last_postfix = postfix
		else:
			return "%d %s"%(value_bits, last_postfix)
