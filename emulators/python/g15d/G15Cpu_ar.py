"""
G15D Early Bus implementation
"""


from G15Subr import *
import G15Cpu


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
        self.add1(late_bus)

    def add0(self, late_bus):
        B30 = 1 << 29
        MASK29 = B30 - 1

        ar = self.g15.drum.read(AR, 0)
        arsign = ar & 1
        lbsign = late_bus & 1
        lbmag = late_bus & ~1
        sum = (ar & ~1) + lbmag
        carry = (sum & B30) > 0
        sum = sum & MASK29

        ch = self.cpu.instruction['ch']
        s = self.cpu.instruction['s']
        d = self.cpu.instruction['d']

        neg0   = False
        print (">>>>>>", ch, "<<<<<<");
        if late_bus == 1:			# addend (2nd no.) is -0?
            neg0 |= ch == 1		                    # 'AD'
            neg0 |= ch==3 and s<28 and d<28         # 'AVA'
        else:
            neg0 |= ch==3 and (s>=28 or d>=28)      # 'SU'
        uncorrectedsign = arsign ^ lbsign
        csign  = uncorrectedsign ^ (carry | neg0);
        fullsum= sum | csign        # complete 29bit word

        #
        # check for overflow
        overflow = 0
        if uncorrectedsign == 0:
            if neg0 and sum < 2:
                overflow = 1	# neg0 -> endcarry=1
            if  carry      and (lbsign == 0 or  sum   == 0):
                overflow = 2
            if (not carry) and  lbsign == 1 and lbmag != 0 :
                overflow = 3
        if overflow:
            self.cpu.overflow = 1

        self.g15.drum.write(AR, 0, fullsum)
        return fullsum


    def add2(self, late_bus):
        global overflow
        B30 = 1 << 29
        MASK29 = B30 - 1

        ar = self.g15.drum.read(AR, 0)
        arsign = ar & 1
        lbsign = late_bus & 1
        lbmag = late_bus & ~1
        sum = (ar & ~1) + lbmag
        carry = (sum & B30) > 0
        sum = sum & MASK29
        neg0 = late_bus == 1  # negative 0: 00...0000.1
        uncorrectedsign = arsign ^ lbsign
        csign = uncorrectedsign ^ (carry | neg0)
        fullsum = sum | csign

        overflow = 0
        if uncorrectedsign == 0:
            if neg0 and sum < 2: overflow = 1  # neg0 -> endcarry=1
            if carry and (lbsign == 0 or sum == 0): overflow = 2
            if (not carry) and lbsign == 1 and lbmag != 0: overflow = 3
        # print(g15tosex(ar), " + ", g15tosex(late_bus), " => ", fullsum);

        self.cpu.overflow = 0
        if overflow:
            self.cpu.overflow = 1

        self.g15.drum.write(AR, 0, fullsum)

        return fullsum

    def add1(self, late_bus):
        ar = self.g15.drum.read(AR, 0)
        ar_sign = ar & 1
        ar_mag = ar & self.MASK29MAG

        late_bus_sign = late_bus & 1
        late_bus_mag = late_bus & self.MASK29MAG

        sum_mag = ar_mag + late_bus_mag
        carry = sum_mag >> 29
        sum_mag &= self.MASK29MAG      # remove any carry out

        sum_sign = ar_sign ^ late_bus_sign ^ carry      # corrected sign
        sum_sign &= 1
        result = sum_mag | sum_sign

        # if a_mag != 0 and b_mag != 0:
        if self.overflow_detect(ar_sign, late_bus_sign, late_bus_mag, sum_mag, carry):
            self.cpu.overflow = 1

        # if result == 1 and ((late_bus >> 28) == 0):
        if result == 1:
            if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_AR:
                print('removing minus 0')
            result = 0  # -0 => + 0

        if False:
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
