#
# read a paper image and conver to PTW format
#
# PTW is a listing format:
#  <block> <word time>  <word contents>
#
# class uses Blocks as its main database
# Blocks are nested lists corresponding to the blocks and the WORDS on the tape
#
# usual flow is to read an acquired tape image in binary format
# symbols from the tape are stored in self.Image
# the image is then checked for known errors and corrected if necessary
#   (at present time:  column reversal)
# Blocks[0] is checked to determine if it is NT and a flag is set
#
# once a tape is read, self.Image is replaced with a corrected one:
#   12"         leader and trailer
#   6"          trailer after each stop code
#   1 symbol    after each reload code
#   2" guanrantee   leader placed in front of stop codes, if previous one is too close
#
#
# once a tape is read a variety of "tape" formats may be generated
# including:
#       disassembly listing
#       synthesizable verilog
#       corrected binary image
#

import sys
import re

sys.path.insert(0,'./scripts')

from g15_ptape_subr import g15_ptape_subr
from g15_ptape_verilog import g15_ptape_verilog
from g15_ptape_dis import g15_ptape_dis


class PaperTape(g15_ptape_subr, g15_ptape_verilog, g15_ptape_dis):
	def __init__(self):
		g15_ptape_subr.__init__(self)
		g15_ptape_verilog.__init__(self)
		g15_ptape_dis.__init__(self)
		self.debug = 0

		self.PT_LEADER = 120
		self.PT_TRAILER = 120
		self.PT_RELOAD_GUANRANTEE = 20		# interval between reload/STOPS
		self.PT_RELOAD_PAUSE = 1			# number of blanks after a reload
		self.PT_STOP_GAP = 60				# 6" gap after a stop code
		
		self.PTI_CHAR_SET = "0123456789uvwxyz-DTS/"
		
		# note: max tape size comes from verilog model which has a 15bit position counter
		self.MAXTAPESIZE = (2<<15) -2
		
		self.Blocks = []		# list of lists
		self.Image = []			# consecutive symbol list (flat), entire tape
		self.NumberTrack = self.CreateNumberTrack()
		self.Block0IsNumberTrack = False
	
	def Update(self):
		self.CheckIfNumberTrack()			
		self.CreateImage()

	#########################################
	# NT routines
	#########################################

	def CreateNumberTrack(self):
		nt = []
		for i in range(1,108):
			word = 1<<28
			word |= i<<13
			word |= i<<21
			nt.append(word)
		nt.append(0x2828f29)

		if self.debug & 1:
			self.PrintPtrBlock(sys.stdout, nt, 99)

		return nt
		
	def	CheckIfNumberTrack(self):
		if len(self.Blocks) > 0:
			self.CheckBlockIfNumberTrack( self.Blocks[0] )
		else:
			self.Block0IsNumberTrack = False		

	def CheckBlockIfNumberTrack(self, block):
		if len(block) != 108:
			return False

		for i in range(108):
			if( block[i] != self.NumberTrack[i]):
				self.Block0IsNumberTrack = False
				return False

		self.Block0IsNumberTrack = True
		return True

	def PrependNumberTrack(self):
		print 'Note: Prepending number track'

		self.Blocks.insert(0, self.NumberTrack)
		self.Block0IsNumberTrack = self.CheckIfNumberTrack()

		# check if number track, create image		
		self.Update()
	
	#########################################
	# PT FORMAT routines
	#########################################

	def ReadFilePt(self,file):
		try:
			with open(file, 'rb') as f:
				Bytes = f.read()
		except:
			print('Cannot open file: ', file)
			Bytes = []

		for byte in Bytes:
			self.Image.append(ord(byte))
			
		self.ReverseImage()
		self.ExtractBlocksFromImage()
		self.Update()

		return self.Image		
		
	def	ReverseImage(self):
		# some tapes have the columns reversed
		# detect if reverse and correct if necessary
		
		newImage = []
		count0 = 0
		count4 = 0
		for byte in self.Image:
			if byte&1:
				count0 += 1
			if byte & 0x10:
				count4 += 1
			
			byteReversed = self.ReverseBits(byte, 5)
			newImage.append(byteReversed)

		if self.debug & 1:
			print 'count0=',count0, 'count4=',count4
			print 'len=', len(self.Image)
			print 'nlen=', len(newImage)

		if count0 > count4:
			print 'Note: tape columns are reversed, repairing image....'
			self.Image = newImage
			
		return self.Image

	def ReverseBits(self, byte, numOfBits):

		newByte = 0
		for i in range(numOfBits):
			newByte = (newByte << 1) | (byte & 1)
			byte >>= 1

		return newByte
			
	def	ExtractBlocksFromImage(self):
		tape_blocks = []
	
		block = []
		databuffer = 0
		sign = 0
		garbageFlag = 0
		for bytec in self.Image:
			# byte = ord(bytec)
			byte = bytec
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
				block = self.SplitQuadWord(databuffer, block)
				databuffer = 0
				tape_blocks.append(block)
				block = []
			elif byte == 5:
				# Reload
				block = self.SplitQuadWord(databuffer, block)
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
			else:
				print 'garbage byte: 0x%02x'%byte
				garbageFlag = 1

		if garbageFlag :
			print 'Note: invalid characters were detected in the tape image'

		self.Blocks = tape_blocks

		return self.Blocks
					
	def SplitQuadWord(self, quadword, block ):
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

	def WritePt(self, file):
		# write a pt binary file

		# create binary database from the word database
		self.CreateImage()

		try:
			if file == sys.stdout:
				fout = sys.stdout
			else:
				fout = open(file, "wb")
		except:
			print 'Error: Cannot write pt file: ', file
			sys.exit(1)

		fout.write( bytearray( self.Image ) )

		if fout != sys.stdout:
			fout.close()

	#########################################
	# PTI FORMAT routines
	#
	# note:
	# a tape is normally spread across multiple PTI files
	# so a read is an incremental.
	#########################################
	
	def ReadPti(self, file):		
		try: 
			if file == sys.stdin:
				fin = sys.stdin
			else:
				fin = open(file, "r")
		except:
			print 'ERROR: Cannot open paper tape file: ', file, ' for reading'
			return

		block = []
		sign = 0
		for line in fin:
					
			# strip trailing newline, both mac and PC
			ii = line.find('\n')
			if ii != -1:
				line = line[:ii]
			ii = line.find('\r')
			if ii != -1:
				line = line[:ii]
								
			if self.debug & 2:
				print 'line=',line
			#
			# some pti files have short garbage lines.
			# so do some length/format checking
			# 
			#
			# check line length (eliminate fragments)
			ll = len(line)
			if ll == 0:
				continue		# ignore blank lines
			if ll < 27:
				errflag = 1
				if self.debug & 2:
					print 'invalid line length, line: ',line
				continue
				
			# trailing character should be reload or stop
			lastchar = line[ len(line) - 1 ]
			if (lastchar != '/') and (lastchar != 'S'):
				errflag = 1
				if self.debug & 2:
					print 'invalid last char: ',c, ' in line: ',line
				continue
					
			# does entire line have valid characters?
			errflag = 0
			for c in line:
				# does entire line have valid characters?
				jj = self.PTI_CHAR_SET.find(c)
				if jj == -1:
					errflag = 1
					if self.debug & 2 :
						print 'invalid character: ',c , ' in line: ',line
					continue
			if errflag:
				continue
			
			# line appears to be valid
			# so let's process it
			if self.debug & 2:
				print 'taking line'

			quadword = 0
			for c in line:
				ii = self.PTI_CHAR_SET.find(c)  # already known to be in character set
				
				if self.debug & 2:
					print 'quadword=%x'%quadword
				
				if ii < 16:
					# valid hex 
					quadword <<= 4
					quadword |= ii
				elif c == '-':
					sign = 1
				elif (c == 'D') or (c == 'T'):
					quadword <<= 1
					quadword |= sign
					sign = 0
				elif (c == '/') or (c == 'S'):
					# add to block
					block = self.SplitQuadWord(quadword, block )
					quadword = 0

					if self.debug & 2:
						print 'block=', block
					
					# if S then put block into Blocks
					# and prepare for more data
					if c == 'S':			
						self.Blocks.append(block)
						block = []
				else:
					# note: should never get here as c previously checked against valid array
					print 'ERROR: Internal, unknown command char: ',c
					continue
					 
		# although we don't know if last file or not, assume it is
		self.Update()
				
		if fin != sys.stdin:
			fin.close()

	#########################################
	# PTW FORMAT routines
	#########################################
	def PrintPtw(self):
		fout = sys.stdout
		self.PrintPtw1(fout)

	def PrintPtw1(self, fout):
		blockCount = 0
		for block in self.Blocks:
			self.PrintPtrBlock(fout, block, blockCount)
			blockCount += 1

	def PrintPtrBlock(self, fout, block, blockCount):
		wordTime = 0
		for word in block:
			print >>fout, '%02d' % blockCount, ' %s' % self.data2sexDecStr(wordTime), '%s' % self.word2str(word)

			wordTime += 1

		print >>fout

	def WritePtw(self, file):
		# write a ptw file

		try:
			if file == sys.stdout:
				fout = sys.stdout
			else:
				fout = open(file, "w")
		except:
			print 'Error: Cannot write file: ', file
			sys.exit(1)
		
		if self.CheckIfNumberTrack():
			print >>fout, "# Block 0 is number Track"

		self.PrintPtw1(fout)

		if fout != sys.stdout:
			fout.close()

	def ReadPtw(self, file):
		try:
			if file == sys.stdin:
				fin = sys.stdin
			else:
				fin = open(file, "r")
		except:
			print 'Error: Cannot open ptw file: ', file
			sys.exit(1)

		contents = []
		block = []
		current_block = -1
		for line in fin.readlines():

			# process comments
			ii = line.find("#")
			if ii != -1:
				line = line[:ii]

			# tokenize
			tokens = line.split()

			ll = len(tokens)
			if ll == 0:
				continue
			elif ll != 3:
				# error
				print 'Error: Ptw format error: line: ',line
				continue

			block_str = tokens[0]
			address_str = tokens[1]
			data_str = tokens[2]

			if current_block != block_str:
				# end of block
				if len(block) != 0:
					# if current/old block is not empty, capture it
					self.Blocks.append(block)
					block = []

				current_block = block_str

			# same block
			address = self.sexDecStr2data(address_str)

			# print 'a_str',address_str, 'address=',address, ' l=',len(block)

			if address != len(block):
				print 'Error: ptw format error, address is not sequential'
				continue

			data = self.str2word(data_str)
			block.append(data)

			if self.debug & 1:
				print 'datastr=', data_str, ' data=0x%08x'%data

		# EOF
		if len(block) != 0:
			self.Blocks.append(block)

		if file != sys.stdin:
			fin.close()
	
		# check if number track, create image		
		self.Update()
		
			
	#########################################
	# PTR FORMAT routines
	#########################################

	def ReadPtr(self,file):
		try:
			f = open(file, 'r')
		except IOerror:
			print('Cannot open file: ', file)
			self.Image = []
			return self.Image
		
		for i in range(80):
			self.Image.append(0)
		
		reg = re.compile('^[0-9u-z]+$')

		errcount = 0
		charSinceReload = 0
		quadsSinceStop = 0
		numBlocks = 0
		for line in f.read().splitlines():
			l = len(line)
			if l<3:
				continue
			
			if line[0] != ' ' and line[0] != '-':
				continue
			if line[l-1] != 'R' and line[l-1] != 'S':
				continue
				
			if l!= 31 and l>=29 and l<=33:
				print 'Error:  suspcious line, character count is in  error'
				errcount += 1					
				continue
				
			if not reg.match(self.g15_hex):
				continue

			# print 'good: ',line
		
			for byte in line:
				if charSinceReload > 100:
					print 'Error:  too many symbols since reload'
					errcount += 1
				if quadsSinceStop > (108/4):
					print 'Error:  too many quadwords since stop'
					errcount += 1					
			
				jj = self.g15_hex.find(byte)
				if jj != -1:
					self.Image.append(jj + 16)
				elif byte == ' ':
					self.Image.append(0)
				elif byte == '-':
					self.Image.append(1)
				elif byte == 'R':
					self.Image.append(5)
					self.Image.append(0)
					quadsSinceStop += 1
				elif byte == 'S':
					self.Image.append(4)
					for i in range(40):
						self.Image.append(0)			
					quadsSinceStop = 0
					numBlocks += 1
				else:
					print 'Error, unknown tape symbol: ',byte
					errcount += 1
						
		print 'Note: ', numBlocks, ' tape blocks detected'
		if errcount:
			print 'Total ', errcount, ' Errors detected'
			sys.exit(1)
			
		self.ExtractBlocksFromImage()
		self.Update()
		return self.Image		
		
			
	#########################################
	# Blocks to image creation
	#
	# takes word information, creats a symbol stream
	# with appropriate space (timing) characters
	#
	# uses G15 standard (undocumented) format
	# 28 symbols - reload or stop  
	# (no sign char)
	#
	#########################################

	def CreateImage(self):
		self.Image = []
		
		self.CI_Fill(self.PT_LEADER)   #  12 inches of leader
		LastReloadLocation = self.CI_CurrentLocation()

		for block in self.Blocks:
			len_mod_4 = len(block) % 4
			if len_mod_4 != 0:
				# oops, not quad word aligned
				block.append( [0] * (4 - len_mod_4))

			# add the data
			quadword = 0
			count = 0
			length = len(block)
			for word in reversed(block):				
				word &= (1 << 29) - 1
				quadword <<= 29
				quadword |= word

				if (count % 4) == 3:
					# have a complete quadword
					self.CI_AddQuad(quadword)
					quadword = 0
					#
					# terminate quadword
					#
					# guanrantee minimum RELOAD spacing for M23
					current_loc = len(self.Image)
										
					fill_need = (LastReloadLocation + self.PT_RELOAD_GUANRANTEE) - current_loc
					self.CI_Fill(fill_need)

					# place reload, stop on last
					if count == (length - 1):
						self.Image.append(self.PT_STOP)
						LastReloadLocation = self.CI_CurrentLocation()
						self.CI_Fill(self.PT_STOP_GAP)
					else:
						self.Image.append(self.PT_RELOAD)
						LastReloadLocation = self.CI_CurrentLocation()
						self.CI_Fill(self.PT_RELOAD_PAUSE)

				count += 1

		self.CI_Fill(self.PT_TRAILER)   #  12 inches of trailer

		if len(self.Image) > self.MAXTAPESIZE:
			print 'ERROR: Exceeded max tape size: ',self.MAXTAPESIZE
			
	def CI_Fill(self, amt):
		if amt > 0:
			self.Image.extend( [self.PT_SPACE] * amt)
			
	def CI_CurrentLocation(self):
		return len(self.Image)

	def CI_AddQuad(self, quadword):
		# add the data symbols for the quadword
		for i in range(112,-1,-4):
			nibble = (quadword >> i) & 0xf
			self.Image.append( nibble | 0x10)

	def SexOutString(self, num):
		ans = '-' if num&1 else ' ';
		ans += self.data2str(num>>1, 28)
		return ans

	###########################################
	#
	# calculate block chksums
	#
	############################################

	def TwosComplement (self, x):
		if (x & 1) == 0:		# positive number
			return x
		x = - (x >> 1)
		return ( (x<<1) & 0x1FFFFFFF ) | 1

	def CreateSum(self, outfile):

		try:
			if file == sys.stdout:
				fout = sys.stdout
			else:
				fout = open(outfile, "w")
		except:
			print 'Error: Cannot write file: ', file
			sys.exit(1)

		print >>fout, 'Block\tSum'
		l = len(self.Blocks)
		for blockid in range(l):
			block = self.Blocks[blockid]
			sum = 0
			i = 10
			for word in block:
				number = self.TwosComplement (word)
				oldsign = sum & 1
				sum = (sum & ~1) + (number & ~1)
				signsum = oldsign + (number & 1) + (1 if sum & 0x20000000 else 0)
				sum = sum & 0x1FFFFFFF
				sum |= (signsum & 1)
			print >>fout, blockid, '\t', self.SexOutString(sum)

		if fout != sys.stdout:
			fout.close()
