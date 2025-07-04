"""
G15D instruction decoder and disassembler

explodes G15 29-bit instruction into python dict describing instruction fields
creates a 'human-readable' disassembly string of the instruction

"""

from G15Subr import *
import G15Cpu

# noinspection PyPep8Naming,PyPep8Naming
class g15d_decode:
    """ g15d instruction decoder and disassembler """
    def __init__(self, cpu, verbosity):
        self.verbosity = verbosity
        self.cpu = cpu
        self.g15 = cpu.g15
        self.msg = cpu.cpu_log.msg

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
            23: {0: 'PG Clear', 3: 'PN*M2->ID, PN*!M2->PN',  'default':'error'},
            24: 'Multiply',
            25: 'divide (ch=1)',
            26: 'shift',
            27: 'Normalize (test non-zero)',
            28: {0: 'Test Ready', 1: 'Test Ready IN', 2: 'Test Ready OUT', 'default': 'Test DA1 Off'},
            29: 'Test Overflow',
            30: 'Mag. File Code',
            31: 'Next Comm.fm.AR'
        }

        self.MDSN = [24,25,26,27]       # multiply,divide,shift,normalize

        # initialize disassembler
        self.dissambly_label = "TRK LOC    HEX    P  T  N C  S  D BP    COMMENTS"


    #######################################
    #
    # decode the 29-bit instruction
    #
    def decode(self, instruction):
        """
        Split an instruction into its fields
        Disassemble the instruction
        Determine the start and end times for the instruction
        """
#        if total_instruction_count == 2278:
#            print("oh boy")
        
        self.split(instruction)
        self.disassemble(instruction)
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
        instruction['Norig'] = instruction['n']  # in the trace we display
        instruction['Torig'] = instruction['t']  # N & T unaltered.
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

    def disassemble(self, instruction):
        """
        convert instruction to string

        :param instruction:     instruction to disassemble
        :return:                disassembly string
        """

        str_instr = instr_2_hex_string(instruction['instr'])

        if instruction['cmd_acc'] == 1:
            str_tape_block = '**'
            str_drum_track = '**'
        else:
            cmd_track = cmd_line_map[instruction['cmd_line']]
            str_drum_track = '%02d' % cmd_track
            tape_block = self.g15.drum.track_origin[cmd_track]
            if tape_block < 0:
                str_tape_block = '**'
            else:
                str_tape_block = '%02d' % tape_block

        str_l = instr_dec_hex_convert(instruction['loc'])

        if instruction['d'] == 31:
            str_p = ' '
        elif instruction['deferred'] == 1:
            str_p = 'w'
        else:       # immediate
            str_p = 'u'

#        str_t = instr_dec_hex_convert(instruction['Torig'])
#        str_n = instr_dec_hex_convert(instruction['Norig'])
        str_t = instr_dec_hex_convert(instruction['t'])
        str_n = instr_dec_hex_convert(instruction['n'])
        str_c = '%1x' % instruction['ch']
        str_s = '%02d' % instruction['s']
        str_d = '%02d' % instruction['d']

        if instruction['bp'] == 1:
            str_bp = ' -'
        else:
            str_bp = '  '

        destination_special = instruction['dspecial']  # destination special
        source_special = instruction['sspecial']  # source special

        str_0 = str_drum_track + '.' + str_l + ':'
        str_1 = str_p + "." + str_t + "." + str_n + \
                        "." + str_c + "." + str_s + "." + str_d + str_bp

        if destination_special != '':
            str_2 = destination_special
        elif source_special != '':
            str_2 = source_special
        else:
            str_2 = ''

        instruction['disassembly'] = str_0 + ' ' + str_1 + '  ' + str_2

        return

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
                relative = 1
            elif instruction['s'] == 25 and instruction['d'] == 31:  # Divide
                time_end = (instruction["loc"] + instruction["t"]) % 108
                relative = 1
            elif instruction['s'] == 26 and instruction['d'] == 31:  # Shift
                time_end = (instruction["loc"] + instruction["t"]) % 108
                relative = 1
            elif instruction['s'] == 27 and instruction['d'] == 31:  # Normalize
                time_end = (instruction["loc"] + instruction["t"]) % 108
                relative = 1
            else:
                # 'regular' instruction
                time_end = instruction["t"] - 1  # stops one before T

            if self.verbosity & G15Cpu.VERBOSITY_CPU_DETAILS:
                print('\timmediate, start time=', time_start, ' end time=', time_end)
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
                print('\tdeferred, start time=', time_start, ' end time=', time_end)

        time_start = (time_start + 108) % 108
        time_end = (time_end + 108) % 108

        if time_end < time_start:
            self.cpu.total_revolutions += 1

        instruction['time_start'] = time_start
        instruction['time_end'] = time_end

        return time_start, time_end

    def minus_20_adj(self, value):
        if value < 20:
            value += 88
        else:
            value -= 20

        return value

