#!/usr/bin/env python

"""
Definitions of the various architectures that can be debugged.
"""


from arm   import ARM
from stump import STUMP
from mu0   import MU0


ARCHITECTURES = {
	1: ARM,
	# 2: MIPS, # Not implemented
	3: STUMP,
	4: MU0,
}


class UnknownArchitecture(Exception):
	"""
	Raised when an unknown architecture is requested.
	"""
	pass


def get_architecture(cpu, cpu_subtype):
	"""
	Get the definition associated with the provided cpu and cpu_subtype.
	"""
	
	if cpu in ARCHITECTURES:
		return ARCHITECTURES[cpu](cpu, cpu_subtype)
	else:
		raise UnknownArchitecture("Unknown Architecture %02X/%02X"%(cpu, cpu_subtype))
