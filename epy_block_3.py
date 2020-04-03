"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt

SYMBOL_SIZE = 8


class blk(gr.basic_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self, startString='10101010', escapeString='10101010', endString='10101010', preambleString= '10101010', preambleLength = 10 ):  # only default arguments here
        """arguments to this functi show up as parameters in GRC"""
        gr.basic_block.__init__(
            self,
            name='Data Link Formatter',   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )
        self._startString    = startString 
        self._escapeString   = escapeString
        self._endString      = endString 
        self._preambleString = preambleString
        self._preambleLength = preambleLength
        self.message_port_register_out(pmt.intern('debug')) 
        self.message_port_register_in(pmt.intern('packet_in'))
        self.message_port_register_out(pmt.intern('packet_out')) 
        self.set_msg_handler(pmt.intern('packet_in'),self._handle_packet)
    def _parse_data_for_characters(self, dataList, index):
        resultSS   = True 
        resultEndS = True 
        resultEscS = True 
        for offset  in range(SYMBOL_SIZE):
            resultSS   = resultSS   and (dataList[index+offset]   == self._startString[offset]   )
            resultEndS = resultEndS and (dataList[index+offset]   == self._endString[offset]     )
            resultEscS = resultEscS and (dataList[index+offset]   == self._escapeString[offset]  )
        result = resultSS or resultEndS or resultEscS
        return result
    def _transform_data(self,packetList, size): 
        outputData = list(self._preambleString*self._preambleLength)
        outputData.extend(list(self._startString))
        iterator = iter(range(size))
        for index in iterator:
            if index >= (size - SYMBOL_SIZE +2):
                outputData.append(packetList[index]) 
            elif self._parse_data_for_characters(packetList, index):
                outputData.extend(list(self._escapeString))
                outputData.append(packetList[index])
                for times in range(SYMBOL_SIZE -1):
                    outputData.append(packetList[next(iterator, None)])
            else :
                outputData.append(packetList[index])
        return outputData
    def _byteList_to_pmtvector(self, byteList):
        length = len(byteList) 
        vector = pmt.make_u8vector(length,0)
        byteIterator = iter(range(length))
        for byte in byteIterator:
            pmt.u8vector_set(vector,byte, byteList[byte])
        return vector 
    def _handle_packet(self, pdu): 
        field       = pmt.car(pdu)
        lengthP     = pmt.to_python(pmt.dict_ref(field,pmt.intern('dataLength'), pmt.from_long(0)))+4
        packetTemp  = pmt.cdr(pdu)   
        packetList  = []
        packet      = pdu
        for index in range(lengthP):
            item = list(bin(pmt.u8vector_ref(packetTemp,index))[2:].zfill(8)) 
            packetList.extend(item)
        lengthP =  len(packetList)
        packetList = self._transform_data(packetList,lengthP)
        packetList.extend(list(self._endString))
        iterator = iter(packetList)
        byteList = [int("".join(sli),2) for sli in zip(*iter([iterator]*SYMBOL_SIZE))]
        data_pdu = self._byteList_to_pmtvector(byteList)
        packet = pmt.cons(pmt.make_dict(),data_pdu)
        self.message_port_pub(pmt.intern('packet_out'), packet)
    
