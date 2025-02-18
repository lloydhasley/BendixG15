#
# run length analyzer
#
#
import sys
#
#
MAXRUNLENGTH=200
#
counts = [0] * MAXRUNLENGTH
count_single_byte = [0] * 32
#
# read the file
filename = sys.argv[1]
file = open(filename,"rb")
filecontents = file.read()
file.close()
#
print len(filecontents)
#
bytes = []
for byte in filecontents :
	bytes.append(ord(byte))

# gather statistics
runlength=0
oldbyte = -1
bytes.append(-1)	# force last entry tabulation
for byte in bytes :
	if byte==oldbyte :
		runlength += 1
	else :
		if runlength != 0:	# not first entry
			if runlength >= MAXRUNLENGTH :
				print 'ERROR: runlength=',runlength,' >=',MAXRUNLENGTH,' detected'
				sys.exit(1)
			counts[runlength] += 1
		if runlength == 1 :
			count_single_byte[oldbyte] += 1
		runlength = 1
	#
#	print 'l=',runlength,' byte=',byte,' oldbyte=',oldbyte
	oldbyte = byte

# print statistics
print 'runlengths'
for i in range(MAXRUNLENGTH) :
	l = counts[i]
	if l != 0 :
		print 'rl:[',i,'] = ',l
		
for i in range(32) :
	l = count_single_byte[i]
	if l != 0 :
		print 'isolated byte:[',i,'] = ',l

	
	
#
# analyze compression options

# method 1, code for 60 spaces 
#	assumes that above all code >=60 was a space.  (very likely, but not certain)
savings = 0
for i in range(60,MAXRUNLENGTH) :
	savingpersymbol = (i - 1)
	saveingforrunlength = savingpersymbol * counts[i]
	savings += saveingforrunlength
print 'method 1: #=',savings,' %=', 100.0*savings/len(filecontents)
	
# method 2, repeat prior char until to 80 times
# effectively any runlength >=3 becomes runlength=2
savings=0
for i in range(3,MAXRUNLENGTH) :
	savingpersymbol = i - 2
	saveingforrunlength = savingpersymbol * counts[i]
	savings += saveingforrunlength
print 'method 2: #=',savings,' %=', 100.0*savings/len(filecontents)

	



