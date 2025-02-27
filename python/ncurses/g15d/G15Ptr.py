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
from G15Constants import *
from G15Subr import *
import copy

VERBOSITY_PT_MOUNT = 1
VERBOSITY_PT_CHECKSUM = 2
VERBOSITY_PT_PARSE = 4


class G15Ptr:
    ''' paper tape reader for the g15
    '''
    def __init__(self, g15, Verbosity=0x2):
        self.g15 = g15
        self.verbosity = Verbosity

        # total number of "patterns" not understood on the tapee
        self.deal_with_me_count = 0

        self.tape_name = ""
        self.read_index = 0		# next block ID to "read" into emulator

        # create empty tape image
        self.tape_parsed = []			# will hold parsed blocks

        # will hold byte image of tape (for output in Verilog)
        self.tape_bytes = []

        # create artificial number track
        self.numbertrack = self.numbertrack_create()
        #
        if self.verbosity & 1:
            print '\tPaper tape Reader Attached'

    def status(self):
        print '\nPaper tape Status:'

        name = self.tape_name
        if name == '':
            name = 'No tape Mounted'

        print '\t    Mounted tape: ', name
        print '\ttape block Index: ', self.read_index

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
            print "Reading tape Image: ", file_name

        print "Mounting tape: ", file_name, " onto paper tape reader"

        dirs = ['./tapes/', './']
        suffixes = ['.pt', '']

        flag = 0
        for directory in dirs:
            for suffix in suffixes:
                self.tape_name = directory + file_name + suffix
                if self.verbosity & 1:
                    print 'Trying to open file: ', self.tape_name

                try:
                    FileP = open(self.tape_name, 'rb')
                    pass
                    flag = 1
                    break
                except IOError:
                    print 'Error:  Cannot open tape file: ', self.tape_name, ' for reading'
                    continue

        if flag:
            print 'Tape: ', self.tape_name, ' has been mounted'
        else:
            print 'Error: Cannot open file: ', file_name, ' for reading'
            return

        # read the file
        # determine if tape is bit transposed (BIG ENDIAN at bit level)

        # calculate sum of bit 1 and bit 5.
        # since bit 5 is set for each numeric value,
        # 		its occurrance should dominate on tape
        # convert input strings to numeric bytes while we count
        bit1_count = 0
        bit5_count = 0
        tape_contents_numeric = []
        for bytestr in FileP.read(-1):

            Byte = ord(bytestr)
            tape_contents_numeric.append(Byte)

            if Byte & 1:
                bit1_count += 1
            if Byte & 0x10:
                bit5_count += 1

        if self.verbosity & VERBOSITY_PT_MOUNT:
            print 'bit1_count=', bit1_count, ' bit5_count=', bit5_count

        # done with file, so close it
        FileP.close()

        # check if file is bit-transposed
        if bit5_count < bit1_count:

            # oops, need to reverse transpose
            if self.verbosity & VERBOSITY_PT_MOUNT:
                print '\tNote: tape has bits reversed, fixing.....'

            Newtape_contents_numeric = []
            for Byte in tape_contents_numeric:
                NewByte = self.byte_transpose(Byte)
                Newtape_contents_numeric.append(NewByte)
            tape_contents_numeric = Newtape_contents_numeric

        # tape_contents_numeric is now a byte list of entire tape
        self.tape_parsed = self.parse_tape(tape_contents_numeric)
        self.tape_contents = tape_contents_numeric

        self.numbertrackflag = 0

        # is now a 2d lists by block,word of entire tape
        print '\ttape Contents:'
        block_content = 0
        for block in self.tape_parsed:
            checksum = 0

            for word in block:
                value = word >> 1
                sign = word & 1
                if sign:
                    checksum -= value
                else:
                    checksum += value

            # block1 = copy.copy(block)
            # for i in range(108):
            #     block1.append(0)
            # checksum1 = self.checksum(block1)
            # print 'sum1=%x'%checksum1

            if self.check_if_numbertrack(block):
                numbertrack_str = 'NT'
                if block_content == 0:
                    self.numbertrackflag = 1
            else:
                numbertrack_str = ''

            print '\t\tblock #%2d' % block_content, ' has %3d' % len(block), ' words, checksum= ', int_to_str(checksum), numbertrack_str
            block_content += 1

        print 'Number of blocks: ', len(self.tape_parsed)

        # for future read block commands
        # determine active index intro tape contents lists
        self.read_index = 0

    def checksum(self, block):
        '''
        :param block: 	block of tape data to be checksumed
        :return:
        '''
        sum = 0
        # j = range(34, 108)
        # j.extend(range(34))
        j = range(0, 108)

        for i in j:
            word = block[i]
            value = signmag_to_int(word)
            sum += value

            if self.verbosity & VERBOSITY_PT_CHECKSUM:
                str = int_to_str(sum)
                print 'i=', i, 'word value (+-dec)=', value, '/value-x=', int_to_str(value), 'temp checksum=', str
                word = int_to_signmag(sum)
                str = signmag_to_str(word)
                print str

                sum &= 0x0fffffff

        print 'checksum', sum

        return sum

    def parse_tape(self, tape_contents):
        ''' process tape contents
        :param self:
        :param tape_contents:
        :return:

        converts entire tape image by a byte stream into
        tape[block][WordAddress]

        not a user routine, called by mount_tape
        '''
        if self.verbosity & VERBOSITY_PT_PARSE:
            print 'Entering Parse Tape'

        # gather up a short block
        block_bytes = []
        block_contents = []
        quad_word = []
        tape = []

        minus_sign = 0			# does current line (long) have a sign bit
        self.deal_with_me_count = 0			# count of items that we didn't deal with
        count_bytes = 0
        count_xfers = 0
        count_stops = 0
        for byte in tape_contents:
            if byte == 0:		# space
                continue
            elif byte >= 0x10 and byte <= 0x1f:
                block_bytes.append(byte - 0x10)
                count_bytes += 1
            elif byte == 0x1:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print "minus"
                minus_sign = 1
            elif byte == 0x2 or byte == 0x3:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print "cr/tab"
                word = 0
                for Byte in block_bytes:
                    word = word << 4
                    word += Byte
                word <<= 1
                word |= minus_sign
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print 'Word=%09x' % word, 'sign=', minus_sign, 'block_bytes=', block_bytes

                # cr and tab clear the minus sign history
                minus_sign = 0

                block_contents.append(word)
                block_bytes = []
                quad_word = []			# should already be empty

            elif byte == 0x4 or byte == 0x5:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    if byte == 0x4:
                        print "Stop detected"
                    else:
                        print "Reload detected"
                    print "block_bytes: ", block_bytes
                    print "quad_word: ", quad_word
                    print "# of bytes: ", count_bytes
                    print "# Xfers=", count_xfers

                if block_bytes != []:
                    quad_word = self.extract_four_words(block_bytes)
                    block_bytes = []

                # move quad_word onto block contents list
                for word in quad_word:
                    block_contents.append(word)
                quad_word = []

                if self.verbosity & VERBOSITY_PT_PARSE:
                    print 'block Contents: ', block_contents

                # stop detected, move block onto tape image
                if byte == 0x04:

                    # note: tape data is sent msb to lsb and MSB to LSB
                    # should reverse list so first entry is address 0
                    blockReversed = list(reversed(block_contents))

                    tape.append(blockReversed)

                    block_contents = []
                    count_bytes = 0
                    count_stops += 1
                    count_xfers = 0

                    minus_sign = 0
                else:
                    count_xfers += 1
            elif byte == 0x6:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print "period"
                self.deal_with_me_count += 1
            elif byte == 0x7:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print "wait"
                self.deal_with_me_count += 1
            else:
                print "Unknown input code: %x" % byte
                self.deal_with_me_count += 1

        print "\tblocks Detected: ", count_stops
        print "\tTotal tape Errors Detected: ", self.deal_with_me_count
        print "\ttape File has been imported, ready to be use"

        return tape

    def extract_four_words(self, bytes):
        ''' extract four words (short line) from tape
        :param self:
        :param bytes:
        :return:

        returns 4 entry list

        note: not a user routine, called by parse_tape
        '''

        byte_count = len(bytes)
        if byte_count != 29:
            print "Error: Current conversion program requires 29 byte (ie full) blocks"

        # have exact number of 29 bit words
        data = 0
        bit_count = 0
        words = []

        for byte in bytes:
            # bring in the byte
            # previous data is MSB over newer data
            if self.verbosity & VERBOSITY_PT_PARSE:
                print 'new byte=%02x' % byte, ' olddata=%08x' % data, ' bit_count=', bit_count

            data <<= 4
            data += byte
            bit_count += 4

            # do we have a 29 bit word?
            if bit_count >= 29:
                word = data			# make a copy
                word >>= (bit_count - 29)  # align the desired 29 bits

                # put on list
                words.append(word)

                mask = ((1 << (bit_count - 29)) - 1)
                data &= mask
                bit_count -= 29

                if self.verbosity & VERBOSITY_PT_PARSE:
                    print 'word extracted=%08x' % word

        if words != 4 and bit_count != 0:
            print "Error: bytes did not fit exactly into a quad word"
            print "bytes were: ", bytes
        return words

    def byte_transpose(self, byte_in):
        '''
        :param self:
        :param byte_in:	tape imaage
        :return: 		tape image, bit columns reversed if necessary

        tape from pricefuller are bit swapped (BIG ENDIAN at
        bit level) need to swap MSB<->LSB
        '''
        byte_out = 0
        byte_in_copy = byte_in

        for i in range(5):
            byte_out <<= 1
            if byte_in & 1:
                byte_out |= 1
            byte_in >>= 1

        if self.verbosity & VERBOSITY_PT_MOUNT:
            print "transpose: in=%02x" % byte_in_copy, " out=%02x" % byte_out

        return byte_out

    @staticmethod
    def numbertrack_word(seed, position):
        ''' create a number track image

        used to determine if first block of tape is a number track
        we want to skip over number track during block reads

        :param seed:
        :param Position:
        :return:
        '''
        word = seed
        word |= position << 21
        word |= position << 13
        #
        return word
    #
    # number track is a know quantity
    # create it in a list to compare against tape blocks
    #

    def numbertrack_create(self):
        #
        numbertrack = []
        for i in range(1, 108):
            numbertrack.append(self.numbertrack_word(0x10000000, i))
        #
        # last word is special, timing stamps are "20"
        # which is a correction factor for tracks being 108 instead of 128
        # words long
        numbertrack.append(self.numbertrack_word(0x00000f29, 20))
        #
        return numbertrack

    #
    #######################################
    #
    # check if block matches the number track
    #
    #######################################
    #
    def check_if_numbertrack(self, block):
        #
        word_count = len(block)
        #
        if word_count != 108:
            # print "Length is incorrect, should be 108, is: ", word_count
            return 0
        #
        for i in range(108):
            if block[i] != self.numbertrack[i]:
                return 0
        #
        # print "Number Track has been identified"
        return 1
        #
    #
    #######################################
    #
    # read a block of tape and place into L19/23
    #
    #######################################
    #

    def read_block(self):

        # are we pass end of tape
        if self.read_index >= len(self.tape_parsed):
            print "ERROR: Attempt at reading Paper tape beyond end of data"
            return

        # read the next block of tape
        block = self.tape_parsed[self.read_index]

        # write the block to M19
        print 'PTR: Reading next tape block #', self.read_index, ' into M19'
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
        print
        print 'PTR Status:'

        if self.tape_name == "":
            name = "No tape is mounted"
        else:
            name = self.tape_name

        print '\t                        Mounted Tape: ', name
        print '\tTape Position: Next Block to be Read: ', self.read_index
