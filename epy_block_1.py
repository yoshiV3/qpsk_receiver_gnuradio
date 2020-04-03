"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt


class blk(gr.basic_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.basic_block.__init__(
            self,
            name='Packet Source',   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )
        self.message_port_register_out(pmt.intern('msg_out'))
        self.message_port_register_in(pmt.intern('msg_in'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)
    def handle_msg(self, msg):
        meta = pmt.make_dict()
        meta = pmt.dict_add(meta,pmt.intern('dataLength'),pmt.from_long(1)) 
        self.message_port_pub(pmt.intern('msg_out'), pmt.cons(meta, pmt.make_u8vector(100, 135)))
