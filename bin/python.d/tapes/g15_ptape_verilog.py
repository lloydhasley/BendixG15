
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

		print('//', file=fout)
		print('// created: ', tstr, file=fout)
		print('// ', file=fout)
		print('`timescale 1 ns / 100 ps', file=fout)
		print('', file=fout)
		print('module ', modname, ' (', file=fout)
		print('\tinput\t\t['+str(upperIndex)+':0]\tPaperTapeAddress,', file=fout)
		print('\toutput\treg\t[4:0]\tPaperTapeData', file=fout)

		print(');', file=fout)

	def WriteVerilogBody(self,  fout, image ):
		print('', file=fout)
		print('always @*', file=fout)

		print('\tcase(PaperTapeAddress) // synthesis full_case parallel_case', file=fout)

		count0 = 0
		for ii in range(len(image)):
			value = image[ii]
			if( value == 0):
				if( count0 == 0 and ii != 0):
					print("\t\t//", file=fout)
				count0 = count0 + 1
				continue
			else:
				count0 = 0
			print("\t\t"+str(self.VERILOGADDRESSBITS)+"'d"+str(ii)+":\tPaperTapeData = 5'h%02x;"%value, file=fout)

		value = 0;      # default is null (ignored by G15)
		print("\t\tdefault:\tPaperTapeData = 5'h%02x;"%value, file=fout)
		print('\tendcase', file=fout)

	def WriteVerilogTrailer(self, fout ):
		print('', file=fout)
		print('endmodule ', file=fout)
		print('', file=fout)

	def WriteVerilog(self,  file, image, modname):
	
		try:
			if file == sys.stdout:
				fout = sys.stdout
			else:
				fout = open(file, "w")
		except:
			print('Error: Cannot write file: ', outfile)
			sys.exit(1)

		# create binary database from the word database
		self.CreateImage()

		self.WriteVerilogHeader( fout , modname)
		self.WriteVerilogBody( fout, image )
		self.WriteVerilogTrailer( fout )
		fout.close()
	