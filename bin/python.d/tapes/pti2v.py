#
# create a synthesizable verilog model of a PTW tape
#
#
import argparse
import sys

sys.path.insert(0,'./scripts')
from g15_ptape import *


def main():
	# defaults
	ModuleName = 'PaperTape'
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', action="append", type=str, dest="InputFiles", help='specify input file (ptw)')
	parser.add_argument('-s', action="store", type=str, dest="MaxTapeSize", help='specify max tape length')
	parser.add_argument('-o', action="store", type=str, dest="OutputFile", help='specify output file')
	parser.add_argument('-m', action="store", type=str, dest="ModuleName", help='specify Verilog module name')
	parser.add_argument('-p', action='store_true', help='prepend number track')
	args = parser.parse_args()

	if (args.InputFiles == None):
		print("Error: no paper tape file specified")
		sys.exit(1)
		
	if (args.ModuleName != None):
		ModuleName = args.ModuleName
		print('mod=', ModuleName)

	if args.OutputFile == None:
		outfile = sys.stdout
	else:
		outfile = args.OutputFile

	for file in args.InputFiles:
		tape = PaperTape()
		tape.ReadPti(file)

		if args.p == True:
			tape.PrependNumberTrack()

		tape.WriteVerilog(outfile, tape.Image, ModuleName )

if __name__ == "__main__":
	main()
