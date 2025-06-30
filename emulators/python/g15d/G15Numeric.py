"""
Class G15Numeric defines a basic early G15 containing the following peripherals:

Paper Tape Reader
Numeric Only Typewriter

No Paper Tape Punch
No Mag Tape
No Alphanumeric IO
"""

# g15 pieces
import G15Drum          # drum memory
import G15Cpu           # main cpu
import G15Io            # io subsystem multiplexor
import G15Ptr           # paper tape reader
import G15Ptp           # paper tape punch
import G15TypeNumeric   # numeric typewrite coupler
import G15Cmds			# queue + G15 side of cmd handler
from G15Constants import *


class G15Numeric:
    """ A complete G15, numeric only IO """
    def __init__(self, emulator, vtracefile, tapename=None, signenable=0):
        self.emul = emulator
        self.vtracefile = vtracefile
        self.signenable = signenable
        self.tapename = tapename
        
        # attach the primary pieces of the g15
        print('building the Numeric G15...')

        # G15 consists of a cpu, memory (drum) and an IO sub-system
        self.cpu = G15Cpu.G15Cpu(self, 0, self.vtracefile, self.signenable)
        self.drum = G15Drum.G15Drum(self)
        self.iosys = G15Io.G15Io(self)

        # All G15s had a paper tape reader (and punch) and a typewriter
        self.ptr = G15Ptr.G15Ptr(self, self.tapename)
        self.iosys.attach(DEV_IO_PTR, self.ptr, 'ptr')

        self.ptp = G15Ptp.G15Ptp(self)
        self.iosys.attach(DEV_IO_PTP, self.ptp, 'ptp')

        self.typewriter = G15TypeNumeric.G15TypeNumeric(self)       # initial G15 only had a numeric IO
        self.iosys.attach(DEV_IO_TYPE, self.typewriter, 'typewriter')
        
        self.cmds = G15Cmds.G15Cmds(self)
