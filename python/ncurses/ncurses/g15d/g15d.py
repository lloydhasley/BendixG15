# ! /opt/local/bin/python
import argparse
import sys
import os

# sys.path.insert(0,'./g15d')
sys.path.insert(0, '.')

sys.dont_write_bytecode = 1


from G15Emulator import *
from G15Logger import *

cwd = os.getcwd()
arg0path = os.path.realpath(__file__)
print('cwd=', cwd)
print('arg0path=', arg0path)

args = []

def g15d(stdscr):
    global args

    print("args=", args)

    G15Emulator(args)


def main():
    global args
    files_startup = ['tests/startup.txt']
    configuration = 'numeric'
    tracefile = 'trace.log'
    tracefile = ''


    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--startup', type=str, dest='startup', default='')
    arg_parser.add_argument('-l', '--logfile', default=None)
    arg_parser.add_argument('-t', '--trace', action='store_true', default=False)
    arg_parser.add_argument('-c', '--configuration', type=str, dest='config', default='numeric')
    arg_parser.add_argument('-g', '--gui', action='store_true', default=False)
    arg_parser.add_argument('-G', '--nogui', action='store_true', default=False)
    args = arg_parser.parse_args()

    # prefix any user startup with the emulator startup file
    args.startup = 'g15d/startup.txt:' + args.startup

    # nogui argument overrides gui argument
    if args.nogui:
        args.gui = False


    print('opts=', args)

#    if args.logfile:
        # logfile specified
        # let's override prints to stdout to also print to file
#        sys.stdout = G15Logger(args.logfile)

#    if args.trace:
#        tracefile = args.trace

#    G15Emulator(configuration, files_startup, tracefile)
    if args.gui:
        curses.wrapper(g15d)
    else:
        g15d(0)

    if args.logfile:
        # close the logfile
        sys.stdout.close()

# start the program
if __name__ == '__main__':
    main()
