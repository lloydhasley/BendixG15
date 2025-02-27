"""
Provides the underlying math routines for the machine

Multiply
Divide

"""

from G15Subr import *
import G15Cpu


# noinspection PyPep8Naming,PyPep8Naming
class g15d_math:
    """ g15d multiply/divide equivalents """
    def __init__(self, cpu, verbosity):
        self.verbosity = verbosity
        self.cpu = cpu
        self.g15 = cpu.g15

    def multiply(self):
        self.multiply_new()

    def multiply_new(self):
        """ Peforms the multiply function """
        bit57 = 1 << 57
        mask58 = (1 << 58) - 1
        mask58_nosign = mask58 - 1

        wt = self.cpu.instruction['word_time']
        t = self.cpu.instruction['t']
        iterations = t >> 1

        reg_id = self.g15.drum.read_two_word(ID, 0)
        reg_mq = self.g15.drum.read_two_word(MQ, 0)
        reg_pn = self.g15.drum.read_two_word(PN, 0)

        for i in range(iterations):
            reg_id >>= 1
            reg_id &= mask58_nosign

            if reg_mq & bit57:
                reg_pn += reg_id
            reg_mq <<= 1
            reg_mq &= mask58

            if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
                # wt = self.cpu.instruction['word_time']
                print('cwt=', wt + (2 * i), 'pn=%015x' % reg_pn, ' id=%015x' % reg_id, ' mq=%015x' % reg_mq)

        # reg_pn >>= 1
        reg_pn &= mask58_nosign

        self.g15.drum.write_two_word(ID, 0, reg_id)
        self.g15.drum.write_two_word(MQ, 0, reg_mq)
        self.g15.drum.write_two_word(PN, 0, reg_pn)

    def divide(self):
        mask59 = (1 << 59) - 1
        mask59a = mask59 - 1

        instruction = self.cpu.instruction
        T = instruction['t']
        iterations = T >> 1

        pn = self.g15.drum.read_two_word(PN, 0)
        id = self.g15.drum.read_two_word(ID, 0)
        mq = self.g15.drum.read_two_word(MQ, 0)

        if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
            print('pn=%015x' % pn)
            print('id=%015x' % id)
            if id == 0:
                print('Note: Attempt to divide by zero\n')

        if id==0:
            idz = 1 << 58
        else:
            idz = ((~id) + 1) & mask59

        IS = 1      # start w subtraction
        for i in range(iterations):
            if IS:
                m = pn + idz
            else:
                m = pn + id

            IS = ((m >> 58) & 1) ^ 1
            mq = (mq << 1) | (IS << 1)
            pn = ((m & mask59a) << 1) & mask59

            if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
                print('i=', i)
                print('pn=%015x' % pn)
                print('mq=%015x' % mq)
                print()

        if T & 1:       # if odd, rotate mq, makes diapers pass
            mq <<= 1
        mq |= 2         # princeton roundoff (sec D-11ac)

        # divide by 0 in diaper, reveals sign clear if PN result is zero over bits of interest
        print(" 1<<i= %07x" % ((1 << iterations)-1) )
        print("pn>>1= %07x" % (pn >> 1) )
        print("  res= %07x" % (((1 << iterations) - 1) & (pn >> 1)) )

        if ((1 << iterations) - 1) & (pn >> 1):
            pn |= 1

#        pn |= 1     # ??? to match Verilog, ttr12_1, instructiont #653, sign bit is affixed.

        if (T & 1):
            if mq & (1 << 29):
                self.cpu.overflow = 1
        else:
            if mq & (1 << 58):
                self.cpu.overflow = 1

        if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
            print('pn=%015x' % pn)
            print('id=%015x' % id)
            print('mq=%015x' % mq)
            print()

        self.g15.drum.write_two_word(PN, 0, pn)
        self.g15.drum.write_two_word(ID, 0, id)
        self.g15.drum.write_two_word(MQ, 0, mq)
