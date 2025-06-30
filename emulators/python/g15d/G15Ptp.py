#
#
#############################################################
#
# Paper tape Unch Emulation
#
# G15 'punches' data in a python list
#
# the ptp command is then used to write this list to a file
# Note: writing the data is the equivalent of ripping the tape from the punch
# and storing it somewhere.
#
#
# user entry points:
#  ptp
#
# list has G15 symbols in it
# converted to ascii when written to file
#
#############################################################
#
from G15Subr import *
import copy
import os

VERBOSITY_PTP_DEBUG = 1


class G15Ptp:
    ''' paper tape punch for the g15
    '''
    def __init__(self, g15,Verbosity=0x0):
        self.g15 = g15
        self.verbosity = Verbosity

                       #  0123456789uvwxyz
        self.sym2ascii = " -CTSR.W--------0123456789uvwxyz"
        self.addNewLine = {'S':2, 'R':1, '/':1}

        # paper tape contents
        self.tape_contents = []

        if self.verbosity & VERBOSITY_PTP_DEBUG:
            print('\tPaper tape Punch Attached')

    def clear(self):
        self.tape_contents = []

    def punch(self, outstr):
#        if len(outstr) == 1:
#            self.punch(outstr)
#        else:
        for c in outstr:
            self.punch_symbol(c)
            
    def punch_symbol(self, symbol):
        print(' entering punch_symbol, symbol=0x%02x' % symbol)
        symbol &= 0x1f
        symbol = self.sym2ascii[symbol]
        self.tape_contents.append(symbol)

        if symbol in self.addNewLine:
            for count in self.addNewLine[symbol]:
                self.tape_contents.append('\n')

    def write_file(self, filename):
        with open(filename, 'w') as f:
            for symbol in self.tape_contents:
                f.write(symbol)

    def count(self):
        return len(self.tape_contents)

    def Status(self):
        print("Paper Tape Punch:")
        print("\tCharacters punched:", self.count())
        print("\t\tand waiting in the PtP buffer:")


