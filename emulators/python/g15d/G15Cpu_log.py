"""
Verilog Trace file generation
(used to compare results of various emulators)
"""

import sys

from G15Subr import *


# noinspection PyPep8Naming
class g15d_log:
    """ g15d cpu execution logger """
    def __init__(self, cpu, stdout_enable, filename):
        self.cpu = cpu
        self.g15 = cpu.g15
        self.fout = None
        self.fout_count = 0     # number of output lines
        self.stdout_enable = stdout_enable
        self.io_active_count = 0

        if filename is not None:
            try:
                self.fout = open(filename, "w")
                print('Verilog vtrace file opened: ', filename)
                cpu.vtrace_enabled = True
            except IOError:
                print('Error, Cannot open Verilog vtrace file: ', filename)
                sys.exit(1)

        self.header = "   ICNT:     TIME : TR  :   INSTR  :TRK.RC:DEF: T: N:C: S: D:BP:      EB:      IB:      "
        self.header += "LB:      AR:          MQ(24):          ID(25):          PN(26):FO:IP:IOSTATUS : DESCRIPTION"

        if stdout_enable:
            cpu.vtrace_enabled = True

    def close(self):
        if self.fout != sys.stdout:
            self.fout.close()

    def msg(self, message):
        print(message, file=self.fout)

    def msg2(self, message):
        print(message, file=self.fout, end="")

    def logger(self, time_start, time_end, early_bus, intermediate_bus, late_bus):
        # determine if we are idling waiting for IO complete
        instruction = self.cpu.instruction

        if self.g15.iosys.status == IO_STATUS_READY:
            status = 1
            self.io_active_count = 0

        elif instruction['s'] == 28 and instruction['d'] == 31:
            status = 0
            self.io_active_count += 1

        status_str = "%8s" % io_status_str[self.g15.iosys.status]

        instruction = self.cpu.instruction

        str1 = "%7d" % self.cpu.total_instruction_count
        str2 = instr_dec_hex_convert(instruction['loc'])
        str3 = instr_dec_hex_convert(self.cpu.word_time_rollover(time_start))

        time_ending = time_end
        str4 = instr_dec_hex_convert(self.cpu.word_time_rollover(time_ending))
        if instruction['cmd_acc']:
            str5 = "ACC"
        else:
            str5 = "%3d" % cmd_line_map[instruction['cmd_line']]

        instr = self.cpu.instruction['instr']
        if self.g15.signenable:
            str7 = signmag_to_str(instr, str_width=8)
        else:
            str7 = "%08x" % instr

        str22 = "%10s" % self.g15.drum.time_get_str()

        lstr1 = str1 + ":" + str22 + ":" + str3 + "-" + str4 + ": " + str7 + ' :' + str5 + ':' + str2 + ':'

        if instruction['deferred']:
            str8 = "  w"
        else:
            str8 = "  u"

        str9 = instr_dec_hex_convert(instruction['t'])
        str10 = instr_dec_hex_convert(instruction['n'])
        str11 = "%1d" % instruction['ch']
        str12 = instr_dec_hex_convert(instruction['s'])
        str13 = instr_dec_hex_convert(instruction['d'])
        # str14 = "%2d" % instruction['bp']
        if instruction['bp']:
            str14 = '-  '
        else:
            str14 = '   '

        lstr2 = str8 + "." + str9 + "." + str10 + "." + str11 + "." + str12 + "." + str13  + str14 + ":"

        ar = self.g15.drum.read(AR, 0, 0)
        reg_pn = (self.g15.drum.read(PN, 1, 0) << 29) | self.g15.drum.read(PN, 0, 0)
        reg_id = (self.g15.drum.read(ID, 1, 0) << 29) | self.g15.drum.read(ID, 0, 0)
        reg_mq = (self.g15.drum.read(MQ, 1, 0) << 29) | self.g15.drum.read(MQ, 0, 0)
        if self.g15.signenable:
            str13 = signmag_to_str(early_bus)
            str14 = signmag_to_str(intermediate_bus)
            str15 = signmag_to_str(late_bus)
            str16 = signmag_to_str(ar)
            str17 = signmag_to_str(reg_mq, str_width=16)
            str18 = signmag_to_str(reg_id, str_width=16)
            str19 = signmag_to_str(reg_pn, str_width=16)
        else:
            str13 = mag_to_str(early_bus, 9)
            str14 = mag_to_str(intermediate_bus, 9)
            str15 = mag_to_str(late_bus, 9)
            str16 = mag_to_str(ar, 9)
            str17 = mag_to_str(reg_mq, 17)
            str18 = mag_to_str(reg_id, 17)
            str19 = mag_to_str(reg_pn, 17)

        str20 = "%2s" % self.cpu.overflow
        str20a = "%2s" % self.cpu.flop_ip

        str21 = status_str

        if instruction['dspecial']:
            str23 = instruction['dspecial']
        else:
            str23 = instruction['sspecial']

        lstr3 = str13 + ":" + str14 + ":" + str15 + ":" + str16 + ":" + str17
        lstr3 = lstr3 + ":" + str18 + ":" + str19 + ":" + str20 + ":" + str20a + ':' + str21 + ' : ' + str23

        if self.stdout_enable:
            print(self.header)
            print(lstr1 + lstr2 + lstr3)

        if self.fout is not None:
            if (self.fout_count % 10) == 0:
                print(self.header, file=self.fout)
            print(lstr1 + lstr2 + lstr3, file=self.fout)
            self.fout.flush()

            self.fout_count += 1

