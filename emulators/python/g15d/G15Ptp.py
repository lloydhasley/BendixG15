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
import gl
import g15_ptape

VERBOSITY_PTP_DEBUG = 1


class G15Ptp:
    # paper tape punch for the g15
    # prints PTI file of the given data
    def __init__(self, g15, Verbosity=0x0):
        self.g15 = g15
        self.verbosity = Verbosity
        
        self.pt = g15_ptape.PaperTape()

                       #  0123456789uvwxyz
        self.sym2ascii = " -CTSR.W--------0123456789uvwxyz"
        self.addNewLine = {'S': 2, 'R': 1, '/': 1}

        # paper tape contents
        self.tape_contents = []

        if self.verbosity & VERBOSITY_PTP_DEBUG:
            gl.logprint('\tPaper tape Punch Attached')

    def clear(self):
        self.tape_contents = []
        
    def punch_track(self, track):
        # extract the words from track and form a "block"
        length = track_lengths[track]
        if length != 108:
            gl.logprint("ERROR: only 108 word tracks may be punched")
            return
        
        block = []
        for i in range(108):
            block.append(self.g15.drum.read(track, i))

        # create binary image
        Image = self.pt.CreateImage(block)

        # output/punch the binary image and add to paper tape image
        for sym in Image:
            self.punch_symbol(sym)

        gl.logprint("Track: " + str(track) + " added to the punched tape")

    def punch_tracks(self, tracks):
        # tracks is an integer list of tracks desired to punch
        
        for track in tracks:
            for c in '# Track: ' + str(track) + '\n':
                self.tape_contents.append(c)
                
            self.punch_track(track)
            
    def punch(self, outstr):
        for c in outstr:
            self.punch_symbol(c)
            
    def punch_symbol(self, symbol):
        if self.verbosity & VERBOSITY_PTP_DEBUG:
            gl.logprint(' entering punch_symbol, symbol=0x%02x' % symbol)

        symbol &= 0x1f
        symbol_ascii = self.sym2ascii[symbol]
        
        if symbol_ascii == ' ':
            if len(self.tape_contents):
                if self.tape_contents[-1]:
                    # suppress multiple spaces
                    return
        
        self.tape_contents.append(symbol_ascii)

        if symbol_ascii in self.addNewLine:
            for count in range(self.addNewLine[symbol_ascii]):
                self.tape_contents.append('\n')

    def write_file(self, filename):
        with open(filename, 'w') as f:
            for symbol in self.tape_contents:
                f.write(symbol)

    def count(self):
        return len(self.tape_contents)

    def Status(self):
        gl.logprint("Paper Tape Punch:")
        gl.logprint("\tCharacters punched:", self.count())
        gl.logprint("\t\tand waiting in the PtP buffer:")
