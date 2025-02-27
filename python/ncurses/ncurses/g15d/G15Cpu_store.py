"""
G15D Store the Late Bus implementation
"""


from G15Subr import *
import G15Cpu


# noinspection PyPep8Naming
class g15d_store:
    """ g15d late bus """
    def __init__(self, cpu):
        self.cpu = cpu
        self.g15 = cpu.g15

    def store_late_bus(self, late_bus, instruction, word_time):
        """ Stores the late bus to its drum target

        :param instruction:    current instruction being executed
        :param late_bus:            late_bus value
        :param word_time:           current drum word time
        :return:                    late bus (29-bit
        """
        destination = instruction['d']
        Ts = instruction['ts']
        viaAR = instruction['cmd_type'] & (CMD_TYPE_TVA | CMD_TYPE_AVA)
        blockWrite = viaAR and Ts        # block during low ordered word if via AR

        if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_LATE_BUS:
            print('bw=', blockWrite, ' viaar=', viaAR, ' ts=', Ts)

        if destination == AR:
            # eliminate minus-0
            if late_bus == 1 and self.cpu.flop_is:
                late_bus = 0
            self.cpu.cpu_ar.write(late_bus)
            # self.g15.drum.write(AR, 0, late_bus)

        elif destination == AR_Plus:
            # new_ar = signmag_plus_signmag(self.g15.drum.read(AR, 0), late_bus)
            # if new_ar == 1:
            #    new_ar = 0      # elimiante minus 0

            self.cpu.cpu_ar.add(late_bus)
            # self.g15.drum.write(AR, 0, new_ar)

        elif destination == MZ:  # test, MZ is not user writable
            if (late_bus & ~1) != 0:
                instruction['next_cmd_word_time'] = instruction['n'] + 1
                self.cpu.flop_cq = 1

        elif destination == PN_plus:
            self.cpu.cpu_pn.add(late_bus, word_time)

        elif destination == ID:
            if blockWrite:
                self.g15.drum.write(ID, word_time, 0)
            else:
                self.g15.drum.write(ID, word_time, late_bus)

            if instruction['cmd_type'] & (CMD_TYPE_TR | CMD_TYPE_TVA):
                self.g15.drum.write(PN, word_time, 0)

        elif destination == PN:
            # self.cpu.cpu_pn.write(late_bus, word_time)
            if blockWrite:
                self.g15.drum.write(PN, word_time, 0)
            else:
                self.g15.drum.write(PN, word_time, late_bus)

        elif destination == MQ:
            if blockWrite:
                self.g15.drum.write(MQ, word_time, 0)
            else:
                self.g15.drum.write(MQ, word_time, late_bus)

        elif destination != SPECIAL:
            # normal write
            if self.cpu.verbosity & G15Cpu.VERBOSITY_CPU_LATE_BUS:
                print('late_bus write:, dest=', destination, ' wt=', word_time, ' val=%x' % late_bus)

            self.g15.drum.write(destination, word_time, late_bus)

