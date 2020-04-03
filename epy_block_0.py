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

    def __init__(self, startOfFrame = '10101010' , endOfFrame='10101010',escapeCharacter='10101010',threshold = 0): 
        gr.sync_block.__init__(
            self,
            name='receiver interpreter block',   # will show up in GRC
            in_sig=[np.byte],
            out_sig=[]
        )
        self.message_port_register_out(pmt.intern("rmsg"))
        self.message_port_register_out(pmt.intern("PDUout"))
        self._startOfFrame          = startOfFrame
        self._endOfFrame            = endOfFrame 
        self._escapeCharacter       = escapeCharacter
        self._threshold             = threshold
        self._size                  = 8
        self._buffer                = ['','','','','','','','']
        self._buffer2               = ['','','','','','','','']
        self._packet                = '' 
        self._endDetectedWithInput  = False
        self._escCharacterDetected  = False
        self._searching             = False
        self._foundPacket           = False 
        self._parserOn              = False 
        self._searchBlock           = False
        self._counter               = 0
    def _startAgain(self):
        self._buffer                = ['','','','','','','','']
        self._buffer2               = ['','','','','','','','']
        self._packet                = '' 
        self._endDetectedWithInput  = False
        self._escCharacterDetected  = False
        self._searching             = True
        self._foundPacket           = False 
        self._parserOn              = True 
        self._searchBlock           = False
        self._counter               = 0
    def _resetState(self):
        self._buffer                = ['','','','','','','','']
        self._buffer2               = ['','','','','','','','']
        self._packet                = '' 
        self._endDetectedWithInput  = False
        self._escCharacterDetected  = False
        self._searching             = False
        self._foundPacket           = False 
        self._parserOn              = False 
        self._searchBlock           = False
        self._counter               = 0
    def _searchForFrameStart(self , newBitString):
        self._updateBuffer(self._buffer,newBitString)
        self._foundPacket =  self._compareBuffer(self._buffer, self._startOfFrame)
    def _parseAndStorePacket(self , newBitString):
        self._updatePacket(newBitString)
        self._endDetectedWithInput = self._compareBuffer(self._buffer,self._endOfFrame)
        self._escCharacterDetected = self._compareBuffer(self._buffer, self._escapeCharacter)
    def _updatePacket(self , newBitString):
        self._packet              = self._packet + self._updateBuffer(self._buffer,newBitString)
    def _packetToPDU(self):
        self.message_port_pub(pmt.intern('rmsg'), pmt.intern('paring packet'))
        if (len(self._packet)%self._size == 0):
            numberOfBytes = int(round(len(self._packet)/self._size)) 
            stream = pmt.make_u8vector(numberOfBytes,0)
            for by in range(numberOfBytes):
                element = int(self._packet[by*self._size:(by+1)*self._size],2)
                pmt.u8vector_set(stream, by, element)
            pdu = pmt.cons(pmt.make_dict(),stream)
            self.message_port_pub(pmt.intern('rmsg'),pmt.intern('sending pdu'))
            self.message_port_pub(pmt.intern("PDUout"), pdu)
    def _resetBuffer(self):
        self._buffer   = ['','','','','','','','']
    def _resetBuffer2(self): 
         self._buffer2 = ['','','','','','','','']       
    def _updateBuffer(self, bufferList, element):
        result = bufferList.pop(0)
        bufferList.append(element)
        return result 
    def _compareBufferElement(self , bufferList, targetString, index):
        if ( bufferList[index] == targetString[index]):
            return 0
        else :
            return 1
    def _compareBuffer(self , bufferList , targetString):
        result = 0
        for index in range(self._size):
            result = result + self._compareBufferElement(bufferList, targetString, index)
        return (result <= self._threshold) 
    def work(self, input_items, output_items):
        for offset in range(len(input_items[0])):
            tags = self.get_tags_in_window(0,offset,offset +1 )
            for tag in tags:
                if pmt.symbol_to_string(tag.key) == "Power":
                    self.message_port_pub(pmt.intern("rmsg"),pmt.intern('power'))
                    if pmt.is_true(tag.value):
                        self.message_port_pub(pmt.intern("rmsg"),pmt.intern('power ok: start search'))
                        self._searching      = True
                        self._parserOn       = True 
                    else:
                        #self.message_port_pub(pmt.intern("rmsg"),pmt.intern(str(self._packet)))
                        self._packetToPDU() 
                        self._resetState()
            if self._parserOn:
                inputBytes        = input_items[0][offset]
                inputString       = str(inputBytes).decode('UTF-8')
                if  self._searching:
                    self._searchForFrameStart(inputString)
                    if self._foundPacket:
                        self._resetBuffer()
                        self._searching = False 
                        self.message_port_pub(pmt.intern("rmsg"), pmt.intern("found packet"))
                elif self._foundPacket:
                    if not self._searchBlock:
                        self._parseAndStorePacket(inputString)
                        if self._escCharacterDetected:
                            self._resetBuffer()
                            self._escCharacterDetected = False 
                            self._searchBlock          = True
                            self._counter              = 0
                    else :
                        self._updatePacket(inputString)
                        self._counter = self._counter + 1
                        if self._counter == 15:
                            self._searchBlock = False 
                    if self._endDetectedWithInput:
                        self.message_port_pub(pmt.intern('rmsg'), pmt.intern('end detected'))
                        self._packetToPDU()
                        self._startAgain() 
        return len(input_items[0])

