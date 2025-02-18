
from __future__ import print_function
import argparse
import sys
import datetime
import time

MAXTAPEBITS = 15
MAXTAPESIZE = 1 << (15 - 1)
module = 'PaperTape'


def WriteVerilogHeader( fout ):
	tstr = time.strftime("%Y-%m-%d %H:%M")

	print('//', file=fout)
	print('// created: ', tstr, file=fout )
	print('// ', file=fout)
	print('`timescale 1 ns / 100 ps', file=fout)
	print('', file=fout)
	print( 'module ', module, ' (', file=fout )
	print('\tinput\t\t[14:0]\tPaperTapeAddress,', file=fout)
	print('\toutput\treg\t[4:0]\tPaperTapeData', file=fout)

	print(');', file=fout)

def WriteVerilogBody( fout, tape ):
	count0 = 0

	print('', file=fout)
	print('always @*', file=fout)
	
	addr_max_index = MAXTAPESIZE
	addr_min_index = 0
	
	print('\tcase(PaperTapeAddress) // synthesis full_case parallel_case', file=fout)
	for ii in range(len(tape)):
		value = ord(tape[ii])
		if( value == 0):
			count0 = count0 + 1
			if( count0 < 3):
				print("\t//", file=fout)
			continue
		else:
			count0 = 0
		print("\t15'd"+str(ii)+":\tPaperTapeData = 5'h%02x;"%value, file=fout)

	print("\tdefault:\tPaperTapeData = 5'h%02x;"%value, file=fout)
	print('\tendcase', file=fout) 

def WriteVerilogTrailer( fout ):
	print('', file=fout)
	print('endmodule ', file=fout)
	print('', file=fout)

def WriteVerilog( file, tape):
	try: 
		fout = open(file, 'w')
	except:
		print(' Cannot open file: ', file,' for writing')

	WriteVerilogHeader( fout )
	WriteVerilogBody( fout, tape )
	WriteVerilogTrailer( fout )
	fout.close()
		
def FileNameExtensionDelete( file ):
	loc = file.find( '.')
	if( loc == -1 ):
		print('no extension found')
		return
	
	filename = file[0:loc]
	
	print('filename=', filename)
	return filename
	
def ReadTapeBinary(file):
	try:
		with open(file, 'rb') as f:
			data = f.read()
	except:
		print('Cannot open file: ', file)
		data = []
	
	return data

def main():
	MaxTapeSize = 24000
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', action="append", type=str, dest="InputFiles" )
	parser.add_argument('-m', action="store", type=int, dest="MaxTapeSize" )
	args = parser.parse_args()
	
	print('ags=',args)
	
	
	if( args.InputFiles == [] ):
		print("Error, no input files specified")
		sys.exit(1)

	if( args.MaxTapeSize != None ):
		MaxTapeSize = args.MaxTapeSize
	
	for file in args.InputFiles:
		tape = ReadTapeBinary(file)
		
		if( len(tape) > MaxTapeSize ):
			print('Error, max tape size has been exceeded')
			print('\tmax=', MaxTapeSize)
			print('\ttape size=', len(tape) )
			sys.exit(1)
		
		filename = FileNameExtensionDelete(file)
		fileverilog = filename + '.v'
		WriteVerilog( fileverilog, tape)


if __name__ == "__main__":
	main()
	