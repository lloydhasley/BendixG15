#
# convert PTI ascii tape image to pt binary files
#
import argparse
import sys

from g15_ptape import *



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action="append", type=str, dest="InputFiles", help='specify input file (ptw)')
    parser.add_argument('-o', action="store", type=str, dest="OutputFile", help='specify output file')
    parser.add_argument('-r', action="store_true", default=False, dest="reverse")
    parser.add_argument('-p', action='store_true', default=False, help='prepend number track')
    args = parser.parse_args()

    if (args.InputFiles == None):
        print("Error: no paper tape file specified")
        sys.exit(1)

    if args.OutputFile == None:
        outfile = sys.stdout
    else:
        outfile = args.OutputFile

    for file in args.InputFiles:
        tape = PaperTape()
        tape.ReadPti(file)

        if args.p == True:
            tape.PrependNumberTrack()

        tape.WritePt(outfile, reverse=args.reverse)

if __name__ == "__main__":
	main()


