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
            23: {0: 'PG Clear', 3: 'PN*M2->ID, PN*!M2->MQ',  'default':'error'},
            24: 'Multiply',
            25: 'divide (ch=1)',
            26: 'shift',
            27: 'Normalize (test non-zero)',
            28: {0: 'Test Ready', 1: 'Test Ready IN', 2: 'Test Ready OUT', 'default': 'Test DA1 Off'},
            29: 'Test Overflow',
            30: 'Mag. File Code',
            31: 'Next Comm.fm.AR'
        }

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

        instruction["sspecial"] = source_special
        instruction["dspecial"] = destination_special

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

            #        s_track_4_word = source >= 20 and  source <= 23
            #        s_track_2_word = source >= 24 and  source <= 26
            #        s_acc = source == 28
            #        d_track_long = destination <= 19
            #        d_track_4_word = destination >= 20 and destination <= 23
            #        d_track_2_word = destination >= 24 and destination <= 26
            #        sd_track_2_word = s_track_2_word or d_track_2_word
            #        sd_track_4_word = s_track_4_word or d_track_4_word
            #        s_track_long = source <= 19
            #        d_acc = destination == 28
            #        d_track_31 = destination == 31

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

        # D==31 normally converted to block
        if False:
            str_p = ' '
            if instruction['d'] == 31 and instruction['deferred'] == 1:
                str_p = 'w'
            elif ((instruction['loc'] + 1) == instruction['t']) and instruction['d'] != 31:
                str_p = 'w'
            # D==31 normally converted to block
            elif instruction['d'] != 31 and instruction['deferred'] == 0:
                str_p = 'u'

        if instruction['deferred'] == 1:
            str_p = 'w'
        else:
            str_p = 'u'

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

        #str_0 = str_tape_block + '  ' + str_drum_track + '  ' + str_l + ':'
        str_0 = str_drum_track + '.' + str_l + ':'
        #str_1 = str_instr + "  " + str_p + " " + str_t + " " + str_n + \
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

            # relative = 0
            # if instruction['d'] == 31 and 24 <= instruction['s'] <= 27:
            #    relative = 1

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
                time_end = instruction["n"] + instruction["t"]
                relative = 1
            elif instruction['s'] == 27 and instruction['d'] == 31:  # Normalize
                time_end = instruction["n"]  + instruction["t"]
                relative = 1
            else:
                time_end = instruction["t"] - 1  # stops one before T

#            if instruction['t'] >= 108:
#                time_end -= 20
#                if relative == 0:
#                    instruction['next_cmd_word_time'] -= 20

            if self.verbosity & 1:
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

        # no instructions are suppose to originate from Loc==107
        # but intercom does.  CN does not apply the timing correction of 20 (128-108).
        # so next T should be programmed 20 higher than normal.
        #   there may be other restrictions, but this one is stated pg 43 of the teory of operation
        # define MINUS_20_ADJ(a)         { a = (a<20) ? a+88 : a-20 ;}
        if instruction['loc'] == 107:
            # 1940 correction is only applied during WT == 107
            # so if mark instr is at 107, then result is 20 less than specified
            # --- if result < 0????  assume we add 108
            instruction['next_cmd_word_time'] = self.minus_20_adj(instruction['next_cmd_word_time'])
            if instruction['deferred']:
                time_start = self.minus_20_adj(time_start)
            time_end = self.minus_20_adj(time_end)

        if time_end < time_start:
            time_end += 108
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

