#
# convert PT files to .pt binary tape image
#
# note files have column reversed

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
file_contents = file.read()
file.close()

numbers = []
for char in file_contents:
	numbers.append(ord(char))

outarray = []

# validate column reversal
count0 = 0
count4 = 0
for number in numbers :

	# count LSB and MSB
	if number&0x01 :
		count0 += 1
	if number&0x10 :
		count4 += 1
		
	# reverse the bits, just in case
	r = 0
	if number & 0x01:
		r |= 0x10
	if number & 0x02:
		r |= 0x08
	if number & 0x04:
		r |= 0x04
	if number & 0x08:
		r |= 0x02
	if number & 0x10:
		r |= 0x01
	outarray.append(r)
	
# list numbers has original data
# list outarray has column reverse data
		
if count4>count0 :
	print 'columns are NOT reversed'
	outarray = numbers
else:
	print 'columns are REVERSED'


file = open(outfile,"w")
byte_outarray = bytearray(outarray)
file.write(byte_outarray)
file.close()
