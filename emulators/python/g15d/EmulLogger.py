"""
G15 Logger replicates stdout to a logfile

Note: G15 Emulator has two loggers.  This one logs stdout.
The other, located in G15CPU, logs instruction execution results
"""

import sys


class EmulLogger:
    def __init__(self, filename):
        # save existing stdout definition
        self.stdout = sys.stdout

        # open logfile
        self.logout = open(filename, "w")

    def write(self, text):
        self.stdout.write(text)     # write to saved stdout
        self.logout.write(text)     # write to logfile

    def flush(self):
        sys.stdout.flush()
        pass

    def close(self):
        self.logout.close()
