#
# convert PTI files to .pt binary tape image
# deleting lines not formated correctly
import sys

COMPRESSED_TAPE_CODE = 0x08
def generate_gap(symbols):
	gap = [0 for num in range(symbols) ]
	return gap	

count=0

# compressed output replaces delimiters with short hand codes
# 0x0e = 6" of tape,  
# must be expanded to 60 codes before being read by g15 computer
flag_compressed_output = 0

pos=1
if sys.argv[pos] == '-c' :
	flag_compressed_output = 1
	pos += 1

outfile = sys.argv[pos]
print 'outfile=',outfile

pos += 1


def generate_gap(symbols):
	if flag_compressed_output == 1:
		return [ COMPRESSED_TAPE_CODE ]
	gap = [0 for num in range(symbols) ]
	return gap	

outarray = []
outarray.extend(generate_gap(60))		# requirement is 4" leader

for arg in sys.argv[pos:]:
	print 'processing file: ',arg
	
	file = open(arg,"r")
	
	for line in file.xreadlines():	
		line = line.rstrip()
		eol = line[-1:]
		if not (eol=='/' or eol=='S') :
			continue
		#		
		for c in line:
			num_c = ord(c)
			#
			# have a valid line, so output it
			#
			if num_c>=ord('0') and num_c<=ord('9') :
				oc = ord(c)-ord('0')+0x10
				outarray.append(oc)
				count += 1
			elif num_c>=ord('u') and num_c<=ord('z') :
				oc = ord(c)-ord('u')+0x1a
				outarray.append(oc)
				count += 1
			elif c=='-':
				outarray.append(0x1)
				count += 1
			elif c=='/':				# reload
				if count<20 :
					outarray.extend(generate_gap(20-count))				
				outarray.append(0x5)
				outarray.append(0x0)	# some tapes have space after reload
				count = 0
			elif c=='S':				# stop
				outarray.append(0x4)
				outarray.extend(generate_gap(60))			
				count = 0
			elif c=='T':				# tab
				outarray.append(0x3)
				count += 1
			elif c=='D':				# cr
				outarray.append(0x2)
				count += 1
			else :
				print 'ERROR: unknown character in file: 0x%02x'%ord(c),' ignored'
			#
#			print outarray
			#
	file.close()
	
	if c!='S' :
		print 'format error, did not end with a stop'
		outarray.extend(generate_gap(60))		# requirement is 4" trailer

#	print outarray

	file = open(outfile,"wb")
	byte_outarray = bytearray(outarray)
	file.write(byte_outarray)
	file.close()
	