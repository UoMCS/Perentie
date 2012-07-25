#!/usr/bin/env python

"""
Utilities for formatting values in the UI
"""


def format_number(value, width_bits, sign_extend = False):
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
	formatted = formatted.rjust((width_bits+3) / 4, "0")
	formatted = "%s0x%s"%(sign, formatted)
	
	return formatted


def formatted_number_to_int(value):
	return int(value, 16)
