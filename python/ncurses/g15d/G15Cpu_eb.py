"""
G15D Early Bus implementation
"""


from G15Subr import *
import G15Cpu


# noinspection PyPep8Naming,PyPep8Naming
class g15d_eb:
    """ g15d early bus """
    def __init__(self, cpu):
        self.cpu = cpu
        self.g15 = cpu.g15

    def early_bus(self, instruction, word_time):
        """ Computes value on the G15 Early Bus

        :param instruction:     instruction to disassemble
        :param word_time:           current drum word time
        :return:                    early bus (29-bit
        """
        source_track = instruction['s']

        if instruction['divide']:
            early_bus = 0  # need make into PA&te equivalent
        elif source_track == 29:
            early_bus = 0
        elif source_track == 27 or source_track == 30 or source_track == 31:
            m20 = self.g15.drum.read(M20, word_time)
            # m20n = invert29(self.g15.drum.read(20, word_time))
            m20n = (~m20) & MASK29BIT
            m21 = self.g15.drum.read(M21, word_time)
            ar = self.g15.drum.read(AR, word_time)
            if source_track == 27:
                early_bus = (m20 & m21) | (m20n & ar)
            elif source_track == 30:
                early_bus = m20n & m21
            else:       # track 31
                early_bus = m20 & m21
        else:
            early_bus = self.g15.drum.read(source_track, word_time)

        if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_EARLY_BUS:
            print "\t       early_bus = ", instr_2_hex_string(early_bus)

        return early_bus
