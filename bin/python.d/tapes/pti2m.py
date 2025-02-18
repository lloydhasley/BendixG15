
#
# convert PTI ascii tape image to .m music format
#
import argparse
import sys

from g15_ptape import *



def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-i', action="append", type=str, dest="InputFiles", help='specify input file (ptw)')
	parser.add_argument('-o', action="store", type=str, dest="OutputFile", help='specify output file')
	parser.add_argument('-C', action="store_false", dest="compressed", default=True, help='compressed (g15 format)')
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


		tape.WriteM(outfile, compressed=args.compressed)

if __name__ == "__main__":
	main()

