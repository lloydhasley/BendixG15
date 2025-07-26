#
# in development
# DO NOT USE for production code
#
# %0 and %n formats are not supported
# emulator needs these
#
import sys

pg15_keywords = {"end=", "file=", "flush="}
pg15_hex = "0123456789uvwxyz"

pg15_file = sys.stdout
pg15_flush = False
pg15_buffer = []


def printg15_int(value, base, sign):
    # set value to absolute value
    global pg15_buffer

    neg = 0
    if sign and value < 0:
        neg = 1
        value = -value

    buffer = []
    for i in range(16):
        cint = value % base
        buffer.append(pg15_hex[cint])
    if neg:
        buffer.append('-')
    
    for c in buffer:
        pg15_buffer.append(c)


def printfg15(*args):
    global pg15_file
    global pg15_flush

    end = '\n'
    file = sys.stdout
    flush = False

    # check for keywords
    #    set keywords, place other onto list
    args1 = []
    found_keywords = []
    for arg in args:
        for keyword in pg15_keywords:
            try:
                ll = len(keyword)
                if arg[:ll] == keyword:
                    key = keyword[:-2]
                    locals()[key] = arg[ll:]
                    
                    found_keywords.append(arg)
            except:
                pass
        else:
            args1.append(arg)

    buffer = sprintfg15(args1)
    print(buffer, found_keywords)

        
def sprintfg15(*args):
    # args1 is now list of arguments minus the keywords
    global pg15_buffer

    fmt = args[0]
    args1 = args[1:]
    state = 0
    for c in fmt:  # traverse format string
        if state == 0:
            if c == '%':
                state = '%'
            else:
                pg15_buffer.append(c)
            continue
        elif state == '%':
            if c == 'd':
                printg15_int(args1[0], 10, 1)
                args1 = args1[1:]
            elif c == 'x' or c == 'p':
                printg15_int(args1[0], 16, 0)
                args1 = args1[1:]
            elif c == 's':
                for ch in args1[0]:
                    pg15_buffer.append(ch)
                args1 = args1[1:]
        elif c == 'c':
            pg15_buffer.append(args1[0][0])
            args1 = args1[1:]
        elif c == '%':
            pg15_buffer.append(c)
        else:
            print("Err: Unknown format: ", fmt)
        state = 0

#    for c in end:
#        putcg15(c)
    
    buffer = "".join(pg15_buffer)
    return buffer


# equivalent int but uses g15 hex char
# and does not bomb w illegal char, instead stops processing
def intg15(s, base=10):
    try:
        neg = 0
        if s[0] == '-':
            neg = 1
            s = s[1:]

        if base == 0:
            # need to determine base by observation
            if s[1:0] == "0x":
                base = 16
                s = s[2:]
            elif s[0] == '0':
                base = 8
    except:
        print("Error: intg15, s=", s)
        return 0

    value = 0
    for c in s:
        cint = c % base
        if cint in pg15_hex:
            value *= base
            value += pg15_hex[cint]
        else:
            break

    if neg:
        value = - value

    return value
