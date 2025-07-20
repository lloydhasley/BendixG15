"""
Class G15Cpu emulates a G15 CPU

NOTE:  This is a ISA emulator working at the word/instruction level
    It is NOT a bit level emulator
"""

import sys
import copy
import time

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
import gl

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
    def __init__(self, g15, Verbosity=0x00, tracefile="", signenable=0):
        self.g15 = g15  # back pointer to g15 main class
        self.emul = g15.emul
        self.verbosity = Verbosity
#        self.verbosity = VERBOSITY_CPU_TRACE

        self.tracefile = tracefile
        self.signenable = signenable    # print numbers with sign+28 instead of 29 bits

        subr_init()
        
        # instantiate the CPU sub-blocks
        self.cpu_fetch = G15Cpu_fetch.g15d_fetch(self)
        self.cpu_decode = G15Cpu_decode.g15d_decode(self, self.verbosity)
        self.cpu_eb = G15Cpu_eb.g15d_eb(self)
        self.cpu_ib = G15Cpu_ib.g15d_ib(self)
        self.cpu_lb = G15Cpu_lb.g15d_lb(self)
        self.cpu_d31 = G15Cpu_d31.g15d_d31(self, self.verbosity)
        self.cpu_store = G15Cpu_store.g15d_store(self)
        self.trace_enabled = self.emul.traceenable

        self.cpu_ar = G15Cpu_ar.g15d_AR(self)
        self.cpu_pn = G15Cpu_pn.g15d_PN(self, self.verbosity)

        self.total_revolutions = 0

        ###############################################
        #
        # Bendix g15 is configured
        #
        # prepare CPU for execution
        #
        ################################################

        # initial switch based variables
        self.power_status = 0

        sw_mappings['enable']['handler'] = self.sw_enable_h
        sw_mappings['tape']['handler'] = self.sw_tape_h
        sw_mappings['compute']['handler'] = self.sw_compute_h
        sw_mappings['dc']['handler'] = self.button_dc_h
        
        sw_mappings['enable']['handler']('off')
        sw_mappings['tape']['handler']('off')
        sw_mappings['compute']['handler']('off')
        sw_mappings['dc']['handler']('off')
        
#        self.sw_enable = 0
#        self.sw_tape = 0
#        self.sw_compute = 0
#        self.sw_compute_bp_enable = 0

        self.cpu_init('off')
        self.bell_ring_count = 0

        # number of instructions executed since start of emulation
        self.total_instruction_count = 0

        # num of instructions that emulator did not implement
        self.unknown_instruction_count = 0

        # num of detected errors (other than unknown instr)
        self.errors = 0

        self.music_enable = False
                
        self.word_time = 0
        
    def cpu_init(self, power_status):
        """
        Initializes the internal variable used the G15 CPU emulator
        Is called by dc_button() when the DC Power On or Power Off buttons are depressed

        :param power_status: 1=Power On Button, 0=Power Off Button
        """

        # noinspection PyDictCreation
        instruction = {}
        instruction['instr'] = 0
        instruction['cmd_line'] = 6     # start execution at 23:0
        instruction['n'] = 0
        instruction['next_cmd_word_time'] = 0
        instruction['next_cmd_line'] = 6
        instruction['next_cmd_acc'] = 0
        instruction['cmd_acc'] = 0
        self.instruction = instruction

        self.mark_time = 0       # initialize saved mark
        self.sign = 0               # clear sign flag
        self.overflow = 0           # clear overflow flag
        self.acc_carry = 0
        self.status_da1 = 0
        self.flop_is = 0
        self.flop_ip = 0

        self.bell_count = 0  # number of times that bell has been rung
        self.power_status = power_status
        self.halt_status = 0
        
    def cpu_close(self):
            # do we have an open logfile?
            if self.cpu_log is not None:
                if self.cpu_log != sys.stdout:
                    self.cpu_log.close()  

    #####################################
    #
    # physical interfaces
    #
    #####################################
    def button_dc_h(self, value):
        
        if (value == 'on') and (self.power_status == 'off'):
            # apply power from a no power state
            gl.logprint("Applying power")
            # intiialize next instr address and cpu flags
            self.cpu_init(value)
    
            # begin system start up sequence
            #
            # first: check that we have a paper tape mounted
            if len(self.g15.ptr.tape_parsed) == 0:
                gl.logprint('User Error: no paper tape is mounted')
                return
    
            # second: rewind the tape
            self.g15.ptr.read_index = 0

            # third: Read a block of tape into line 19'
            self.g15.ptr.insure_NT()        # but first prepend NT if it is not already there
            self.block = self.g15.ptr.read_block()

            # fourth: verify that block read was number track
            if not self.g15.ptr.check_if_numbertrack(self.block):
                gl.logprint('Mounted paper tape does not have number first tape block')
                gl.logprint('Power is NOT applied, please mount a tape with NT')
                return
            else:
                gl.logprint('Number Track found')
                gl.logprint('Copying Number Track into Place')

            # fifth: copy line 19 to CN
            # copy M19 into CN (number track)
            for i in range(108):
                temp = self.g15.drum.read(M19, i)
                self.g15.drum.write(CN, i, temp)
            self.g15.drum.track_origin[CN] = self.g15.drum.track_origin[M19]    # emulator specific
    
            # sixth: read second block to L19
            self.block = self.g15.ptr.read_block()
        elif (value == 'off') and (self.power_status == 'on'):
            # off button pressed, while power is applied
            # turn things off
            self.cpu_init(value)
  
        else:
            # same button pressed again, ignore it
            pass  
        
    def sw_enable_h(self, value):
        self.sw_enable = value
        
    def sw_tape_h(self, value):
        self.sw_tape = value
        if value == "rewind":
            self.g15.ptr.read_index = 0     # rewind the tape
        elif value == "punch":
            pass
        else:           # center
            pass
                
    def sw_compute_h(self, value):
        self.halt_status = 0
        # gl.logprint("compute sw: instr=", self.instruction)
        self.sw_compute = value
        if value == "bp":
            self.sw_compute_bp_enable = True
            self.RUNSTATE = STATE_RUNNING
        elif value == 'go':
            self.sw_compute_bp_enable = False
            self.RUNSTATE = STATE_RUNNING
        else:       # center
            self.sw_compute_bp_enable = False
            self.RUNSTATE = STATE_IDLE

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

        if self.verbosity & VERBOSITY_CPU_DETAILS:
            gl.logprint('entering exec instr')

        if not self.power_status:
            gl.logprint("DC power has not been applied")
            gl.logprint("Enter 'button dc on' to apply")
            return -1

        # get/fetch the instruction (retain origin of instruction + the 29bit instruction
        instruction = self.cpu_fetch.fetch()
        self.cpu_decode.decode(instruction)

        # display instruction
        # note: most emulators display results of insturctions
        # but since we are debugging the emulator, we display the instruction first

        # determine the begining and ending times for this instruction
        time_start = instruction['time_start']
        time_end = instruction['time_end']

        self.g15.drum.revolution_check(time_end % 108)

        if self.verbosity & (VERBOSITY_CPU_DEBUG | VERBOSITY_CPU_MICRO_TRACE):
            gl.logprint('\t        Number of instructions executed: ', self.total_instruction_count)
            gl.logprint('instruction=', instruction)
            gl.logprint('word times: start=', time_start % 108, ' end=', time_end % 108)

        # perform the instruction
        #   specials in the emulator execute once at the end time slot (so the bus logs align with Verilog trace)
        if instruction['d'] == SPECIAL:     # track 31 destination
            self.word_time = time_end
            early_bus, intermediate_bus, late_bus = self.execute(instruction, self.word_time)
        else:
            # regular instructions cycle through the appropriate word times
            te = time_end
            if te < time_start:
                te += 108

            if self.verbosity & VERBOSITY_CPU_TRACE:
                gl.logprint("\tts=", time_start, " te=", te, '/', te % 108)

            self.te = te
            for self.word_time in range(time_start, te + 1):
                early_bus, intermediate_bus, late_bus = self.execute(instruction, self.word_time)

            # handle emulator oddities
            self.execute_instruction_notd31_special(instruction, time_start, time_end)  # copy tape block origin

        # add drum revolution pause if we are playing music
        if self.g15.drum.revolution_check(time_end % 108):
            try:
                if self.emul.music.music_enable:
                    time.sleep(TRACK_TIME / 1000000)
            except:
                pass

        # at end of drum rev, check slow_out (handles M19 print)
        rotate = False
        if instruction['time_end_last'] >= instruction['loc']:
            rotate = True
        if instruction['loc'] >= instruction['time_end']:
            rotate = True
        if rotate:
            self.g15.iosys.slow_out_doit()       

        # breakpoint
        if instruction['bp']:
            self.sw_compute_bp_enable = 0
            if self.verbosity & VERBOSITY_CPU_MICRO_TRACE:
                gl.logprint("Cpu has hit breakpoint")

        # noinspection PyUnboundLocalVariable
        if self.trace_enabled:
            self.emul.log.logger(time_start, time_end, early_bus, intermediate_bus, late_bus)

        # increment instruction count
        self.total_instruction_count += 1

        time2next_instr = 1
        return time2next_instr

    def execute(self, instruction, word_time):
        if self.verbosity & VERBOSITY_CPU_DEBUG:
            gl.logprint('==== word_time ====', word_time % 108)

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
            gl.logprint('\nword time=', word_time)
            gl.logprint("%15s:" % "early_bus", '  %08x' % early_bus, '%08x' % (early_bus >> 1))
            gl.logprint("%15s:" % "intermediate_bus", '  %08x' % intermediate_bus, '  %08x' % (intermediate_bus >> 1))
            gl.logprint("%15s:" % "late_bus", '  %08x' % late_bus, '  %08x' % (late_bus >> 1))

        self.cpu_store.store_late_bus(late_bus, early_bus, instruction, word_time)

        if self.verbosity & VERBOSITY_CPU_TRACE:
            gl.logprint("%6d" % self.total_instruction_count, "\t\t\t\twrite",
                  str(instruction['d']) + '.' + str(instruction['word_time'] % 108) + ': %8s' % signmag_to_str(late_bus))

        if instruction['d'] == SPECIAL:
            self.cpu_d31.d31_special(instruction)

        return early_bus, intermediate_bus, late_bus

    def execute_instruction_notd31_special(self, instruction, time_start, time_end):
        """ check if destination!=31 and need special instruction """

        source = instruction['s']
        destination = instruction['d']

        exec_length = (time_end + 109 - time_start)
        if exec_length > 108:
            exec_length -= 108

        # tag drum line if we moved an entire track to another
        if instruction['n'] == time_start:
            if exec_length >= 108 and source < 20 and destination < 20:
                # moving a complete line in memory
                # so copy drum origin track id
                self.g15.drum.track_origin[destination] = self.g15.drum.track_origin[source]
                gl.logprint("Copying line: ", source, " to line: ", destination)

        # check if music is playing and copying a new note into a track
        try:
            if self.emul.music.music_enable and exec_length == 108:
                self.g15.emul.music.trackcopy(instruction)
        except:
            pass

    def Status(self):
        acc = self.g15.drum.read(AR, 0)

        gl.logprint('\nG15 CPU Status:')

        if self.power_status:
            status = 'ON'
        else:
            status = 'OFF'
            
        gl.logprint('\tDc Power is: ' + status)
        gl.logprint('\t  IO status: ', io_status_str[self.g15.iosys.status])
#        gl.logprint('\t   IO Ready: ', self.g15.iosys.get_status())
        gl.logprint('\t         AR: ', int_to_str(acc))
        gl.logprint('\t  acc_carry: ', self.acc_carry, ' OvrFlow: ', self.overflow)
        gl.logprint('\t     DA1_GO: ', self.status_da1)
        gl.logprint('\t       HALT: ', self.halt_status)
        
        cmd_line = self.instruction['next_cmd_line']
        cmd_track = cmd_line_map[cmd_line]
        gl.logprint('\t    CmdLine: ', cmd_line, '(' + str(cmd_track) + ') N:',
              instr_dec_hex_convert(self.instruction['next_cmd_word_time']))

        #
        # $ of insturctions executed to date
        #
        gl.logprint()
        gl.logprint('\t          Number of instructions executed: ', self.total_instruction_count)
        gl.logprint('\t  Number of unknown instructions executed: ', self.unknown_instruction_count)
        gl.logprint('\t               Number of drum revolutions: ', self.total_revolutions)
        gl.logprint('\tEstimated execution time on real G15 (ms): ', (self.total_revolutions * TRACK_TIME)/1000.0 )
        gl.logprint()
        gl.logprint('\t                     Number of Bell Rings: ', self.bell_ring_count)

