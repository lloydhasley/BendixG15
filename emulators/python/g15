#! /bin/bash
# G15 emulator start up script
# first look for tape directory
# either it is a child here or we need to traverse the tree upward to locate
#
# a directory name "tapes" is required.  if it is not in the local directory
# a user may specify its location, else the program will go up the tree looking
#

PRGRM=run
TESTS=""
EMULATOR=g15d/g15d.py

PYTHON=python3
TAPEDIR=tapes
VCOMPARE="-v vtrace.log"
COMPARE=$VCOMPARE     # change to "" to make default no log
LOGFILE=""
RUNSCRIPT=""
DEBUG=0

function Usage () {
  echo "Usage: $PRGM [-t <test_script>] [-T <tapedir>] [-l <logfile>] [-v] [test_script]..."
  exit 1
}

CPWD=`pwd`


while [[ $# -gt 0 ]] ; do
  echo $1
  case $1 in
  "-e" | "emulator")
    if [[ ! $# -gt 1 ]] ; then
      Usage
    fi
    EMULATOR="$2"
    shift
    shift
    ;;
  "-t" | "tapes")
    if [[ ! $# -gt 1 ]] ; then
      Usage
    fi
    TAPEDIR=$2
    shift
    shift
    ;;
  "-v" | "vcompare")
    COMPARE=$VCOMPARE
    shift
    ;;
  "-V")
    COMPARE=""
    shift
    ;;
  "-l" | "logfile")
    if [[ ! $# -gt 1 ]] ; then
      Usage
    fi
    LOGFILE=" -l $2"
    shift
    shift
    ;;
  "-f" | "scriptfile")
    if [[ ! $# -gt 1 ]] ; then
      Usage
    fi
    if [[ ! -e $2 ]] ; then
      Usage
    fi
    RUNSCRIPT="$RUNSCRIPT $2"
    shift
    shift
    ;;
  *)
    Usage
    shift
    ;;
  esac
done

if [[ $DEBUG = "1" ]] ; then
  echo "PYTHON=" $PYTHON
  echo "TAPEDIR=" $TAPEDIR
  echo "COMPARE=" $COMPARE
  echo "LOGFILE=" $LOGFILE
  echo "RUNSCRIPT=" $RUNSCRIPT
fi

# recurse upward until tapes directory is located
if [ ! -e $TAPEDIR ] ; then
  while True
  do
    curdir=`pwd`
    if [[ $curdir == '/' ]] ; then
      echo "ERROR: Cannot locate tape directory"
      exit 1
    fi
    curdirname=`dirname $curdir`
    ptapes=$curdirname/$TAPEDIR
    if [ -e $ptapes ] ; then
      break
    fi
    cd ..
  done
fi
TAPES=$ptapes

# have located a "tapes" directory
# descend into "images" if it exists
if [[ -e ${TAPES}"/images" ]] ; then
  TAPES=$TAPES/images
fi

if [[ $DEBUG = "1" ]] ; then
  echo "ptapes=" $ptapes
  echo "TAPES: " $TAPES
fi

cd $CPWD

echo $PYTHON $EMULATOR $LOGFILE $COMPARE -t $TAPES $RUNSCRIPT
time $PYTHON $EMULATOR $LOGFILE $COMPARE -t $TAPES $RUNSCRIPT

stty sane
