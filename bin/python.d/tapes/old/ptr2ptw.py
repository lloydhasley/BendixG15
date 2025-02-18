#
# read a paper image (from pt reader)
# and conver to PTW format
#
# PTW is a listing format:
#  <block> <word time>  <word contents>
#
import argparse
import sys

sys.path.insert(0,'./scripts')
from g15_ptape import *


def main():
	MaxTapeSize = 24000

	parser = argparse.ArgumentParser()
	parser.add_argument('-m', action="store", type=int, dest="MaxTapeSize", help='specify max tape length')
	parser.add_argument('-o', action="store", type=str, dest="OutputFile", help='specify output file')
	parser.add_argument('-p', action='store_true', help='prepend number track')
	parser.add_argument('ifiles', default=[], nargs='*')

	args = parser.parse_args()

	# print 'ags=', args

	if (args.ifiles == None):
		print("Error: no paper tape file specified")
		sys.exit(1)

	if args.OutputFile == '':
		outfile = sys.stdout
	else:
		outfile = args.OutputFile

	if (args.MaxTapeSize != None):
		MaxTapeSize = args.MaxTapeSize

	tape = PaperTape()
	for file in args.ifiles:
		tape.ReadPtr(file)

		if args.p == True:
			tape.PrependNumberTrack()

		tape.WritePtw(outfile)

if __name__ == "__main__":
	main()
