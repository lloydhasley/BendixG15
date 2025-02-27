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
        iterations = (t/2)

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
                print 'cwt=', wt + (2* i), 'pn=%015x' % reg_pn, ' id=%015x' % reg_id, ' mq=%015x' % reg_mq
        # reg_pn >>= 1
        reg_pn &= mask58_nosign

        self.g15.drum.write_two_word(ID, 0, reg_id)
        self.g15.drum.write_two_word(MQ, 0, reg_mq)
        self.g15.drum.write_two_word(PN, 0, reg_pn)

    def multiply_old(self):
        """ Peforms the multiply function """

        t = self.cpu.instruction['t']

        # TTR specials (exercises multiply to non-standard timings)
        shift_amt = 28 - ((56 - t)/2)

        reg_id = self.g15.drum.read_two_word(ID, 0)
        reg_mq = self.g15.drum.read_two_word(MQ, 0)
        # reg_id &= ~1
        # reg_md &= ~1

        #reg_pn = (reg_id >> 29) * (reg_mq >> 29)
        reg_pn = reg_id * reg_mq    # perform 58x58=116bit multiply
        reg_pn >>= 58               # note TTR2 > 29 fractional bits in ID

        reg_pn &= (1 << 58) - 1
        self.g15.drum.write_two_word(PN, 0, reg_pn)

        self.g15.drum.write_two_word(ID, 0, reg_id >> shift_amt)
        self.g15.drum.write_two_word(MQ, 0, 0)

    def multiply_old1(self):
        """ Peforms the multiply function """

        t = self.cpu.instruction['t']

        # TTR specials (exercises multiply to non-standard timings)
        shift_amt = 28 - ((56 - t)/2)

        reg_id = self.g15.drum.read_two_word(ID, 0)
        reg_mq = self.g15.drum.read_two_word(MQ, 0)
        # reg_id &= ~1
        # reg_md &= ~1
        reg_pn = (reg_id >> 29) * (reg_mq >> 29)
        reg_pn &= (1 << 58) - 1
        self.g15.drum.write_two_word(PN, 0, reg_pn)

        self.g15.drum.write_two_word(ID, 0, reg_id >> shift_amt)
        self.g15.drum.write_two_word(MQ, 0, 0)

    def divide_old(self):
        reg_pn = self.g15.drum.read_two_word(PN, 0)
        reg_id = self.g15.drum.read_two_word(ID, 0)

        reg_pn &= ~1
        reg_id &= ~1

        # determine quotient
        reg_id >>= 29
        reg_md = int(reg_pn / reg_id)

        remainder = reg_pn - (reg_id * reg_md)
        print 'remain=', remainder, '/x%x' % remainder

        reg_md <<= 29
        reg_md |= 2
        self.g15.drum.write_two_word(MQ, 0, reg_md)

    def divide(self):
        mask59 = (1 << 59) - 1
        mask59a = mask59 - 1

        instruction = self.cpu.instruction
        t = instruction['t']
        iterations = t / 2

        pn = self.g15.drum.read_two_word(PN, 0)
        id = self.g15.drum.read_two_word(ID, 0)
        mq = self.g15.drum.read_two_word(MQ, 0)

        if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
            print 'pn=%015x' % pn
            print 'id=%015x' % id

        idz = ((~id) + 1) & mask59
        # mq = 0

        IS = 1      # start w subtraction
        # for i in range(58):
        for i in range(iterations):
            if IS:
                m = pn + idz
            else:
                m = pn + id

            IS = ((m >> 58) & 1) ^ 1
            mq = (mq << 1) | (IS << 1)
            pn = ((m & mask59a) << 1) & mask59

            if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
                print 'i=', i
                print 'pn=%015x' % pn
                print 'mq=%015x' % mq
                print

        mq |= 2     # ??? to match Verilog  (should it be ~(IS << 1) ??)
        pn |= 1     # ??? to match Verilog, ttr12_1, instructiont #653, sign bit is affixed.

        if mq >= (1 << 58):
            self.cpu.overflow = 1

        if self.verbosity & G15Cpu.VERBOSITY_CPU_MATH:
            print 'pn=%015x' % pn
            print 'id=%015x' % id
            print 'mq=%015x' % mq
            print

        self.g15.drum.write_two_word(PN, 0, pn)
        self.g15.drum.write_two_word(ID, 0, id)
        self.g15.drum.write_two_word(MQ, 0, mq)
