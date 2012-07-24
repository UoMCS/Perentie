#!/usr/bin/env python

"""
Utility functions.
"""


def i2b(num, num_bytes):
	"""
	Convert a number into bytes
	"""
	out = ""
	for byte in range(num_bytes):
		out += chr(num & 0xFF)
		num >>= 8
	return out


def b2i(data):
	"""
	Convert a stream of bytes into a number
	"""
	out = 0
	for char in data[::-1]:
		out <<= 8
		out |= ord(char)
	return out


# Conversion of numbers into various length byte streams
def byte(num): return i2b(num, 1)
def half(num): return i2b(num, 2)
def word(num): return i2b(num, 4)
def dblw(num): return i2b(num, 8)



def bits_to_bytes(bits):
	"""
	Round up to the next whole number of bytes.
	"""
	return (bits + 7) / 8
