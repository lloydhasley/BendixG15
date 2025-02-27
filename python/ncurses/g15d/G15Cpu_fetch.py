"""
G15D fetch the next instruction
"""

from G15Subr import *


# noinspection PyPep8Naming,PyPep8Naming
class g15d_fetch:
    """ g15d command fetch """
    def __init__(self, cpu):
        self.cpu = cpu
        self.g15 = cpu.g15

    def fetch(self):
        """
        Fetches the next instruction from the G15D drum memory

        instructions normally come from the next 'word' time, but may come from the accumulator
        """

        # print 'fetch: cmd-next_cmd_line=', self.instruction['next_cmd_line']

        #
        # get the next instruction from the drum, also returns location instruction was taken from
        #
        instruction = self.cpu.instruction

        if instruction['next_cmd_acc']:
            instruction['cmd_acc'] = 1
            instruction['next_cmd_acc'] = 0

            instruction['loc'] = instruction['next_cmd_word_time']
            instruction['instr'] = self.g15.drum.read(AR, 0)
        else:
            instruction['cmd_acc'] = 0
            instruction['next_cmd_acc'] = 0

            cmd_line = instruction['next_cmd_line']
            instruction['cmd_line'] = cmd_line
            loc = instruction['next_cmd_word_time'] % 108

            instruction['instr'] = self.g15.drum.read(cmd_line_map[cmd_line], loc)
            instruction['loc'] = loc

        self.cpu.flop_is = 0        # RC (instruction fetch) clears IS flop

        instruction['d31_print_flag'] = 0  # re=enable d31 prints

        return instruction
