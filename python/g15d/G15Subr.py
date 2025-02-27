'''
low-level support routines, that are potentially useful in multiple places
provided routines are:

word2str(word)
        takes a 29-bit word; extracts sign and returns as a signed-string

value2str(value)
        takes a signed-valued (sign+28bits) and returns a signed-string.

str2value(str)
        take a signed string and return signed value

str2word(str)
        take a signed string and return a 29-bit word (as found in the drum)
'''

from G15Constants import *

STR_WIDTH = 8
STR_PAD = '000000000000000000000'

hex_to_ascii = '0123456789uvwxyz'
ascii_to_hex = {}

# establish cmdline index table
cmd_line_map = [0, 1, 2, 3, 4, 5, 19, 23]

IO_DEVICE_TYPEWRITER = 1
IO_DEVICE_PAPER_TAPE = 2

if False:
    IO_STATUS_READY = 0x10
    IO_STATUS_PT_REV1 = 0x06
    IO_STATUS_PT_REV2 = 0x07
    IO_STATUS_TYPE_AR = 0x08
    IO_STATUS_TYPE_M19 = 0x09
    IO_STATUS_TYPE_IN = 0x0c


# dictionary of ascii to 5-level code conversions
ascii_to_code = {		# device: 2=paper tape, 1=typwriter
    '0': {'code': 0x10, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '1': {'code': 0x11, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '2': {'code': 0x12, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '3': {'code': 0x13, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '4': {'code': 0x14, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '5': {'code': 0x15, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '6': {'code': 0x16, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '7': {'code': 0x17, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '8': {'code': 0x18, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '9': {'code': 0x19, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'u': {'code': 0x1a, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'v': {'code': 0x1b, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'w': {'code': 0x1c, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'x': {'code': 0x1d, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'y': {'code': 0x1e, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'z': {'code': 0x1f, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    ' ': {'code': 0x00, 'devices': IO_DEVICE_PAPER_TAPE},
    '\n': {'code': 0x00, 'devices': IO_DEVICE_PAPER_TAPE},
    '-': {'code': 0x01, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'C': {'code': 0x02, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '\t': {'code': 0x03, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    # since pycharm eats tabs in its console
    't': {'code': 0x03, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    's': {'code': 0x04, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'S': {'code': 0x04, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '/': {'code': 0x05, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'r': {'code': 0x05, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    'R': {'code': 0x05, 'devices': IO_DEVICE_TYPEWRITER | IO_DEVICE_PAPER_TAPE},
    '.': {'code': 0x06, 'devices': IO_DEVICE_PAPER_TAPE},
    'W': {'code': 0x07, 'devices': IO_DEVICE_PAPER_TAPE}
}

code_to_ascii = {}


def subr_init():
    ''' initialize subr conversions '''
    global ascii_to_hex
    global code_to_ascii

    # numeric digit to ascii reverse table
    for i in range(len(hex_to_ascii)):
        ascii_to_hex[hex_to_ascii[i]] = i

    # g15 5-level code to ascii reverse table
    for key in ascii_to_code:
        entry = ascii_to_code[key]
        code = entry['code']
        devices = entry['devices']

        newdict = {'ascii': code, 'devices': devices}
        code_to_ascii[code] = newdict
    pass

def ascii_2_code(Device, ascii):
    ''' convert ascii char to 5-level code

    :param Device:
    :param ascii:
    :return: -2 error, -1 device ignores this symbol
    '''
    if ascii not in ascii_to_code:
        return -2

    dict = ascii_to_code[ascii]

    code = dict['code']
    devices = dict['devices']

    if (Device & devices) != 0:
        return(code)
    else:
        return(-1)


def code_2_ascii(code):
    '''	convert 5-level code to ascii
    :param code:
    :return:

    only valid for typewriter
    as paper tape outputs all codes
    '''
    if code not in code_to_ascii:
        return -2

    dict = code_to_ascii[code]

    ascii = dict['ascii']
    devices = dict['devices']

    if (devices & DEV_TYPEWRITER) != 0:
        return ascii

    return -1		# typewriter ignores


def int_to_str(num):
    ''' take a signed int and convert to string '''

    signmag = int_to_signmag(num)
    ret_str = signmag_to_str(signmag)
    return ret_str


def invert29(number):
    # return 1s complement of number, clipped to 29bit
    value = (1 << 30) - number - 1
    return value


def comp2s(number, size):
    ''' generate two's complement of number '''

    value = (1 << size) - number
    value &= (1 << size) - 1

    print('int: number=0x%x' % number, 'value=0x%x' % value)

    return value


def signmag_to_str(signmag, str_width=8):
    ''' convert sign-mag number to string '''

    sign = signmag & 1
    mag = signmag >> 1

    if sign:
        sign_str = '-'
    else:
        sign_str = ' '

    ret_str = sign_str + mag_to_str(mag, str_width)

    return ret_str


def mag_to_str(num, str_width=8):
    ''' convert 28bit magnitude number to a string '''

    vstr = ''
    while num:
        str_digit = hex_to_ascii[num % 16]
        vstr = str_digit + vstr

        num >>= 4

    l = len(vstr)
    pad_length = str_width - l - 1
    if pad_length > 0:
        vstr = STR_PAD[:pad_length] + vstr

    return vstr


def str_to_signmag(text):
    l = len(text)
    if l == 0:
        return 0

    # extract sign mag nomenclature
    sign = 0
    value = 0
    for c in text:
        if c == '-':
            sign = 1
        elif c in ascii_to_code:
            entry = ascii_to_code[c]
            code = entry['code']
            if code & 0x10:
                char_value = code & 0xf
                value = value * 16 + char_value
            else:
                pass
                # self.increment_error_count('Unknown hex digit: ' + c + ' ignored')

    value = (value << 1) | (sign & 1)

    return value


def signmag_to_comp2s_29(signmag):
    ''' convert sign magnitude to 2s complement '''

    sign = signmag & 1
    mag = signmag >> 1

    if sign != 0:
        num = (~mag) + 1
    else:
        num = mag
    num &= MASK29BIT

    return num


def signmag_to_int(signmag):
    ''' convert sign magnitude notation to signed int notation '''

    sign = signmag & 1
    mag = signmag >> 1
    if sign:
        int = -mag
    else:
        int = mag

    return int

def int_plus_int(a, b):
    total = a + b
    sign = total & (1<<29)
    if sign:
        total = ((~total) + 1) & ((1<<29) - 1)
        total = -total

    print('a=',a, ' b=',b, ' total=',total)

    return total

def signmag_plus_signmag(a, b):
    # total = (a & (MASK29BIT - 1)) + (b & (MASK29BIT - 1))

    total = (a >> 1) + (b >> 1)
    total <<= 1

    sign = (a & 1) + (b & 1)
    if total & (1 << 29):
        sign += 1
    sign &= 1
    total = (total & (MASK29BIT - 1)) + sign

    return total

def int_to_signmag(value2s):
    ''' convert signed int notation to sign magnitude notation '''

    if value2s >= 0:
        #if value2s & (1<<28):
        #    # have rollover
        #    val = (~value2s) + 1
        #    sigmag = (val << 1) | 1
        #else:
        # positive number
        sigmag = value2s << 1
    else:
        # negative number
        value = -value2s
        sigmag = value << 1
        sigmag |= 1
        sigmag &= MASK29BIT

    return sigmag


def wordtime_to_str(value):
    if value > 116:
        print('INTERNAL ERROR: bad word time specified: ',value)
        value = 0

    lsd = value % 10
    value = int(value / 10)
    value_str = hex_to_ascii[value] + hex_to_ascii[lsd]

    return value_str


def str_to_wordtime(text):
    if text == '':
        return 0

    value = 0
    ll = len(text)
    for ii in range(0, ll):
        c_value = hex_to_ascii.index(text[ii])
        value = value * 10 + c_value

    return value


def bits_extract(word, width, offset):
    return (word >> offset) & ((1 << width) - 1)

#######################################
#
# convert instruction dictionary entry to a printable string
#
#######################################
#
# convert a int to a psuedo decimal number
# decimal 0-99, then u0-u6 for remainder of range
#
def instr_dec_hex_convert(number):
    #
    if number > 116:  # beyond range of S/D
        return "ER"
    else:
        FirstDigit = int(number / 10)
        SecondDigit = number % 10
        #
        return hex_to_ascii[FirstDigit] + hex_to_ascii[SecondDigit]


def instr_2_hex_string(instr):
    '''
    convert the binary encoded instruction value
    :param encoded:
    :return:

    converted the binary encoded instruction value
    to G15 SIGNED hex

    '''
    # extract sign bit (LSB)
    if instr & 1:
        out_str = '-'
    else:
        out_str = ' '

    instr >>= 1
    for i in range(7):
        j = 6 - i
        nibble = (instr >> (4 * j)) & 0xf
        out_str += hex_to_ascii[nibble]
    return out_str


