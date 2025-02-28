"""
Implement a basic line oriented command interpreter frontend to the g15.

These are the under-the-hood commands to control the emulator
for example, mount a particular paper tape onto the ptr (paper tape reader)

Some commands are local while others are in specific device class (ptr for instance)

"""
from time import sleep
import argparse
import os


from G15Subr import *
from G15Constants import *
from EmulLogger import *
from intg15 import intg15

PAUSE_CHECK_INTERVAL = 0.005	# default: 5ms


# noinspection PyPep8
class EmulCmds:
    """ Emulator Command Intrepreter """

    # noinspection PyPep8,PyPep8Naming
    def __init__(self, emul, g15, Verbosity=0):
        """
        Instantiate command interpreter

        :param emul:            # pointer to the emulator
        :param g15:             # g15 device class
        :param Verbosity:       # bit mask of debug verbosity
        """
        self.verbosity = Verbosity
        self.emul = emul
        self.g15 = g15

        self.prompt = "G15> "
        self.in_files = [sys.stdin]
        self.syms = {}                  # macro variables
        self.exit_flag = 0
        self.current_line_buffer = ''       # contents of current command line unparsed

        self.cmd_table = [
            ['button <on|off>                         : dc on/off (start/stop)',                self.cmd_button],
            ['dc <on|off>                             : dc on/off (start/stop)',                self.cmd_dc],
            ['dd <<drum address>                      : display drum',                          self.cmd_dd],
            ["echo [args....]                         : perform basic unix stye echo function", self.cmd_echo],
            ["exit                                    : early exit from an include file",       self.cmd_exit],
            ['help [cmds...]                          ; this help message',                     self.cmd_help],
            ['include <file>                          : execute command in file',               self.cmd_include],
            ['music <on|off>                          : enable music extraction',               self.cmd_music],
            ['pause                                   : wait for kybrd input',                  self.cmd_pause],
            ['ptr [mount <filename>]                  : paper tape reader',                     self.cmd_ptr],
            ['quit                                    : quit the g15d emulator',                self.cmd_quit],
            ['run [-t] <number of instrs>             : run quietly, -1 infinite',              self.cmd_run],
            ['set <macro name> <value>                : set a macro variable',                  self.cmd_set],
            ['status <all>|<block>                    : status',                                self.cmd_status],
            ['switch <sw type> <position>             : typewriter switch <enable,tape,computer>', self.cmd_switch],        
            ['system <linux sys cmd                   : send command to host OS',               self.cmd_system],
#            ['trace <number of instrs>                : run verbose, -1 infinite',              self.cmd_trace],
            ['type [-e] <typewriter  chars>           : typewriter input',                      self.cmd_type],
            ['verbosity <block name> <level>          : set verbosity bit mask on a block',     self.cmd_verbosity],
            ['verify <drum> <drum address> <sum>      : validate chksum on drum address range', self.cmd_verify]
        ]

        self.fout = sys.stdout
        self.fins = [sys.stdin]

    def start(self, files):
        """
        Start the command interpreter

        :param files:   list of included files to execute at start
        :return:        none
        """
        print("start files: ", files)
        startlist = []
        for file_name in files:
            startlist.append(['include', file_name])
        startlist.reverse()
        for item in startlist:
            print("AAAA START ", item)
            self.cmd_include(item)

    def cmd_do_from_processor_loop(self):
        fin = self.fins[-1]

        if fin == sys.stdin:
            # get input from terminal via queue
            if self.emul.getc.q.empty():
                return      # no stdin input available

            line = self.emul.getc.q.get()

        else:
            # get a line from an open file
            line = self.get_cmd(fin)

        if line is None:
            # file is complete
            if fin != sys.stdin:
                fin.close()
                self.fins = self.fins[:-1]
                return
            else:
                print("ERROR: attempt to close stdin, ignored")
                return

        # save the line and execute the command
        self.current_line_buffer = line
        self.process_command(line)

    def cmd_do(self, fin):
        """
        Read a command from input (stdin or file) and execute it

        :param fin: file handle to get command from
        :return:    none
        """
        while True:
#            if fin == sys.stdin:
#                print("calling kbhit")
#                # if keyboard input, is there anything available
#                if not self.emul.ascii.kbhit():
#                    continue
            if fin == sys.stdin:
                if not self.emul.getc.q.empty():
                    line = self.emul.getc.q.get()
            else:

                # we are reading from a file or there is input at the keyboard
                line = self.get_cmd(fin)

            if line is None:
                print("ERRROR EMPYT LINE")
                break

            # echo line if not done by system io subsystem
#            if fin != sys.stdin:
#                print line

            # save the line and execute the command
            self.current_line_buffer = line
            self.process_command(line)

            if self.exit_flag:
                break

    def process_command(self, line):
        """
        Process  user supplied command line

        :param line:        # command line
        :return:
        """

        if self.verbosity & 1:
            print('entering process command, line=', line)
        if len(line) == 0:
            return

        line = line.split('#')[0]

#        ii = line.find('#')
#        if ii != -1:
#            if ii > 0:
#                line = line[:ii]
#            else:
#                return

        args = line.split()
        if len(args) == 0:
            return

        # find number of commands that match first arg
        count = 0
        l = len(args[0])
        if l == 0:
            return

        cmd_handler = self.cmd_help
        for cmd_name, cmd_fcn in self.cmd_table:
            if args[0] == cmd_name[:l]:
                count += 1
                cmd_handler = cmd_fcn

        # do we have a match
        if count == 0:
            print('Error: unknown command: ', args[0])
            return
        elif count > 1:
            print('Unable to resolve command: ', args[0])
            return

        # have an exact match
        # will execute command, but first expand macros
        args = self.expand_macro(args)

        # before we execute a command, we need to stop the CPU
#        self.emul.request_lock(SIM_REQUEST_LOCK)

        # execute the command
        cmd_handler(args)

        # release CPU
 #       self.emul.request_lock(SIM_REQUEST_UNLOCK)

    def get_cmd(self, fin):
        """
        Gets a command line from file or stdin
        (Do not tokensize)

        :param fin:
        :return:
        """
        self.fout.write(self.prompt)
        self.fout.flush()

        # get a command
        line = fin.readline()
        if len(line) == 0:
            return None

        line = line.strip()

        # strip any trailing EOL characters
#        loc = line.find('\n')
#        if loc != -1:
#            line = line[:loc]
#        loc = line.find('\r')
#        if loc != -1:
#            line = line[:loc]

        if fin != sys.stdin:
            print(line)

        return line

    @staticmethod
    def parse_colon(text):
        """ Split a text string using ':' as delimited """
        subargs = text.split(':')

        for arg in subargs:
            if not arg.isnumeric():
                print("non numeric digit detect in range specification")
                return None

        return subargs

    def help(self, label):
        """ Display all the help available for the command """
        self.cmd_help(['', label])

    def expand_macro(self, args):
        """
        Expands a command line macro expansion

        Either entire token or if token contains : then subtoken
        """
        for ii in range(len(args)):
            # exact fit
            if args[ii] in self.syms:
                args[ii] = self.syms[args[ii]]
                continue

            # drum address complex address
            if ':' in args[ii]:
                tokens = args[ii].split(':')
                ll = len(tokens)
                for jj in range(ll):
                    if tokens[jj] in self.syms:
                        tokens[jj] = self.syms[tokens[jj]]
                        continue

                lstr = tokens[0]
                for jj in range(1, ll):
                    lstr = lstr + ':' + tokens[jj]

                args[ii] = lstr

        for sym, symvalue in self.syms.items():
            for i in range(len(args)):
                arg = args[i]
                arg.replace(sym, symvalue)
                if sym in arg:
                    args[i] = arg.replace(sym, symvalue)
        return args
        
    def cmds_pause(self):
        " monitor pause from pause command"

        if self.g15.cpu.sw_compute == "center" or \
	            (self.g15.cpu.sw_compute == "center" and not self.g15.cpu.sw_compute_bp_enable):
            self.cmd_pause_count = 0

        while self.cmd_pause_count:
            sleep(PAUSE_CHECK_INTERVAL)		# check every 5ms

    #############################################
    #
    # command handlers
    #
    ############################################

    def cmd_button(self, args):
        """ Emulate the DC power buttons (on/off) """

        self.cmd_switch(args)

    def cmd_dc(self, args):
        """ Emulate DC ON/OFF buttons on the G15 front panel """
        args.insert(0, 'button')
        self.cmd_switch(args)

    def cmd_dd(self, args):
        """ dd <track:startaddress:endaddress> """

        ll = len(args)
        if ll != 2:
            self.help('dd')
            return

        subargs = self.parse_colon(args[1])
        if subargs is None:
            return
        track, start, stop = self.g15.drum.address_decode(subargs)

        print('track = ',track, 'start=', start, 'stop=', stop)

        if track < 0:
                self.help('dd')
                return

        for wordtime in range(start, stop + 1):
            signmag = self.g15.drum.read(track, wordtime)
            outstr = signmag_to_str(signmag)
            outstr += ' ' + hex(self.g15.drum.read(track, wordtime))

            print(' %0d' % track, '%03d' % wordtime, ': ', outstr)

    @staticmethod
    def cmd_echo(args):
        """ Basic linux echo command """

        l = len(args)
        for i in range(l):
            print('%3s: ' % i, args[i])

    def cmd_exit(self, _args):
        """ early exit from an include file """
        self.exit_flag = 1

    def cmd_help(self, args):
        """ print all lines that begin w arg1 """

        l = len(args)
        if l > 1:
            allflag = 0
            cmp_str = args[1]
            l = len(args[1])
        else:
            allflag = 1
            cmp_str = ''
            l = 1

        for cmd_name, cmd_fcn in self.cmd_table:
            if (cmp_str == cmd_name[:l]) or allflag:
                print(cmd_name)

    def cmd_include(self, args):
        """ Read emulator commands from specified include file(s) """
        ll = len(args)
        if ll > 1:
            filename = args[1]
        else:
            print(self.help('include'))
            return

        try:
            fin = open(filename, 'r')
        except IOError:
            print('Error: Cannot open file: ', filename)
            return

        self.fins.append(fin)
        print("fins=", self.fins)
#        self.cmd_do(fin)
#        fin.close()

    def cmd_music(self, args):
        if len(args) < 2:
            self.help('music')
            return

        if args[1] == 'on':
            self.emul.music.enable(True)
            return
        elif args[1] == 'off':
            self.emul.music.enable(False)
            return

        self.help("music")
        return

    def cmd_pause(self, args):
        """ Pause the emulator for N instructions """

        ll = len(args)
        if ll != 2:
            self.help("pause")
            return
			
#        self.emul.cmd_pause_count = int(args[1], 0)
        self.emul.cmd_pause_count = intg15(args[1], 0)

        return


    def cmd_ptr(self, args):
        """
        Emulator paper tape Reader

        ptr                             returns tape status
        ptr mount <Tape Filename>       mount specified paper tape on the ptr

        :param args:
        :return:
        """

        ptr = self.g15.ptr

        ll = len(args)
        if ll <= 1:
            # print current status
            print('Taped Mounted: ', ptr.TapeName)
            print('Current Tape Position: Block ', ptr.ReadIndex)
            if ptr.NumberTrack:
                print('First Block is Number Track')
            else:
                print('First Block is not number Track')
            return

        cmd = args[1]
        if cmd == 'mount':
            if ll < 3:
                print("Error: ")
                return
            ptr.mount_tape(args[2])
            return

    def cmd_quit(self, _args):
        """ Quit the emulator """

        if self.verbosity & 1:
            print('entering quit')
        self.emul.quit()
        
    def cmd_run(self, args):
        arg_parser = argparse.ArgumentParser(prog="run")
        
        arg_parser.add_argument('-t', dest='trace', action='store_true', default=False)
        arg_parser.add_argument('iterations', type=int, default=1)

        if len(args) <= 1:
            self.help("run")
            return

        cmd_args = arg_parser.parse_args(args[1:])
        
        # trace        1
        self.g15.cpu.trace_flag = cmd_args.trace
        
        print("run, iterations=", cmd_args.iterations)

#        self.emul.request_lock(SIM_REQUEST_LOCK)

        self.emul.number_instructions_to_execute = cmd_args.iterations
        self.g15.cpu.halt_status = 0  # remove machine from Halt

#        self.emul.request_lock(SIM_REQUEST_UNLOCK)


    def cmd_set(self, args):
        """ set macro variables to control emulation  """

        ll = len(args)

        # list known macros
        if ll == 1:
            for var, value in self.syms.items():
                print('%25s:' % var, ' %s' % value)
            return

        # new variable
        if ll != 3:
            self.help('set')
            return

        var = args[1]
        value = args[2]

        self.syms[var] = value

        return

    def cmd_status(self, args):
        """ Display status of specified block of the emulator """

        ll = len(args)

        block_dict = self.g15.__dict__
        blocks = []
        for block_key in block_dict:
            block = block_dict[block_key]
            if hasattr(block, 'Status'):
                blocks.append(str(block_key))

        if ll == 1:
            print('Status is available on the following blocks: ', blocks)
            return

        flag = 1
        for block_name in blocks:
            if (block_name in args) or (args[1] == 'all'):
                block = block_dict[block_name]
                try:
                    block.Status()
                    flag = 0
                except AttributeError:
                    pass
        if flag:
            print("Unknown block or block does not have status option: ", args[1])
			
        return
        
    def cmd_switch(self, args):   
        # format: switch <id> <pos>
#        print("sw: ", args)
  
        ll = len(args)
        if ll == 1:
            print("sw  enable: ", self.g15.cpu.sw_enable)
            print("sw    tape: ", self.g15.cpu.sw_tape)
            print("sw compute: ", self.g15.cpu.sw_compute)
            return
        elif ll != 3:
            self.help("switch")
            return
    
        sw = args[1]
        value = args[2]
        
        if sw not in sw_mappings:
            print("sw is unknown: ", sw)
            known_switches = []
            for sw in sw_mappings:
                known_switches.append(sw)
            print("known switches are: ", sw)
            self.help("switch")
            return
        
        mapping = sw_mappings[sw]       # allowable switch positions       
        if value not in mapping:
            print("sw position is unknown: ", value)
            known_switch_pos = []
            for pos in mapping:
                known_switch_pos.append(pos)
            print("known switch positions are: ", known_switch_pos)
            self.help("switch")
            return        

        mesg_type = sw
        mesg_value = mapping[value]
        print("moving switch")
        self.emul.send_mesg(mesg_type, mesg_value)

    def cmd_system(self, args):
        if len(args) < 2:
            self.help("system")
            return

        # reassemable cmd line
        line = ''
        for arg in args[1:]:
            line += ' ' + arg

        os.system(line)

    def cmd_type(self, args):
        """ Emulate the G15 typewriter keyboard """

        if len(args) < 1:
            self.help("type")

        print("type: total_revolutions: ", self.g15.cpu.total_revolutions)
        self.g15.typewriter.type(args[1])

#        self.emul.request_lock(SIM_REQUEST_LOCK)
#        self.emul.number_instructions_to_execute = 2
#        self.emul.request_lock(SIM_REQUEST_UNLOCK)

    def cmd_verbosity(self, args):
        """ Control the emulator debug verbosity of the various emulator blocks/pieces """
        ll = len(args)

        known_blocks = {
            'cpu': self.g15.cpu,
            'drum': self.g15.drum,
            'emul': self.emul,
            'ptr': self.g15.ptr
        #cmd_verbosity
        }
        if ll == 1:
            for block_name, handle in known_blocks.items():
                print('%5s' % block_name, ' 0x%02x' % handle.verbosity)
            return

        if ll != 3:
            self.help("verbosity")
            return

        if args[1] in known_blocks:
            handle = known_blocks[args[1]]
            #level = int(args[2], 0)
            level = intg15(args[2], 0)
            handle.verbosity = level

        else:
            self.help("verbosity")
            print()

        print('Verbosity flags:')
        for block, handle in known_blocks.items():
            print('%4s' % block, ' %04x' % handle.verbosity)

    def cmd_verify(self, args):
        """
        Verify some machine element

        verify < "drum" > <drum_address> <check_value>

        Note: Other targets to be added.

        if drum target is selected:
            takes a drum address and checks the value(s) read
            if an address range is given, then the checksum of data is verified

            drumaddress take the form of:
                <track> ':' <word id>     or
                <track> ':' <word_id_start> ':' <word_id_stop>
        """

        ll = len(args)
        if ll < 2:
            self.help('verify')
            return

        if args[1] == 'drum':
            # form is:  verify 'drum' <drum_address> <value>
            # where drum_address = <track id> ':' <word id start> [ ':' <word id stop> ]
            if ll < 4:
                self.help('verify')
                return

            subargs = self.parse_colon(args[2])
            if subargs is None:
                return
            track, start, stop = self.g15.drum.address_decode(subargs)
            if track < 0:
                self.help('verify')
                return

            sum_signmag = self.g15.drum.checksum(track, start, stop)
            sum_signmag_str = signmag_to_str(sum_signmag)

            sum_target_str = args[3]
            sum_target_signmag = str_to_signmag(sum_target_str)

            if sum_target_signmag != sum_signmag:
                self.emul.increment_error_count('chksum error: target=' + sum_target_str +
                                    ' drum=' + sum_signmag_str)
            else:
                print('Chksum is correct: ', sum_target_str)

            return

        elif args[1] == 'iostatus':
            """ Display G15 IO subsystem status """
            if ll != 3:
                self.help('verify')

            io_status = self.g15.iosys.status
            str_io_status = int_to_str(io_status)
            expected_status = intg15(args[2], 0)
            expected_status_str = int_to_str(expected_status)

            if expected_status == io_status:
                print('Correct io status detectec: ', str_io_status)
            else:
                self.emul.increment_error_count('iostatus error: expected=' + expected_status_str +
                            ' actual=' + str_io_status)

        elif args[1] == 'pc':
            """ Display/Change the 'program counter' (next instruction location) """

            if ll < 3:
                self.help('verify')
                return

            # where is next instruction coming from
            if self.g15.cpu.instruction['next_cmd_acc']:
                next_instr_address = [28, 0]
            else:
                cmd_line = self.g15.cpu.instruction['next_cmd_line']
                cmd_line_track = cmd_line_map[cmd_line]
                next_instr_address = [cmd_line_track, self.g15.cpu.instruction['next_cmd_word_time']]

            subargs = self.parse_colon(args[2])
            if subargs is None:
                return
            if len(subargs) != 2:
                self.help('verify')
                return

            for ii in range(len(subargs)):
                subargs[ii] = intg15(subargs[ii],0)

            flag = 1
            for i in range(2):
                if next_instr_address[i] != subargs[i]:
                    flag = 0

            if flag:
                print('next instruction address matches: ', args[2])
            else:
                self.emul.increment_error_count(' next instruction address does not match, expected: ' + args[2] +
                            ' was: ' + str(next_instr_address[0]) + ':' + str(next_instr_address[1]))

            return

        elif args[1] == 'flags':
            """
            Display the various G15 flag bits
            
            Can also use to validate the values of the flag bits for self testing
            """
            if ll != 3:
                self.help('verify')
                return

            # what flaga are expected?
            flags_expected = intg15(args[2], 0)

            flag_overflow = self.g15.cpu.overflow
            flag_carry = self.g15.cpu.acc_carry
            flag_da1 = self.g15.cpu.status_da1

            flags = flag_da1
            flags = (flags << 1) | flag_carry
            flags = (flags << 1) | flag_overflow

            if flags == flags_expected:
                print('correct: flags match')
            else:
                self.emul.increment_error_count(' flags do not match, expected: ' + args[2] +
                            ' was: ' + hex(flags))

        elif args[1] == 'bell':
            """ Display/Verify number of bell rings """

            if ll != 3:
                self.help('verify')
                return

            bell_count_expected = intg15(args[2],0)

            bell_count = self.g15.cpu.bell_count  # number of times that bell has been rung

            if bell_count == bell_count_expected:
                print('correct: bell count matches')
            else:
                self.emul.increment_error_count(' bell count does not match, expected: ' + args[2] +
                            ' was: ' + hex(bell_count))

        elif args[1] == 'error':
            """ Verify number of emulator validation errors detected """
            if ll != 3:
                self.help('verify')
                return

            expected_errors = intg15(args[2])
            self.emul.check_error_count(expected_errors)

            return

        else:
            self.emul.increment_error_count('Unknown verify cmd type: ' + args[1])
            return

        return
