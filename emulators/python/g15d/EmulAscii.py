#
# handles actual ASCII IO to the terminal
# GUIs will replace this file
#
import sys
import select

# not currently used
# need to change input stream to non-blocking.
# this sets the stage for a port to windows,
# which does have a kbhit method
#
class EmulAscii:
    def __init__(self):
        pass

    @staticmethod
    def kbhit():
        # do we have any input
        timeout = 0  # Non-blocking check
        readable, _, _ = select.select([sys.stdin], [], [], timeout)
        return bool(readable)
