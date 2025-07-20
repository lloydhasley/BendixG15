
#! /opt/homebrew/bin/python3        # mac python location
#! /usr/bin/python3                 # ubuntu python location

import argparse
import sys
import os

EMULATOR_VERSION='v1.0.0'

# sys.path.insert(0,'./g15d')
sys.path.insert(0,'.')
sys.dont_write_bytecode = 1


argpath = os.path.realpath(__file__)
dir = os.path.dirname(argpath)
dir1 = os.path.dirname(dir)
testdir = dir1 + '/tests'


import Emul


# search upward for specified directory (dir1) then down for dir2
def find_tapedir(seed, dir1, dir2):
    # user did not specify a tape directory
    # so let's go find it.  go up the directory tree from the g15 python executable
    edir = os.path.realpath(os.path.dirname(seed))  # where does this program live
    while edir != '/':
        tdir = edir + '/' + dir1
        if os.path.isdir(tdir):
            # have the directory
            # insure that it has 'images' inside of it
            t1dir = tdir + '/' + dir2
            if os.path.isdir(t1dir):
                # we have the tapes/images directory that we want!!!! :)
                return t1dir
        edir = os.path.dirname(edir)
    return None


def main():
    file_startup = dir + '/startup.txt'
    configuration = 'numeric'

    arg_parser = argparse.ArgumentParser(description='A Bendix G-15 emulator')
    arg_parser.add_argument('-s', '--startfile', action='append', default=file_startup)
    arg_parser.add_argument('-l', '--logfile', default=None)
    arg_parser.add_argument('-t', '--traceenable', action='store_true', default=False)
    arg_parser.add_argument('-c', '--configuration', action='store', default=configuration)
    arg_parser.add_argument('-S', action='store_false', dest='signenable', default=True)
    arg_parser.add_argument('-b', action='store_true', dest='bkuker', default=False)
    arg_parser.add_argument('-d', '--tapedir', action='store', default=None, help="tape directory")
    arg_parser.add_argument('scriptfiles', nargs='?', default=None)
    args = arg_parser.parse_args()

    # check if user specified the directory of known BendixG15 tape images
    # if not, let's go looking for it
    if args.tapedir is None:
        cpwd = os.getcwd()
        tdir = find_tapedir(cpwd, 'tapes', 'images')            # look in current tree
        if tdir is None:
            tdir = find_tapedir(__file__, 'tapes', 'images')    # look in prgrm tree
        if tdir is None:
            tdir = '.'      # let's hope program tape is in current directroy
        args.tapedir = tdir
        print("lcoated tapedir=", tdir)

    # add version label to the argument list
    args.version = EMULATOR_VERSION


    Emul.Emulator(args)


# start the program
if __name__ == '__main__':
    main()
