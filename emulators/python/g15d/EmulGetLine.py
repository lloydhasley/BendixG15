####################################################
#
# monitors keyboard for keystrokes
#
# runs in its own thread waiting for keystroke
#
# returns either an ASCII char or
# a Unicode sequence that has been mapped to a particular
# g15 (enable) command
#

import queue
import sys
import time

import EmulAscii


class EmulGetLine:
    def __init__(self, emul):
        self.emul = emul

        self.ascii = EmulAscii.EmulAscii(self)

        self.buffer = ""
        self.q = queue.Queue()
        self.q_enable = queue.Queue()
        
    def close(self):
        self.ascii.close()

    def thread_getline(self):
        # gets a line from stdin
        # runs in the foreground thread

        self.buffer = ""
        while True:
            while True:
                k = self.ascii.kbhit()
                if k:
                    # end loop if we have a character
                    break

                # check if emulator is exiting
                if self.emul.exit_emulator:
                    return

                time.sleep(0.03)    # wait for next char pull; surrender python to processor thread

            # have straight ASCII char from above loop

            # process delete/backspace
            if k == '\b' or k == '\xff':
                if len(self.buffer) > 0:
                    self.buffer = self.buffer[:-1]
                    sys.stdout.write('\b  \b\b')        # why two \b at end???
                    sys.stdout.flush()
                continue

            # echo character, handling backspace/erase
            self.buffer += k
            sys.stdout.write(k)
            sys.stdout.flush()

            if k == '\n' or k == '\r':
                self.q.put(self.buffer)
                self.buffer = ""
                continue
    
    def get_line():
        if len(self.q):
            return self.q.pop()
        return None
    
