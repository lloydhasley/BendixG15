"""
Class G15Cpu emulates a G15 CPU

NOTE:  This is a ISA emulator working at the word/instruction level
    It is NOT a bit level emulator
"""

import sys
import copy

from G15Subr import *
import G15Cpu_ar
import G15Cpu_pn
import G15Cpu_fetch
import G15Cpu_decode
import G15Cpu_eb
import G15Cpu_ib
import G15Cpu_lb
import G15Cpu_d31
import G15Cpu_store
import G15Cpu_log

VERBOSITY_CPU_DETAILS = 1
VERBOSITY_CPU_TRACE = 2
VERBOSITY_CPU_MICRO_TRACE = 4
VERBOSITY_CPU_DEBUG = 8         # used for temporary debug prints
VERBOSITY_CPU_EARLY_BUS = 16
VERBOSITY_CPU_INTERMEDIATE_BUS = 32
VERBOSITY_CPU_LATE_BUS = 64
VERBOSITY_CPU_D31 = 128
VERBOSITY_CPU_MATH = 256        # multiply/divide
VERBOSITY_CPU_PN = 512
VERBOSITY_CPU_LOG_STDOUT = 1024
VERBOSITY_CPU_AR = 2048

WORD_WIDTH = 29
SP_MASK = (1 << WORD_WIDTH) - 1
DP_MASK = (1 << (WORD_WIDTH * 2)) - 1

SPECIAL = 31


# noinspection PyAttributeOutsideInit
class G15Cpu:
    """ Emulates the CPU portion of a G15D computer """

    # noinspection PyPep8Naming
    def __init__(self, g15, Verbosity=0x00, vtracefile=""):
        self.g15 = g15  # back pointer to g15 main class
        self.verbosity = Verbosity
        # self.verbosity = VERBOSITY_CPU_DETAILS | VERBOSITY_CPU_DEBUG
        self.vtracefile = vtracefile

        print('g15=', self.g15)

        # instantiate the CPU sub-blocks
        self.cpu_fetch = G15Cpu_fetch.g15d_fetch(self)
        self.cpu_decode = G15Cpu_decode.g15d_decode(self, self.verbosity)
        self.cpu_eb = G15Cpu_eb.g15d_eb(self)
        self.cpu_ib = G15Cpu_ib.g15d_ib(self)
        self.cpu_lb = G15Cpu_lb.g15d_lb(self)
        self.cpu_d31 = G15Cpu_d31.g15d_d31(self, self.verbosity)
        self.cpu_store = G15Cpu_store.g15d_store(self)
        flag = 0
        if self.verbosity & VERBOSITY_CPU_LOG_STDOUT:
            flag = 1
        self.cpu_log = G15Cpu_log.g15d_log(self, flag, vtracefile)    # Verilog trace output

        self.cpu_ar = G15Cpu_ar.g15d_AR(self)
        self.cpu_pn = G15Cpu_pn.g15d_PN(self, self.verbosity)

        ###############################################
        #
        # TTR12 tape is read, commands are in M19,M23
        #
        # prepare rest of CPU for execution
        #
        ################################################

        self.cpu_init(0)

        self.bell_ring_count = 0

        # number of instructions executed since start of emulation
        self.total_instruction_count = 0

        # num of instructions that emulator did not implement
        self.unknown_instruction_count = 0

        # num of detected errors (other than unknown instr)
        self.errors = 0

        # default is silent running
        self.trace_flag = 0
        self.file_elog = None

        # create a sim event and schedule it for time 0
        # self.event = create_event('cpu', self.event_handler)

    def start(self, sim):
        """
        Starts the CPU event queue

        :param sim: pointer back to the main simulator
        """
        self.sim = sim

        # called by simulator, after it is brought online
        self.event = self.sim.create_event('cpu', self.event_handler)
        self.sim.schedule_event(self.event, 0)

    def cpu_init(self, power_status):
        """
        Initializes the internal variable used the G15 CPU emulator

        Is called by dc_button() when the DC Power On or Power Off buttons are depressed

        :param power_status: 1=Power On Button, 0=Power Off Button
        """

        # noinspection PyDictCreation
        instruction = {}
        instruction['instr'] = 0
        instruction['cmd_line'] = 7     # start execution at 23:0
        instruction['n'] = 0
        instruction['next_cmd_word_time'] = 0
        instruction['next_cmd_line'] = 7
        instruction['next_cmd_acc'] = 0
        instruction['cmd_acc'] = 0
        self.instruction = instruction
        # self.instruction_decode(self.instruction)

        self.mark_time = 0       # initialize saved mark
        self.sign = 0               # clear sign flag
        self.overflow = 0           # clear overflow flag
        self.acc_carry = 0
        self.status_da1 = 0
        self.halt_flag = 0

        self.flop_is = 0
        self.flop_ip = 0
        self.flop_ic = 0
        self.flop_cq = 0

        self.bell_count = 0  # number of times that bell has been rung

        self.power_status = power_status

    def event_handler(self):
        """
        Event Entry point from the simulator

        Have an event from the emulator queue
        CPU event is an execute instruction event
        """
        time_length = self.instruction_execute(self.trace_flag)
        # self.g15.sim.schedule_event(self.event, self.g15.sim.sim_time + time_length)
        self.g15.sim.schedule_event(self.event, time_length)

    #####################################
    #
    # physical interfaces
    #
    #####################################

    def dc_button(self, button):
        """
        Emulates the DC Power ON/OFF button presses

        :param button:  1=On, 0=Off
        """
        if button and (not self.power_status):

            # intiialize next instr address and cpu flags
            self.cpu_init(button)

            # begin system start up sequence
            #
            # first: check that we have a paper tape mounted
            if len(self.g15.ptr.tape_parsed) == 0:
                print('User Error: no paper tape is mounted')
                return

            # second: rewind the tape
            self.g15.ptr.read_index = 0

            # third: Read a block of tape into line 19'

            # print('Reading tape block')
            self.block = self.g15.ptr.read_block()

            # fourth: verify that block read was number track
            if not self.g15.ptr.check_if_numbertrack(self.block):
                print('Mounted paper tape does not have number first tape block')
                return
            else:
                print('Number Track found')
                print('Copying Number Track into Place')

            # fifth: copy line 19 to CN
            # copy M19 into CN (number track)
            for i in range(108):
                temp = self.g15.drum.read(M19, i)
                self.g15.drum.write(CN, i, temp)
            self.g15.drum.track_origin[CN] = self.g15.drum.track_origin[M19]

            # sixth: read second block to L19
            #   should not be number track

            # print('Reading tape block')
            self.block = self.g15.ptr.read_block()

            # everything is ready, start the G15
            self.g15.sim.request_lock(SIM_REQUEST_UNLOCK)  # allow execution thread to commenc

        elif (not button) and self.power_status:
            # off button pressed

            self.g15.sim.request_lock(SIM_REQUEST_LOCK)  # stop the execution thread.

            # turn things off
            self.cpu_init(button)

            if self.vtracefile is not None:
                if self.vtracefile != sys.stdout:
                    self.vtracefile.close()
        else:
            # same button pressed again, ignore it
            pass

    ########################################################################
    #
    # INSTRUCTION EXECUTION
    #
    ########################################################################

    def instruction_execute(self, trace_flag):
        """
        Executes a single instruction

        Will fetch, decode, and execute a G15 instruction

        :param trace_flag:      1=print machine state following instruction
        """
        if self.verbosity & VERBOSITY_CPU_TRACE:
            trace_flag = 1

        if self.verbosity & VERBOSITY_CPU_DETAILS:
            print('entering exec instr')
        #

        if not self.power_status:
            print("DC power has not been applied")
            print("Enter 'button on' to apply")
            return

        # get/fetch the instruction (retain origin of instruction + the 29bit instruction
        instruction = self.cpu_fetch.fetch()
        self.cpu_decode.decode(instruction)

        # display instruction
        # note: most emulators display results of insturctions
        # but since we are debugging the emulator, we display the instruction first
        if trace_flag:
            print(instruction['disassembly'])

        # determine the begining and ending times for this instruction
        time_start = instruction['time_start']
        time_end = instruction['time_end']

        if self.verbosity & (VERBOSITY_CPU_DEBUG | VERBOSITY_CPU_MICRO_TRACE):
            print('instruction=', instruction)
            print('word times: start=', time_start % 108, ' end=', time_end % 108)

        # perform the instruction
        #   specials in the emulator execute once at the end time slot (so the bus logs align with Verilog trace)
        if instruction['d'] == SPECIAL:     # track 31 destination
            word_time = time_end
            early_bus, intermediate_bus, late_bus = self.execute(instruction, word_time)
        else:
            effective_time_end = time_end;
            if time_end < time_start:
                effective_time_end += 108;

            for word_time in range(time_start, effective_time_end + 1):
                early_bus, intermediate_bus, late_bus = self.execute(instruction, word_time)

            self.execute_instruction_notd31_special(instruction, time_start, time_end)  # copy tape block origin

        # increment instruction count
        self.total_instruction_count += 1

        # noinspection PyUnboundLocalVariable
        self.cpu_log.logger(time_start, time_end, early_bus, intermediate_bus, late_bus)

        # if trace_flag:
        if self.verbosity & VERBOSITY_CPU_MICRO_TRACE:
            self.status_cpu()

        # time2next_instr = self.determine_next_instr_sim_time(instruction, time_start, time_end)
        time2next_instr = 1
        return time2next_instr

    def execute(self, instruction, word_time):
        if self.verbosity & VERBOSITY_CPU_DEBUG:
            print('==== word_time ====', word_time % 108)

        ###########################################
        #
        # basic timing
        #
        ############################################

        # single precession & not divide or even word times
        instruction['ts'] = (not instruction['dp']) and (not instruction['divide']) or \
                            ((word_time & 1) == 0)
        instruction['word_time'] = word_time

        ############################################
        #
        # G15 passes the data through three main buses:
        # early_bus -> intermediate_bus -> late_bus (-> store the data)
        #
        early_bus = self.cpu_eb.early_bus(instruction, word_time)
        intermediate_bus = self.cpu_ib.intermediate_bus(early_bus, instruction)
        late_bus = self.cpu_lb.late_bus(intermediate_bus, instruction)

        if self.verbosity & VERBOSITY_CPU_DEBUG:
            print('\nword time=', word_time)
            print("%15s:" % "early_bus", '  %08x' % early_bus, '%08x' % (early_bus >> 1))
            print("%15s:" % "intermediate_bus", '  %08x' % intermediate_bus, '  %08x' % (intermediate_bus >> 1))
            print("%15s:" % "late_bus", '  %08x' % late_bus, '  %08x' % (late_bus >> 1))

        # self.flop_is = 0
        self.cpu_store.store_late_bus(late_bus, instruction, word_time)

        if instruction['d'] == SPECIAL:
            self.cpu_d31.d31_special(instruction)

        return early_bus, intermediate_bus, late_bus

    @staticmethod
    def determine_next_instr_sim_time(instruction, time_start, time_end):
        """
        Time is measured in units of Drum Words

        time of next instruction is relative to current time (fetch time)

        """
        time2start = time_start - instruction['loc']

        time_exe = time_end - time_start
        if time_exe <= 0:
            time_exe += 108

        time2next_instr = instruction['next_cmd_word_time'] - time_end
        if time2next_instr <= 0:
            time2next_instr += 108

        next_instr_time = time2start + time_exe + time2next_instr
        delta_time = next_instr_time

        return delta_time

    def execute_instruction_notd31_special(self, instruction, time_start, time_end):
        """ check if destination!=31 and need special instruction """

        source = instruction['s']
        destination = instruction['d']
        exec_length = time_end - time_start + 1

        if instruction['n'] == time_start:
            if exec_length == 108 and source < 20 and destination < 20:
                # moving a complete line in memory
                # so copy drum origin track id
                self.g15.drum.track_origin[destination] = self.g15.drum.track_origin[source]

    #
    # take 29 bit word, return signed integer, and a string
    @staticmethod
    def word29decode(value29):
        """ Converts a 29bit value to int and str """
        value = value29 >> 1
        sign = value29 & 1

        if sign == 1:
            value = -value
            str_value = '-'
        else:
            str_value = ' '
        #
            str_value += '%08x' % value
        #
        return value, str_value

    #
    ##############################

    # print a log of instruction execution to compare against Verilog results
    #
    #############################
    #
    @staticmethod
    def word_time_rollover(num):
        if num >= 108:
            num = num - 108

        return num

    def status_cpu(self):
        acc = self.g15.drum.read(AR, 0)

        print('\nG15 CPU Status:')

        if self.power_status:
            status = 'ON'
        else:
            status = 'OFF'
        print('\tDc Power is: ' + status)

        print('IO status ', self.g15.iosys.status)

        print('\t   IO Ready: ', self.g15.iosys.get_status())
        print('\t         AR: ', int_to_str(acc))
        print('\t  acc_carry: ', self.acc_carry, ' OvrFlow: ', self.overflow)
        print('\t     DA1_GO: ', self.status_da1)

        cmd_line = self.instruction['next_cmd_line']
        cmd_track = cmd_line_map[cmd_line]
        print('\t    CmdLine: ', cmd_line, '(' + str(cmd_track) + ') N:',
                instr_dec_hex_convert(self.instruction['next_cmd_word_time']))

        #
        # display next instruction
        #
        next_instr_dict = copy.deepcopy(self.instruction)
        next_instr_dict['instr'] = self.g15.drum.read(cmd_track, self.instruction['next_cmd_word_time'])
        print('\t  Next Intr: ', next_instr_dict['disassembly'])

        #
        # $ of insturctions executed to date
        #
        print()
        print('\t        Number of instructions executed: ', self.total_instruction_count)
        print('\tNumber of unknown instructions executed: ', self.unknown_instruction_count)
        print()

        print('\tNumber of Bell Rings: ', self.bell_ring_count)

    def status(self):
        # gather machine status for display
        self.status_cpu()
