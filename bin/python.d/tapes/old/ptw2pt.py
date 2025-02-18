#
# read a paper image from PTW format
#
# generate a pt format file
#
#
import argparse
import sys

sys.path.insert(0,'./scripts')
from g15_ptape import *


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-r', action="store_true", help='reverse bit columns')
	parser.add_argument('-i', action="append", type=str, dest="InputFiles", help='specify input file (ptw)')
	parser.add_argument('-o', action="store", type=str, dest="OutputFile", help='specify output file')
	parser.add_argument('-p', action='store_true', help='prepend number track')
	args = parser.parse_args()

	if (args.InputFiles == None):
		print("Error: no paper tape file specified")
		sys.exit(1)

	if args.OutputFile == '':
		outfile = sys.stdout
	else:
		outfile = args.OutputFile

	for file in args.InputFiles:
		tape = PaperTape()
		tape.ReadPtw(file)

		if args.p == True:
			tape.PrependNumberTrack()

		if args.r == True:
			tape.WritePt(outfile, reverse=True)
		else:
			tape.WritePt(outfile)

if __name__ == "__main__":
	main()
