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


def putcg15(ch):
    pg15_file.write(ch)
    if pg15_flush:
        pg15_file.flush()


def printg15_int(value, base, sign):
    # set value to absolute value
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


def printg15(*args):
    global pg15_file
    global pg15_flush

    end = '\n'
    file = sys.stdout
    flush = False

    # check for keywords
    #    set keywords, place other onto list
    args1 = []
    for arg in args:
        for keyword in pg15_keywords:
            try:
                ll = len(keyword)
                if arg[:ll] == keyword:
                    key = keyword[:-2]
                    locals()[key] = arg[ll:]
            except:
                pass
        else:
            args1.append(arg)

    pg15_file = file
    if isinstance(flush, str):
        if flush == "True":
            pg15_file = True
        else:
            pg15_file = False
    else:
        pg15_flush = flush

    # args1 is now list of arguments minus the keywords
    fmt = args1[0]
    args1 = args1[1:]
    state = 0
    for c in fmt:  # traverse format string
        if state == 0:
            if c == '%':
                state = '%'
            else:
                putcg15(c)
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
                    putcg15(ch)
                args1 = args1[1:]
        elif c == 'c':
            putcg15(args1[0][0])
            args1 = args1[1:]
        elif c == '%':
            putcg15(c)
        else:
            print("Err: Unknown format: ", fmt)
        state = 0

    for c in end:
        putcg15(c)


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
