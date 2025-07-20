"""
    G15 DRUM MEMORY EMULATOR

    user entry points:
        Read(track,word)
        Write(track,word,data)

    note:  the G15 used word ID of [1:108],  0 is not used
    in python 0:107.   this offset is handled inside the drum routines

"""

from G15Subr import *
import gl



VERBOSITY_DRUMP_CREATE = 1
VERBOSITY_DRUM_OP = 2
VERBOSITY_DRUM_PRECESS = 4
VERBOSITY_DRUM_DETAILS = 8


class G15Drum:
    """ G15 Drum Memory Emulation """

    # noinspection PyPep8Naming
    def __init__(self, g15, Verbosity=0x0):
        """ Create G15Drum class instance """

        self.g15 = g15                # back pointer to main computer

        self.verbosity = Verbosity
        # verbosity.1 = drum creation
        # verbosity.2 = drum ops
        # self.verbosity = VERBOSITY_DRUM_OP

        # generate the drum
        self.drum = []
        self.track_origin = []
        for i in track_lengths:
            self.drum.append([0] * track_lengths[i])
            self.track_origin.append(-1)

        if self.verbosity & VERBOSITY_DRUMP_CREATE:
            for i in track_lengths:
                gl.logprint('Track %02d' % i, ' len=%03d' % len(self.drum[i]))

        # make pep8 happy
        self.rev_count = 0
        self.stop_time_previous = 0

        self.revolution_init()
        
    # determine line length
    def track_length(self, track):
        """ Determine number of word in specified track """

        try:
            length = track_lengths[track]
        except:
            gl.logprint('Error: Unknown Track: ', track)
            length = 1			# default
            
        return length        

        
    def map_address(self, track, word):
        """
        Map track,word into proper word time

        performs modulo operation across all tracks of various lengths
        adjusts for 108,4,2,1 word tracks
        Determine number of word in specified track
        """

        length = self.track_length(track)
        new_word = word % length

        if self.verbosity & VERBOSITY_DRUM_DETAILS:
            gl.logprint('map_address: Track=%02d' % track, 'word=%02d' % word, 'address=%02d' % new_word)

        return new_word

    def read(self, track, word_time, flag=1):
        """ Read a word from somewhere on the drum """

        address = self.map_address(track, word_time)
        read_data = self.drum[track][address]

        if flag and (self.verbosity & VERBOSITY_DRUM_OP):
            gl.logprint('Drum  Read: Track=%02d' % track, ' word=%03d' % word_time,
                  '  read_data= ', signmag_to_str(read_data),
                  ' /%08x' % read_data)

        return read_data

    def write(self, track, word_time, write_data):
        """ Write a word to somewhere on the drum """

        address = self.map_address(track, word_time)
        write_data &= MASK29BIT

        self.drum[track][address] = write_data

        if self.verbosity & VERBOSITY_DRUM_OP:
            gl.logprint("Address=", address)
            gl.logprint('Drum Write: Track=%02d' % track, ' word=%03d' % word_time,
                  ' write_data= ', signmag_to_str(write_data), ' /%08x' % write_data)

    def write_block(self, block_id, track, data):
        """
        Bulk write, write a block of data onto a track starting at address 0

        Usually used to transfer a block of data from the tape device
        also annotates the track with the tape block id (for emeulator breakpoints)

        id = tape block id (usually index)
        drum track #
        data = python list of data words from input media
        """

        track_length = self.track_length(track)
        datalength = len(data)

        if datalength > track_length:
            gl.logprint("Error: source and destination are of different sizes")
            gl.logprint("   datalength=", datalength, " track_length=", track_length)
            return

        # move data word by word (to avoid errors)
        address = 0
        for data_word in data:
            self.write(track, address, data_word)
            address += 1

        # record media block that the data came from
        self.track_origin[track] = block_id

    def read_two_word(self, track, starting_word):
        """ Reads two words from the drum """

        low = self.read(track, starting_word)
        high = self.read(track, starting_word + 1)
        word2 = (high << 29) | low

        return word2

    def write_two_word(self, track, starting_word, data):
        """ Write two words to the drum """

        self.write(track, starting_word, data)
        self.write(track, starting_word + 1, (data >> 29))

    def precess(self, track, amount):
        """
        Presess a drum track the specified amount

        In G15 terminology it is called precess.  This is equivalent
        to a left shift of the entrie memory track.  The most
        common use of a track precess is to create a hole to put
        data into during IO reads (typewriter or PTR)

        0s are inserted into the LSBs

        """
        if amount > 29:
            gl.logprint('ERROR: max precess amount exceeded, amount=', amount)

        for i in range(track_lengths[track]):  # 0-3,1-107
            addr = track_lengths[track] - i - 1

            data_word = self.read(track, addr)
            data_word <<= amount

            if self.verbosity & VERBOSITY_DRUM_PRECESS:
                gl.logprint('i=', i, 'addr=', addr)

            # add bits from lower word
            if addr != 0:
                new_bits = self.read(track, addr - 1)

                if self.verbosity & VERBOSITY_DRUM_PRECESS:
                    gl.logprint('vew-bits = %x' % new_bits)

                new_bits >>= 29 - amount

                if self.verbosity & VERBOSITY_DRUM_PRECESS:
                    gl.logprint('vew-bits = %x' % new_bits)

                data_word |= new_bits

            self.write(track, addr, data_word)

    def display(self, track, start_word, length):
        """ Display a range of drum addresses """

        for i in range(length):
            word_time = start_word + i
            data = self.read(track, word_time)
            gl.logprint('%-3d' % word_time, ' %08x' % data, ' ', signmag_to_str(data))

    @staticmethod
    def address_decode(tokens):
        """
        Parses a drum address string

        track ':' beginwordtime ':' endwordtime

        endwordtime defaults to beginwordtime
        """
        ll = len(tokens)
        if (ll < 2) or (ll > 3):
            gl.logprint('Error: unknown drum address syntax:  track ":" beginwordtime ":" endwordtime')

        elif ll == 2:
            tokens.append(tokens[1])

        t0 = int(tokens[0])
        t1 = str_to_wordtime(tokens[1])
        t2 = str_to_wordtime(tokens[2])
        return t0, t1, t2

    def checksum(self, track, start, stop):
        """ Compute checksum over a drum track (or subset of a drum track) """

        if not (track in track_lengths):
            self.g15.increment_error_counter("Unknown Track id: " + str(track))
            return -1

        # get length of drum track
        length = self.track_length(track)

        stop += 1

        # handle track wrap around
        if stop == start:
            stop += length

        while stop <= start:
            stop += length

        chk_sum = 0
        for word_time in range(start, stop):
            signmag = self.g15.drum.read(track, word_time)
            word_2s = signmag_to_comp2s_29(signmag)
            chk_sum += word_2s

        # chk_sum is not a 29bit signed int
        if chk_sum & ((MASK29BIT + 1) >> 1):
            mag = (~chk_sum) + 1
            mag &= MASK29BIT
            sign = 1
        else:
            mag = chk_sum
            sign = 0

        mag &= (MASK29BIT >> 1)
        signmag = (mag << 1) | sign

        return signmag

    def revolution_init(self):
        self.rev_count = 0
        self.stop_time_previous = -1

    def revolution_check(self, stop_time):
        retval = 0
        if stop_time <= self.stop_time_previous:
            self.rev_count += 1
            retval = 1
        self.stop_time_previous = stop_time

        return retval

    def revolution_get(self):
        return self.rev_count

    def time_get(self):
        drum_position_current = self.g15.cpu.word_time % 108
        return self.rev_count, drum_position_current

    def time_get_str(self):
        rev, pos = self.time_get()
        outstr = "%3d" % rev + '.' + instr_dec_hex_convert(pos)
        return outstr
