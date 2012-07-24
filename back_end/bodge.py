#!/usr/bin/env python

"""
XXX: Bodges for working around the back-end's limitations.

The back-end only supports sending elements of size 1, 2, 4 or 8 bytes. As a
result, all values sent must be padded to this length.
"""

from util import bits_to_bytes


def xxx_pad_width(width_bits):
	"""
	Pad the given width in bits to an allowed number.
	"""
	
	assert(width_bits <= 64)
	return filter((lambda n: width_bits <= n), [8, 16, 32, 64])[0]
