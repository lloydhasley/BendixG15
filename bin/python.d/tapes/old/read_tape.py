####################################################
#
# read tape images from original sources
#		pricefuller website
#		dgreen email
#
####################################################

import argparse

byte_encodings='s-CTSR.Wxxxxxxxx0123456789uvwxyz'
#
def byte_decode(byte):
	if byte>=32 :
		decode = 's'	# error, return space
		errflag=1
	else:
		decode = byte_encodings[byte]
		errflag=0
	print 'byte=%02x'%byte,' decode=',decode,' errflag=',errflag
	return decode,errflag

#
# parse a tape image
def	ParseTape(image):
	STATE_IDLE = 0
	STATE_IN_QWORD = 1
	STATE_BETWEEN_QWORD = 2
	#
	state = STATE_IDLE
	count = 0
	errcount = 0
	quadword = []
	quadwords = []
	for byte in image:
		symbol,errflag = byte_decode(byte)
		if errflag :
			errcount += 1
		#
		if symbol=='s':						# space
			continue
		elif symbol=='S' or symbol=='R':	# reload
			quadword.append(symbol)
			quadwords.append(quadword)
			quadword = []
		elif byte>=0x10 and byte<=0x1f:		# hex digit
			quadword.append(symbol)
		elif symbol=='-':					# minus sign
			quadword.append(symbol)
		else:
			print 'unexpected symbol: ',symbol
	#
	for quadword in quadwords:
		print quadword

	if quadword != []:
		print 'Error: end of image, quad is not empty: ',quadword
	if errcount!=0 :
		print 'Error: ',errcount,' symbol errors were detected'
		
		
	
				
				

# 
# check if columns are bit swapped in binary file
def	CheckSwappedBinary(image):
	sum0 = 0
	sum4 = 0
	for byte in image:
		if (byte&0x01)!=0 :
			sum0 += 1
		if (byte&0x10)!=0 :
			sum4 += 1
	print 'sum4=',sum4
	print 'sum0=',sum0
	if sum0>sum4 :
		print 'tape image is reversed and is being fixed'
		newbytes = []
		for byte in image:
			oldbyte = byte
			newbyte=0
#			while oldbyte!=0:
			for i in range(5):
				newbyte <<= 1
				if oldbyte & 0x1:
					newbyte |= 1
				oldbyte>>=1
#			print 'byte=%02x'%byte,' newbyte=%02x'%newbyte
			newbytes.append(newbyte)
		print 'newbytes=',newbytes
		return newbytes
	else:
		return image

#
# read a binary file
def	ReadBinaryFile(filename) :
	if filename=="":
		return
		
	f = open(filename,"rb")
	try:
		bytes = f.read()
	finally:
		f.close()
	#
	image=[]
	for byte in bytes:
#		print 'byte=',byte
		image.append(ord(byte))
		
	return image
	
# read multiple binary files
def ReadBinaryFiles(inputfiles):
	image=[]
	for inputfilename in inputfiles:
		image += ReadBinaryFile(inputfilename)
	print 'image=',image
	return image
		
#
#
def main():
	parser = argparse.ArgumentParser(description='Read G15 PaperTape images')
#	parser.add_argument('-i', "--infile", help='input filename', required=False)
	parser.add_argument('-o', '--outfile', action="store", dest="outfile", help='output filename', required=False, default="")
	parser.add_argument('-b', '--binary', action="store_true", help='binary pt5 file', required=False, default=False)
	parser.add_argument('inputfiles',  type=str, nargs="+", help='one of more input filenames',default="")
	#
	args = parser.parse_args()
	#
	print args
	print 'outfile=',args.outfile
	print 'binary=',args.binary
	print 'inputfiles=',args.inputfiles
	
	if args.binary :
		image = ReadBinaryFiles(args.inputfiles)
		image = CheckSwappedBinary(image)
		image = CheckSwappedBinary(image)

		ParseTape(image)
#
#
if __name__ == "__main__":
	main()
#
#
