#
# take a reverse tape image from a paper document
# and generate a tape image binary file
#
import argparse
import sys
import re

# source_file = "diaper.txt"
# out_file = 'diaper.ptw'
DEBUG = 0


start_id = 'START_OF_BLOCK'
end_id = 'END_OF_BLOCK'
FIRSTOPTIONAL = 1
MAXADDR = 108
MASK29BIT = (1 << 29) - 1


class TapeOcr:
    def __init__(self, nt_flag):
        self.block = []
        self.tape = []

        self.map_g15hex_to_binary = "0123456789uvwxyz"
        self.pattern_g15num = re.compile(r'[\-]*[0-9u-z]+$')

        if nt_flag:
	        self.addNT()

        self.linecount = 0
        self.line = ''
        self.errorcount = 0
        self.line_id = 0
        self.test_id = 0
        self.stats = {}
        
    def init_tape_block(self):
        self.block = [-1] * 108
        self.stats_clear()

    def addNT(self):
    	print 'adding NT'
        nt = self.CreateNumberTrack();
        self.block = nt
        self.tape.append(nt)
        chksum_str = self.chksum(self.block)
        print 'chkchksum: test: ', -1, ' line: ', -1, ' chksum: ', chksum_str

    def CreateNumberTrack(self):
        nt = []
        for i in range(1, 108):
            word = 1 << 28
            word |= i << 13
            word |= i << 21
            nt.append(word)
        nt.append(0x2828f29)

        return nt

    def store(self, addr, data):
        if addr > MAXADDR:
            print 'error, address is too big: ', addr
            self.syntax_error()
            return

        if addr < 0:
            print 'error, address is negative??: ', addr
            self.syntax_error()
            return

        if (data != (data & MASK29BIT)) or data < 0:
            print ' data = %08x' % data, ' dataM = %08x' % (data & MASK29BIT)
            print 'error, data is in error,ignored: %x' % data
            self.syntax_error()

        if self.block[addr] != -1:
            print 'error: address used twice: ', addr
            self.syntax_error()

        self.block[addr] = data

    def write_tape(self, filename):
        try:
            fout = open(filename, "w")
        except IOError:
            print 'Error: Cannot open file: ', filename, ' for writing'
            sys.exit(1)

        for block_id in range(len(self.tape)):
            block = self.tape[block_id]

            # validate block length
            l = len(self.tape[block_id])
            if l != MAXADDR:
                print "Error: expect block length = ", MAXADDR, ' got ', l, ' instead'

            # print out each word
            for word_id in range(MAXADDR):
                addr_str = self.bin2sexdecstr(word_id)
                word_str = self.data2str(block[word_id], 29)
                out_str = "%02d" % block_id + " " + addr_str + " " + word_str
                print >>fout, out_str
            print >>fout

    def data2str(self, data, width):
        data_str = ""
        digits = int((width + 3) / 4)
        for i in range(digits):
            nibble = data & 0xf
            nibble_c = self.map_g15hex_to_binary[nibble]
            data_str = nibble_c + data_str
            data >>= 4

        return data_str

    def chksum(self, block):
        sum = 0
        for word in block:
            if word & 1:
                number = - (word >> 1)
            else:
                number = word >> 1
            sum += number

        if sum < 0:
            print 'sum is negative'
            sum = -sum
            sum &= (1 << 28) - 1
            outstr = '-' + self.data2str(sum, 28)
        else:
            sum &= (1 << 28) - 1
            outstr = ' ' + self.data2str(sum, 28)
        return outstr
        
    def stats_clear(self):
    	self.stats["unused"] = 0;
    	self.stats["instr"] = 0;
    	self.stats["bp"] = 0;
    	self.stats["u"] = 0;
    	self.stats["w"] = 0;
    	self.stats["noprefix"] = 0;
    	self.stats["L1=T"] = 0;
    	self.stats["d31"] = 0;
    	self.stats["TADJSP"] = 0;
    	self.stats["TADJDP"] = 0;
    	self.stats["TADJDP_Odd"] = 0;
    	self.stats["TADJDP_Even"] = 0;
    	self.stats["TADJ>108"] = 0;
    	self.stats["NADJ"] = 0;
    	self.stats["unused"] = 0;
    	self.stats["immed"] = 0;
    	
    def stats_print(self):
    	outstr = ''
    	for key, value in self.stats.iteritems():
    		outstr += ' ' + key + ':' + str(value)
    	print 'stats: ', outstr

    def end_of_block(self):
        block_id = len(self.tape)

        print 'block = ', block_id
        print '\ttest = ', self.test_id
        print '\tline = ', self.line_id
        
        self.stats_print()
                                # self.store(len(self.values), value)
        if len(self.values) != 0:
			if len(self.values) != 108:
				print 'error: incomplete tape block detected'
			for i in range(len(self.values)):
				self.store(i, self.values[i])
        else:
        
            unused_str = ''
            for i in range(MAXADDR):
                if self.block[i] == -1:
                    # unused word
                    if unused_str != '':
                         unused_str += ' '
                    unused_str += "%02d" % i
                    self.block[i] = 0
                    self.stats["unused"] += 1

            if unused_str == '':
                unused_str = 'None'
            print '\tunused locations: ', unused_str
		
        # overflow????
        chksum_str = self.chksum(self.block)
        print 'chkchksum: test: ', self.test_id, ' line: ', self.line_id, ' chksum: ', chksum_str

        self.tape.append(self.block)

    def syntax_error(self):
        print "Error: line # ", self.linecount, " Unknown line format: ", self.line
        self.errorcount += 1

    def bin2sexdecstr(self, value):
        tens = value/10
        if(tens > 10):
            print 'error, sexidecimal value exceeded: ', value
            return 'ER'
        outstr = self.map_g15hex_to_binary[tens] + self.map_g15hex_to_binary[value % 10]
        return outstr

    def sexdecimal2binary(self, decimal_str, maxvalue):
        # convert secdecimal (00-u7) string to integer
        if maxvalue < 0:
            if len(decimal_str) != 0:
                print 'error: expected zero length field, got: ', decimal_str
                self.syntax_error()
            return - 1

        num = -1
        if len(decimal_str) < 1:
            print 'error: expected field, got null field'
            self.syntax_error()
            return -1

        if len(decimal_str) < 2:
            decimal_str = '0' + decimal_str

        if len(decimal_str) > 2:
            self.syntax_error()
            return -1

        # first digit
        i = self.map_g15hex_to_binary.find(decimal_str[0])
        if i != -1:
            num = i
        else:
            print 'error: first digit, str=', decimal_str
            self.syntax_error()

        # second digit
        i = self.map_g15hex_to_binary.find(decimal_str[1])
        if i != -1:
            num *= 10
            num += i
        else:
            print 'error: second digit, str=', decimal_str
            self.syntax_error()

        # validate num is within allowable range
        if -1 < maxvalue < num:
            num = -1

        return num

    def convert(self, ilist, maxlist, flag):
        # convert list of secadecimal strings to list of integers
        olist = []
        errflag = 0

        if len(maxlist) != len(ilist):
            print 'Error: not enough valid terms'
            self.syntax_error()
            retval = [0] * len(maxlist)
            return retval

        for i in range(len(ilist)):
            if i == 0 and ilist[0] == '':
                maxvalue = -1
            else:
                maxvalue = maxlist[i]
            olist.append(self.sexdecimal2binary(ilist[i], maxvalue))

        if errflag:
            self.syntax_error()
        return olist

    def convert_g15hex(self, istr):

        num = 0
        for c in istr:
            i = self.map_g15hex_to_binary.find(c)
            if i == -1:
                self.syntax_error()
            num = num * 16 + i

        return num

    def convert_g15hex29(self, istr):
        sign = 0
        if istr[0] == '-':
            sign = 1
            istr = istr[1:]

        num = self.convert_g15hex(istr)
        num = num * 2 + sign

        return num

    @staticmethod
    def get_comment(tokens, start):
        comment = '# '
        for token in tokens[start:]:
            if comment == '':
                comment = token
            else:
                comment = comment + ' ' + token

        return comment

    # noinspection PyPep8Naming
    def parse(self, filename):
        docpage = -1
        page = -1
        block_id_txt = ""
        track_id = -1
        token1_valid_check = {'s': 1, '.': 1}
        token2_valid_check = {'u': 1, 'w': 1, '.': 1}

        try:
            filep = open(filename, "r")
        except IOError:
            print "ERROR: Cannot open file: ", filename
            sys.exit(1)

        self.linecount = 0
        for line in filep.readlines():
            self.linecount += 1
            line = line.rstrip()
            self.line = re.sub('\(', '', line)
            self.line = re.sub('\)', '', line)
            # print line
            
#            i = line.find('//')
#            if i != -1:
#            	self.line = self.line[:i]
#           	print 'line=', line

            tokens = self.line.split()
            num_tokens = len(tokens)
            if num_tokens == 0:
                continue

            if tokens[0] == "DocPage:":
                docpage = tokens[1]
                continue
            elif tokens[0] == "Page:":
                page = tokens[1]
                continue
            elif tokens[0] == "Block:":
                block_id_txt = tokens[1]
                continue
            elif tokens[0] == "Line:":
                self.line_id = tokens[1]
                continue
            elif tokens[0] == "Test:":
                self.test_id = tokens[1]
                continue
            elif tokens[0] == "Unused":
                continue

            elif tokens[0] == start_id:
                # beginning of tape bloock
                self.init_tape_block()
                self.values = []			# hold values if line is constant encoded
                self.stats_clear()
                
                continue
            elif tokens[0] == end_id:
                # end of tape bloock
                self.end_of_block()
                
                self.stats_print()
                continue

            if num_tokens >= 3 and tokens[0][0] == '.':
                # check for instruction source line
                if tokens[1][0] in token1_valid_check:
                    t1_check = True
                else:
                    t1_check = False
                if tokens[2][0] in token2_valid_check:
                    t2_check = True
                else:
                    t2_check = False

                if tokens[0][0] == '.' and t1_check and t2_check:
                    # have a source line
                    location_list = self.convert(tokens[0].split('.'), [-1, 107], 0)
                    location = location_list[1]
                    terms = tokens[2].split(',')

                    if DEBUG:
                        print 'terms=', terms

                    instr = self.convert(tokens[2].split('.'), [12, 107, 107, 7, 31, 31], FIRSTOPTIONAL)

                    if DEBUG:
                        print 'loc=', location, ' bkpoint', tokens[1], ' instr=', instr

                    comment = self.get_comment(tokens, 3)

                    BP = 0
                    if tokens[1] == 's':
                        BP = 1
                        self.stats["bp"] += 1
                    # BP = 0

                    T = instr[1] & 0x7f
                    N = instr[2] & 0x7f
                    CH = instr[3] & 0x7
                    S = instr[4] & 0x1f
                    D = instr[5] & 0x1f
                    if CH > 3:
                        SD = 1
                        CH &= 0x3
                    else:
                        SD = 0
                    
                    self.stats["instr"] += 1
                    if instr[0] == 10:		# u prefix
                        BLOCK = 1
                        self.stats["u"] += 1
                    elif instr[0] == 12:	# w prefix
                        BLOCK = 0
                        self.stats["w"] += 1
                    else:                   # no prefix
                        self.stats["noprefix"] += 1
                        if D == 31:         # special (Destination = 31)
                            BLOCK = 1
                            self.stats["d31"] += 1
                        else:               # destination < 31
                            if (location + 1) == T:
                                self.stats["L1=T"] += 1
                                if CH < 4:  # C < 4
                                    T = T + 1
                                    BLOCK = 1
                                    self.stats["TADJSP"] += 1
                                else:       # C >= 4
                                    if T & 1:
                                        # Odd T
                                        T = T + 1
                                        BLOCK = 1
                                        self.stats["TADJDP_Odd"] += 1
                                    else:
                                        # Even T
                                        T = T + 2
                                        BLOCK = 1
                                        self.stats["TADJDP_Even"] += 1
                                if T >= 108:
                                    self.stats["TADJ>108"] += 1
                                    print 'warning T was > 108'
                                    if location != 107:
	                                    T = T % 108		# ensure in range (not in manual)                    
                            else:
                                BLOCK = 0
                                self.stats['immed'] += 1

                    if N >= 108:
                        self.stats["NADJ"] += 1
                        print 'warning N is > 108'
                        if location != 107:
                            N = N % 108

                    DEFERRED = BLOCK ^ 1

                    instruction = DEFERRED << 29
                    instruction |= T << 22
                    instruction |= BP << 21
                    instruction |= N << 14
                    instruction |= CH << 12
                    instruction |= S << 7
                    instruction |= D << 2
                    instruction |= SD << 1
                    instruction >>= 1

                    if DEBUG:
                        print 'loc =', location, ' instr=%08x' % instruction

                    self.store(location, instruction)
                    continue

            if self.linecount == 2357:
                pass

            if num_tokens >= 2:
                # check for constants
                if tokens[0][0] == '.':
                    if re.match(self.pattern_g15num, tokens[1]):
                        # have valid constant
                        location_list = self.convert(tokens[0].split('.'), [-1, 107], 0)
                        location = location_list[1]
                        value = self.convert_g15hex29(tokens[1])

                        if DEBUG:
                            print 'loc=', location, ' value=%x' % value

                        comment = self.get_comment(tokens, 3)

                        self.store(location, value)
                        continue
                    else:
                        # ignore  .<addr> <comment>
                        continue

            if num_tokens == 4:
            	# ASSUMPTION is that an entire line may be written via print M19 command
            	# which will print 4/line, word 107 first down to word 00
                if self.map_g15hex_to_binary.find(tokens[0][0]) != -1:
                    for token in tokens:
                        value = self.convert_g15hex29(token)
                        # self.store(len(self.values), value)
                        # self.values.append(value)
                        self.values.insert(0,value)
                        # print 'l=',len(self.values), ' first value=%x'%self.values[0]
                    continue

            if tokens[0][0] != '.':
                continue  # throw away lines that do not start with '.'

            self.syntax_error()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', action="store", type=str, dest="OutputFile", help='specify output file')
    parser.add_argument('-i', action="store", type=str, dest="InputFile", help='specify input file')
    parser.add_argument('-p', action='store_true', help='prepend number track')
    parser.add_argument('ifiles', default=[], nargs='*')
    args = parser.parse_args()

    if args.InputFile == '':
        print 'ERROR: no input file specified'
        sys.exit(1)
    else:
        infile = args.InputFile

    if args.OutputFile == '':
        outfile = sys.stdout
    else:
        outfile = args.OutputFile

    ocr = TapeOcr(args.p)
    ocr.parse(infile)
    ocr.write_tape(outfile)
    print 'total errors detected: ', ocr.errorcount


if __name__ == "__main__":
    main()
