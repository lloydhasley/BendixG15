#! /usr/local/bin/python3

#########################################
#
# python based G15 emulator
#
# uses ncurses as IO terminal (optional, preferred)
# uses instruction accurate python backend
#
########################################

import curses
import argparse
import sys
import time
import datetime
from pathlib import Path


##################################
# g15 emulator curses interface
#
# divides screen into three windows
# typeout, messages, and status
##################################
VERSION="0.0.0"

class G15TypeCurses:
    def __init__(self, debug):
        self.debug = 0

        # define minimum terminal size
        self.MAXX = 80
        self.MAXY = 24

        # create screen (and sub windows), status bar
        # and address for error messages
        self.screens  = self.curses_init()

        self.display_status("STATUS TEST")
        self.display_message("Welcome to the Bendix G15 Emulator, Version: " + VERSION)
        self.display_typeout("\nUser 'Q' to qutie\n")

        count = 0
        while True:
            c = self.get_input()
            if c  == ord('Q'):
                sys.exit(0)
            self.display_status(str(count))
            count += 1
            self.display_refresh()

    def get_input(self):
        time.sleep(0.05)
        win = self.screens['typeout']['window']

        c = self.screens['stdscr']['window'].getch()    # returns int
        if c == -1:
            win.addstr(22, 5, "None   ")
            return -1       # no character available

        win.addstr(22, 5, "c=0x%02x  " % c)
        win.noutrefresh()
        self.display_refresh()
        time.sleep(3)
        return c

    def decode_input(self, c):
        numeric_input = {
            0x61: ['a', 'enable', 'type ar', self.decode_error],
            0x62: ['b', 'enable', 'start photo tape reverse cycle', self.decode_error],
            0x63: ['c', 'enable', 'set command line = 00', self.decode_error],
            0x66: ['f', 'enable', 'set N = 00', self.decode_error],
            0x69: ['i', 'enable', 'execute one command', self.decode_error],
            0x6c: ['l', 'enable', 'unknown', self.decode_error],
            0x6d: ['m', 'enable', 'mark place', self.decode_error],
            0x70: ['p', 'enable', 'photo tape read', self.decode_error],
            0x71: ['q', 'enable', 'set type-in', self.decode_error],
            0x72: ['r', 'enable', 'return to marked place', self.decode_error],
            0x73: ['s', 'enable', 'stop input/output', self.decode_error],
            0x74: ['t', 'enable', 'N --> AR', self.decode_error],
            # data codes (tape and typewriter)
            0x30: ['0', 'noenable', 'number 0', self.decode_error],
            0x31: ['1', 'noenable', 'number 1', self.decode_error],
            0x32: ['2', 'noenable', 'number 2', self.decode_error],
            0x33: ['3', 'noenable', 'number 3', self.decode_error],
            0x34: ['4', 'noenable', 'number 4', self.decode_error],
            0x35: ['5', 'noenable', 'number 5', self.decode_error],
            0x36: ['6', 'noenable', 'number 6', self.decode_error],
            0x37: ['7', 'noenable', 'number 7', self.decode_error],
            0x38: ['8', 'noenable', 'number 8', self.decode_error],
            0x39: ['9', 'noenable', 'number 9', self.decode_error],
            0x75: ['u', 'noenable', 'number 10', self.decode_error],
            0x76: ['v', 'noenable', 'number 11', self.decode_error],
            0x77: ['w', 'noenable', 'number 12', self.decode_error],
            0x78: ['x', 'noenable', 'number 13', self.decode_error],
            0x79: ['y', 'noenable', 'number 14', self.decode_error],
            0x7a: ['z', 'noenable', 'number 15', self.decode_error],
            #
            0x09: ['\t', 'noenable', 'tab', self.decode_error],
            0x2d: ['-', 'noenable', 'minus', self.decode_error],
            0x0a: ['\n', 'noenable', 'cr', self.decode_error],
            0x2f: ['/', 'noenable', '/', self.decode_error],

            # emulator Commands
            0x51: ['Q', 'enable', 'tab', self.decode_quit],

        }
        win = self.screens['typeout']['window']
        win.addstr(10, 5, "c=0x%02x" % c)
        win.noutrefresh()
        self.display_refresh()
        time.sleep(3)

        self.display_message("c=0x%02x" % c)
#        if c not in numeric_input:
#            self.decode_error(c)
#            return False

        # have a known key
        fcn = numeric_input[c][3]
        if fcn:
            if fcn != self.decode_error:
                # call function
                fcn[3]()
            else:
                self.display_message("key: " + "0x%02x" % c + " " + numeric_input[c][2])

        return True

    def decode_error(self, c):
        self.display_message("Error, input key is not implemented: " + "0x%02x" % c)

    def decode_quit(self):
        self.display_message("leaving G15 Emulator")
        sys.exit(0)

    def display_message(self, mesg, refresh=1):
        TIMER_MESSAGES = 2      # freeze and display message for N seconds

        win = self.screens['messages']['window']
        win.clear()
        win.addstr(0, 0, mesg)
        win.noutrefresh()

        self.display_refresh()
        time.sleep(TIMER_MESSAGES)

    def display_status(self, mesg, refresh=1):
        TIMER_MESSAGES = 2      # freeze and display message for N seconds

        win = self.screens['status']['window']
        win.clear()
        win.addstr(0, 0, "STATUS MESSAGE: " + mesg)
        win.noutrefresh()

        self.display_refresh()
        time.sleep(TIMER_MESSAGES)

    def display_typeout(self, refresh=1):
        win = self.screens['typeout']['window']
        #win.clear()
        win.addstr(5, 5, "Hello World")
        win.noutrefresh()
        self.display_refresh()
        time.sleep(3)


    def display_refresh(self, refresh=1):
        if refresh:
            curses.doupdate()

    def curses_init(self):
        # note the embedded definition of the individual sub windows!
        #
        # insist on 24x80 or larger terminal

        (maxY, maxX) = curses.getsyx()
        if maxY < self.MAXY or maxX < self.MAXX:
            # oops, too small
            # make bigger
            curses.resize_term(self.MAXY, self.MAX)


        # create main window
        screen = curses.initscr()
        screen.clear()
        screen.nodelay(True)
        curses.noecho()             # remove auto echo of charactedrs
        curses.raw()                # disable cooked & ^C
        curses.curs_set(False)      # do not display cursor
        if curses.has_colors():
            curses.start_color()
        screen.keypad(True)    # get sequences as integer

        # create sub-window definitions
        maxY, maxX = screen.getmaxyx()
        screens = {
            "stdscr": { 'window':screen, 'size':[maxY, maxX], 'origin': [0, 0]},
            "typeout": { 'size':[maxY - 2, maxX], 'origin': [0, 0]},
            "messages": { 'size':[1, maxX], 'origin': [maxY - 2,0]},
            "status": { 'size':[1, maxX], 'origin': [maxY - 1,0]}
        }

        # fill in 'window' in screens database
        for key, screen in screens.items():
            if key == "stdscr":
                continue
            screens[key]['window'] = curses.newwin(screen['size'][0], screen['size'][1],
                                        screen['origin'][0], screen['origin'][1])

        return screens


class G15Emulator:
    # This layer is the curses interface and runs in foreground
    # actual g15 emulator runs on 2nd detached thread
    def __init__(self, args):
        self.debug = args.debug

        if args.curses:
            self.TermC = G15Curses(self.debug)
#        else:
#            self.TermIO = TermIO(self.debug)



def main(stdscr):
    parser = argparse.ArgumentParser(
        prog="g15emul",
        description="G15 emulator",
        epilog="Goodbye"
    )
    parser.add_argument("-c","--curses", action="store_true", default=False)
    parser.add_argument("-d","--debug", action="store_true", default=False)
    parser.add_argument("-l","--log", action="store_true", default=False)
    args = parser.parse_args()

    g15emul = G15Emulator(args)



if __name__ == "__main__":
    curses.wrapper(main)

