"""
special destination (D=31)
"""


from G15Subr import *
import G15Cpu_math

VERBOSITY_MATH_MULTIPLY = 1
VERBOSITY_MATH_DIVIDE = 2
VERBOSITY_D31_MARKRET = 4
VERBOSITY_D31 = 8


# noinspection PyPep8Naming
class g15d_d31(G15Cpu_math.g15d_math):
    """ g15d special destination (d=31) """

    SPRINT_NOT_DONE = 0  # last print from a special D=31 command
    SPRINT_DONE = 1  # not last print from a D=31 commnad

    def __init__(self, cpu, verbosity):
        G15Cpu_math.g15d_math.__init__(self, cpu, verbosity)
        self.cpu = cpu
        self.g15 = cpu.g15
        self.verbosity = verbosity

        # self.verbosity |= VERBOSITY_MATH_DIVIDE

    def d31_special(self, instruction):
        """ Explicit decode of instructions given the coding manual

            Some of these might be better covered by the basic move
            (after complete CH decode is complete
        """
        if instruction['d'] != SPECIAL:
            print('INTERNAL ERROR:  D31 handler called, but D31 is invalid')
            return

        loc = instruction['loc']

        if instruction['s'] == 0:
            # self.unverified_instruction()

            status = self.g15.iosys.get_status()
            if status & 3:
                self.g15.drum.precess(M19, WORD_SIZE)
                self.g15.drum.precess(M19, WORD_SIZE)
                self.g15.drum.precess(M19, WORD_SIZE)
                self.g15.drum.precess(M19, WORD_SIZE)
            self.g15.iosys.set_status(IO_STATUS_READY)

            return
        elif instruction['s'] == 1:
            self.unverified_instruction()
            return
        elif instruction['s'] == 2:
            self.unverified_instruction()
            return
        elif instruction['s'] == 3:
            self.unverified_instruction()
            return
        elif instruction['s'] == 4:
            self.unverified_instruction()
            return
        elif instruction['s'] == 5:
            self.unverified_instruction()
            return
        elif instruction['s'] == 6:
            #
            # reverse paper tape
            #
            #
            self.d31_special_print('reverse paper tape reader by one block', g15d_d31.SPRINT_DONE)
            self.cpu.block = self.g15.ptr.reverse(1)
            return

        elif instruction['s'] == 7:
            # in theory this instruction is not needed in an emulator as it should
            # always follow a 6:31 instruction
            self.unverified_instruction()
            return
            
        elif instruction['s'] == 8:
            if instruction['ch'] == 4 and (loc + 5) == instruction['t']:
                #
                # print AR in alphanumeric mode
                #
                # clears AR
                #
                self.unverified_instruction()

                ar = self.g15.drum.read(AR, 0)
                self.d31_special_print('print AR in alphanumeric mode - need to implement', g15d_d31.SPRINT_NOT_DONE)
                self.d31_special_print('   ar = %09x' % ar, g15d_d31.SPRINT_DONE)

                self.g15.drum.write(AR, 0, 0)

                return

            elif instruction['ch'] == 0:
                # print AR in numeric mode
                # using format in line 3 (see appendix)
                #
                # clears AR (if standard format is used)
                #
                ar = self.g15.drum.read(AR, 0)
                self.d31_special_print("TypeAR, numeric mode", g15d_d31.SPRINT_DONE)
                self.g15.iosys.slow_out(DEV_IO_TYPE, AR)
                return

        elif instruction['s'] == 9:
            if loc + 2 >= 108:
                loctest = loc + 2 - 108 + 20
            else:
                loctest = loc + 2
                
            if instruction['ch'] == 4 and instruction['s'] == 9 and (loc + 5) == instruction['t']:
                #
                # print line 19 in alphanumeric mode
                #
                # prints until l19 is 0 or until 8-bit code group where 7:4]==0
                #
                self.unverified_instruction()
                print()
                self.d31_special_print('print line 19 in alphanumeric mode - need to add', g15d_d31.SPRINT_DONE)

                self.g15.iosys.slow_out(DEV_IO_TYPE, 19)
                return

            elif instruction['ch'] == 0 and (loctest == instruction['t']):
                #
                # print line 19 in numeric mode
                # using format in line 3 (see appendix)
                #
                # clears 19 (if standard format is used)
                #
                self.d31_special_print("Type19, numeric mode", g15d_d31.SPRINT_DONE)
                print("total_instruction_count", self.cpu.total_instruction_count)

                self.g15.iosys.slow_out(DEV_IO_TYPE, 19)
                return

        elif instruction['s'] == 10:
            if instruction['ch'] == 0 and (loc + 2) == instruction['t']:
                #
                # punch line 19 to tape
                # using format in line 02
                #
                self.unverified_instruction()

                self.d31_special_print('punch line 19 to paper tape, need to implement', g15d_d31.SPRINT_DONE)
                return

        elif instruction['s'] == 11:
            pass

        elif instruction['s'] == 12:
            if instruction['ch'] == 4 and (loc + 5) == instruction['t']:
                #
                # permit alpha type-in
                #
                self.unverified_instruction()

                self.d31_special_print('activate alphanumeric type-in', g15d_d31.SPRINT_DONE)
                return

            elif instruction['ch'] == 0 and (loc + 2) == instruction['t']:
                #
                # permit numeric type-in
                #
                self.d31_special_print('activate numeric type-in', g15d_d31.SPRINT_DONE)

                self.g15.iosys.set_status(IO_STATUS_IN_TYPEWRITER)
                return

        elif instruction['s'] == 13:
            if (loc + 2) == instruction['t']:
                #
                # mag tape read
                #
                self.unverified_instruction()

                tape_unit = instruction['ch']

                self.d31_special_print('read mag tape, from unit: ' + str(tape_unit), g15d_d31.SPRINT_DONE)
                return

        elif instruction['s'] == 14:
            pass
            
        elif instruction['s'] == 15:
            if True:
                #
                # read paper tape
                #
                self.d31_special_print('read punched tape', g15d_d31.SPRINT_DONE)
                self.cpu.block = self.g15.ptr.read_block()
                return

        elif instruction['s'] == 16:
            #
            # halt
            #
            self.cpu.halt_status = 1
            return

        elif instruction['s'] == 17:
            ch = instruction['ch']
            if ch == 0:
                pass
            elif ch == 1:
                self.d31_special_print('Check Typwriter Punch Switch', g15d_d31.SPRINT_DONE)
                if self.cpu.sw_tape == 'punch':
                    instruction['next_cmd_word_time'] += 1
            elif ch == 2:
                self.d31_special_print('Start Input Register, if attached', g15d_d31.SPRINT_DONE)
            elif ch == 3:
                self.d31_special_print('Stop Input Register, if attached', g15d_d31.SPRINT_DONE)

            #
            # RING BELL
            #
            self.cpu.bell_ring_count += 1
            self.d31_special_print('ring bell', g15d_d31.SPRINT_DONE)
            print(chr(7), end="")
            return

        elif instruction['s'] == 18:
            self.unverified_instruction()
            return

        elif instruction['s'] == 19:
            if instruction['ch'] == 0:
                #
                # start DA-1
                #
                self.unverified_instruction()

                self.d31_special_print('Start DA-1', g15d_d31.SPRINT_DONE)
                self.cpu.status_da1 = 1
                return

            elif instruction['ch'] == 1:
                #
                # stop DA-1
                #
                self.d31_special_print('Stop DA-1', g15d_d31.SPRINT_DONE)
                self.cpu.status_da1 = 0
                return

        elif instruction['s'] == 20:
            #
            # select command line and return
            #
            self.ReturnFromMark(instruction)
            return

        elif instruction['s'] == 21:
            #
            # select command line and mark
            #
            self.GoToMark(instruction)
            return

        elif instruction['s'] == 22:
            #
            # test if sign of AR negative
            #
            # sign bit is in bit 0
            signbit = self.g15.drum.read(AR, 0) & 1
            if signbit == 1:
                instruction['next_cmd_word_time'] += 1

            return

        elif instruction['s'] == 23:
            ch2bit = instruction['ch'] & 0x3
            if ch2bit == 0:
                #
                # clear MQ,ID,PN
                #
                if instruction['time_start'] != instruction['time_end']:
                    self.g15.drum.write_two_word(MQ, 0, 0)
                    self.g15.drum.write_two_word(ID, 0, 0)
                    self.g15.drum.write_two_word(PN, 0, 0)
                else:
                    wt = instruction['word_time']
                    odd = wt % 2
                    self.g15.drum.write(MQ, odd, 0)
                    self.g15.drum.write(ID, odd, 0)
                    self.g15.drum.write(PN, odd, 0)

                self.cpu.flop_ip = 0
                return

            elif ch2bit == 3:
                #
                # extract and copy into reg_id the bits from PN that corespond to "one" bits of
                # word T in line 02
                #
                et = instruction['time_end']
                if et < instruction['time_start']:
                    et += 108

                for wt in range(instruction['time_start'], instruction['time_end'] + 1):
                    pn = self.g15.drum.read(PN, wt)
                    m2 = self.g15.drum.read(M2, wt)

                    id = pn & m2
                    pn &= ~m2
                    
                    self.g15.drum.write(PN, wt, pn & MASK29BIT)
                    self.g15.drum.write(ID, wt, id & MASK29BIT)

                return

        elif instruction['s'] == 24:
            #
            # multiply
            #
            self.multiply(self.verbosity & VERBOSITY_MATH_MULTIPLY)
            return

        elif instruction['s'] == 25:
            #
            # divide
            #
            self.divide(self.verbosity & VERBOSITY_MATH_DIVIDE)
            return

        elif instruction['s'] == 26:
            #
            # shift MQ left and ID right under control of command
            #  (1/2 of T)
            #
            # rotate mq and id left until AR=0
            #  subject limit of T
            ch = instruction['ch'] & 3

            # get mq and id from drum
            reg_md = self.g15.drum.read_two_word(MQ, 0)
            reg_id = self.g15.drum.read_two_word(ID, 0)
            reg_ar = self.g15.drum.read(AR, 0)

            for j in range(instruction['t'] >> 1):
                if reg_ar & (1 << 29):
                    reg_ar = 0
                    break
                reg_md <<= 1
                reg_md &= MASK58BIT
                reg_ar += 2
                reg_id >>= 1

            self.g15.drum.write_two_word(MQ, 0, reg_md)
            self.g15.drum.write_two_word(ID, 0, reg_id)
            if ch == 0:
                self.g15.drum.write(AR, 0, reg_ar & MASK29BIT)
            return

        elif instruction['s'] == 27:
            #
            # normalize mq
            #
            # rotate mq left until MSB = 1
            #  subject limit of T
            ch = instruction['ch'] & 3
            
            reg_mq = self.g15.drum.read_two_word(MQ, 0)
            reg_ar = self.g15.drum.read(AR, 0)

            for j in range(0, instruction['t'], 2):
                if reg_mq & (1 << 57):
                    break
                reg_mq <<= 1
                reg_mq &= MASK58BIT
                reg_ar += 2     # 1 (sign bit is in 2**0)

            self.g15.drum.write_two_word(MQ, 0, reg_mq)
            if ch == 0:
                self.g15.drum.write(AR, 0, reg_ar)

            return

        elif instruction['s'] == 28:
            ch = instruction['ch'] & 0x3
            if ch == 0:
                if self.g15.iosys.get_status() == IO_STATUS_READY:
                    instruction['next_cmd_word_time'] += 1
            elif ch == 1 or ch == 2:
                print('test external IO register status -- ignored')
            elif ch == 3:
                if self.cpu.status_da1 == 0:
                    instruction['next_cmd_word_time'] += 1
            return

        elif instruction['s'] == 29:
            #if instruction['ch'] == 0 and (loc + 2) == instruction['t']:
            if instruction['ch'] == 0:
                #
                # test overflow
                #
                if self.cpu.overflow == 1:
                    instruction['next_cmd_word_time'] += 1
                self.cpu.overflow = 0
                return

        elif instruction['s'] == 30:
            self.unverified_instruction()
            return
            
        elif instruction['s'] == 31:
            # if instruction['ch'] == 0 and (loc + 2) == instruction['t'] and (loc + 1) == instruction['n']:
            if instruction['ch'] == 0:
                #
                # take next command from AR
                #
                instruction['next_cmd_acc'] = 1       # take next instruction from AR
                return
            elif instruction['ch'] == 1:
                #
                # logical OR  M18 <= NT
                #
                start = instruction['time_start']
                end = instruction['time_end']
                if end < start:
                    end += 108
                for time in range(start, end + 1):
                    data = self.g15.drum.read(M18, time)
                    data |= self.g15.drum.read(CN, time)
                    self.g15.drum.write(M18, time, data)
                return

        print('ERROR: UNKNOWN special command')
        self.unverified_instruction()
        return

    def ReturnFromMark(self, instruction):
        instruction['next_cmd_line'] = instruction['ch']

        start_search = instruction['time_end']
        start_search += 1
        if start_search > 107: start_search -= 108

        marked_word = self.cpu.mark_time

        # check each WT after TR for the marked_word
        next_cmd_time = instruction['n']  # default case
        end_search = instruction['n']  # one beyond end
        if end_search < start_search: end_search += 108
        for wt in range(start_search, end_search):  # start_search..N-1 inclusive
            if (wt % 108) == marked_word:
                if self.verbosity & VERBOSITY_D31_MARKRET:
                    print("FOUND MARK for ", wt, "/", marked_word)
                next_cmd_time = marked_word
                break

        instruction['next_cmd_word_time'] = next_cmd_time

        if self.verbosity & VERBOSITY_D31_MARKRET:
            print("\tRTMv0.33: xx-", instruction['time_end'], "  marked_word=", marked_word, " N=", instruction['n'],
                  " searching:", start_search, "-", end_search - 1, " next_cmd_word_time=",
                  instruction['next_cmd_word_time'])

    def GoToMark(self, instruction):
        instruction['next_cmd_line'] = instruction['ch']

        if instruction['deferred']:
            self.cpu.mark_time = instruction['t']
        else:
            self.cpu.mark_time = instruction['loc'] + 1

        cmdLineMapped = cmd_line_map_names[instruction['next_cmd_line']]

        if self.verbosity & VERBOSITY_D31_MARKRET:
            print("cmdLineMapped", cmdLineMapped)
            print("MARK set: ", cmdLineMapped + "." + str(self.cpu.mark_time))

    def unverified_instruction(self):
        """ Increment unverifiied instuction execution count """

        print('unverified instruction detected, instr = ', instr_2_hex_string(self.cpu.instruction['instr']))
        print('\t', self.cpu.instruction)

        self.cpu.unknown_instruction_count += 1

    def d31_special_print(self, txt, flag):
        """ Limit descriptive prints to once during an instruction time """

        if not self.cpu.instruction['d31_print_flag']:
            print(txt)

        if flag == g15d_d31.SPRINT_DONE:
            self.cpu.instruction['d31_print_flag'] = 1  # re=enable d31 prints
