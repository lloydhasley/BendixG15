#
# in development
# DO NOT USE for production code
#


intg15_hex = "0123456789uvwxyz"


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
            else:
                base = 10
    except:
        print("Error: intg15, s=", s)
        return 0

    value = 0
    try:
        for c in s:
            v = intg15_hex.index(c)
            if v >= base:
                break
            value *= base
            value += v
    except:
        print("Error: intg15, s=", s)

    if neg:
        value = - value

    return value
