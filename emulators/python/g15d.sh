####################################
#
# script runs the g15 emulator
# default is the python version
#

TESTDIR=tests   # script files should be in current directroy or in this directory
PYTHONVER=python3
PYTHON=`which $PYTHONVER`
EMULATOR=g15d/g15d.py

Usage () {
    echo "Usage: g15.sh [-V]"
    echo
    echo "-V enables verilog trace file generation"
}

testfile () {
    PREFIX=". ./tests"
    for prefix in $PREFIX ;
    do
      filename=$prefix/$1
      if [ -e $filename ] ; then
        return
      fi
    done

    echo "Cannot locate specified script: " $filename
    exit 1
}

if [ "$PYTHON" = "" ] ; then
    echo "Python does not appear to be installed"
    exit 1
fi


OPTIONS=""
RUNFILE=""
while [ $# != 0 ] ;
do
    case $1 in
    -V)
        OPTIONS="$OPTIONS -v vtrace.log"
        shift
        ;;
    -e)
        shift
        EMULATOR=$1
        shift
        ;;
    -l)
        shift
        OPTIONS="$OPTIONS -l g15d.log"
        shift
        ;;
    *)
        testfile $1
        RUNFILE="$RUNFILE $filename"
        shift
        echo "setting runfile(s)=" $RUNFILE
    esac
done

# echo $PYTHON $EMULATOR $OPTIONS $RUNFILE
time $PYTHON $EMULATOR $OPTIONS $RUNFILE
