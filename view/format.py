#!/usr/bin/env python

"""
Utilities for formatting values in the UI. Contains two variables (base and
show_prefix) which can be changed to alter the format of values produced.

This module is slightly hacky as its interface was later updated to allow the
base to be changed.
"""

# What base should numbers be shown in
format_base = 16

# Should prefixes be added to represent the base
format_show_prefix = False

# Call to update the formatting info after changing format_base
def _base_changed():
	global format_base, format_digits, format_max_width, format_prefix
	format_digits = {
		2:  (lambda num: bin(num)[2:] if num >= 0 else "-%s"%(bin(num)[3:])),
		8:  (lambda num: "%o"%num),
		10: (lambda num: "%d"%num),
		16: (lambda num: "%X"%num),
	}[format_base]
	format_max_width = {
		2:  (lambda width_bits:  width_bits),
		8:  (lambda width_bits: (width_bits+2) / 3),
		10: (lambda width_bits: 0), # Don't zero-pad for decimal
		16: (lambda width_bits: (width_bits+3) / 4),
	}[format_base]
	format_prefix = {
		2:  "0b",
		8:  "0o",
		10: "", # No prefix for decimal numbers
		16: "0x",
	}[format_base]
_base_changed()


def set_base(base):
	"""
	Change the base numbers are formatted into.
	"""
	global format_base
	format_base = base
	_base_changed()


def set_show_prefix(show_prefix):
	"""
	Show or don't show the prefix such as 0x for hex.
	"""
	global format_show_prefix
	format_show_prefix = show_prefix


def format_number(value, width_bits, sign_extend = False):
	"""
	Format a number in the current base. This is used for values from the device
	for example register or memory values and addresses but generally not for
	scalars such as "number of steps".
	"""
	# Truncate to fit in the field
	value &= (1<<width_bits) - 1
	
	# Put the sign back on if the top bit is set
	if sign_extend:
		value |= (-1 << width_bits) if bool(value >> (width_bits-1)) else 0
		width_bits -= 1
	
	# Format in the selected base
	formatted = format_digits(value)
	
	# Chop off the sign character (to prepend to the start, after the prefix)
	sign = ""
	if formatted[0] == "-":
		sign = "-"
		formatted = formatted[1:]
	
	# Pad with zeros
	formatted = formatted.zfill(format_max_width(width_bits))
	
	# Add the prefix/sign
	formatted = "%s%s%s"%(sign, format_prefix if format_show_prefix else "", formatted)
	
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
