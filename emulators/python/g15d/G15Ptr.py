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
from G15Subr import *
import copy
import os

VERBOSITY_PT_MOUNT = 1
VERBOSITY_PT_CHECKSUM = 2
VERBOSITY_PT_PARSE = 4


class G15Ptr:
    ''' paper tape reader for the g15
    '''
    def __init__(self, g15, tapedir=None, Verbosity=0x2):
        self.g15 = g15
        self.tapedir = tapedir
        self.verbosity = Verbosity

        # total number of "patterns" not understood on the tapee
        self.deal_with_me_count = 0

        self.tape_dirname = 'tapes'
        self.read_index = 0		# next block ID to "read" into emulator
        self.suffixes = ['', '.pt', '.pti', '.ptr']
        self.tape_paths = self.searchForTapesDirectory(tapedir)

        print("tape-path=", self.tape_paths)

        # create empty tape image
        self.tape_parsed = []			# will hold parsed blocks

        # create artificial number track
        self.numbertrack = self.numbertrack_create()

        if self.verbosity & 1:
            print('\tPaper tape Reader Attached')

    def searchForTapesDirectory(self, tapedir):
        tape_paths = []
        if tapedir:
            tape_paths.append(tapedir)  # specified directory
        tape_paths.append('.')          # current directory

        # get python executable directory
        spath = os.path.abspath(__file__)
        sdir = os.path.dirname(spath)
        tape_paths.append(sdir)         # executable directory

        # search upward looking for "tapes" directory
        dir = os.path.dirname(sdir)
        while True:
            tdir = dir + '/' + self.tape_dirname
            if os.path.exists(tdir):
                tape_paths.append(tdir + '/images') # found it
                break
            dir = os.path.dirname(dir)
            print("dir=", dir)
            if dir == '/':      # all done
                # no tapes directory dir tree
                break

        return(tape_paths)

    def insure_NT(self):
        if len(self.tape_parsed) == 0:
            print("Paper tape is not mounted")
            return

        if not self.check_if_numbertrack(self.tape_parsed[0]):
            print("Note: PT does not have NT, automatically prepending NT")

            # tape does not have number track, so add it
            block = copy.copy(self.numbertrack)
            new_tape = [block]
            for block in self.tape_parsed:
                new_tape.append(block)
            self.tape_parsed = new_tape

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

        # make list of possible file names
        # not most efficient approach, but less confusing

        file_names = []
        if file_name[0] == '/':
            # an absolute path
            file_names.append(file_name)
        else:
            # develop paths
            for dir in self.tape_paths:
                for suffix in self.suffixes:
                    filename = dir + '/' + file_name + suffix
                    file_names.append(filename)

        # filenames is a list of possible filenames
        # note: if user fname begins with / it is assumed to be complete path

#        print("file_names=", file_names)
#        print("will try to mount the following:")
#        for file_name in file_names:
#            print("\t", file_name)

        flag = 0
        for file_name in file_names:
            if self.verbosity & 1:
                print('Trying to open file: ', self.file_name)
            try:
                FileP = open(file_name, 'rb')
                flag = 1
                break
            except IOError:
                # print('Error:  Cannot open tape file: ', self.tape_name, ' for reading')
                continue

        if flag == 0:
            print('Error: Cannot open file: ', file_name, ' for reading')
            return

        print('Tape: ', file_name, ' has been mounted')

        # read the file
        # determine if tape is bit transposed (BIG ENDIAN at bit level)

        # calculate sum of bit 1 and bit 5.
        # since bit 5 is set for each numeric value,
        # 		its occurrence should dominate on tape
        # convert input strings to numeric bytes while we count
        image = []
        for bytestr in FileP.read(-1):
            image.append(bytestr)

        # done with file, so close it
        FileP.close()

        image = self.pti_remove_comments(image)
        image = self.pti_tape(image)                # convert to binary if image is pti
        image = self.tape_image_reversal(image)     # check if binary image is column reversed and correct
        self.tape_parsed = self.parse_tape(image)   # convert to ptw (tape blocks and words

        # tape is now a 2d lists by block,word of entire tape
        print('\ttape Contents:')
        block_content = 0
        for block in self.tape_parsed:
            sum2 = self.checksum2(block)

            checksum = 0
            for word in block:
                value = word >> 1
                sign = word & 1
                if sign:
                    value = (~value) + 1
                checksum += value
            checksum &= 0x1fffffff

            if checksum & 0x10000000:
                checksum = - (checksum & 0xfffffff)

            if self.check_if_numbertrack(block):
                numbertrack_str = 'NT'
            else:
                numbertrack_str = '  '

            print('\t\tblock #%2d' % block_content, ' has %3d' % len(block), ' words, checksum= ', signmag_to_str(sum2), numbertrack_str)
            block_content += 1

        print('Number of blocks: ', len(self.tape_parsed))

        # for future read block commands
        # determine active index intro tape contents lists
        self.read_index = 0

    def checksum2(self, block):

        checksum = 0
        for word in block:
            value = word >> 1
            sign = word & 1
            if sign:
                value = (~value) + 1
            value &= 0x1fffffff
            checksum += value
        checksum &= 0x1fffffff

        # convert to sign mag
        chksum2 = (checksum << 1) | (checksum >> 28)
        chksum2 &= 0x1fffffff

        #outstr = signmag_to_str(chksum2)
        #print("chksum2=%x"% chksum2)
        # print("sum2c=", outstr)

        return chksum2  # sign/mag

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
            print('Entering Parse Tape')

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
                    print("minus")
                minus_sign = 1
            elif byte == 0x2 or byte == 0x3:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print("cr/tab")
                word = 0
                for Byte in block_bytes:
                    word = word << 4
                    word += Byte
                word <<= 1
                word |= minus_sign
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print('Word=%09x' % word, 'sign=', minus_sign, 'block_bytes=', block_bytes)

                # cr and tab clear the minus sign history
                minus_sign = 0

                block_contents.append(word)
                block_bytes = []
                quad_word = []			# should already be empty

            elif byte == 0x4 or byte == 0x5:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    if byte == 0x4:
                        print("Stop detected")
                    else:
                        print("Reload detected")
                    print("block_bytes: ", block_bytes)
                    print("quad_word: ", quad_word)
                    print("# of bytes: ", count_bytes)
                    print("# Xfers=", count_xfers)

                if block_bytes != []:
                    quad_word = self.extract_four_words(block_bytes)
                    block_bytes = []

                # move quad_word onto block contents list
                for word in quad_word:
                    block_contents.append(word)
                quad_word = []

                if self.verbosity & VERBOSITY_PT_PARSE:
                    print('block Contents: ', block_contents)

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
                    print("period")
                self.deal_with_me_count += 1
            elif byte == 0x7:
                if self.verbosity & VERBOSITY_PT_PARSE:
                    print("wait")
                self.deal_with_me_count += 1
            else:
                print("Unknown input code: %x" % byte)
                self.deal_with_me_count += 1

        print("\tblocks Detected: ", count_stops)
        print("\tTotal tape Errors Detected: ", self.deal_with_me_count)
        print("\ttape File has been imported, ready to be use")

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
            print("Error: Current conversion program requires 29 byte (ie full) blocks")

        # have exact number of 29 bit words
        data = 0
        bit_count = 0
        words = []

        for byte in bytes:
            # bring in the byte
            # previous data is MSB over newer data
            if self.verbosity & VERBOSITY_PT_PARSE:
                print('new byte=%02x' % byte, ' olddata=%08x' % data, ' bit_count=', bit_count)

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
                    print('word extracted=%08x' % word)

        if words != 4 and bit_count != 0:
            print("Error: bytes did not fit exactly into a quad word")
            print("bytes were: ", bytes)
        return words

    def pti_remove_comments(self, image):
        newimage = []
        eat = 0
        for c in image:
            # if c == '#':
            if c == 0x23:
                eat = 1
            #elif c == '\n':
            elif c == 0x0a:
                eat = 0
            if not eat:
                newimage.append(c)
        return newimage

    def pti_tape(self, image):
        # determines if tape image is really a PTI file
        # and converted to binary (G15) if it is

        # is this an ascii file
        # we count in case of noise in the file (raw images)
        count_ascii = 0
        for symbol in image:
            #symbol_ord = ord(symbol)
            symbol_ord = symbol
            if symbol_ord >= 0x30:       # numeral 0
                count_ascii += 1
            else:
                count_ascii -= 1

        if count_ascii < 0:
            return image            # inbary (PT) file

        # yes it is ascii, let's convert it to binarhy (PT)
        new_image = []
        error_count = 0
        for char in image:
            if chr(char) == '\n':
                continue
            code = ascii_2_code(IO_DEVICE_PAPER_TAPE, chr(char))
            if code < 0:
                print("ERROR: unknown code: ", chr(char), " .... character is ignored")
                error_count += 1
            else:
                new_image.append(code)
        if error_count:
            print(error_count, " Errors were detected")

        return new_image

    def tape_image_reversal(self, image):
        # some binary tapes are bit column reversed
        # we count the columns and reverse if necessary

        bit1_count = 0
        bit5_count = 0
        for char in image:
            if char & 1:
                bit1_count += 1
            if char & 0x10:
                bit5_count += 1

        if self.verbosity & VERBOSITY_PT_MOUNT:
            print('bit1_count=', bit1_count, ' bit5_count=', bit5_count)

        # check if file is bit-transposed
        if bit5_count >= bit1_count:
            return image    # not reversed

        # oops, need to reverse transpose
        if self.verbosity & VERBOSITY_PT_MOUNT:
            print('\tNote: tape has bits reversed, fixing.....')

        new_image = []
        for char in image:
            new_char = self.byte_transpose(char)
            new_image.append(new_char)

        return new_image

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
            print("transpose: in=%02x" % byte_in_copy, " out=%02x" % byte_out)

        return byte_out

    @staticmethod
    def numbertrack_word(seed, position):
        ''' create a number track image

        used to determine if first block of tape is a number track
        we want to skip over number track during block reads

        :param seed:
        :param position:
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
            #print("i=",i, ' block=%08x'%block[i], " nt=%08x"%self.numbertrack[i])
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
            print("ERROR: Attempt at reading Paper tape beyond end of data")
            return

        # read the next block of tape
        block = self.tape_parsed[self.read_index]

        # write the block to M19
        print('PTR: Reading next tape block #', self.read_index, ' into M19')
        self.g15.drum.write_block(self.read_index, M19, block)

        # write 1st four words to M23
        for i in range(4):
            self.g15.drum.write(M23, i, self.g15.drum.read(M19, i))

        self.g15.iosys.status = IO_STATUS_READY

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
        print('\nPaper tape Status:')

        name = self.tape_name
        if name == '':
            name = 'No tape Mounted'

        print('\t                        Mounted tape: ', name)
        print('\tTape Position: Next Block to be Read: ', self.read_index)
        