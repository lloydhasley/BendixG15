"""
base emulator/enironment

controls the g15d computer
and acts as the interface between the GUI and computer

gui runs in one thread.
the simultor/g15 runs in another thread.
semiphores are used to synchronize betwee the two threads.

the g15 simulator is an event driven simulator
the next instruction is scheduled on an event queue
This allow IO actiivty to be intermixed with CPU instruction,
    as on the real machine
IO devices stream in and out at their 'nominal' rates


events have a function to call at the appropriate time in the emulation
time is expressed as a total number of word sicne system boot.
    from this time, revolutions and word time can be calculated. (modulo 108)

"""
import signal
import sys
import threading
from time import sleep
import platform


# G16D machine imports
from G15Constants import *

# g15 emulator imports
# import G15Event

# SEMAPHORE_WAIT_TIME = 0.01


class G15Sim:
    # noinspection PyPep8Naming
    def __init__(self, emulator, Verbosity=0, WatchDog=90000000):
        self.emulator = emulator
        self.g15 = emulator.g15

        self.verbosity = Verbosity
        self.watchdog_timer_value = WatchDog

        self.event_queue = []
        self.sim_time = 0
        self.error_state = False
        self.error_count = 0

        # set a system watch dog timer
        watchdog = self.create_event("watchdog", self.watch_dog_event)
        self.schedule_event(watchdog, self.watchdog_timer_value)

        machine_os = platform.system()
        if machine_os == 'Darwin':
            print 'MAC OSX detected'
        else:
            print 'Unknown host OS'

        self.execute_trace_enable = 0
        self.number_instructions_to_execute = 0

        # initialize semaphores to the G15
        self.lock_request = SIM_REQUEST_LOCK  # block instr execution until we finish initialization
        self.lock_grant = SIM_REQUEST_UNLOCK

        self.initialize_error_count()        # culmulated count of errors.

        self.sim_start()

    def sim_start(self):
        # create and schedule events
        self.g15.cpu.start(self)

        # start the gui in another thread
        # gui will handshake with this class, who will then pass on deltas to the g15
        # thread.start_new_thread( self.GuiIF)

        ################################################################
        # on windows platforms, one cannot determine if a keyboard char is avail
        # so we need to run keyboard operations in a separate thread and then
        # use semaphores to bring actions back to execution thread.
        ###############################################################

        # start execution thread
        # noinspection PyAttributeOutsideInit
        self.sim_thread = threading.Thread(target=self.thread_cpu_execution)
        self.sim_thread.start()

        # capture exit conditions, shut down secondary thread
        signal.signal(signal.SIGINT, self.quit_signal_handler)

    def watch_dog_event(self):
        self.quit()

    #####################################
    #
    # manage simulator events
    #
    #####################################

    @staticmethod
    def create_event(name, command):

        # noinspection PyDictCreation
        event = {}
        event['name'] = name           # human name of event
        event['time'] = 0              # time of event
        event['command'] = command     # function to call when event triggers

        return event

    def schedule_event(self, event_to_schedule, delta_time):
        # place onto event queue, keeping events time ordered

        event_time = self.sim_time + delta_time
        event_to_schedule['time'] = event_time

        ll = len(self.event_queue)
        if ll == 0:
            self.event_queue.append(event_to_schedule)
            return

        for ii in range(ll):
            entry = self.event_queue[ii]
            entry_time = entry['time']
            if event_time < entry_time:
                self.event_queue.insert(0, event_to_schedule)

    def peek_next_event(self):
        ll = len(self.event_queue)
        if ll == 0:
            return ''

        return self.event_queue[0]['name']

    def get_next_event(self):
        ll = len(self.event_queue)
        if ll == 0:
            return None

        event = self.event_queue[0]
        self.event_queue = self.event_queue[1:]
        self.sim_time = event['time']
        return event

    def print_eventqueue(self):
        for i in range(len(self.event_queue)):
            event = self.event_queue[i]
            print '%2d: ' % i, event

    #####################################
    #
    # simulator shutdown/exit
    #
    #####################################

    def quit_signal_handler(self, signum, stack):
        """ Captures ^C quit signal """

        print 'entering quit signal handler'
        self.quit()

    def quit(self):
        """ Shut things down """

        if self.verbosity & 1:
            print 'Entering emulator quit'
        self.request_lock(SIM_REQUEST_TERMINATE)

        print 'quit-aa'

        # g15 is suspended
        self.sim_thread.join()

        print 'quit-ab'

        retval = self.shutdown_error_count()

        print 'quit-ac'

        if self.verbosity & 1:
            print 'exiting program'

        sys.exit(retval)

    #####################################
    #
    # simulator semaphores between threads
    #
    #####################################

    def request_lock(self, lock):
        """ Request or release the lock to the background thread

        :param lock:       lock/block execution enginer
        :return:
        """

        if (lock == SIM_REQUEST_LOCK) or (lock == SIM_REQUEST_TERMINATE):
            # request lock
            self.lock_request = lock
            # wait for control to be granted
            while self.lock_grant == SIM_REQUEST_UNLOCK:
                sleep(SEMAPHORE_WAIT_TIME)

            if self.verbosity & 1:
                print 'lock granted'

            return 1
        else:
            # release lock
            self.lock_request = SIM_REQUEST_UNLOCK
            # wait for control to be released
            while self.lock_grant == SIM_REQUEST_LOCK:
                sleep(SEMAPHORE_WAIT_TIME)
            return 0

    #####################################
    #
    # G15 detected error handling
    #
    #####################################

    def initialize_error_count(self):
        """ Clear the global error statistics """
        self.error_count = 0
        self.error_state = False

    def increment_error_count(self, text):
        """ Increment global error counts """

        print 'Entering incr error count'

        print 'Error: ', text
        self.error_count += 1

    def check_error_count(self, value):
        """ Validate the accumulated error count against supplied expected value """
        if self.error_count != value:
            print 'ERROR: Total expected error count mismatch, expected: ', value,
            print '\tExpected error count: ', value
            print '\tTotal errors detected: ', self.error_count
            print

            self.error_state = True
            return True
        else:
            print 'CORRECT: expected error count matches, count=', value
            return False

    def shutdown_error_count(self):
        """ Display accumulated error counts on program exit """

        print 'Total (expected and unexpected) G15 Errors detected: ', self.error_count

        if self.error_state:
            print 'ERROR: One or more unexpected errors were detected'
            return False
        else:
            print 'CORRECT: No unexpected errors were detected'
            return True

    #####################################
    #
    # simulation loop
    #
    #####################################

    def thread_cpu_execution(self):
        """ Runs in background thread,  performs all actual g15 activity """

        if self.verbosity & 1:
            print 'background thread started'

        while True:
            #
            # foreground requesting termination of execution thread
            #
            if self.lock_request == SIM_REQUEST_TERMINATE:

                # acknowledge terminate request and return
                self.lock_grant = SIM_REQUEST_LOCK
                return
            #
            # is foreground requesting a pause?
            #
            if self.lock_request == SIM_REQUEST_LOCK:
                #
                # acknowledge and grant control to foreground
                #
                self.lock_grant = SIM_REQUEST_LOCK
                #
                # wait for foreground to finish
                #
                while self.lock_request == SIM_REQUEST_LOCK:
                    sleep(SEMAPHORE_WAIT_TIME)
                #
                # once request is remove, remove grant
                #
                self.lock_grant = SIM_REQUEST_UNLOCK
                #
            #
            # background is enabled,
            # so execute an instruction
            #
            # have a event to execute
            #  if it is a cpu event, we need to be enabled.
            #
            if (self.peek_next_event() == 'cpu') and (self.number_instructions_to_execute == 0):
                sleep(SEMAPHORE_WAIT_TIME)
            elif self.number_instructions_to_execute != 0:
                event = self.get_next_event()
                if self.verbosity & 1:
                    print 'entering command:', event['name']
                event['command']()
                if self.verbosity & 1:
                    print 'leaving command'

                # if position instruction count, decrement
                if self.number_instructions_to_execute > 0:
                    self.number_instructions_to_execute -= 1

    def status_emulator(self):
        """ Display emulator status """

        print '\nEmulator Status:'

        if self.g15.cpu.power_status:
            str_status = 'ON'
        else:
            str_status = 'OFF'
        print '\tDc Power is :' + str_status

    def status_exec(self):
        """ Display emulator execution status """

        print '\tEmulator Status:'
        print '\t\tUnknown Instructions Encountered: ', self.g15.cpu.unknown_instruction_count
        print '\t\tTotal number of Instructions Executed: ', self.g15.cpu.total_instruction_count
        print

    def status(self):
        """ Display all emulator status/statistics """

        self.status_emulator()
        self.status_exec()
        self.shutdown_error_count()

    def guit_if(self):
        pass
