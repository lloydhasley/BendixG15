"""
G15D instruction decoder and disassembler

explodes G15 29-bit instruction into python dict describing instruction fields
creates a 'human-readable' disassembly string of the instruction

"""

from G15Subr import *
import G15Cpu
import gl


# noinspection PyPep8Naming,PyPep8Naming
class g15d_decode:
    """ g15d instruction decoder and disassembler """
    def __init__(self, cpu, verbosity):
        self.verbosity = verbosity
        self.cpu = cpu
        self.g15 = cpu.g15
        self.msg = self.g15.emul.log.msg

        self.source_special_dict = {24: 'MQ', 25: 'ID', 26: 'PN', 27: '20*21 + 20z*AR',
                                    28: 'AR', 29: '20*IR', 30: '20z*21', 31: '20*21'}
        self.destination_special_track_dict = {24: 'MQ', 25: 'ID', 26: 'PNc', 27: 'Test', 28: 'ARc', 29: 'AR+',
                                               30: 'PN+'}
        self.destination_special_dict = {
            0: 'Set Ready',
            1: 'Mag Write',
            2: 'Fast Punch Ldr',
            3: 'Fast Punch L19',
            4: 'Mag Search Rev',
            5: 'Mag Search Fwd',
            6: 'Ph Tape Rev. 01',
            7: 'Ph Tape Rev. 02',
            8: 'Type AR',
            9: 'Type M19',
            10: 'Punch 19',
            11: 'Punch Car 19',
            12: 'Type In',
            13: 'Mag Read',
            14: 'Card Read',
            15: 'Ph Tape Read',
            16: 'Halt',
            17: {1: 'Ring Bell, Man Punch Test', 2: 'Ring Bell, Start Input Register',
                 3: 'Ring Bell, Stop Input Register',
                 'default': 'Ring Bell'},
            18: '20*ID to OR',
            19: {1: 'Stop DA-1', 'default': 'Start DA-1'},
            20: 'Return',
            21: 'Mark',
            22: 'Test T1*AR',
            23: {0: 'PG Clear', 3: 'PN*M2->ID, PN*!M2->PN',  'default': 'error'},
            24: 'Multiply',
            25: 'divide (ch=1)',
            26: 'shift',
            27: 'Normalize (test non-zero)',
            28: {0: 'Test Ready', 1: 'Test Ready IN', 2: 'Test Ready OUT', 'default': 'Test DA1 Off'},
            29: 'Test Overflow',
            30: 'Mag. File Code',
            31: 'Next Comm.fm.AR'
        }

        self.MDSN = [24, 25, 26, 27]       # multiply,divide,shift,normalize

    #######################################
    #
    # decode the 29-bit instruction
    #
    def decode(self, instruction):
        """
        Split an instruction into its fields
        Determine the start and end times for the instruction
        """
        
        self.split(instruction)
        self.determine_start_end_times(instruction)

        return instruction

    def split(self, instruction):
        """
        Decode the 29-bit instruction

        Fills in the instruction dict with all the particulars from instruction previously fetched
        """

        instruction_word = instruction['instr']

        instruction['count'] = self.cpu.total_instruction_count

        # get the base fields
        sign = bits_extract(instruction_word, 1, 0)
        instruction['sign'] = sign
        instruction['dp'] = sign

        destination = bits_extract(instruction_word, 5, 1)
        instruction['d'] = destination
        source = bits_extract(instruction_word, 5, 6)
        instruction['s'] = source

        instruction['ch'] = bits_extract(instruction_word, 2, 11) + (sign << 2)

        instruction['n'] = bits_extract(instruction_word, 7, 13)  # current instruction (for trace prints)

        instruction['bp'] = bits_extract(instruction_word, 1, 20)
        instruction['t'] = bits_extract(instruction_word, 7, 21)
        instruction['deferred'] = bits_extract(instruction_word, 1, 28)

        # unusual source tracks
        if source in self.source_special_dict:
            source_special = self.source_special_dict[source]
        else:
            source_special = ''
        #
        # determine if special instruction and decode it
        #
        destination_special = ''
        if destination == 31:
            if source in self.destination_special_dict:
                destination_special = self.destination_special_dict[source]
                if isinstance(destination_special, dict):
                    if instruction['ch'] in destination_special:
                        destination_special = destination_special[instruction['ch']]
                    else:
                        destination_special = destination_special['default']
        elif destination in self.destination_special_track_dict:
            destination_special = self.destination_special_track_dict[destination]

        instruction["sspecial"] = source_special        # label not num
        instruction["dspecial"] = destination_special   # label not num

        # if cmd is from WT=107, then N & T are 20 too high
        # but if Multiply/divide/shift/normalize then N (not T) is 20 too high.
        instruction['Ndisplay'] = instruction['n']  # in the trace we display
        instruction['Tdisplay'] = instruction['t']  # N & T unaltered.
        if instruction['loc'] == 107:
            instruction['n'] -= 20
            if not (instruction["d"] == 31 and instruction['s'] in self.MDSN):
                instruction['t'] -= 20
        
        # configure defaults for the next fetch (instructions may change during actual execution
        instruction['next_cmd_acc'] = 0
        instruction['next_cmd_word_time'] = instruction['n']

        ######################################################
        #
        # helper decodes
        #

        # odd = (instruction['t'] % 2) == 1
        instruction['divide'] = source == 25 and destination == 31
        
        instruction['ts'] = (not instruction['dp']) and (not instruction['divide']) or \
            (instruction['word_time'] & 1) == 0

        ch_low = instruction['ch'] & 0x3
        if ch_low == 0:
            instruction['cmd_type'] = CMD_TYPE_TR
        elif ch_low == 1:
            instruction['cmd_type'] = CMD_TYPE_AD
        elif ch_low == 2:
            if source < 28 and destination < 28:
                instruction['cmd_type'] = CMD_TYPE_TVA
            else:
                instruction['cmd_type'] = CMD_TYPE_AV
        else:
            if source < 28 and destination < 28:
                instruction['cmd_type'] = CMD_TYPE_AVA
            else:
                instruction['cmd_type'] = CMD_TYPE_SU

        return instruction

    def determine_start_end_times(self, instruction):
        if instruction["deferred"] == 0:
            # immediate instruction
            time_start = instruction['loc'] + 1
            relative = 0

            if instruction['s'] == 21 and instruction['d'] == 31:  # Mark
                time_end = time_start

            # need to adjust the following.  see drawing 19 once testing shift/mult/div/norm instructions
            elif instruction['s'] == 24 and instruction['d'] == 31:  # Multiply
                time_end = (instruction["loc"] + instruction["t"]) % 108
            elif instruction['s'] == 25 and instruction['d'] == 31:  # Divide
                time_end = (instruction["loc"] + instruction["t"]) % 108
            elif instruction['s'] == 26 and instruction['d'] == 31:  # Shift
                time_end = (instruction["loc"] + instruction["t"]) % 108
            elif instruction['s'] == 27 and instruction['d'] == 31:  # Normalize
                time_end = (instruction["loc"] + instruction["t"]) % 108
            else:
                # 'regular' instruction
                time_end = instruction["t"] - 1  # stops one before T

            if self.verbosity & G15Cpu.VERBOSITY_CPU_DETAILS:
                gl.logprint('\timmediate, start time=', time_start, ' end time=', time_end)
                
        else:
            # deferred instruction
            time_start = instruction["t"]
            if time_start < 0:
                time_start += 108

            # mark exit
            if instruction['s'] == 21 and instruction['d'] == 31:  # Mark
                time_end = time_start
            else:
                if instruction["sign"]:  # if double precision
                    if time_start & 1:
                        time_end = time_start + 0
                    else:
                        time_end = time_start + 1
                        # instruction['ch'] &= 3
                else:
                    time_end = time_start

            if self.verbosity & G15Cpu.VERBOSITY_CPU_DETAILS:
                gl.logprint('\tdeferred, start time=', time_start, ' end time=', time_end)

        time_start = (time_start + 108) % 108
        time_end = (time_end + 108) % 108

        if time_end < time_start:
            self.cpu.total_revolutions += 1

        instruction['time_start'] = time_start
        instruction['time_end'] = time_end

        return time_start, time_end
