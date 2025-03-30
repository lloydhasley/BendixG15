#
#
# emulates kbit,
# but within a class so opening/closing can be separated
#
# returns char if one present
# returns None if no chars present
#

import select
import sys
import termios
import tty

class EmulAscii():
    def __init__(self, emul ):
        self.emul = emul

        self.open()

    def open(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setraw(sys.stdin.fileno())

    def close(self):
        # restore original terminal settings
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def kbhit(self):
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            c = sys.stdin.read(1)

            if c == 3:      # control-c
                self.emul.quit()

            print(c, end='')
            return c
        else:
            return False

