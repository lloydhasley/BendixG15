#
#
# G15D IO subsystem
#
#
# take io system command moves data to/from the various IO devices
# typewriter, paper tape reader, mag tape
#
import sys

from G15Subr import *

MAXIODEVICES = 16

VERBOSITY_IO_SLOW_OUT = 2
VERBOSITY_IO_FORMAT = 4
VERBOSITY_IO_DETAIL = 0xf


class G15Io:
    # noinspection PyPep8Naming
    def __init__(self, g15, Verbosity=0):

        self.g15 = g15
        self.verbosity = Verbosity

        self.devices = [0] * 16
        self.device_names = {}

        self.status = IO_STATUS_READY         # set io subsystem to Ready
        self.sign = 0

    def attach(self, identifier, device, name):
        if identifier >= MAXIODEVICES or identifier < 0:
            print 'Error: Illegal IO device id:', identifier
            sys.exit(1)

        self.devices[identifier] = device
        self.device_names = name

    def set_status(self, status):

        if status == IO_STATUS_READY:
            self.status = IO_STATUS_READY

        elif status == IO_STATUS_IN_TYPEWRITER:
            if status == IO_STATUS_READY:
                self.sign = 0
            self.status = IO_STATUS_IN_TYPEWRITER

        else:
            print 'Error: unsupported IO device, ignored'
            self.status = IO_STATUS_READY

        return self.status == IO_STATUS_READY

    def get_status(self):
        if self.status != IO_STATUS_READY:
            self.slow_in()
        return self.status

    def slow_in(self):
        # read from device

        if self.status == IO_STATUS_IN_TYPEWRITER:
            in_data = self.g15.typewriter.read()
        else:
            print 'Error unsupported input device code'
            return

        if not in_data:
            return

        for data in in_data:

            if self.verbosity & VERBOSITY_IO_DETAIL:
                print 'data = ', mag_to_str(data)
                self.g15.drum.display(M23, 0, 4)

            if data & G15_DIGIT:
                # data nibble
                self.g15.drum.precess(M23, 4)

                if self.verbosity & VERBOSITY_IO_DETAIL:
                    print 'after precess, data = ', mag_to_str(data)
                    self.g15.drum.display(M23, 0, 4)

                m23_data = self.g15.drum.read(M23, 0)
                m23_data |= data & 0xf
                self.g15.drum.write(M23, 0, m23_data)
                continue

            elif data == G15_MINUS:
                self.sign = 1
                continue

            elif data == G15_CR or data == G15_TAB:
                self.g15.drum.precess(M23, 1)
                m23_data = self.g15.drum.read(M23, 0)
                m23_data |= self.sign & 1
                self.g15.drum.write(M23, 0, m23_data)
                self.sign = 0
                continue

            elif data == G15_SPACE:
                # ignore
                continue

            elif data == G15_RELOAD or data == G15_STOP:
                # shift M19 and copy M23

                # precess M19 by by four words
                for i in range(108 - 4):
                    j = 107 - i
                    data_word = self.g15.drum.read(M19, j - 4)
                    self.g15.drum.write(M19, j, data_word)

                    if self.verbosity & VERBOSITY_IO_DETAIL:
                        print 'moving from ', j - 4, ' to ', j

                # copy M23 to lower 4 words of M19
                for i in range(4):
                    data_word = self.g15.drum.read(M23, i)
                    self.g15.drum.write(M19, i, data_word)

                if data == G15_STOP:
                    self.set_status(IO_STATUS_READY)

                continue

            elif data == G15_PERIOD:
                # ignore
                continue

            elif data == G15_WAIT:
                # ignore
                continue

            print 'unknown slowin character: 0x%0x' % data

    def slow_out(self, device, data_track):
        # device = dev id.
        # data_track = line 19 or line 23
        #
        outstr = self.slow_out_format(device, data_track)
        if device == DEV_IO_TYPE:
            self.g15.typewriter.write(outstr)
        else:
            print 'Error: unknown IO device, device id: ', device

    #######################################
    #
    # format output
    #
    # note: routines converts to G15 alphabet
    #  and then converts to ascii
    #  this to preserve and allow paper tape punch to operate
    #
    #######################################

    def slow_out_format(self, device, data_track):
        outstr = []

        if device == DEV_IO_TYPE:
            enable_zero_suppress = 1
        else:
            enable_zero_suppress = 0

        if data_track == AR:  # AR
            words_to_print = 1
            format_track = 3
        elif data_track == M19:  # M19
            words_to_print = 108
            format_track = 2
        else:
            print 'Error: Illegal data track specified: %d', data_track
            self.g15.cpu.unknown_instruction_count += 1
            format_track = 2

        if self.verbosity & VERBOSITY_IO_SLOW_OUT:
            print 'slowout: data_track=', data_track, ' format_track=', format_track

        # gather format word pieces and assemble
        g15_format = self.g15.drum.read(format_track, 3)
        g15_format <<= 29
        g15_format |= self.g15.drum.read(format_track, 2)
        g15_format <<= 29
        g15_format |= self.g15.drum.read(format_track, 1)
        g15_format <<= 29
        g15_format |= self.g15.drum.read(format_track, 0)

        if self.verbosity & VERBOSITY_IO_SLOW_OUT:
            print 'format= 0x%x039x' % g15_format

        if self.verbosity & VERBOSITY_IO_FORMAT:
            print 'format3:= 0x%08x' % self.g15.drum.read(format_track, 3)
            print 'format2:= 0x%08x' % self.g15.drum.read(format_track, 2)
            print 'format1:= 0x%08x' % self.g15.drum.read(format_track, 1)
            print 'format0:= 0x%08x' % self.g15.drum.read(format_track, 0)

        end_flag = 0
        zero_suppress = enable_zero_suppress
        while not end_flag:
            for format_i in range(0, 38):

                # extract the format code
                shift_amt = 113 - format_i * 3
                format_code = g15_format >> shift_amt
                format_code &= 7

                if self.verbosity & VERBOSITY_IO_SLOW_OUT:
                    print 'format_i=', format_i, ' format_code=', format_code
                    if data_track == 19:
                        m19 = self.g15.drum.read(data_track, 107)
                        print ' m19_107: s=', m19 & 1, ' mag=%08x' % (m19 >> 1)

                if format_code == FORMAT_DIGIT:
                    data = self.g15.drum.read(data_track, 107)
                    self.g15.drum.precess(data_track, 4)

                    nibble = (data >> 25) & 0xf         # bits 24-27 (bit 28 has sign bit
                    if zero_suppress and nibble == 0:
                        outstr.append(G15_SPACE)
                    else:
                        outstr.append(G15_DIGIT | nibble)
                        #
                    if nibble != 0:
                        zero_suppress = 0

                elif format_code == FORMAT_SIGN:
                    # we ASSUME SIGN bit format is aligned to word boundry,  will
                    # fail if not.
                    word = self.g15.drum.read(data_track, 107)
                    if word & 1:
                        outstr.append(G15_MINUS)
                    else:
                        outstr.append(G15_SPACE)

                elif format_code == FORMAT_CR:
                    outstr.append(G15_CR)
                    zero_suppress = enable_zero_suppress
                    self.g15.drum.precess(data_track, 1)

                elif format_code == FORMAT_TAB:
                    outstr.append(G15_TAB)
                    zero_suppress = enable_zero_suppress
                    self.g15.drum.precess(data_track, 1)

                elif format_code == FORMAT_STOP:
                    # if M19, check if empty
                    zero_suppress = enable_zero_suppress
                    if data_track == 19:
                        zero_flag = 1
                        for i in range(108):
                            w = self.g15.drum.read(19, i)
                            if w != 0:
                                zero_flag = 0
                                break  # inner loop break

                        # precess is done above
                        if zero_flag == 1:
                            outstr.append(G15_STOP)
                            if self.verbosity & VERBOSITY_IO_SLOW_OUT:
                                print 'format complete'
                                print 'output=', outstr
                            end_flag = 1       # signal break of outer loop
                            break  # inner loop break
                        else:
                            outstr.append(G15_RELOAD)
                            break  # inner loop break, repeat outer loop, reset format

                    else:
                        # AR being output
                        outstr.append(G15_STOP)
                        if self.verbosity & VERBOSITY_IO_SLOW_OUT:
                            print 'format complete'
                            print 'output=', outstr
                        end_flag = 1
                        break  # inner loop break

                elif format_code == FORMAT_RELOAD:
                    zero_suppress = enable_zero_suppress
                    # not supported, in real g15, causes format to recycle
                    print 'Unverified: reload format character is not tested in the emulator'
                    self.g15.cpu.unknown_instruction_count += 1
                    break

                elif format_code == FORMAT_WAIT:
                    # outstr.append(G15_WAIT)
                    self.g15.drum.precess(data_track, 4)
                    zero_suppress = enable_zero_suppress

                elif format_code == FORMAT_PERIOD:
                    outstr.append(G15_PERIOD)
                    zero_suppress = 0

                else:
                    print 'Error:Unknown output format code: ', format
                    self.g15.cpu.unknown_instruction_count += 1
                    break

        # return the string of characters (g15 encoded) to output
        return outstr

    #
    # convert G15 io tape codes to typewriter outputs
    #   includes ASCII conversionsts
    def io_2_ascii(self, data_out):

        hex2ascii = ['0', '1', '2', '3', '4', '5', '6',
                     '7', '8', '9', 'u', 'v', 'w', 'x', 'y', 'z']

        if self.verbosity & VERBOSITY_IO_DETAIL:
            print 'L2Str: t data_out=', data_out

        str_out = ''
        for data in data_out:
            if data & G15_DIGIT:  # Numeric value
                char = hex2ascii[data & 0xf]
            elif data == G15_MINUS:
                char = '-'
            elif data == G15_CR:
                char = '\n'
            elif data == G15_TAB:
                char = '\t'
            elif data == G15_SPACE:
                char = ' '
            elif data == G15_PERIOD:
                char = '.'
            else:
                char = ''
            str_out += char
        return str_out

    def status(self):
        print
        print 'IO subsystem status:'
        print '\t', self.status
        print '\t', io_status_str[self.status]
