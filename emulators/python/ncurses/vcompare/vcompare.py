#
# compare emulator vtrace output against a Verilog trace file.
#
# reports any differences.  verilog - which is passing TTR12 is to be considered
# as the golden database
#
#
import argparse
import re
import sys

ErrorCount = 0

must_match = ["RC", "TSTRT", "TSTOP", "TRK", "WTME", "DEF", "T", "N", "CH", "S", "D", \
     'BP', "EB", "IB", "LB", "AR", "PN", "ID", "MQ", "FO", "IP" ]

hex_converts = ['EB', 'IB', 'LB', 'AR', 'PN', 'ID', 'MQ']
during_d31_ignore_buses_during_source = [19, 23, 24, 25, 26, 27]    # io input channel, multiply, divide, normalize
fields_to_skip_during_d31_ignores = ["EB", "IB", "LB", "TSTOP"]
fillstr = '    '

def Error(v_db, p_db, vlines, plines, v_index, p_index):
    global ErrorCount
    print 'Missmatch error:'

    for label,line in [ ["v", vlines[v_index]], ["p", plines[p_index]] ]:
        pstr = line.lstrip()
        l = pstr.find(':')
        if l < 3:
            pstr = fillstr[:3 - l] + pstr
        print label + '= ' + pstr

    ErrorCount += 1
    if ErrorCount >= 10:
        print 'max error exceeded'
        sys.exit(1)


def VerilogMassage(v_db, v_lines):
    """
    Tweak the Verilog output.

    Remove the IO wait loops (compression)
    move forward the -0 suppress from trailing instruction into the one that caused it
    """
    print 'beginning verilog output massage'

    v_index = 0
    num_waits_removed = 0
    num_ar_minus0 = 0
    num_pn_minus0 = 0
    num_ar_print_clr = 0
    suppress_wait = 0

    print 'len vlines=', len(v_lines), ' len vdb=', len(v_db)
    while True:
        if v_index >= len(v_db):
            break

        # IO Not Ready following a type AR
        if v_db[v_index]['D'] == 31:
            if v_db[v_index]['S'] == 8:
                suppress_wait = 1
            elif v_db[v_index]['S'] == 15:
                suppress_wait = 1

        if v_db[v_index]['D'] != 31:
            suppress_wait = 0

        if v_db[v_index]['S'] == 28 and v_db[v_index]['D'] == 31:
            if v_db[v_index]['IOSTATUS'] == 0:  # and suppress_wait:
                # print 'removing: ', v_lines[v_index]
                del v_db[v_index]
                del v_lines[v_index]
                num_waits_removed += 1
                continue
            else:       # test with IOSTATUS == 1
                if v_db[v_index]['RC'] == v_db[v_index+1]['RC']:
                    del v_db[v_index]
                    del v_lines[v_index]
                    num_waits_removed += 1
                    continue
                # print 'not compressed'
                # print v_lines[v_index]

        if v_db[v_index]['S'] == 25 and v_db[v_index]['D'] == 31:
            # divide instruction
            v_db[v_index]['PN'] |= 1
            v_lines[v_index] = v_lines[v_index] + '\t## PN Adjusted (|=1)'

        if v_db[v_index]['S'] == 27 and v_db[v_index]['D'] == 31:
            # divide instruction
            v_db[v_index]['MQ'] <<= 1
            v_lines[v_index] = v_lines[v_index] + '\t## MQ Adjusted (<<1)'

        #  ARplus result was minus 0
        if v_db[v_index]['D'] == 29:
            if v_db[v_index]['AR'] == 1:  # negative 0
                v_db[v_index]['AR'] = 0
                num_ar_minus0 += 1

        #  PNplus result was minus 0
        if v_db[v_index]['D'] == 30:
            if v_db[v_index]['PN'] == 1:  # negative 0
                v_db[v_index]['PN'] = 0
                num_pn_minus0 += 1

        # type AR, test Read following (that python does not iterate), clears AR
        if v_db[v_index]['D'] == 31 and v_db[v_index]['S'] == 8:
            v_db[v_index]['AR'] = 0
            num_ar_print_clr += 1

        v_index += 1


    print 'len vlines=', len(v_lines), ' len vdb=', len(v_db)
    print 'num_waits_removed = ', num_waits_removed
    print 'num_ar_minus0 = ', num_ar_minus0
    print 'num_pn_minus0 = ', num_pn_minus0
    print 'num_ar_print_clr = ', num_ar_print_clr


def PythonMassage(p_db, p_lines):
    """
    Tweak the Python output.

    Remove the IO wait loops (compression)
    """
    print 'beginning python output massage'

    p_index = 0
    num_waits_removed = 0
    num_ar_minus0 = 0
    num_pn_minus0 = 0
    num_ar_print_clr = 0
    suppress_wait = 0

    print 'len plines=', len(p_lines), ' len pdb=', len(p_db)
    while True:
        if p_index >= len(p_db):
            break

        if p_db[p_index]['S'] == 28 and p_db[p_index]['D'] == 31 and \
                p_db[p_index]['IOSTATUS'] == 0:  # and suppress_wait:
            # if suppress_wait:
            if True:
                print 'removing: ', p_lines[p_index]
                del p_db[p_index]
                del p_lines[p_index]
                num_waits_removed += 1
                continue
            else:
                print 'not compressed'
                print p_lines[p_index]

        p_index += 1

    print 'len plines=', len(p_lines), ' len pdb=', len(p_db)
    print 'num_waits_removed = ', num_waits_removed


def Compare(v_db, p_db, vlines, plines):
    v_index = 0
    p_index = 0
    print 'verilog database has ', len(v_db), ' logged instructions'
    print 'python database has ', len(p_db), ' logged instructions'

    last_wait = 0
    while True:
        for entry in must_match:
            if v_db[v_index]['D'] == 31:
                if v_db[v_index]['S'] in during_d31_ignore_buses_during_source:
                    if entry in fields_to_skip_during_d31_ignores:
                        continue

            if v_db[v_index]['D'] == 30:
                if entry == 'PN':       # skip PN check for i vector following add (corrected sign bit)
                    continue

            if v_db[v_index][entry] != p_db[p_index][entry]:
                # error
                if entry == 'AR':
                     if (v_db[v_index][entry] & ((1<<29)-2)) == ((p_db[p_index][entry])  & ((1<<29)-2)):
                        continue
                if entry == 'PN':
                    if (v_db[v_index][entry] & ((1 << 58) - 2)) == ((p_db[p_index][entry]) & ((1 << 58) - 2)):
                        continue

                Error(v_db, p_db, vlines, plines, v_index, p_index)
                break
        v_index += 1
        p_index += 1
        if v_index >= len(v_db):
            print 'End of Verilog file detected'
            break
        if p_index >= len(p_db):
            print 'End of Python file detected'
            break

    print 'total miscompares detected: ', ErrorCount


def TraceRead(filename):
    try:
        fin = open(filename, "r")
    except IOError:
        print 'Error: Cannot open verilog trace file: ', filename

    vtrace = []
    vlines = []
    for line in fin:
        line = re.sub('[\n\r]', '', line)

        num = line.count(':')
        if num < 10:
            continue

        tokens = line.split(':')
        wordcheck = 1
        for token in tokens:
            try:
                num = int(token)
                wordcheck = 0
                break
            except:
                pass

        if wordcheck:
            # have a label line
            label = []
            for token in tokens:
                label.append(token.lstrip())
            continue
        token_count = len(label)

        # have a trace record, let's extract the fields
        tr_len = len(tokens)
        if token_count != tr_len:
            print 'Error: record length mismatch: '
            print tokens
            print label
            print 'token_count(labels)=', token_count, ' tr=', tr_len
            continue

        rec_dict = {}
        for i in range(tr_len):
            value_str = tokens[i]
            try:
                if label[i] in hex_converts:
                    value = int(value_str, 16)  # numeric, hex
                else:
                    value = int(value_str)  # numeric
            except:
                value = value_str.lstrip()  # alpha
            rec_dict[label[i]] = value
        vtrace.append(rec_dict)
        vlines.append(line)

    return vtrace, vlines


def main():
    verilog_trace_file = 'ttr12_1_v.log'
    python_trace_file = 'vtrace.log'

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-i', action='store', dest='verilog_trace_file')
    arg_parser.add_argument('-p', action='store', dest='python_trace_file')
    opts = arg_parser.parse_args()
    print 'opts=',opts

    if opts.verilog_trace_file:
        verilog_trace_file = opts.verilog_trace_file
    if opts.python_trace_file:
        python_trace_file = opts.python_trace_file

    v_db, vlines = TraceRead(verilog_trace_file)
    p_db, plines = TraceRead(python_trace_file)

    print 'Verilog log tweak...'
    VerilogMassage(v_db, vlines)

    print 'Python log tweak...'
    PythonMassage(p_db, plines)

    print 'compare begin....'
    Compare(v_db, p_db, vlines, plines)


if __name__ == "__main__":
    main()
