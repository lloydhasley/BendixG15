#
# convert PT binary files to .pti ascii tape image
#

import sys

def generate_gap(symbols):
	gap = [0 for num in range(symbols) ]
	return gap	

outarray = []

outarray.extend(generate_gap(60))		# requirement is 4" leader

count=0
#args = sys.argv[1:]
outfile = sys.argv[1]
print 'outfile=',outfile
infile = sys.argv[2]
print 'processing file: ',infile

file = open(infile,"rb")
outarray = []

file_contents = file.read()
for char in file_contents:
	num_c = ord(char)	
#	print 'c= 0x%02x'%num_c
	#
	# have a valid line, so output it
	#
	if num_c==0x0 :				# space, ignore
		continue
	elif num_c>=0x10 and num_c<=0x19 :
		oc = str(num_c - 0x10)
		outarray.append(oc)
	elif num_c>=0x1a and num_c<=0x1f :
		oc = str(unichr( num_c - 0x1a + ord('u')))
		outarray.append(oc)
	elif num_c==0x1:			# minus
		oc= '-'
		outarray.append('-')
	elif num_c==0x5:			# reload
		outarray.append('/')
		outarray.append('\n')
	elif num_c==0x4:			# stop
		outarray.append('S')
		outarray.append('\n')
		outarray.append('\n')
	elif num_c==0x3:			# tab
		outarray.append('T')
	elif num_c==0x2:			# Cr
		outarray.append('D')

	else :
		print 'ERROR: unknown character in file: 0x%02x'%num_c,' ignored'
	#
#			print outarray
	#
file.close()

file = open(outfile,"w")
byte_outarray = bytearray(outarray)
file.write(byte_outarray)
file.close()
