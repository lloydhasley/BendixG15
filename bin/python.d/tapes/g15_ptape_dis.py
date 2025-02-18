

import sys
import datetime
import time


g15_specials = [
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

class g15_ptape_dis:
	def __init__(self):
		self.HEADERMODULUS = 10				# how often to print the legend
		self.Block0IsNumberTrack = False	# placeholder
		
	def WriteDisassembly(self, filename):

		try:
			if filename != sys.stdout :
				fout = open(filename,"w")	
			else:
				fout = sys.stdout
		except:
			print('Error: Cannot for writing file: ', filename)
			
		#
		# is first block Number Track
		if self.Block0IsNumberTrack:
			startindex = 1
			print('Note: First Block is Number Track', file=fout)
			print('', file=fout)
		else:
			startindex = 0

		blockcount = startindex
		for block in self.Blocks[startindex:]:
			wordcount = 0	
			
			for word in block:
				if (wordcount % self.HEADERMODULUS) == 0:
					self.DisassembleHeader(fout)

				str_word = self.DisassembleWord( blockcount, wordcount, word)
				print(str_word, file=fout)

				wordcount = wordcount + 1
			blockcount = blockcount + 1
			print('', file=fout)
		fout.close()	
		
	def	DisassembleHeader(self, fout):
		print("BCK  L       HEX     DECIMAL  P  T  N C  S  D BP", file=fout)

	def DisassembleWord(self, blockcount, wordcount, word):
		# generate address field
		str_blockcount = "%02d"%blockcount
		str_wordcount = self.data2sexDecStr(wordcount)
		str_address = str_blockcount + ', ' + str_wordcount + ', '

		str_word_hex = self.data2str(word, 29)
		
		if word & 1:
			str_s = '-'
		else:
			str_s = ' '
		decimal = ((word >> 1) * 1000000000) >>28
		str_word_decimal = ".%09d"%decimal
		
		if self.debug & 1:
			print("word=%x"%word, 'dec=',decimal)
		
		str_word = str_word_hex + " " + str_s + str_word_decimal

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
		dict_instr, str_prefix = self.DeterminePrefix(dict_instr)
		str_t = self.data2sexDecStr(t)
		str_n = self.data2sexDecStr(n)

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
			special_entry = g15_specials[source]
			if isinstance(special_entry, list):
				if ch >= len(special_entry) :
					special_entry = "** ===???  Ch out of known range ?? "
				else:
					if self.debug & 1:
						print('ch=',ch, ' lspec=',len(special_entry))
					special_entry = (special_entry[ch])
			str_comment = "# " + special_entry
		
		str_full = 	str_address + str_word + '  ' + str_instruction + '  ' + str_comment

		return str_full		
	
	def DecrementT(self,  T, amount ):
		T = T - amount
		if T < 0 :
			T = T + 108
		return T

	def	DeterminePrefix(self, dict_instr):
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
						dict_instr['T'] = self.DecrementT( T, 1)
						prefix = ' '
					elif T & 1:
						# CH>=4 && T ODD
						prefix = 'u'
					else:
						# CH>=4 && T EVEN
						dict_instr['T'] = self.DecrementT( T, 1)
						prefix = ' '			
				elif T== (L + 3):
					if CH < 4:
						prefix = 'u'
					elif T & 1:
						# CH>=4 && T ODD
						prefix = 'u'
					else:
						dict_instr['T'] = self.DecrementT( T, 2)
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

