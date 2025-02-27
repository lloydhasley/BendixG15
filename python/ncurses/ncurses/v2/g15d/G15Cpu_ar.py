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

    def add_new_broken(self, late_bus):
        ar = self.g15.drum.read(AR, 0)
        ar1 = self.rotate_sign(ar)
        late_bus1 = self.rotate_sign(late_bus)

        new_ar = ar1 + late_bus1
        if new_ar & (1 << 29):
            new_ar |= 1
        new_ar &= MASK29BIT

        carry = 0
        if self.overflow_detect(ar & 1, late_bus & 1, late_bus & (MASK29BIT - 1), new_ar & (MASK29BIT - 1), carry):
            self.cpu.overflow = 1

    def add(self, late_bus):

        if self.cpu.total_instruction_count == 542:
            pass

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

        if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_AR:
            wt = self.cpu.instruction['word_time'] % 108
            outstr = "wt=%3d: " % wt
            outstr += " lb=%08x" % late_bus
            outstr += " ar=%08x" % ar
            outstr += " ucs: " + str((late_bus & 1) ^ (ar & 1))
            outstr += ' co: ' + str(carry)
            outstr += " result = %08x" % result
            outstr += " cs: " + str(result % 2)
            print(outstr)

        # if result == 1 and ((late_bus >> 28) == 0):
        if result == 1:
            if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_AR:
                print('removing minus 0')
            result = 0  # -0 => + 0

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

    @staticmethod
    def adder_old_really(a_in, b_in, size):
        """ Adds two numbers with sign bit in LSB

        :param a_in:    1st number to add
        :param b_in:    2nd number to add
        :param size:    size in bits (usually 29 or 58)
        :return:        resultant sum
        """
        a_sign = a_in & 1
        b_sign = b_in & 1

        mask_carry = 1 << size
        mask_mag = mask_carry - 2

        a_mag = a_in & mask_mag
        b_mag = b_in & mask_mag
        ab_mag = a_mag + b_mag
        carry_out = ab_mag & mask_carry
        if carry_out:
            carry_out = 1
        else:
            carry_out = 0

        # print 'sum=%x'%sum, 'mask_num=%x'%mask_mag, 'carry_out=',carry_out

        ab_mag &= mask_mag      # remove any carry out

        sign_out = a_sign ^ b_sign ^ carry_out
        sign_out &= 1
        sign_mag = ab_mag | sign_out

        # alternate implementation
        aaa = signmag_to_int(a_in)
        bbb = signmag_to_int(b_in)
        print('aaa %x ' % aaa, '/', aaa)
        print('bbb %x ' % bbb, '/', bbb)
        ccc = int_plus_int(aaa, bbb)
        print('ccc %x ' % ccc, '/', ccc)
        ddd = int_to_signmag(ccc)
        print('ddd %x ' % ddd, '/', ddd)

        eee = signmag_plus_signmag(a_in, b_in)
        print('eee %x ' % eee, '/', eee)

        sm = int_to_signmag(signmag_to_int(a_in) + signmag_to_int(b_in))
        print('sm %x ' % sm, '/', sm)
        print('sign_mag %x ' % sign_mag, '/', sign_mag)

        if sm != sign_mag:
            print('sm and signmag did NOT agree')
            pass

        return sign_mag
