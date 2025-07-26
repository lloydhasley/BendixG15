"""
G15 emulator

Basic structure is a command interpreter sitting on top of a python
model of a G15.

Optional gui ontop of the command interpreter

Users can mount a paper tape image and execute it

NOTE:  This is a ISA emulator working at the word/instruction level
   It is NOT a bit level emulator

The g15 keyboard is emulated, complete with the switches (bp,compute,etc...)

Futures:
   paper tape punch is not modelled, but planned
   magnetic tape is not modelled, but planned
"""
MUSIC = False     # default is no music processing

import threading
from time import sleep
import signal
import sys

import G15Numeric
import EmulLogger
from G15Constants import *
if MUSIC:
    import EmulMusic
import EmulGetLine
import EmulCmds
import gl

known_g15_configurations = {
    'numeric': G15Numeric.G15Numeric        # numeric machine, no mag tape units
}


class Emulator:
    def __init__(self, args):
        self.configuration = args.configuration
        self.startfiles = [args.startfile]
        self.traceenable = args.traceenable
        self.signenable = args.signenable
        self.scriptfiles = args.scriptfiles
        self.tapedir = args.tapedir
        
        self.verbosity = 0
        
        # determine g15 program(s) to execute
        if self.scriptfiles is not None:
            if isinstance(self.scriptfiles, str):
                self.scriptfiles = [self.scriptfiles]
            for scriptfile in self.scriptfiles:
                self.startfiles.append(scriptfile)
       
        # build emulation
        self.log = EmulLogger.EmulLogger(self, args.logfile)
        self.interactive = True    # if interactive, prints to both log and screen

        gl.logprint('Welcome to the BendixG15 python emulator, version: ' + args.version + '\n')

        gl.logprint('Note:', 'Loading configuration: ', self.configuration)

        if self.configuration in known_g15_configurations:
            self.g15 = known_g15_configurations[self.configuration](self, self.traceenable, self.tapedir, self.signenable)
        else:
            gl.logprint('Unknown G15D configuration:', self.configuration)
            sys.exit(1)

        self.cpu = self.g15.cpu
        self.error_count = 0
        self.g15.bkuker = args.bkuker

        self.log.cpu_attach(self.cpu)       # attach cpu to the logger (gives pointers)

        if MUSIC:
            self.music = EmulMusic.EmulMusic(self.g15)

        signal.signal(signal.SIGINT, self.sigC_handler)
        
        self.number_instructions_to_execute = 0     # num of cmds to execute
        self.cmd_pause_count = 0                    # numb of cmds to pause cmd file processing

        # bring in the command interpreter
        self.getline = EmulGetLine.EmulGetLine(self)
        self.cmds = EmulCmds.EmulCmds(self, self.g15)

        self.RUNSTATE = STATE_IDLE
        self.exit_emulator = False

        gl.logprint("Bringing up Emulator and G15 machine")

        # character IO is in background thread  (needs to become foreground thread)
        # today is attached same terminal window
        # future this thread gets replaced with a GUI or two
        self.t1 = threading.Thread(target=self.processor_thread, daemon=True)
        self.t1.start()

        # foreground thread deals with host IO
        self.getline.thread_getline()      # infinite loop, returns only on exit

    def processor_thread(self):
        # setup is complete, good to start
        # execute startup files
        self.cmds.start(self.startfiles)

        # start the processor
        self.execution_loop()       # remain in loop until emul finishes                
            
    def execution_loop(self):
        halted_flag = False

        while not self.exit_emulator:
            # note: runflag = 0 will cause thread/emulator to exit

            # execute enable keys
            if not self.getline.q_enable.empty():
                cmd = self.getline.q_enable.get()
                self.g15.typewriter.type_enable(cmd)

            # g15 executes any recv messages
            # execute commands
            if self.cmd_pause_count == 0 and self.number_instructions_to_execute == 0:
                self.cmds.cmd_do_from_processor_loop()

#            self.g15.cmds.do_cmd()

            ok2run = self.RUNSTATE
            if self.cpu.halt_status:
                if not halted_flag:
                    print("Machine is halted!")
                halted_flag = True
                ok2run = False
                self.number_instructions_to_execute = 0		# early termination of "run"
            else:
                halted_flag = 0

            # execute an instruction
            if ok2run:
                retvalue = self.g15.cpu.instruction_execute(0)
                if retvalue > 0:  # negative number is error/no execution
                    # reflect that we did execute an instruction
                    self.number_instructions_to_execute -= 1
                    if self.number_instructions_to_execute == 0:
                        self.RUNSTATE = STATE_IDLE

                    # count down cmd pause, if we are paused
                    if self.cmd_pause_count != 0:
                        self.cmd_pause_count -= 1
            else:
                # cannot run an instruction
                sleep(0.010)        # pause 10ms

            continue

    def sigC_handler(self, sig, frame):
        self.quit()
        
    def quit(self):
        gl.logprint("Quitting Emulator")
        self.exit_emulator = True   # stops execution loop AND getchar loop
        try:
            self.music.close()
        except:
            pass

        sleep(0.2)
        self.getline.close()        # graceful shutdown host io subsystem

        # last thing to do during shutdown is close the logfile
        self.log.close()

        sys.exit(0)

    def increment_error_count(self, mesg):
        print("ERROR: ", mesg)
        self.error_count += 1
