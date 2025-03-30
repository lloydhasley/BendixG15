"""
G15D Early Bus implementation
"""


from G15Subr import *
import G15Cpu
from printg15 import *

# noinspection PyPep8Naming,PyPep8Naming
class g15d_AR:
    """ g15d early bus """
    def __init__(self, cpu):
        self.cpu = cpu
        self.g15 = cpu.g15
        self.MASK29MAG = MASK29BIT - 1

    def write(self, data):
        self.g15.drum.write(AR, 0, data)

    @staticmethod
    def rotate_sign(value):
        if value % 2:
            return (value - 1) + (1 << 29)
        else:
            return value

    def add(self, late_bus):
        if True:
            # Robb's
            ar = self.g15.drum.read(AR, 0)

            sum = (ar & ~1) + (late_bus & ~1)
            carry = 1 if (sum & (1<<30)) > 0 else 0
            arsign = ar & 1
            lbsign = late_bus & 1
            uncorrectedsign = arsign ^ lbsign
            csign = uncorrectedsign ^ carry
            csum = (sum & MASK29BIT) | csign
            if late_bus == 1: csum ^= 1
            if uncorrectedsign == 0:
                if carry == 1 and (lbsign == 0 or csum == 0): overflow = 1
                if carry == 0 and lbsign == 1:             overflow = 1


            if False:
                asign = a & 1
                amag = a & self.MASK29MAG
                b = late_bus
                bsign = late_bus & 1
                bmag = late_bus & self.MASK29MAG

                csum = amag + bmag
                if (csum & (1<<30)) != 0:
                    carry = 1
                else:
                    carry = 0
                uncorrectedsign = (asign + bsign) & 1
                csign = (uncorrectedsign + carry) & 1
                csum = (csum & MASK29BIT) | csign
                if b == 1:
                    csum ^= 1
                if uncorrectedsign == 0:
                    if carry==0 and bsign==1:
                        self.cpu.overflow = 1
                    if carry==1 and (bsign==0 or csum ==0):
                        self.cpu.overflow = 1

            icnt = self.cpu.total_instruction_count
            print("\t%d" % icnt, "late_bus=", signmag_to_str(late_bus),
                  " ar=", signmag_to_str(csum))
            self.g15.drum.write(AR, 0, csum)
        else:
            # Lloyd's
            ar = self.g15.drum.read(AR, 0)
            ar_sign = ar & 1
            ar_mag = ar & self.MASK29MAG

            late_bus_sign = late_bus & 1
            late_bus_mag = late_bus & self.MASK29MAG

            sum_mag = ar_mag + late_bus_mag
            carry = sum_mag >> 29
            sum_mag &= self.MASK29MAG      # remove any carry out

    #        instruction = self.cpu.instruction
    #        ch1_3 = instruction['ch'] == 1 or instruction['ch'] == 3

    #        if late_bus == 1 and ch1_3:
    #        if late_bus == 1:t

            if ar == 1:
                carry = 1   # compensate for -0

            sum_sign = ar_sign ^ late_bus_sign ^ carry      # corrected sign
            result = sum_mag | sum_sign

            # if a_mag != 0 and b_mag != 0:
            if self.overflow_detect(ar_sign, late_bus_sign, late_bus_mag, sum_mag, carry):
                self.cpu.overflow = 1

            # if result == 1 and ((late_bus >> 28) == 0):
            if False:
                if result == 1:
                    if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_AR:
                        print('removing minus 0')
                    result = 0  # -0 => + 0

            #if False:
            if late_bus == 1:
                print('AR data0=%x' % ar, ' data1=%x' % late_bus, ' sum=%x' % result)

            self.g15.drum.write(AR, 0, result)

    def read(self):
        return self.g15.drum.read(AR, 0)

    @staticmethod
    def overflow_detect(ar_sign, late_sign, late_bus_mag, sum_mag, carry):
        if (ar_sign == late_sign) and carry and (ar_sign == 0 or sum_mag == 0):
            return 1
        if late_bus_mag and (ar_sign == late_sign) and (not carry) and ar_sign:
            return 1

        return 0
