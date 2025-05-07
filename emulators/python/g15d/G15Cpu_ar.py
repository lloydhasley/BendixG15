"""
G15D Early Bus implementation
"""


from G15Subr import *
import G15Cpu
from printg15 import *


overflow = 0
B30 = 1 << 29


def complement (b):
    if b&1 == 0: return b
    sign = b&1
    b ^= 1
    b = (-b) & MASK29BIT
    return b | 1


def g15tosex (g15word):
    seennonzero = 0
    out = ""
    if g15word & 1: out = '-'
    if g15word & ~1 == 0: return out + '0'
    for i in range(25, 0, -4):
        digit = (g15word >> i) & 0x0F
        if digit == 0 and seennonzero==0: continue
        seennonzero = 1
        if digit <= 9: out += str (digit)
        else:          out += chr (digit - 10 + ord('u') )
    return out


def sextoint (str):
    n = 0
    neg = 0
    for char in str:
        if char == '-':
            neg = 1
            continue
        if '0' <= char <= '9':
            n = 16*n + int(char)
            continue;
        if 'u' <= char <= 'z':
            n = 16*n + ord(char) - ord('u') + 10
            continue
        if 'U' <= char <= 'Z':
            n = 16*n + ord(char) - ord('U') + 10
            continue
        print ("BAD INPUT CHAR: ", char);
    return ((n<<1) | neg);


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
        if False:
            # Robb's
            ar = self.g15.drum.read(AR, 0)
            armag = ar & self.MASK29MAG
            arsign = ar & 1
            lbmag = late_bus & self.MASK29MAG
            lbsign = late_bus & 1

            sum = armag + lbmag
            carry = 1 if (sum & B30) > 0 else 0
            uncorrectedsign = arsign ^ lbsign
            csign = uncorrectedsign ^ carry
            csum = (sum & MASK29BIT) | csign

            if late_bus == 1:
                csum ^= 1 # lb==-0 then change sign on sum

            if uncorrectedsign == 0:
                if carry == 1 and (lbsign == 0 or csum == 0): self.cpu.overflow = 1
                if carry == 0 and lbsign == 1 and lbmag: self.cpu.overflow = 1
#            print(g15tosex(ar), "+", g15tosex(late_bus), "=", g15tosex(csum), "-1->", g15tosex(complement(csum)))

        else:
            # Lloyd's
            ar = self.g15.drum.read(AR, 0)
            ar_sign = ar & 1
            ar_mag = ar & self.MASK29MAG

            late_bus_sign = late_bus & 1
            late_bus_mag = late_bus & self.MASK29MAG

            sum_mag = ar_mag + late_bus_mag
            endcarry = sum_mag >> 29
            sum_mag &= self.MASK29MAG      # remove any carry out

            ch = self.cpu.instruction['ch']
#            if ch == 1 or ch == 3:
#                endcarry = 1
            if self.cpu.te == self.cpu.word_time:
                pass
                # last word.   do not corrrect -0 to +0


            sum_sign = ar_sign ^ late_bus_sign ^ endcarry      # corrected sign
            result = sum_mag | sum_sign

            # if a_mag != 0 and b_mag != 0:
            if self.overflow_detect(ar_sign, late_bus_sign, late_bus_mag, sum_mag, endcarry):
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
