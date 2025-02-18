
#
# create a synthesizable verilog RTL representation of the tape image
#
# due to the FPGA design, tape images are restricted to 32K symbols
#

import argparse
import sys
import time

class g15_ptape_verilog:
	def __init__(self):
		self.VERILOGADDRESSBITS = 15
		self.Image = []
		
		# note: max tape size comes from verilog model which has a 15bit position counter
		self.MAXTAPESIZE = (2<<self.VERILOGADDRESSBITS) -2

	def WriteVerilogHeader(self,  fout, modname ):
		tstr = time.strftime("%Y-%m-%d %H:%M")
		
		upperIndex = self.VERILOGADDRESSBITS - 1

		print >>fout, '//'
		print >>fout, '// created: ', tstr
		print >>fout, '// '
		print >>fout, '`timescale 1 ns / 100 ps'
		print >>fout, ''
		print >>fout, 'module ', modname, ' ('
		print >>fout, '\tinput\t\t['+str(upperIndex)+':0]\tPaperTapeAddress,'
		print >>fout, '\toutput\treg\t[4:0]\tPaperTapeData'

		print >>fout, ');'

	def WriteVerilogBody(self,  fout, image ):
		print >>fout, ''
		print >>fout, 'always @*'

		print >>fout, '\tcase(PaperTapeAddress) // synthesis full_case parallel_case'

		count0 = 0
		for ii in range(len(image)):
			value = image[ii]
			if( value == 0):
				if( count0 == 0 and ii != 0):
					print >>fout, "\t\t//"
				count0 = count0 + 1
				continue
			else:
				count0 = 0
			print >>fout, "\t\t"+str(self.VERILOGADDRESSBITS)+"'d"+str(ii)+":\tPaperTapeData = 5'h%02x;"%value

		value = 0;      # default is null (ignored by G15)
		print >>fout, "\t\tdefault:\tPaperTapeData = 5'h%02x;"%value
		print >>fout, '\tendcase'

	def WriteVerilogTrailer(self, fout ):
		print >>fout, ''
		print >>fout, 'endmodule '
		print >>fout, ''

	def WriteVerilog(self,  file, image, modname):
		try:
			fout = open(file, 'w')
		except:
			print('Error: Cannot open file: ', file,' for writing')
			return

		# create binary database from the word database
		self.CreateImage()

		self.WriteVerilogHeader( fout , modname)
		self.WriteVerilogBody( fout, image )
		self.WriteVerilogTrailer( fout )
		fout.close()
	