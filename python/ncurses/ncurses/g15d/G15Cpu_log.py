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

        if filename != '':
            try:
                self.fout = open(filename, "w")
                print('Trace file opened: ', filename)
            except IOError:
                print('Error, Cannot open execution log file: ', filename)
                self.fout = sys.stdout

        self.header = "   ICNT:RC:TSTRT:TSTOP:TRK:WTME:   INSTR:DEF: T: N:CH: S: D:BP:      EB:      IB:      "
        self.header += "LB:      AR:              PN:              ID:              MQ:FO:IP:IOSTATUS:     TIME"

        print(self.header, file=self.fout)

    def close(self):
        self.fout.close()

    def logger(self, time_start, time_end, early_bus, intermediate_bus, late_bus):

        instruction = self.cpu.instruction

        str1 = "%7d" % self.cpu.total_instruction_count
        str2 = wordtime_to_str(instruction['loc'])
        str3 = '   ' + wordtime_to_str(self.cpu.word_time_rollover(time_start))
        str4 = '   ' + wordtime_to_str(self.cpu.word_time_rollover(time_end))
        str5 = "%3d" % cmd_line_map[instruction['cmd_line']]
        str6 = '  ' + wordtime_to_str(instruction['loc'])
        str7 = instr_2_hex_string(instruction['instr'])
        lstr1 = str1 + ":" + str2 + ":" + str3 + ":" + str4 + ":" + str5 + ":" + str6 + ":" + str7 + ':'

        if instruction['deferred']:
            str8 = "  D"
        else:
            str8 = "  I"
        str9 = wordtime_to_str(instruction['t'])
        str10 = wordtime_to_str(instruction['n'])

        str11 = "%2d" % instruction['ch']
        str12 = "%2d" % instruction['s']
        str13 = "%2d" % instruction['d']
        str14 = "%2d" % instruction['bp']

        lstr2 = str8 + ":" + str9 + ":" + str10 + ":" + str11 + ":" + str12 + ":" + str13 + ":" + str14 + ":"

        str13 = signmag_to_str(early_bus)
        str14 = signmag_to_str(intermediate_bus)
        str15 = signmag_to_str(late_bus)
        str16 = signmag_to_str(self.g15.drum.read(AR, 0, 0))

        reg_pn = (self.g15.drum.read(PN, 1, 0) << 29) | self.g15.drum.read(PN, 0, 0)
        str17 = signmag_to_str(reg_pn, width=15)
        reg_id = (self.g15.drum.read(ID, 1, 0) << 29) | self.g15.drum.read(ID, 0, 0)
        str18 = "%015x" % reg_id
        str18 = signmag_to_str(reg_id, width=15)
        reg_mq = (self.g15.drum.read(MQ, 1, 0) << 29) | self.g15.drum.read(MQ, 0, 0)
        str19 = "%015x" % reg_mq
        str19 = signmag_to_str(reg_mq, width=15)

        str20 = "%2s" % self.cpu.overflow
        str20a = "%2s" % self.cpu.flop_ip

        if self.g15.iosys.status == IO_STATUS_READY:
            status = 1
        else:
            status = 0
        str21 = "%8s" % status
        str22 = "%10d" % self.g15.sim.sim_time

        lstr3 = str13 + ":" + str14 + ":" + str15 + ":" + str16 + ":" + str17
        lstr3 = lstr3 + ":" + str18 + ":" + str19 + ":" + str20 + ":" + str20a + ':' + str21 + ':' + str22

        if self.stdout_enable:
            print(self.header)
            print(lstr1 + lstr2 + lstr3)

        if self.fout is not None:
            if (self.fout_count % 10) == 0:
                print(self.header, file=self.fout)
            print(lstr1 + lstr2 + lstr3, file=self.fout)
            self.fout.flush()

            self.fout_count += 1
