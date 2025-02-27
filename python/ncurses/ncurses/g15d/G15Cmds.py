"""
Implement a basic line oriented command interpreter frontend to the g15.

These are the under-the-hood commands to control the emulator
for example, mount a particular paper tape onto the ptr (paper tape reader)

Some commands are local while others are in specific device class (ptr for instance)

"""
from time import sleep

from G15Subr import *

# sys.path.append('../g15_emul')
from G15Logger import *
from G15Constants import *


# noinspection PyPep8
class G15Cmds:
    """ Emulator Command Intrepreter """

    # noinspection PyPep8,PyPep8Naming
    def __init__(self, sim, Verbosity=0):
        """
        Instantiate command interpreter

        :param sim:             # pointer to simulator
        :param Verbosity:       # bit mask of debug verbosity
        """
        self.verbosity = Verbosity

        self.sim = sim
        self.g15 = sim.g15

        self.prompt = "G15> "
        self.in_files = [sys.stdin]
        self.syms = {}                  # macro variables
        self.exit_flag = 0

        self.current_line_buffer = ''       # contents of current command line unparsed

        self.cmd_table = [
            ['button <on|off>                         : dc on/off (start/stop)',                self.cmd_dc],
            ['dc <on|off>                             : dc on/off (start/stop)',                self.cmd_dc],
            ['dd <<drum address>                      : display drum',                          self.cmd_dd],
            ["echo [args....]                         : perform basic unix stye echo function", self.cmd_echo],
            ["exit                                    : early exit from an include file",       self.cmd_exit],
            ['help [cmds...]                          ; this help message',                     self.cmd_help],
            ['include <file>                          : execute command in file',               self.cmd_include],
            ['pause                                   : wait for kybrd input',                  self.cmd_pause],
            ['ptr [mount <filename>]                  : paper tape reader',                     self.cmd_ptr],
            ['quit                                    : quit the g15d emulator',                self.cmd_quit],
            ['run <number of instrs>                  : run quietly, -1 infinite',              self.cmd_run],
            ['set <macro name> <value>                : set a macro variable',                  self.cmd_set],
            ['status <all>|<block>                    : status',                                self.cmd_status],
            ['trace <number of instrs>                : run verbose, -1 infinite',              self.cmd_trace],
            ['type <typewriter  chars>                : typewriter input',                      self.cmd_type],
            ['verbosity <block name> <level>          : set verbosity bit mask on a block',     self.cmd_verbosity],
            ['verify <drum> <drum address> <sum>      : validate chksum on drum address range', self.cmd_verify]
        ]

        self.fout = sys.stdout
        self.fin = sys.stdin

    def start(self, files):
        """
        Start the command interpreter

        :param files:   list of included files to execute at start
        :return:        none
        """

        file_names = files.split()
        for file_name in file_names:
            if file_name == " __dummy__":
                continue
            aa = ['include', file_name]
            self.cmd_include(aa)

        self.cmd_do(sys.stdin)

    def cmd_do(self, fin):
        """
        Read a command from input (stdin or file) and execute it

        :param fin: file handle to get command from
        :return:    none
        """

        while True:
            line = self.get_cmd(fin)

            if line is None:
                break

            # echo line if not done by system io subsystem
#            if fin != sys.stdin:
#                print(line)

            # save the line and execute the command
            self.current_line_buffer = line
            self.process_command(line)

            if self.exit_flag:
                break

    def process_command(self, line):
        """
        Process an user supplied command line

        :param line:        # command line
        :return:
        """

        if self.verbosity & 1:
            print('entering process command, line=', line)
        if len(line) == 0:
            return

        ii = line.find('#')
        if ii != -1:
            if ii > 0:
                line = line[:ii]
            else:
                return

        args = line.split()

        # find number of commands that match first arg
        count = 0
        length = len(args[0])
        if length == 0:
            return

        cmd_handler = self.cmd_help
        for cmd_name, cmd_fcn in self.cmd_table:
            if args[0] == cmd_name[:length]:
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
        if self.g15.cpu.power_status:
            self.sim.request_lock(SIM_REQUEST_LOCK)

        # execute the command
        cmd_handler(args)

        # release CPU
        if self.g15.cpu.power_status:
            self.sim.request_lock(SIM_REQUEST_UNLOCK)

    def get_cmd(self, fin):
        """
        Gets a command line from file or stdin
        (Do not tokenize)

        :param fin:
        :return:
        """

        self.fout.write(self.prompt)

        # get a command
        line = fin.readline()

        if len(line) == 0:
            return None

        # strip any trailing EOL characters
        loc = line.find('\n')       # unix/linux/MAC
        if loc != -1:
            line = line[:loc]
        loc = line.find('\r')       # windows
        if loc != -1:
            line = line[:loc]

        if fin != sys.stdin:
            print(line)

        return line

    @staticmethod
    def parse_colon(text):
        """ Split a text string using ':' as delimited """
        subargs = text.split(':')
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

        return args

    #############################################
    #
    # command handlers
    #
    ############################################

    def cmd_button(self, args):
        """ Emulate the DC power buttons (on/off) """

        self.cmd_dc(args)

    def cmd_dc(self, args):
        """ Emulate DC ON/OFF buttons on the G15 front panel """

        length = len(args)

        if length == 1:
            # display current DC status
            return

        cmd = args[1].lower()

        if (cmd == 'on') or (cmd == 'dc_off'):
            self.g15.cpu.dc_button(DC_ON)
        elif (cmd == 'off') or (cmd == 'dc_off'):
            self.g15.cpu.dc_button(DC_OFF)
        else:
            self.help("dc")

    def cmd_dd(self, args):
        """ dd <track:startaddress:endaddress> """

        length = len(args)
        if length != 2:
            self.help('dd')
            return

        subargs = self.parse_colon(args[1])
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

        length = len(args)
        for i in range(length):
            print('%3d: ' % i, args[i])

    def cmd_exit(self, args):
        """ early exit from an include file """
        self.exit_flag = 1

    def cmd_help(self, args):
        """ print all lines that begin w arg1 """

        length = len(args)
        if length > 1:
            allflag = 0
            cmp_str = args[1]
            length = len(args[1])
        else:
            allflag = 1
            cmp_str = ''
            length = 1

        for cmd_name, cmd_fcn in self.cmd_table:
            if (cmp_str == cmd_name[:length]) or allflag:
                print(cmd_name)

    def cmd_include(self, args):
        """ Read emulator commands from specified include file(s) """

        length = len(args)
        if length > 1:
            filename = args[1]
        else:
            print(self.help('include'))
            return

        try:
            fin = open(filename, 'r')
        except IOError:
            print('Error: Cannot open file: ', filename)
            return

        self.cmd_do(fin)
        fin.close()

    def cmd_pause(self, args):
        """ Pause the emulator - <cr> to continue emulation """

        print('Enter <cr> to continue')
        sys.stdin.readline()

    def cmd_ptr(self, args):
        """
        Emulator paper tape Reader

        ptr                             returns tape status
        ptr mount <Tape Filename>       mount specified paper tape on the ptr

        :param args:
        :return:
        """

        ptr = self.g15.ptr

        length = len(args)
        if length <= 1:
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
            if length < 3:
                print("Error: ")
                return
            ptr.mount_tape(args[2])
            return

    def cmd_quit(self, args):
        """ Quit the emulator """

        if self.verbosity & 1:
            print('entering quit')
        self.sim.quit()

    def cmd_run(self, args):
        """ Execute (without trace) N G15 instructions """

        length = len(args)
        if length < 2:
            iterations = 1
        else:
            iterations = int(args[1], 0)

        self.sim.execute_trace_enable = 0
        self.g15.cpu.trace_flag = 0

        self.cmd_trace_execute(iterations)

    def cmd_set(self, args):
        """ set macro variables to control emulation  """

        length = len(args)

        # list known macros
        if length == 1:
            print('type=', self.syms)
            print('dir=', self.syms)
            for var, value in self.syms.items():
                print('%15s:' % var, ' %s' % value)

        # new variable
        if length != 3:
            self.help('set')
            return

        var = args[1]
        value = args[2]

        self.syms[var] = value

        return

    def cmd_status(self, args):
        """ Display status of specified block of the emulator """

        length = len(args)

        block_dict = self.g15.__dict__

        blocks = []
        for block_key in block_dict:
            block = block_dict[block_key]
            if hasattr(block, 'Status'):
                blocks.append(str(block_key))
            if hasattr(block, 'status'):
                blocks.append(str(block_key))

        if length == 1:
            print('Status is available on the following blocks: ', blocks)
            return

        for block_name in blocks:
            if (block_name in args) or (args[1] == 'all'):
                block = block_dict[block_name]
                try:
                    block.Status()
                except AttributeError:
                    pass
                try:
                    block.status()
                except AttributeError:
                    pass
        return

    def cmd_trace(self, args):
        """ Execute (with trace) N G15 instructions """

        length = len(args)

        flag = TRACE_ENABLE
        if length >= 2:
            c = args[1][0]
            if c == '-':

                # -a
                if 'a' in args[1]:
                    flag = TRACE_ACC

                # shift the arguments down
                length -= 1
                if length >= 2:
                    args[1] = args[2]

                print('args1=', args[1])

        if length < 2:
            iterations = 1
        else:
            try:
                iterations = int(args[1], 0)
            except:
                self.help('trace')
                return

        self.sim.execute_trace_enable = 1
        self.g15.cpu.trace_flag = flag

        self.cmd_trace_execute(iterations)

    def cmd_trace_execute(self, iterations):
        """
        Executes specified number of instructions

        Is called by both cmd_run() and cmd_trace()
        """

        if iterations < 0:
            iterations = 0

        self.sim.number_instructions_to_execute = iterations

        if iterations:
            # release execution thread since cmds will lock first
            self.sim.request_lock(SIM_REQUEST_UNLOCK)

            while self.sim.number_instructions_to_execute:
                sleep(SEMAPHORE_WAIT_TIME)

    def cmd_type(self, args):
        """ Emulate the G15 typewriter keyboard """

        length = len(args)
        if length < 2:
            type_string = ''
        else:
            type_string = self.current_line_buffer

        self.g15.typewriter.type(type_string)

    def cmd_verbosity(self, args):
        """ Control the emulator debug verbosity of the various emulator blocks/pieces """
        length = len(args)

        known_blocks = {
            'cpu': self.g15.cpu,
            'drum': self.g15.drum,
            'sim': self.g15.sim,
            'ptr': self.g15.ptr
        }
        if length == 1:
            for block_name, handle in known_blocks.items():
                print('%5s' % block_name, ' 0x%02x' % handle.verbosity)
            return

        if length != 3:
            self.help("verbosity")
            return

        if args[1] in known_blocks:
            handle = known_blocks[args[1]]
            level = int(args[2], 0)
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

        length = len(args)
        if length < 2:
            self.help('verify')
            return

        if args[1] == 'drum':
            # form is:  verify 'drum' <drum_address> <value>
            # where drum_address = <track id> ':' <word id start> [ ':' <word id stop> ]
            if length < 4:
                self.help('verify')
                return

            subargs = self.parse_colon(args[2])
            track, start, stop = self.g15.drum.address_decode(subargs)
            if track < 0:
                self.help('verify')
                return

            sum_signmag = self.g15.drum.checksum(track, start, stop)
            sum_signmag_str = signmag_to_str(sum_signmag)

            sum_target_str = args[3]
            sum_target_signmag = str_to_signmag(sum_target_str)

            if sum_target_signmag != sum_signmag:
                self.g15.sim.increment_error_count('chksum error: target=' + sum_target_str +
                        ' drum=' + sum_signmag_str)
            else:
                print('Chksum is correct: ', sum_target_str)

            return

        elif args[1] == 'iostatus':
            """ Display G15 IO subsystem status """
            if length != 3:
                self.help('verify')

            io_status = self.g15.iosys.status
            str_io_status = int_to_str(io_status)
            expected_status = int(args[2], 0)
            expected_status_str = int_to_str(expected_status)

            if expected_status == io_status:
                print('Correct io status detectec: ', str_io_status)
            else:
                self.g15.sim.increment_error_count('iostatus error: expected=' + expected_status_str +
                        ' actual=' + str_io_status)

        elif args[1] == 'pc':
            """ Display/Change the 'program counter' (next instruction location) """

            if length < 3:
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
            if len(subargs) != 2:
                self.help('verify')
                return

            for ii in range(len(subargs)):
                subargs[ii] = int(subargs[ii], 0)

            flag = 1
            for i in range(2):
                if next_instr_address[i] != subargs[i]:
                    flag = 0

            if flag:
                print('next instruction address matches: ', args[2])
            else:
                self.g15.sim.increment_error_count(' next instruction address does not match, expected: ' + args[2] +
                            ' was: ' + str(next_instr_address[0]) + ':' + str(next_instr_address[1]))

            return

        elif args[1] == 'flags':
            """
            Display the various G15 flag bits
            
            Can also use to validate the values of the flag bits for self testing
            """
            if length != 3:
                self.help('verify')
                return

            # what flaga are expected?
            flags_expected = int(args[2], 0)

            flag_overflow = self.g15.cpu.overflow
            flag_carry = self.g15.cpu.acc_carry
            flag_da1 = self.g15.cpu.status_da1

            flags = flag_da1
            flags = (flags << 1) | flag_carry
            flags = (flags << 1) | flag_overflow

            if flags == flags_expected:
                print('correct: flags match')
            else:
                self.g15.sim.increment_error_count(' flags do not match, expected: ' + args[2] +
                            ' was: ' + hex(flags))

        elif args[1] == 'bell':
            """ Display/Verify number of bell rings """

            if length != 3:
                self.help('verify')
                return

            bell_count_expected = int(args[2], 0)

            bell_count = self.g15.cpu.bell_count  # number of times that bell has been rung

            if bell_count == bell_count_expected:
                print('correct: bell count matches')
            else:
                self.g15.sim.increment_error_count(' bell count does not match, expected: ' + args[2] +
                            ' was: ' + hex(bell_count))

        elif args[1] == 'error':
            """ Verify number of emulator validation errors detected """
            if length != 3:
                self.help('verify')
                return

            expected_errors = int(args[2])
            self.g15.sim.check_error_count(expected_errors)

            return

        else:
            self.g15.sim.increment_error_count('Unknown verify cmd type: ' + args[1])
            return

        return

