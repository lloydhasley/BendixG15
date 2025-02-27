"""
G15D Early Bus implementation


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
            except IOError:
                print('Error, Cannot open execution log file: ', filename)
                self.fout = sys.stdout

        self.header = "   ICNT:   TIME   :TRK:RC:   TR   :   INSTR:DEF: T: N:C: S: D:BP:      EB:      IB:      "
#        self.header += "LB:      AR:              PN:              ID:              MQ:FO:IP:IOSTATUS:      TIME"
        self.header += "LB:      AR:              PN:              ID:              MQ:FO:IP:IOSTATUS"

    def close(self):
        if self.fout != sys.stdout:
            self.fout.close()

    def logger(self, time_start, time_end, early_bus, intermediate_bus, late_bus):
        # determine if we are idling waiting for IO complete
        if self.g15.iosys.status == IO_STATUS_READY:
            status = 1
            self.io_active_count = 0
        else:
            status = 0
            self.io_active_count += 1
            if self.io_active_count > 3:
                return
        status_str = "%8s" % io_status_str[self.g15.iosys.status]

        instruction = self.cpu.instruction

        str1 = "%7d" % self.cpu.total_instruction_count
        str2 = instr_dec_hex_convert(instruction['loc'])
#        str3 = ' ' + instr_dec_hex_convert(self.cpu.word_time_rollover(time_start)) + '  '
#        str4 = ' ' + instr_dec_hex_convert(self.cpu.word_time_rollover(time_end)) + '  '
        str3 = ' ' + instr_dec_hex_convert(self.cpu.word_time_rollover(time_start))
        str4 = ' ' + instr_dec_hex_convert(self.cpu.word_time_rollover(time_end))
        if instruction['cmd_acc']:
            str5 = "ACC"
        else:
            str5 = "%3d" % cmd_line_map[instruction['cmd_line']]
        #str6 = ' ' + instr_dec_hex_convert(instruction['loc']) + ' '

        instr = self.cpu.instruction['instr']
        if self.g15.signenable:
            str7 = signmag_to_str(instr, str_width=8)
        else:
            str7 = "%08x" % instr

        str22 = "%10s" % self.g15.drum.time_get_str()

        lstr1 = str1 + ":" + str22 + ":" + str5 + ":" + str2 + ":" + str3 + "-" + str4 + ":" + ":" + str7 + ':'

        if instruction['deferred']:
            str8 = "  u"
        else:
            str8 = "  w"
#        if instruction['deferred']:
#            str8 = "  D"
#        else:
#            str8 = "  I"

        str9 = instr_dec_hex_convert(instruction['t'])
        str10 = instr_dec_hex_convert(instruction['n'])
        str11 = "%1d" % instruction['ch']
        str12 = instr_dec_hex_convert(instruction['s'])
        str13 = instr_dec_hex_convert(instruction['d'])
        str14 = "%2d" % instruction['bp']

        lstr2 = str8 + ":" + str9 + ":" + str10 + ":" + str11 + ":" + str12 + ":" + str13 + ":" + str14 + ":"

        ar = self.g15.drum.read(AR, 0, 0)
        reg_pn = (self.g15.drum.read(PN, 1, 0) << 29) | self.g15.drum.read(PN, 0, 0)
        reg_id = (self.g15.drum.read(ID, 1, 0) << 29) | self.g15.drum.read(ID, 0, 0)
        reg_mq = (self.g15.drum.read(MQ, 1, 0) << 29) | self.g15.drum.read(MQ, 0, 0)
        if self.g15.signenable:
            str13 = signmag_to_str(early_bus)
            str14 = signmag_to_str(intermediate_bus)
            str15 = signmag_to_str(late_bus)
            str16 = signmag_to_str(ar)
            str17 = signmag_to_str(reg_pn, str_width=16)
            str18 = signmag_to_str(reg_id, str_width=16)
            str19 = signmag_to_str(reg_mq, str_width=16)
        else:
            str13 = mag_to_str(early_bus, 9)
            str14 = mag_to_str(intermediate_bus, 9)
            str15 = mag_to_str(late_bus, 9)
            str16 = mag_to_str(ar, 9)
            str17 = mag_to_str(reg_pn, 17)
            str18 = mag_to_str(reg_id, 17)
            str19 = mag_to_str(reg_mq, 17)

        str20 = "%2s" % self.cpu.overflow
        str20a = "%2s" % self.cpu.flop_ip

        str21 = status_str


        if instruction['dspecial']:
            str23 = instruction['dspecial']
        else:
            str23 = instruction['sspecial']

        lstr3 = str13 + ":" + str14 + ":" + str15 + ":" + str16 + ":" + str17
        lstr3 = lstr3 + ":" + str18 + ":" + str19 + ":" + str20 + ":" + str20a + ':' + str21 + ':' + str23

        if self.stdout_enable:
            print(self.header)
            print(lstr1 + lstr2 + lstr3)

        if self.fout is not None:
            if (self.fout_count % 10) == 0:
                print(self.header, file=self.fout)
            print(lstr1 + lstr2 + lstr3, file=self.fout)
            self.fout.flush()

            self.fout_count += 1
