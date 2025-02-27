#
#
#############################################################
#
# Paper tape Reader Emulation
#
# data (paper tape image is store in binary file)
#
#
# user entry points:
#  mount_tape(file_name)
# 		"emulates the mounting of a tape onto the reader"
# 		reads the entire file into a list
# 		bytes are assumed to be transposed (MSB <=> LSB) (paul pierce)
# 		returns a 2D list:  tape[blockIndex][WordIndex]
#
#############################################################
#
import sys

sys.path.append("g15d")
sys.path.append("g15d/lib")

# from G15Constants import *
from G15Subr import *
import g15_ptape

VERBOSITY_PT_MOUNT = 1
VERBOSITY_PT_CHECKSUM = 2
VERBOSITY_PT_PARSE = 4


class G15Ptr:
    ''' paper tape reader for the g15
    '''
    def __init__(self, g15, Verbosity=0x2):
        self.g15 = g15
        self.verbosity = Verbosity

        self.paper_tape = g15_ptape.PaperTape()

        # total number of "patterns" not understood on the tapee
        self.deal_with_me_count = 0

        self.tape_name = ""
        self.read_index = 0		# next block ID to "read" into emulator
        #
        if self.verbosity & 1:
            print('\tPaper tape Reader Attached')

    def status(self):
        print('\nPaper tape Status:')

        name = self.tape_name
        if name == '':
            name = 'No tape Mounted'

        print('\t    Mounted tape: ', name)
        print('\ttape block Index: ', self.read_index)

    def mount_tape(self, file_name):
        ''' mounts a 'tape onto the papertape reader'

            specified file is read and its contents are extracted
            a 2D list is created:  tape[blockIndex][WordIndex]

            to permit dynamic bit transposition, an entire byte image
            is created and then manipulated.  If change to static is
            made, then byte image may be skipped

        :param file_name:		file_name containing tape image
        :return:

        '''
        if self.verbosity & VERBOSITY_PT_MOUNT:
            print("Reading tape Image: ", file_name)

        print("Mounting tape: ", file_name, " onto paper tape reader")

        # use main tape library to read the paper tape
        self.paper_tape.ReadPti(file_name)

        print("Tape=", file_name)
        print("Number of blocks read=", len(self.paper_tape.Blocks))
        self.paper_tape.CheckSum(sys.stdout)

        # for future read block commands
        # determine active index intro tape contents lists
        self.read_index = 0

    #
    #######################################
    #
    # read a block of tape and place into L19/23
    #
    #######################################
    #
    def read_block(self):

        # are we pass end of tape
        if self.read_index >= len(self.paper_tape.Blocks):
            print("ERROR: Attempt at reading Paper tape beyond end of data")
            return

        # read the next block of tape
        block = self.paper_tape.Blocks[self.read_index]

        # write the block to M19
        print('PTR: Reading next tape block #', self.read_index, ' into M19')
        self.g15.drum.write_block(self.read_index, M19, block)

        # write 1st four words to M23
        for i in range(4):
            self.g15.drum.write(M23, i, self.g15.drum.read(M19, i))

        self.read_index += 1
        return block
    #
    #######################################
    #
    # reverse paper tape by number of blocks specified
    #
    # count = 0 => rewind the entire tape
    #
    #######################################
    #
    def reverse(self, count):
        if count == 0:
            self.read_index = 0
        elif count > 0:
            self.read_index -= count
            if self.read_index < 0:
                self.read_index = 0

    def Status(self):
        print()
        print('PTR Status:')

        if self.tape_name == "":
            name = "No tape is mounted"
        else:
            name = self.tape_name

        print('\t                        Mounted Tape: ', name)
        print('\tTape Position: Next Block to be Read: ', self.read_index)
