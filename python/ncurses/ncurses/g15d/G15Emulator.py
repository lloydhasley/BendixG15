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
import curses

import G15Logger
import G15Sim
import G15Cmds
import G15Numeric
import G15TypeCurses

known_g15_configurations = {'numeric': G15Numeric.G15Numeric}


class G15Emulator:
    def __init__(self, args):
        if args.logfile:
            # logfile specified
            # let's override prints to stdout to also print to file
            sys.stdout = G15Logger.G15Logger(args.logfile)

        print('Loading configuration: ', args.config)

        if args.config in known_g15_configurations:
            self.g15 = known_g15_configurations[args.config](self, args.trace)
        else:
            print('Unknown G15D configuration:', args.config)
            sys.exit(1)

        # determine active GUI if any
        if args.gui:    # only 1 supported GUI, right now, hooks for additional
            self.gui_type = 'curses'
            self.gui = G15TypeCurses.G15TypeCurses()
        else:
            # default straight terminal
            self.gui_type = ''
            self.gui = None


        # bring in simulation environment
        # note:  this is the workhorse
        self.sim = G15Sim.G15Sim(self)
        self.g15.sim = self.sim

        # bring in the command interpreter
        cmds = G15Cmds.G15Cmds(self.sim)

        # feed initial files
        args.startup = args.startup.replace(":", " ")
        print("startup=", args.startup)
        cmds.start(args.startup)
