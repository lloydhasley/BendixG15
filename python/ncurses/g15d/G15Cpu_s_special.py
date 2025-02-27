********
code fragment from earlier version
handles special sources
kept here in case needed again later





# end of dest=31
# begin is special, dest!=31
if not True:
    if (instruction['ch'] == 0 and instruction['d'] == ID and t_odd) or \
            (instruction['ch'] == 6 and instruction['d'] == ID and t_even):
        #
        # load multiplicand or denominator
        #
        self.unverified_instruction()

        # filter
        flag = 0
        if t_even and (instruction['s'] < AR):
            flag = 1
        elif t_odd:
            flag = 1
        if instruction['s'] == PN or instruction['s'] == MQ:
            flag = 0

        if flag == 1:
            word = self.g15.drum.read(instruction['s'])
            self.g15.drum.write(ID, 0, word)
            word = self.g15.drum.read(instruction['s'] + 1)
            self.g15.drum.write(ID, 1, word)
            #
            # AR destroyed
            #
            self.g15.Drum.DrumWrite(AR, 0, 0)
            #
            return

    #
    elif (instruction['ch'] == 0 and instruction['d'] == MQ and t_odd) or \
            (instruction['ch'] == 6 and instruction['d'] == MQ and t_even):
        #
        # load multiplier
        #
        self.unverified_instruction()

        # filter
        flag = 0
        if t_even and (instruction['s'] < AR):
            flag = 1
        elif t_odd:
            flag = 1
        if instruction['s'] == ID or instruction['s'] == PN:
            flag = 0

        if flag == 1:
            word = self.g15.drum.read(instruction['s'])
            self.g15.drum.write(MQ, 0, word)
            word = self.g15.drum.read(instruction['s'] + 1)
            self.g15.drum.write(MQ, 1, word)

            # AR destroyed
            self.g15.drum.write(AR, 0, 0)

            return
    #
    elif (instruction['ch'] == 0 and instruction['d'] == PN and t_odd) or \
            (instruction['ch'] == 6 and instruction['d'] == PN and t_even):
        #
        # load numerator
        #
        self.unverified_instruction()

        # filter
        flag = 0
        if t_even and (instruction['s'] < AR):
            flag = 1
        elif t_odd:
            flag = 1
        if instruction['s'] == ID or instruction['s'] == MQ:
            flag = 0

        if flag == 1:
            word = self.g15.drum.read(instruction['s'])
            self.g15.drum.write(PN, 0, word)
            word = self.g15.drum.read(instruction['s'] + 1)
            self.g15.drum.write(PN, 1, word)

            # AR destroyed
            self.g15.Drum.DrumWrite(AR, 0, 0)

            return

    elif instruction['ch'] == 0 and instruction['s'] == 26 and \
            ((instruction['t'] % 2) == 1):
        #
        # store product
        #  (move 28 bits??)
        #
        self.unverified_instruction()

        flag = 1
        if not d_track_2_word:
            flag = 0

        if flag == 1:
            # rotate???
            reg_pn = self.g15.drum.read_2_word(PN, 0)
            self.g15.drum.write2word(instruction['d'], instruction['t'], reg_pn << 1)

            return

    elif instruction['ch'] == 0 and instruction['s'] == 24 and \
            ((instruction['t'] % 2) == 0):
        #
        # store quotient
        #  (move 29 bits??)
        #
        self.unverified_instruction()

        flag = 1
        if not d_track_2_word:
            flag = 0

        if flag == 1:
            reg_md = self.g15.drum.read_2_word(MQ, 0)
            self.g15.drum.write2word(instruction['d'], instruction['t'], reg_md)

            return

    elif instruction['ch'] == 0 and instruction['d'] == 27:
        #
        # test non-zero
        #
        self.unverified_instruction()

        data = self.g15.drum.read(instruction['s'], instruction['t'])

        if data != 0:
            instruction['next_cmd_word_time'] += 1

        return

    elif instruction['ch'] == 0 and instruction['s'] == 31:
        #
        # extract 'one' bits of word in line 21
        # that correspoind to 'one' bits of same-numbered word in line 20
        #
        # result is placed into D,t
        #
        self.unverified_instruction()

        t = instruction['t']
        word21 = self.g15.drum.read(21, t)
        word20 = self.g15.drum.read(20, t)
        self.g15.drum.write(instruction['d'], t, word21 & word20)

        return

    elif instruction['ch'] == 0 and instruction['s'] == 30:
        #
        # extract 'one' bits of word in line 21
        # that correspoind to 'zero' bits of same-numbered word in line 20
        #
        # result is placed into D,t
        #
        self.unverified_instruction()

        t = instruction['t']
        word21 = self.g15.drum.read(21, t)
        word20 = self.g15.drum.read(20, t)

        word_and = (~word21) & word20
        self.g15.drum.write(instruction['d'], t, word_and)

        return

    else:
        print 'ERROR: Unknown command (non dest=31)'
        self.unverified_instruction()
        return