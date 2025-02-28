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

# import threading
import queue
import readchar
import sys


class CharIO:
    def __init__(self):
        self.buffer = ""
        self.q = queue.Queue()
        self.q_enable = queue.Queue()

#    def thread_start(self):
#        # daemon, will stop automatically
#        self.thread_c = threading.Thread(target=self.thread_getchars, daemon=True)
#        self.thread_c.start()
#
#    def thread_end(self):
#        pass

    def thread_getchars(self):
        # get a character from stdin

        self.buffer = ""

        while True:
            # k = readchar.readchar()
            # readkey on escape waits for next char,
            #   we shall use this property for the enable switch
            # all other keys strokes immediately are available
            k = readchar.readkey()
            if len(k) > 1:  # extended command
                print("mesg0=%x" % ord(k[0]))
                if k[0] != '\x1b':
                    continue
                enable_cmd = k[1]
                print("placing onto enable queue: %s" % enable_cmd)
                self.q_enable.put(enable_cmd)
                continue

            # have straight ASCII char

            if k == '\b' or k == '\xff':
                if len(self.buffer) > 0:
                    self.buffer = self.buffer[:-1]
                    sys.stdout.write('\b  \b\b')        # why two \b at end???
                    sys.stdout.flush()
                continue

            self.buffer += k
            sys.stdout.write(k)
            sys.stdout.flush()

            if k == '\n':
                line = self.buffer
                self.buffer = ""
                print("placing onto cmd queue: %s" % line)

                self.q.put(line)
                continue
