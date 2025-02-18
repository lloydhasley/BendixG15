#
# copies .ptw files from src directories to main tape images directory
# for later conversion to .v, .pt, and other file formats
#

import sys
import os
from shutil import copyfile

sys.path.insert(0,'./scripts')
from g15_ptape import *

def usage():
	print 'install <target_dir> <fname suffix> <filename>.....'
	sys.exit(1)

def main(debug=0):
	print sys.argv
	count = len(sys.argv)
	if count < 4:
		usage()
		
	dir_target = sys.argv[1]
	suffix = sys.argv[2]
	
	for i in range(3, count):
		src_file = sys.argv[i]
		
		if debug & 1:
			print 'src_file=', src_file
		
		if not os.path.exists(src_file):
			print 'Error: file ', src_file, ' does not exist'
			continue
		
		j = src_file.find('.')
		if j != -1:
			src_file_name = src_file[:j]
			src_file_suffix = src_file[j:]
		else:		
			src_file_name = src_file
			src_file_suffix = ''
			
		dest_file = dir_target + '/' + src_file_name + '_' + suffix + src_file_suffix

		src_time = os.path.getmtime(src_file)
		
		if os.path.exists(dest_file):
			dest_time = os.path.getmtime(dest_file)
		else:
			dest_time = 0
		
		if debug & 1:
			print 'src_time=', src_time
			print 'dest_time=', dest_time
		
		if src_time > dest_time:
			# source is newer, we need to copy
			print 'copying ', src_file, ' to ', dest_file
			copyfile(src_file, dest_file)

if __name__ == "__main__":
	main()
