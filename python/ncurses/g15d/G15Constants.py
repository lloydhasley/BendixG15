
#############################################################
#
# define constants used throughout the G15 emulation
#
#
#############################################################
#
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

G15_SPACE = 0x00
G15_MINUS = 0x01
G15_CR = 0x02
G15_TAB = 0x03
G15_STOP = 0x04
G15_RELOAD = 0x05
G15_PERIOD = 0x06
G15_WAIT = 0x07
G15_DIGIT = 0x10

# io subsystem device io defs
DEV_IO_TYPE = 8
DEV_IO_PTR = 15

IO_STATUS_READY	            = 0x0
IO_STATUS_IN_TYPEWRITER     = 0xc
IO_STATUS_IN_PAPER_TYPE_IN  = 0xf
IO_STATUS_IN_CARDS          = 0xe
IO_STATUS_IN_MAG_TAPE       = 0xd
IO_STATUS_OUT_TYPE_L19      = 0x9
IO_STATUS_OUT_PUNCH_L19     = 0xa
IO_STATUS_OUT_CARDS         = 0xb
IO_STATUS_OUT_AR            = 0x8
IO_STATUS_OUT_MAG_TAPE      = 0x1
IO_STATUS_SEARCH_MAG_FORWARD = 0x5
IO_STATUS_SEARCH_MAG_REVERSE = 0x4

io_status_str = {
	IO_STATUS_READY : 				'ready',					# 0
	IO_STATUS_IN_TYPEWRITER :		'typewriter in',			# c
	IO_STATUS_IN_PAPER_TYPE_IN:		'paper tape reader', 		# f
	IO_STATUS_IN_CARDS:				'card reader', 				# e
	IO_STATUS_IN_MAG_TAPE:			'mag tape in',				# d
	IO_STATUS_OUT_TYPE_L19:			'type L19',					# 9
	IO_STATUS_OUT_PUNCH_L19:		'punch L19',				# a
	IO_STATUS_OUT_CARDS:			'card punch',				# b
	IO_STATUS_OUT_AR: 				'AR out',					# 8
	IO_STATUS_OUT_MAG_TAPE:			'mag tape out',				# 1
	IO_STATUS_SEARCH_MAG_FORWARD:	'search mag tape forward',  # 5
	IO_STATUS_SEARCH_MAG_REVERSE:	'search mag tape reverse' 	# 4
}


MASK29BIT = 0x1fffffff
MASK58BIT = (1 << 58) - 1

ioSym_to_Binary = {
	'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
	'8': 8, '9': 9, 'u': 10, 'v': 11, 'w': 12, 'x': 13, 'y': 14, 'z': 15,
	'-': 1, '\n': 2, '\t': 3, 'S': 4, 'R': 5, '.': 6, ' ': 0
}

SIM_REQUEST_UNLOCK      = 0     # unloack and allow execution thread to run
SIM_REQUEST_LOCK        = 1     # lock and prevent execution of new instructions
SIM_REQUEST_TERMINATE   = 2     # after current instruction, instruction thread is to terminate

SEMAPHORE_WAIT_TIME = 0.01		# time to wait between thread polls

DC_ON = 1                       # dc_on (start) button has been pressed
DC_OFF = 0                      # dc_off (stop) button has been pressed

TRACE_ENABLE = 1
TRACE_ACC = 2
