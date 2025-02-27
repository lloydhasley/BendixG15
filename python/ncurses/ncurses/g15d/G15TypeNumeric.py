

from G15Constants import *
from G15Subr import *


class G15TypeNumeric:
    def __init__(self, g15, Verbosity=0):
        self.verbosity = Verbosity
        self.g15 = g15

        self.output_history = []            # output (and input) history buffer
        self.input_buffer = []              # line buffer of G15 symbols types, ready for transfer to G15

    def write(self, outstr):
        # type on typewriter

        print(outstr)

        ascii_str = self.g15.iosys.io_2_ascii(outstr)
        self.output_history.append(ascii_str)
        print(ascii_str)

    def read(self):
        # characters from keyboard,
        # move characters received into G15
        data = self.input_buffer
        self.input_buffer = []
        return data

    def type(self, in_str):
        # accepts string inputs from typewriter
        # stores until g15 prompts for input
        #   g15 gets typewrite input when it tests for io ready
        #
        # maintains a 50 line history buffer (in ascii)
        # buffer is shared without output
        #
        # maintins a one-line buffer for transfer to G15 (in G15 symbols)
        #

        # if called without a 'typed' string, then display typewrite history
        if in_str == '':
            print(self.output_history)
            return

        # if not control input, take as data if IOsys is accepting typewriter input
        if self.g15.iosys.status != IO_STATUS_IN_TYPEWRITER:
            print('warning, typewriter input ignored, g15 not in type io mode')
            return

        cmd_str = 'type '
        ii = in_str.find(cmd_str)
        if ii == 0:
            in_str = in_str[len(cmd_str):]

        # IO sys is accepting input
        for c in in_str:
            if c in ascii_to_code:
                # known char
                dict = ascii_to_code[c]
                code = dict['code']
                devices = dict['devices']

                # throw away if unknown
                if not (devices & IO_DEVICE_TYPEWRITER):
                    continue

                self.input_buffer.append(code)
