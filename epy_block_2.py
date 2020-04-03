"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt


class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self, threshold = 0.5):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='input detector',   # will show up in GRC
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self._threshold = threshold
        self._power     = False
        self._key       = pmt.intern('Power')

    def work(self, input_items, output_items):
        for ind, sample in enumerate(input_items[0]):
            if not self._power:
                if  abs(sample) >= self._threshold:
                    self.add_item_tag(0,self.nitems_written(0) + ind,self._key, pmt.from_bool(True))
                    self._power = True
            else:
                if abs(sample) < self._threshold:
                    self.add_item_tag(0,self.nitems_written(0) + ind, self._key, pmt.from_bool(False))
                    self._power = False
        output_items[0][:] = input_items[0]
        return len(output_items[0])
