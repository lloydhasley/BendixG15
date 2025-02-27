"""
G15D Intermeidate Bus implementation
"""


from G15Subr import *
import G15Cpu


# noinspection PyPep8Naming
class g15d_ib:
    """ g15d Intermediate bus """
    def __init__(self, cpu):
        self.cpu = cpu
        self.g15 = cpu.g15
        self.old_early_bus = 0

    def intermediate_bus(self, early_bus, instruction):
        """ Emulates the G15D Intermediate Bus

        :param early_bus:           early bus contents
        :param instruction:         current instruction being executed
        :return:                    intermediate bus (29-bit
        """
        if self.cpu.total_instruction_count == 273:
            pass
        if instruction['s']==26 and instruction['d']==27:
            pass

        Ts = instruction['ts']

        sign_bit = early_bus & 1

        ip_block_d = (instruction['cmd_type'] & (CMD_TYPE_TR | CMD_TYPE_TVA)) and \
                     (instruction['d'] in two_word_tracks) and Ts
        ip_block_s = (instruction['cmd_type'] & (CMD_TYPE_TR | CMD_TYPE_TVA)) and \
                     (instruction['s'] in two_word_tracks) and Ts
        ip_pn_tr_pn_IP = Ts and self.cpu.flop_ip and ip_block_d and (instruction['s'] == PN) and (instruction['d'] == PN)

        if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_INTERMEDIATE_BUS:
            print 'cmd_type=', instruction['cmd_type']
            print 'ip_block_d=', ip_block_d
            print 'ip_block_s=', ip_block_s

        if Ts:

            if sign_bit and (instruction['cmd_type'] & (CMD_TYPE_AD | CMD_TYPE_AVA)):
                sp_insert_sign = 0
                self.cpu.flop_is = 1
            elif (sign_bit == 0) and (instruction['cmd_type'] & CMD_TYPE_SU):
                sp_insert_sign = 1
                self.cpu.flop_is = 1
            else:
                sp_insert_sign = 0
                self.cpu.flop_is = 0

            if ip_pn_tr_pn_IP:
                self.cpu_flop_is = 1



            #############################################################
            # double precession sign handling

            ip_sign_block = ip_block_d or ip_block_s

            if (instruction['s'] not in two_word_tracks) and ip_block_d:
                # capture current sign bit (perform modulo-2 sum)
                if (not self.cpu.flop_ip) and sign_bit:
                    self.cpu.flop_ip = 1
                elif self.cpu.flop_ip and (instruction['d'] != ID) and sign_bit:
                    self.cpu.flop_ip = 0
                elif self.cpu.flop_ip and (instruction['d'] == ID) and (not sign_bit):
                    self.cpu.flop_ip = 0

            # PG Clear
            if (instruction['s'] == 23) and (instruction['d'] == SPECIAL):
                self.cpu.flop_ip = 0

            ip_double_to_not_double = self.cpu.flop_ip and \
                                      (instruction['d'] not in two_word_tracks) and \
                                      (instruction['d'] != D_TEST)  and \
                                       ip_block_s

            ip_sign_insert = ip_pn_tr_pn_IP or ip_double_to_not_double

            ############################################################
            # sign bit blocking/insertion
            sp_block_sign = instruction['cmd_type'] & (CMD_TYPE_SU | CMD_TYPE_AV)

            if self.cpu.flop_is:
                intermediate_bus = ((~early_bus) + 2) & MASK29BIT
            else:
                intermediate_bus = early_bus
            intermediate_bus &= ~1      # remove sign

            new_sign_bit = sign_bit and (not ip_sign_block) and (not sp_block_sign)
            new_sign_bit = new_sign_bit or sp_insert_sign or ip_pn_tr_pn_IP or ip_sign_insert

            if new_sign_bit:
                intermediate_bus |= 1

            if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_INTERMEDIATE_BUS:
                print "\tintermediate_bus = ", signmag_to_str(intermediate_bus)

            self.old_early_bus = early_bus

        else:
            # have a double precission, odd word time
            early_bus_extended = (early_bus << 29) | self.old_early_bus
            early_bus_2s = (~early_bus_extended) + 1

            if self.cpu.flop_is:
                intermediate_bus = (early_bus_2s >> 29) & MASK29BIT
            else:
                intermediate_bus = early_bus

        return intermediate_bus
