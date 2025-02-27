"""
G15D Late Bus implementation
"""


from G15Subr import *
import G15Cpu


# noinspection PyPep8Naming
class g15d_lb:
    """ g15d late bus """
    def __init__(self, cpu):
        self.cpu = cpu
        self.g15 = cpu.g15

    def late_bus(self, intermediate_bus, instruction):
        """ Emulate the G15D Late Bus

        :param instruction:    current instruction being executed
        :param intermediate_bus:    intermediate_bus value
        :return:                    late bus (29-bit
        """
        if instruction['cmd_type'] & (CMD_TYPE_TVA | CMD_TYPE_AVA):
            late_bus = self.cpu.cpu_ar.read()
            self.cpu.cpu_ar.write(intermediate_bus)

        else:
            late_bus = intermediate_bus

        if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_LATE_BUS:
            print "\t        late_bus = ", signmag_to_str(late_bus)

        return late_bus
