#!/usr/bin/env python

"""
Views for various supported device peripherals.
"""


from xilinx import Spartan3


# Mapping of (id, sub_id0, sub_id1) to (name, view) where view may be None if no view is
# available. If the sub_id0/1 is none, any value matches.
PERIPHERALS = {
	(0x0, None, None): ("Terminal", None),
	
	(0x8, None, None): ("Performance Monitor", None),
	
	(0x11, None, None): ("Xilinx Spartan XL", None),
	(0x12, None, None): ("Xilinx Virtex", None),
	(0x13, None, None): ("Xilinx Virtex-E", None),
	
	(0x14, 0x00, None): ("Xilinx Spartan-3 XC3S50",   Spartan3),
	(0x14, 0x02, None): ("Xilinx Spartan-3 XC3S200",  Spartan3),
	(0x14, 0x04, None): ("Xilinx Spartan-3 XC3S400",  Spartan3),
	(0x14, 0x0A, None): ("Xilinx Spartan-3 XC3S1000", Spartan3),
	(0x14, 0x0F, None): ("Xilinx Spartan-3 XC3S1500", Spartan3),
	(0x14, 0x14, None): ("Xilinx Spartan-3 XC3S2000", Spartan3),
	(0x14, 0x28, None): ("Xilinx Spartan-3 XC3S4000", Spartan3),
	(0x14, 0x32, None): ("Xilinx Spartan-3 XC3S5000", Spartan3),
}


def get_peripheral_view(periph_id, periph_sub_id):
	"""
	Get the view widget class for the given peripheral ID/sub-ID. Returns a pair
	(name, view) or None if the peripheral is unknown. If no view is available,
	view will be None.
	"""
	
	periph_sub_id0 = (periph_sub_id>>8) & 0xFF
	periph_sub_id1 = (periph_sub_id>>0) & 0xFF
	
	# Peripherals may match any of the following (in descending order of priority)
	matchables = (
		(periph_id, periph_sub_id0, periph_sub_id1),
		(periph_id, None,           None),
		(periph_id, periph_sub_id0, None),
		(periph_id, None,           periph_sub_id1),
	)
	
	# Return the matching view
	for key in matchables:
		if key in PERIPHERALS:
			return PERIPHERALS[key]
	
	# Not found
	return None

