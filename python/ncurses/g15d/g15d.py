
#! /opt/local/bin/python
import argparse
import sys
import os

# sys.path.insert(0,'./g15d')
sys.path.insert(0,'.')

sys.dont_write_bytecode = 1

cwd = os.getcwd()
arg0path = os.path.realpath(__file__)

print 'cwd=', cwd
print 'arg0path=', arg0path

from G15Emulator import *
from G15Logger import *

def main():
    files_startup = ['tests/startup.txt']
    configuration = 'numeric'
    vtracefile = 'vtrace.log'


    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-d', dest='g15_configuration')
    arg_parser.add_argument('-i', action='append', dest='startfiles')
    arg_parser.add_argument('-l', dest='logfile')
    arg_parser.add_argument('-v', dest='vtrace')
    arg_parser.add_argument('-c', action='store', dest='configuration')
    opts = arg_parser.parse_args()
    print 'opts=',opts

    if opts.g15_configuration:
        g15_configuration = opts.g15_configuration

    if opts.startfiles:
        files_startup = opts.startfiles      # use specified file instead of default

    if opts.configuration:
        configuration = opts.configuration

    if opts.logfile:
        # logfile specified
        # let's override prints to stdout to also print to file
        sys.stdout = G15Logger(opts.logfile)

    if opts.vtrace:
        vtracefile = opts.vtrace

    G15Emulator(configuration, files_startup, vtracefile)

    if opts.logfile:
        # close the logfile
        sys.stdout.close()

# start the program
if __name__ == '__main__':
    main()
