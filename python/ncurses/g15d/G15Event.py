'''
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
IO devices stream in and out and their 'nominal' rates


events have a function to call at the appropriate time in the emulation
time is expressed as a total number of word sicne system boot.
    from this time, revolutions and word time can be calculated. (modulo 108)

'''
import thread
from time import sleep


class G15Event:
    def __init__(self):
        self.EventQueue = []

    def CreateEvent(self, name, command):
        event = {}
        event['name'] = name           # human name of event
        event['time'] = 0              # time of event
        event['command'] = command     # function to call when event triggers

        return event

    def ScheduleEvent(self, new_event):
        # place onto event queue, keeping events time ordered
        new_event_time = new_event['time']

        ll = len(self.EventQueue)
        if ll == 0:
            self.EventQueue.append(new_event)
            return

        for ii in range(ll):
            entry = self.EventQueue[ii]

            entry_time = entry['time']
            if new_event_time < entry_time:
                self.EventQueue.insert(0, new_entry)

    def GetNextEvent(self):
        ll = len(self.EventQueue)
        if ll == 0:
            return None

        event = self.EventQueue[0]
        self.EventQueue = self.EventQueue[1:]

        return event
