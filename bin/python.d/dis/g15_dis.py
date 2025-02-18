#########################################################
#
# g15 disassembler
#
# tries to be a holistic disassembler that traces through all of a program's
# possible execution threads to identfiy which words are instructions and
# which are for data
#
#
# reads a paper tape, into a block tape image
# creates a psuedo g15 drum memory image where tape blocks may be assigned.
#
# possible program execution traced.
#   mark/rets are followed.
#   drum line memory line copies are followed (must be an entire line)
#   conditional branches:
#       one branch is followed.
#       alternative branch is push'd onto stack for later tracing
#
# when a drum copy would overwrite an existing track that is being traced.
# it is rememberd,  other contexts on that track are followed first.
# when no other contexts remain, then the track copy is performed.
# thus the tape block contents
#
##########################################################

import sys
sys.path.append('../tapes')
import g15_ptape as pt
import g15_ptape_subr as PTSUBR

pt_subr = PTSUBR.g15_ptape_subr()

STATUS_UNINIT = 1       # empty memory, not written by paper tape
STATUS_INIT = 2         # contents came from tape
STATUS_EXECUTED = 4     # contents was executed
STATUS_BRANCH = 8       # contents is an executed instruction that contains a branch


class Dis:
    def __init__(self, file_pti, verbose=0):
        self.verbose = verbose
        self.unknown_count = 0      # total number of unknown instructions encoutered

        self.verbose = 1

        self.CmdLines = [0,1,2,3,4,5,19,23]
        self.cmdline = 7        # start is track 23
        self.N = 0

        # create drum memory
        self.tracks = []
        for i in range(24):
            size = 108
            if i > 19:
                size = 4
#            self.tracks.append( { 'size': size, 'tape': {} )
            self.tracks.append( { 'size': size, 'sequences':[]} )

        self.tape = pt.PaperTape()
        self.tape.ReadPti(file_pti)

        # create (tape) database
        self.db = []
        for i in range(len(self.tape.Blocks)):
            block = self.tape.Blocks[i]
            numberTrack = self.tape.CheckBlockIfNumberTrack(block)

            data = []
            for instr in block:
                entry = {'instr': instr}
                entry['decode'] = self.instr_decode(instr, len(data))
                entry['status'] = STATUS_INIT
                data.append(entry)

            for i in range(108-len(data)):
                entry = {'status':STATUS_UNINIT}
                data.append(entry)

            print("length data=", len(data))

            block = {'blockid': i, 'data': data, 'NT': numberTrack, 'sequences': [ [] ], 'graph':[]}
            self.db.append(block)

        self.block_id = 0           # current tape block index
        self.instruction_count = 0


    def extract_bits(self, value, offset, width=1, g15=True):
        if g15:
            offset -= 1

        value >>= offset
        value &= (1<<width) - 1
        return value

    def instr_decode(self, instr, L):
        # base instruction
        Deferred = self.extract_bits(instr, 29)
        T = self.extract_bits(instr, 22, 7)
        BP = self.extract_bits(instr, 21)
        N = self.extract_bits(instr, 14, 7)
        CH = self.extract_bits(instr, 12, 2)
        S = self.extract_bits(instr, 7, 5)
        D = self.extract_bits(instr, 2, 5)
        Double = self.extract_bits(instr, 1)
        ECH = CH | (Double << 2)

        decode = {'Deferred': Deferred, 'T': T, 'BP': BP, 'N': N, 'CH': CH, 'S': S, 'D': D, 'Double': Double, 'ECH': ECH }
        decode['L'] = L

        # add location specific information
        jump_mark = 1 if S == 21 and D == 31 else 0
        jump_return = 1 if S == 20 and D == 31 else 0
        jump = jump_mark or jump_return

        if Deferred:
            # deferred instruction
            Start = T
            End = Start + 1
            if Double and not jump and not (End & 1):
                End = End + 1
        else:
            # immediate instruction
            Start = L + 1
            if jump:
                End = Start + 1
            elif D == 31 and S in [24, 25, 26, 27]:
                End = L + T
            else:
                End = T - 1

        decode['L'] = L
        decode['start'] = self.normalize_time(Start)
        decode['end'] = self.normalize_time(End)
        return decode

    def trace(self):
        # start, move first block into L19, set execution point to 23:0
        self.read_tape()        # moves a block from paper tape into the drum memory

        self.trace_execute_init()
        self.trace_execute_multiple()

    def trace_execute_init(self):
        self.next_cmd_line = 7
        self.next_cmd_word_time = 0

        track = self.CmdLines[self.next_cmd_line]
        block_image = self.tracks[track]['tape']

        graph_node = {'sequence':[block_image['sequences']], 'graph':[]}
        block_image['graph'] = [graph_node]

    def trace_execute_multiple(self):
        while True:
            self.trace_execute(self.next_cmd_word_time)
            if self.instruction_count > 10:
                print("execute multiple early terminate, by count")
                break

    def trace_execute(self, L):
        # execute instruction (well sortof)
        # L = self.next_cmd_word_time

        track = self.CmdLines[self.next_cmd_line]
        block_image = self.tracks[track]['tape']
        instr_db = block_image['data'][L]

        # check if instruction already executed
        if instr_db['status'] & STATUS_EXECUTED:
            return

        # check if instruction was even written, or are we pointing at garbage
        if (instr_db['status'] & STATUS_INIT) == 0:
            print("Oops, program is trying to execute un-initialized memory")
            pass
            return

        decode = instr_db['decode']
        instr = instr_db['instr']
        instr_str = pt_subr.word2str(instr)

        print("\nProcessing instruction # ", self.instruction_count, ": @" + str(track) + ':' + str(L) + ': ', decode)

        source = decode['S']
        dest = decode['D']
        start = decode['start']
        end = decode['end']
        N = decode['N']

        self.next_cmd_word_time = N         # default
        track_copy_flag = 0
        branch = 0

        unknown = 1
        if dest == 31:
            # special
            if source in [19,22,23,31]:
                # special without any impact on instruction flow
                unknown = 0

            elif source == 20:
                # return
                self.next_cmd_line = decode['ECH']
                self.next_cmd_word_time = self.mark_time

                if self.verbose:
                    print("\tmark, to: ", self.next_cmd_line, ':', self.next_cmd_word_time)
                unknown = 0

            elif source == 21:
                self.next_cmd_line = decode['ECH']
                if decode['Deferred']:
                    self.mark_time = decode['T']
                else:
                    self.mark_time = decode['L'] + 1

                if self.verbose:
                    print("\texit, to: ", self.next_cmd_line, ':', self.next_cmd_word_time)
                unknown = 0

            else:
                print("unknown special destination instruction")
        elif dest == 27:
            branch = 1
        else:
            # data move (w/ or w/o calculation)

            # check if move entire long track track
            if (source < 20) and (start == self.normalize_time(end + 1)):
                print("\tmoving entire track", source, ' to ', dest)
                track_copy_flag = 1

                # insert old track out here
                # check if last pointer to this track
                # assumption is that we will not be backing up the tape to read it again

                # copy the track
                if dest < 20:   # ASSUMPTION is that short tracks are DATA ONLY, not instructions!!!
                    instr_db['comment'] = 'Line ' + str(source) + ' to Line ' + str(dest)
                    if 'tape' in self.tracks[source]:
                        # if we have source track, then copy it
                        self.tracks[dest]['tape'] = self.tracks[source]['tape']
            unknown = 0

        if not unknown:
            self.sequence_add_current(block_image, instr_db)
#            block_image['current_sequence'].append(instr_db)

        if unknown:
            self.unknown_count += 1
            print("Warning: unknown instruction: @", track, ':', self.N, ': ', decode)

        instr_db['status'] |= STATUS_EXECUTED
        #
        # determine if initial instruction
        #    if L0 L1, add L1 into main sequence behind L0
        #
        # if track_copy_flag and self.instruction_count == 0:
        if track_copy_flag:
            nextL = self.normalize_time(L+1)
            next_instr_db = block_image['data'][nextL]
            next_instr = block_image['data'][nextL]['instr']
            if (instr + (1<<21)) == next_instr:
                # instr #2 is 2nd move line but T=T+1
                #block_image['current_sequence'].append(instr_db)
                self.sequence_add_current(block_image, next_instr_db)
                next_instr_db['status'] |= STATUS_EXECUTED

        self.instruction_count += 1

        if branch:
            self.trace_execute_branch(block_image['data'], instr_db)

        return N

    def trace_execute_branch(self, block_image, cur_instr):
        # handles branching (ie forking) of the exectution path

        decode = cur_instr['decode']
        N = decode['N']
        L = decode['L']

        for branchL in [N, N+1]:
            block_image['sequence'][branchL].append([])
            self.trace_execute_multiple(branchL)

    def sequence_add_current(self, block, instr_db):
#        block['current_sequence'].append(instr_db)
        block['sequences'][-1].append(instr_db)

    def read_tape(self):
        # "copy" next block of tape into L19 (and L23)
        if self.db[self.block_id]['NT']:
            self.block_id += 1

        self.tracks[19]['tape'] = self.db[self.block_id]
        self.tracks[23]['tape'] = self.db[self.block_id]

    def normalize_time(self, T, modulus=108):
        T += 216                # insure positive number (108*2)
        T %= modulus            # scale back to range
        return T









def main():
    dis = Dis("diaper_reel1.pti")
    dis.trace()




main()
