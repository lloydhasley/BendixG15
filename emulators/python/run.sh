#! /bin/bash
# G15 emulator start up script
#
# note: the program needs to know the installation directory of BendixG15
# tape images.  Users may specify the location using the -d option
# if the -d option is not given, the program will attempt to locate it
# by traversing the directories upward.
#

PYTHON=python3
EMULATOR=g15d/g15d.py
LOGFILE="-l trace.log"

echo $PYTHON $EMULATOR $LOGFILE $*
time $PYTHON $EMULATOR $LOGFILE $*

stty sane
