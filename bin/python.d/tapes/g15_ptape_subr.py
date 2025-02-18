#
# common g15 routines
#


class g15_ptape_subr:
	def __init__(self):
		self.g15_hex = "0123456789uvwxyz"
		self.debug = 0

		self.PT_MINUS = 0x1
		self.PT_CR = 0x2
		self.PT_TAB = 0x3
		self.PT_STOP = 0x4
		self.PT_RELOAD = 0x5
		self.PT_PERIOD = 0x6
		self.PT_WAIT = 0x7
		self.PT_SPACE = 0x0

	def data2str(self, data, width):
		data_str = ""
		digits = int( (width + 3) / 4 )
		for i in range(digits):
			nibble = data & 0xf
			nibble_c = self.g15_hex[nibble]
			data_str = nibble_c + data_str
			data >>= 4

		return data_str

	def word2str(self, data):
		return self.data2str(data, 29)

	def str2word(self, data_str):
		data = 0
		for i in range(len(data_str)):
			if data_str[i] == '.':
				continue
			ii = self.g15_hex.find(data_str[i])
			if ii == -1:
				# format error
				print('Error: invalid hex number:', data_str)
				return -1

			data = data * 16 + ii

		return data

	def data2sexDecStr(self, data):
		# converts 0-107 to 0-99,u0-u7
		lower_str = self.g15_hex[data % 10]
		data = int(data / 10)

		if data >=16 :
			return 'zz'         # ummmm....

		upper_str = self.g15_hex[data]

		return upper_str + lower_str

	def sexDecStr2data(self, sexStr):
		upper = self.g15_hex.find(sexStr[0])
		lower = int(sexStr[1])

		if upper == -1:
			print('Error: bad sexStr number: ', sexStr)
			number = 0x7f
		else:
			number = upper * 10 + lower

		return number

