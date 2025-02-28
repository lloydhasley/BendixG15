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

import queue
import threading
from time import sleep
import signal

import G15Numeric
from EmulLogger import *
import EmulAscii
import EmulCmds
from G15Constants import *
import EmulMusic
import EmulGetc

known_g15_configurations = {'numeric': G15Numeric.G15Numeric}


class Emulator:
    def __init__(self, args):
        self.configuration = args.configuration
        self.startfiles = args.startfiles
        self.vtrace = args.vtrace
        self.signenable = args.signenable
        self.scriptfile = args.scriptfile
        self.tapes = args.tapes
        
        self.verbosity = 0

        if args.logfile is not None:
            # logfile specified
            # let's override prints to stdout to also print to file
            sys.stdout = EmulLogger(args.logfile)

        print('Loading configuration: ', self.configuration)

        if self.configuration in known_g15_configurations:
            self.g15 = known_g15_configurations[self.configuration](self, self.vtrace, self.tapes, self.signenable)
        else:
            print('Unknown G15D configuration:', self.configuration)
            sys.exit(1)

        self.cpu = self.g15.cpu
        self.error_count = 0
        self.getc = EmulGetc.CharIO()

        self.music = EmulMusic.EmulMusic(self.g15)

        # queue for messages across thread boundary
        self.qcmd = queue.Queue()	        # cmds -> cpu

        # bring in the command interpreter
        signal.signal(signal.SIGINT, self.sigC_handler)
        
        self.number_instructions_to_execute = 0
        self.execute_trace_enable = 0
        self.cmd_pause_count = 0

        self.ascii = EmulAscii.EmulAscii()
        self.cmds = EmulCmds.EmulCmds(self, self.g15)
        
        # start execution
        #  main thread: cmds
        #  2nd thread: g15
        self.lock_request = SIM_REQUEST_UNLOCK
        self.lock_status = SIM_REQUEST_UNLOCK
        self.runflag = 1
        
        print("Bringing up Emulator and G15 machine")
 #       self.t1 = threading.Thread(target=self.execution_loop, daemon=True)
        self.t2 = threading.Thread(target=self.getc.thread_getchars, daemon=True)

#        self.t1.start()
        self.t2.start()

        # setup is complete, good to start
        # execute startup files
        if self.scriptfile is not None:
            self.startfiles.append(self.scriptfile)

        self.cmds.start(self.startfiles)

        # start the procssor
        print("calling execution loop")
        self.execution_loop()

        if args.logfile:
            # close the logfile
            sys.stdout.close()
            
    def execution_loop(self):
    	# G15 runs in its own thread,
    	# runflag will exit the thread
        while self.runflag:
            # note: runflag = 0 will cause thread to exit

            # execute enable keys
            if not self.getc.q_enable.empty():
                cmd = self.getc.q_enable.get()
                self.g15.typewriter.type_enable(cmd)

            # g15 executes any recv messages
            # execute commands
            if self.cmd_pause_count == 0 and self.number_instructions_to_execute == 0:
                self.cmds.cmd_do_from_processor_loop()

            self.g15.cmds.do_cmd()

            ok2run = 0
            # compute is used during interactive emulator use
            if self.cpu.sw_compute_bp_enable or self.cpu.sw_compute == 'go':
                ok2run = 1
            # run command is typically used during batch test operation
            # and run executes specified number of commands
            if self.number_instructions_to_execute:
                ok2run = 1
            if self.cpu.halt_status:
                print("Machine is halted!")
                ok2run = 0
                self.number_instructions_to_execute = 0		# early termination of "run"

            # execute an instruction
            if ok2run:
                retvalue = self.g15.cpu.instruction_execute(0)
                if retvalue > 0:  # negative number is error/no execution
                    # reflect that we did execute an instruction
                    self.number_instructions_to_execute -= 1
                    
                    # count down cmd pause, if we are paused
                    if self.cmd_pause_count != 0:
                        self.cmd_pause_count -= 1
            else:
                # cannot run an instruction
                sleep(0.010)        # pause 10ms

            continue
            # semaphore pause 
            if self.lock_request == SIM_REQUEST_LOCK:
                self.lock_status = self.lock_request

                # wait for unlock request
                while self.lock_request != SIM_REQUEST_UNLOCK and self.runflag:
                    sleep(SEMAPHORE_WAIT_TIME)       

                self.lock_status = self.lock_request
                
    def sigC_handler(self, sig, frame):
        self.quit()
        
    def quit(self):
        print("Quitting Emulator")
        self.runflag = 0

#        self.t1.join()      # daemon thread auto exit, but here for completeness
        self.music.close()

        sys.exit(0)

    def request_lock(self, flag):
        # LOCK: request pause of the g15 cpu, waits for it to pause
        # UNLOCKL: releases the g15 cpu for execution
        self.lock_request = flag
        
        while self.lock_status != flag:
            sleep(SEMAPHORE_WAIT_TIME)
        
    def send_mesg(self, mesg_type, mesg_value):
        mesg = [mesg_type, mesg_value]
        self.qcmd.put(mesg)

    def get_mesg(self):
        mesg = self.qcmd.get()
        return mesg

    def increment_error_count(self, mesg):
        print("ERROR: ", mesg)
        self.error_count += 1
