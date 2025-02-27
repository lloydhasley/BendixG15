"""
G15 emulator

Basic structure is a command interpreter sitting on top of a python
model of a G15.

Optional gui ontop of the command interpreter

Users can mount a paper tape image and execute it

NOTE:  This is a ISA emulator working at the word/instruction level
   It is NOT a bit level emulator

The g15 keyboard is emulated, complete with the switches (bp,compute,etc..)

Futures:
   paper tape punch is not modelled, but planned
   magnetic tape is not modelled, but planned
"""

import sys

import G15Sim
import G15Cmds
import G15Numeric

known_g15_configurations = {'numeric': G15Numeric.G15Numeric}


class G15Emulator:
    def __init__(self, g15_configuration, startup_files, tracefile):

        print('Loading configuration: ', g15_configuration)

        if g15_configuration in known_g15_configurations:
            self.g15 = known_g15_configurations[g15_configuration](self, tracefile)
        else:
            print('Unload G15D configuration:', g15_configuration)
            sys.exit(1)

        # bring in simulation environment
        self.sim = G15Sim.G15Sim(self)
        self.g15.sim = self.sim

        # bring in the command interpreter
        cmds = G15Cmds.G15Cmds(self.sim)
        cmds.start(startup_files)
