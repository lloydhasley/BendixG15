
#############################################################
#
# define constants used throughout the G15 emulation
#
#
#############################################################
#


WORD_SIZE = 29
WORDS_PER_TRACK = 108
BITS_PER_TRACK = WORDS_PER_TRACK * WORD_SIZE

BIT_TIME = 9.4
WORD_TIME = BIT_TIME * WORD_SIZE
TRACK_TIME = WORD_TIME * WORDS_PER_TRACK

#
# mappings for non-numeric names tracks
#
# CM=29, not used by emulator
# CN=30, number track
# note: these must in contiguous (similar to an enum)
M0 = 0
M1 = 1
M2 = 2
M3 = 3
M4 = 4
M5 = 5
M6 = 6
M7 = 7
M8 = 8
M9 = 9
M10 = 10
M11 = 11
M12 = 12
M13 = 13
M14 = 14
M15 = 15
M16 = 16
M17 = 17
M18 = 18
M19 = 19
M20 = 20
M21 = 21
M22 = 22
M23 = 23
MQ = 24
ID = 25
PN = 26
MZ = 27     # io transfers w M23, not user accessible
AR = 28
CM = 29     # command register, not user accessible
CN = 30     # Number Track, not user accessible
PN_plus = 30
D_TEST = 27

AR_Plus = 29
SPECIAL = 31

two_word_tracks = [ID, MQ, PN]

CMD_TYPE_TR = 1
CMD_TYPE_AD = 2
CMD_TYPE_TVA = 4
CMD_TYPE_AV = 8
CMD_TYPE_AVA = 16
CMD_TYPE_SU = 32

################
#
# implements the numeric coupler
#
################

FORMAT_DIGIT = 0
FORMAT_SIGN = 4
FORMAT_CR = 2
FORMAT_TAB = 6
FORMAT_STOP = 1
FORMAT_RELOAD = 5
FORMAT_PERIOD = 3
FORMAT_WAIT = 7

G15_SPACE	= 0x00
G15_MINUS	= 0x01
G15_CR		= 0x02
G15_TAB		= 0x03
G15_STOP	= 0x04
G15_RELOAD	= 0x05
G15_PERIOD	= 0x06
G15_WAIT	= 0x07
G15_DIGIT	= 0x10

# io subsystem device io defs
DEV_IO_TYPE = 8
DEV_IO_PTR = 15

#IO_STATUS_READY	            = 0x00
IO_STATUS_READY	            	= 0x10
IO_STATUS_IN_TYPEWRITER     	= 0x0c
IO_STATUS_IN_PAPER_TYPE_IN  	= 0x0f
IO_STATUS_IN_CARDS          	= 0x0e
IO_STATUS_IN_MAG_TAPE       	= 0x0d
IO_STATUS_OUT_TYPE_L19      	= 0x09
IO_STATUS_OUT_PUNCH_L19     	= 0x0a
IO_STATUS_OUT_CARDS         	= 0x0b
IO_STATUS_OUT_AR            	= 0x08
IO_STATUS_OUT_MAG_TAPE      	= 0x01
IO_STATUS_SEARCH_MAG_FORWARD	= 0x05
IO_STATUS_SEARCH_MAG_REVERSE 	= 0x04


io_status_str = {
	IO_STATUS_READY : 				'Ready',			# 0
	IO_STATUS_IN_TYPEWRITER :		'Type-In',			# c
	IO_STATUS_IN_PAPER_TYPE_IN:		'PTR-In', 			# f
	IO_STATUS_IN_CARDS:				'Card-In', 			# e
	IO_STATUS_IN_MAG_TAPE:			'MTape-In',			# d
	IO_STATUS_OUT_TYPE_L19:			'Type-L19',			# 9
	IO_STATUS_OUT_PUNCH_L19:		'Punch-L19',		# a
	IO_STATUS_OUT_CARDS:			'Card-Punch',		# b
	IO_STATUS_OUT_AR: 				'Type-AR',			# 8
	IO_STATUS_OUT_MAG_TAPE:			'MTape-Out',		# 1
	IO_STATUS_SEARCH_MAG_FORWARD:	'Search MTapeFor',	# 5
	IO_STATUS_SEARCH_MAG_REVERSE:	'Search MTapeRevm' 	# 4
}


MASK29BIT = (1 << 29) - 1
MASK58BIT = (1 << 58) - 1

ioSym_to_Binary = {
	'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
	'8': 8, '9': 9, 'u': 10, 'v': 11, 'w': 12, 'x': 13, 'y': 14, 'z': 15,
	'-': 1, '\n': 2, '\t': 3, 'S': 4, 'R': 5, '.': 6, ' ': 0
}
hex2ascii = "0123456789uvwxyz"

SIM_REQUEST_UNLOCK      = 0     # unloack and allow execution thread to run
SIM_REQUEST_LOCK        = 1     # lock and prevent execution of new instructions
#SIM_REQUEST_TERMINATE   = 2     # after current instruction, instruction thread is to terminate

SEMAPHORE_WAIT_TIME = 0.01		# time to wait between thread polls


TRACE_ENABLE = 1
TRACE_ACC = 2

sw_mappings = {
	"enable": {'sw': 'enable', 
		'on': 'on', 
		'off': 'off'
	},
	"tape": {'sw': 'tape',
		'center': 'center', 'off': 'center', 
		'rew': 'rewind', 'rewind': 'rewind', 
		'punch': 'punch'
	},
	"compute": {'sw': 'compute',
		'bp': 'bp', 'left': 'bp',
		'center': 'center', 'off': 'center',
		'go': 'go', 'right': 'go', 'run': 'go'
	},
	"dc": {'sw': 'dc',
		'on': 'on',
		'off': 'off'
	}
}

cmd_line_map_names = {
	0: 'L0',
	1: 'L1',
	2: 'L2',
	3: 'L3',
	4: 'L4',
	5: 'L5',
	6: 'L19',
	7: 'L23'
}

