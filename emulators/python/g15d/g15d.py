
#! /opt/local/bin/python
import argparse
import sys
import os

# sys.path.insert(0,'./g15d')
sys.path.insert(0,'.')
sys.dont_write_bytecode = 1


argpath = os.path.realpath(__file__)
dir = os.path.dirname(argpath)
dir1 = os.path.dirname(dir)
testdir = dir1 + '/tests'


import Emul


def main():
    files_startup = [dir + '/startup.txt']
    configuration = 'numeric'
#    vtracefile = 'vtrace.log'

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-i', action='append', dest='startfiles', default=files_startup)
    arg_parser.add_argument('-l', dest='logfile', default=None)
    arg_parser.add_argument('-v', dest='vtrace', default=None)
    arg_parser.add_argument('-c', action='store', dest='configuration', default=configuration)
    arg_parser.add_argument('-S', action='store_false', dest='signenable', default=True)
    arg_parser.add_argument('-t', action='store', dest='tapes', default='.')
    	# signenable=1 vtrace files displays integers as signed, else 29bits unsigned
    arg_parser.add_argument('scriptfile', nargs='?', default=None)
    	
    args = arg_parser.parse_args()

    Emul.Emulator(args)


# start the program
if __name__ == '__main__':
    main()
