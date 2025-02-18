
from __future__ import print_function
import argparse
import sys
import datetime
import time

MAXTAPEBITS = 15
MAXTAPESIZE = 1 << (15 - 1)
PAD = "00000000"

HEADERMODULUS = 10			# how often to print the legend

specials = [
	"Set READY",
	[ "Mag Tape Write Unit 0", "Mag Tape Write Unit 1", "Mag Tape Write Unit 2", "Mag Tape Write Unit 3" ],
	"Fast Punch Ldr.",
	"Fast Punch M19",

	["Mag Search Rev. Unit 0", "Mag Search Rev. Unit 1", "Mag Search Rev. Unit 2", "Mag Search Rev. Unit 3" ],
	["Mag Search Fwd. Unit 0", "Mag Search Fwd. Unit 1", "Mag Search Fwd. Unit 2", "Mag Search Fwd. Unit 3" ],
	"Ph Tape Rev. 01",
	"Ph Tape Rev. 02",
	
	"Type AR",
	"Type M19",
	"Punch M19",
	"Punch Card M19",
	
	"Type In",
	[ "Mag Tape Read Unit 0", "Mag Tape Read Unit 1", "Mag Tape Read Unit 2", "Mag Tape Read Unit 3" ],
	"Card Read",
	"Photo Tape Read",

	"Halt",
	"Ring Bell",
	"20*ID to OR",
	[ "Stop DA-1", "Start DA-1", "DA1 ??", "DA1 ??" ],
	
	"Return",
	[ "Mark to Track 0", "Mark to Track 1", "Mark to Track 2", "Mark to Track 3", \
		"Mark to Track 4", "Mark to Track 5", "Mark to Track 19", "Mark to Track 23" ],
	"Test T1*AR",
	"PG Clear",
	
	"Multiply",
	"Divide (ch=1)",
	"Shift",
	"Normalize",
	
	"Test Ready",
	"Test Overflow",
	"Mag File Code",
	[ "Next Command from AR", "Transfer NT to M18", "M18 + M20" ]
]

def CalculateNumberTrack():
	NT = []
	word = 0x10000000
	for i in range(107):
		word = word + 0x202000
		NT.append(word)
	
	word = (0x1414794 << 1) | 1
	NT.append(word)
	
	return NT

def	Binary2SexDecStr(data):
	# converts 0-107 to 0-99,u0-u7
	if data > 107:
		str_data = "**"
	elif data >= 100:
		# note: G15 does not support L,T> 107......
		# would need true hex to support all 7 bits.
		# G15 scheme only supports range [0:109]
		data = data - 100
		datas = Binary2HexStr(data, 1)
		# str_data = "u" + "%d"%data
		str_data = "u" + datas
	else:
		str_data = "%2d"%data
	return str_data

def	Binary2HexStr1(data):
	# note: sign bit must already be removed	
	if data == 0:
		return("")
		
	digit = data & 0xf;
	
	if digit < 10:
		digit_str = chr( ord('0') + digit)
	else:
		digit_str = chr( ord('u') - 10 + digit)
		
	data_str = Binary2HexStr1(data>>4) + digit_str
	
	return(data_str)

def	Binary2HexStr(data, length):
	str_base = Binary2HexStr1(data)

	l = len(str_base)
	if length > l :
		str_pad = PAD[0:length-l]
	else:
		str_pad = ""
		
	return( str_pad + str_base )
	
def DecrementT( T, amount ):
	T = T - amount
	if T<0 :
		T = T + 108
	return T

def	DeterminePrefix(dict_instr):
	L = dict_instr['L']
	T = dict_instr['T']
	D = dict_instr['D']
	CH = dict_instr['CH']
	BLOCK = dict_instr['BLOCK']
	
	if BLOCK:
		if D != 31:
			if T == (L + 2) :
				if CH < 4:
					# CH < 4
					dict_instr['T'] = DecrementT( T, 1)
					prefix = ' '
				elif T & 1:
					# CH>=4 && T ODD
					prefix = 'u'
				else:
					# CH>=4 && T EVEN
					dict_instr['T'] = DecrementT( T, 1)
					prefix = ' '			
			elif T== (L + 3):
				if CH < 4:
					prefix = 'u'
				elif T & 1:
					# CH>=4 && T ODD
					prefix = 'u'
				else:
					dict_instr['T'] = DecrementT( T, 2)
					prefix = ' '						
			else:
				prefix = 'u'
		else:
			prefix = ' '
	else:
		# NORMAL Command
		if (D != 31) and (T != (L + 1)):
			prefix = ' '
		else:
			prefix = 'w'

	return dict_instr, prefix					
	
def DisassembleWord( blockcount, wordcount, word):

	# generate address field
	str_blockcount = "%02d"%blockcount
	str_wordcount = Binary2SexDecStr(wordcount)
	str_address = str_blockcount + ', ' + str_wordcount + ', '

	if( word & 1 ):
		s="-"
	else:
		s=" "
	instr_word = word>>1

	if True:
		str_word_hex = Binary2HexStr(word, 8)
	else:
		str_word_hex = s + Binary2HexStr(instr_word, 7)
	
	decimal = (0.0 + instr_word) / (1<<28)
	str_word_decimal = str(round(decimal,8))
	str_word_decimal = str_word_decimal[1:]
	str_word_decimal = str_word_decimal + '00000000'
	str_word_decimal = str_word_decimal[:9]
	str_word = str_word_hex + "  " + str_word_decimal

	# extract fields
	f_p = " "

	# TNCSD BP K OP CH WD
	sd = word & 1
	ch = (word>>11) & 2 + (sd << 2)

	destination = (word>>1) & 0x1f
	source = (word>>6) & 0x1f
	n = (word>>13) & 0x7f
	bp = (word>>20) & 1
	t = (word>>21) & 0x7f

	normal = (word>>29) & 1
	block = normal ^ 1
	
	dict_instr = { 'CH':ch, 'N':n, 'BP':bp, 'T':t, 'BLOCK':block, 'D':destination, 'S':source, 'L':wordcount, 'INSTR':word }
	dict_instr, str_prefix = DeterminePrefix(dict_instr)
	str_t = Binary2SexDecStr(t)
	str_n = Binary2SexDecStr(n)
	str_c = str(ch)
	str_source = "%2d"%source
	str_dest = "%2d"%destination
	
	if bp:
		str_bp = "BP"
	else:
		str_bp = '  '
		
	str_instruction = str_prefix + ' ' + str_t + ' ' + str_n + ' ' + str_c + ' ' + str_source + ' ' + str_dest + ' ' + str_bp	
	
	# determine any comments
	str_comment = ''
	if destination == 31:
		special_entry = specials[source]
		if isinstance(special_entry, list):
			if ch > len(special_entry) :
				special_entry = "** ???  Ch out of known range ?? "
			else:
				special_entry = (special_entry[ch])
		str_comment = "# " + special_entry
		
	str_full = 	str_address + str_word + '  ' + str_instruction + '  ' + str_comment

	return str_full
	

def WriteDisassembly( file_dis, blocks):

	filename = file_dis + '.dis'
	fp = open(filename,"w")	
	
	NT = CalculateNumberTrack()
	
	blockcount = 0
	for block in blocks:	
		wordcount = 0	
		
		if block == NT:
			print("\n%02d"%blockcount, "This block is number track", file=fp)
		else:			
			for word in block:
#				fp.write('%08x'%word + '\n')	
				if (wordcount % HEADERMODULUS) == 0:
					print("BCK  L       HEX    DECIMAL  P  T  N C  S  D BP", file=fp)

				str_word = DisassembleWord( blockcount, wordcount, word)
				print(str_word, file=fp)

				wordcount = wordcount + 1
		blockcount = blockcount + 1
		print("", file=fp)
	fp.close()
		
		
def FileNameExtensionDelete( file ):
	loc = file.find( '.')
	if( loc == -1 ):
		print('no extension found')
		return
	
	filename = file[0:loc]
	return filename
	
	
def SplitQuadWord( quadword, block ):
	# split a 29*4 bit quad word into its individual 29 bit words
	mask = (1<<29) - 1
	
	words = []
	for i in range(4):
		word = quadword & mask
		quadword = quadword >> 29
		words.append(word)
		
	for i in range(3,-1,-1):
		block.insert( 0, words[i] )
			
	return block
		
def HexPrintList( data ):
	s = ""
	for w in data:
		s=s+' '+'%08x'%w
	print(s)	

def	ExtractBlocksFromTape(tape):
	tape_blocks = []
	
	block = []
	databuffer = 0
	sign = 0
	for bytec in tape:
		byte = ord(bytec)
		if byte & 0x10:
			# data byte
			databuffer = databuffer << 4
			databuffer = databuffer & ((1<<(29*4))-1)
			databuffer = databuffer | (byte & 0xf)
		elif byte == 0x1:
			# sign bit
			sign = 1;
		elif (byte == 2) or (byte == 3):
			# CR or TAB
			databuffer = databuffer << 1
			databuffer = databuffer & ((1<<(29*4))-1)
			databuffer = databuffer | sign			
			sign = 0
		elif byte == 4:
			# STOP (reload + end of block)
			block = SplitQuadWord(databuffer, block)
			databuffer = 0
			tape_blocks.append(block)
			block = []
		elif byte == 5:
			# Reload
			block = SplitQuadWord(databuffer, block)
			databuffer = 0
		elif byte == 6:
			# Period		
			continue
		elif byte == 7:
			# wait
			# equivalent to a data zero
			databuffer = databuffer << 4
		elif byte == 0:
			# space
			# ignore
			continue
	return tape_blocks
			
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
				
		blocks = ExtractBlocksFromTape(tape)
		
		filename = FileNameExtensionDelete(file)
		WriteDisassembly( filename, blocks)
	


if __name__ == "__main__":
	main()
	