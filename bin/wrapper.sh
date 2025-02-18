#
# generic wrapper
#
# calls equivalent python script
#
#
# notes:
#   all functionality has been moved from shell scripts to python scripts
#
# underlyiing python scripts are located in
# 1) python.d/tapes/<script>.py
# 2) python.d/<script>/<script.py>          if multiple files

PYTHON_DIR=python.d          # where are the python scripts relative to this script
PVERS_EXPECTED=3
TARGETDIRS="tapes"			# one or more sub directories

PROGRAM=`basename $0`
PROGRAM_DIR=`dirname $0`

#
# add bin/scripts directory to path, if not already there
#
PATH_TEST=`which $PROGRAM 2>/dev/null`
if [ "$PATH_TEST" = "" ] ; then
    export PATH="$PROGRAM_DIR:$PATH"
fi

#
# check version of python
#  
# do we have executable of correct name
PYTHON_EXE="python"$PVERS_EXPECTED
PYTHON=`which $PYTHON_EXE 2>/dev/null`
if [ "$PYTHON" == "" ] ; then
    echo "ERROR: Cannot locate " $PYTHON_EXE
    exit 1n
fi

# ask executable to verify version
PVERS=$(python3 -V 2>&1 | cut -d ' ' -f2 | head -c 1)
if [ $PVERS != $PVERS_EXPECTED ] ; then
    echo "ERROR: Incorrect python version"
    echo "  expected: " $PVERS_EXPECTED
    echo "    actual: " $PVERS
    exit 1
fi

#
# find the specified python script
#
EXE=$(echo $PROGRAM | sed -e 's/\./_/g')
targetdirs="$TARGETDIRS $EXE"
for targetdir in $targetdirs
do
	PEXE=$PROGRAM_DIR/$PYTHON_DIR/$targetdir/$EXE.py
	if [ -r $PEXE ] ; then
		#
		# have it, so execute
		#
		CMDLINE="$PEXE $*"
		$PYTHON_EXE $CMDLINE
		exit 0	
	fi
done

