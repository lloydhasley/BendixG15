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
