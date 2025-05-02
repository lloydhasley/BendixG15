"""
G15D Early Bus implementation
"""


from G15Subr import *
import G15Cpu


# noinspection PyPep8Naming,PyPep8Naming
class g15d_PN:
    """ g15d early bus """
    def __init__(self, cpu, verbosity):
        self.verbosity = verbosity
        self.cpu = cpu
        self.g15 = cpu.g15
        self.MASK58BIT = (1 << 58) - 1
        self.MASK58MAG = self.MASK58BIT - 1
        self.MASK29BIT = (1 << 29) - 1
        self.MASK29MAG = self.MASK29BIT - 1
        self.old_late_bus = 0
        self.old_pn = 0

    def write(self, late_bus, word_time):
        if (word_time % 2) == 0:
            self.old_pn = late_bus

        self.g15.drum.write(PN, word_time, late_bus)

    def add(self, late_bus, word_time):
        if self.cpu.instruction["time_end"] == self.cpu.instruction["time_start"]:
            late_bus_sign = late_bus & 1
            late_bus_mag = late_bus & self.MASK29MAG

            pn = self.g15.drum.read(PN, word_time)
            pn_sign = pn & 1
            pn_mag = pn & self.MASK29MAG

            sum_mag = late_bus_mag + pn_mag
            carry_out = (sum_mag >> 29) & 1
            sum_mag &= self.MASK29MAG
            sign_out = (late_bus_sign ^ pn_sign ^ carry_out) & 1
            pn_new = sum_mag | sign_out
            pn_low = pn_new & self.MASK29BIT
            self.g15.drum.write(PN, word_time, pn_low)

            # overflow detect?  on single word adds on PN
            return

        if (word_time % 2) == 0:
            # low ordered word
            self.old_pn = self.g15.drum.read(PN, word_time)
            self.old_late_bus = late_bus
        else:
            # high ordered word
            late_bus_extended = (late_bus << 29) | self.old_late_bus
            pn = (self.g15.drum.read(PN, word_time) << 29) | self.old_pn

            if self.verbosity & G15Cpu.VERBOSITY_CPU_PN:
                print('late bus =%015x' % late_bus_extended)
                print('      pn =%015x' % pn)

            late_bus_sign = late_bus_extended & 1
            late_bus_mag = late_bus_extended & self.MASK58MAG

            pn_sign = pn & 1
            pn_mag = pn & self.MASK58MAG

            sum_mag = late_bus_mag + pn_mag

            if self.verbosity & G15Cpu.VERBOSITY_CPU_PN:
                print('late_bus_mag=%08x' % late_bus_mag)
                print('      pn_mag=%08x' % pn_mag)
                print('     sum_mag=%08x' % sum_mag)

            carry_out = sum_mag >> 58
            sum_mag &= self.MASK58MAG      # remove any carry out

            sign_out = (late_bus_sign ^ pn_sign ^ carry_out) & 1

            if late_bus_mag == 0 and late_bus_sign:
                # -0
                sign_out ^= 1

            pn_new = sum_mag | sign_out

            if self.overflow_detect(late_bus_sign, pn_sign, late_bus_mag, sum_mag, carry_out):
                self.cpu.overflow = 1

            if pn_new == 1:  # mimic Verilog bug,  allows -0 to slip into PN
                pn_new = 0

            if self.verbosity & G15Cpu.VERBOSITY_CPU_D31:
                print('PN: pn=%015x' % pn, ' late_bus=%015x' % late_bus_extended, ' sum=%015x' % pn_new, " carry=", carry_out)

            pn_high = pn_new >> 29
            pn_low = pn_new & MASK29BIT

            self.g15.drum.write(PN, word_time, pn_high)
            self.g15.drum.write(PN, word_time + 1, pn_low)   # 2w track, drum needs positive word time index

    @staticmethod
    def overflow_detect(a_sign, b_sign, late_bus_mag, sum_mag, carry):
        if (a_sign == b_sign) and carry and (a_sign == 0 or sum_mag == 0):
            return 1
        if late_bus_mag and (a_sign == b_sign) and (not carry) and a_sign:
            return 1

        return 0

    def read(self):
        return self.g15.drum.read(PN, 0)
