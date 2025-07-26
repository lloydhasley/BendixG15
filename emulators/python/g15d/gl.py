

import sys

logprint = sys.stdout


def setlogprint(fcn):
    global logprint
    logprint = fcn
