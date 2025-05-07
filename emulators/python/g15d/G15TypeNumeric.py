

from G15Subr import *


class G15TypeNumeric:
    def __init__(self, g15, Verbosity=0):
        self.verbosity = Verbosity
        self.g15 = g15

        self.output_history = []            # output (and input) history buffer
        self.input_buffer = []              # line buffer of G15 symbols types, ready for transfer to G15

        self.out_history = ['']

    def type_enable(self, cmd_str):
        for c in cmd_str:
            if (c == ' ') or (c == '\t'):
                continue
                
            if c in '01234567':
                self.g15.cpu.instruction['next_cmd_line'] = int(c, 0)
                continue

            if c == 'a':
                self.g15.iosys.slow_out(DEV_IO_TYPE, AR)
                self.g15.drum.write(AR, 0, 0)     # verilog shows AR is preserved, so restore value
                continue

            if c == 'b':
                self.g15.cpu.block = self.g15.ptr.reverse(1)
                continue

            if c == 'c':
                self.g15.cpu.instruction['next_cmd_line'] = self.g15.cpu.instruction['ch']
                continue
                
            if c == 'i':
                self.g15.cpu.instruction_execute(0)
                continue

            if c == 'f':
                self.g15.cpu.instruction['next_cmd_word_time'] = 0
                continue
                
            if c == 'm':
                self.g15.cpu.cpu_d31.GoToMask(self.g15.cpu.instruction)
                continue

            if c == 'p':
                # read a block of paper tape
                print("enable-p detected")
                self.g15.ptr.read_block()
                self.g15.cpu.instruction['next_cmd_word_time'] = 0
                self.g15.cpu.instruction['next_cmd_line'] = 7
                continue

            if c == 'q':
                self.g15.iosys.set_status(IO_STATUS_IN_TYPEWRITER)
                continue
                
            if c == 'r':
                self.g15.cpu.cpu_d31.ReturnToMark(self.g15.cpu.instruction)
                continue

            if c == 's':
                self.g15.iosys.set_status(IO_STATUS_READY)
                continue
                
            if c == 't':
                wt = self.g15.cpu.instruction['next_cmd_word_time']
                self.g15.drum.write(AR, 0, wt)
                continue
                                
    def write(self, outstr):
        # type on typewriter

        # list(filter(G15_WAIT.__ne__, outstr))
        # list(filter(G15_RELOAD.__ne__, outstr))
        # list(filter(G15_STOP.__ne__, outstr))

        ascii_str = self.g15.iosys.io_2_ascii(outstr)
        #self.output_history.append(ascii_str)

        # loading spaces
#        while True:
#            if ascii_str[0] == ' ':
#                ascii_str = ascii_str[1:]
#            else:
#                break

        # following handles output whose lines span multiple format statements
        for c in ascii_str:
            self.out_history[-1] += c
            if c == '\n':
                print("TYPEOUT: ", self.out_history[-1])
                self.out_history.append('')
        if len(self.out_history[-1]):
            print("TYPEOUT: ", self.out_history[-1])

        if False:
            for c in ascii_str:
                self.out_history[-1].append(c)
                if c == '\n':
                    print("TYPEOUT: ", self.out_history[-1])
                    self.out_history.append([])
            if len(self.out_history[-1]):
                print("TYPEOUT: ", self.out_history[-1])

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
        # buffer is shared with output
        #
        # maintains a one-line buffer for transfer to G15 (in G15 symbols)
        #
        # if called without a 'typed' string, then display typewrite history
        if in_str == '':
            print(self.output_history)
            return
                    
        if self.g15.cpu.sw_enable == 'on':
            # the enable sw is on 
            self.type_enable(in_str)
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
                dict1 = ascii_to_code[c]
                code = dict1['code']
                devices = dict1['devices']

                if not (devices & IO_DEVICE_TYPEWRITER):
                    continue

                self.input_buffer.append(code)
