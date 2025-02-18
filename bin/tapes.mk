#
# create tape images from raw source directories.
#
# syntax:
#   tapes.mk		# create the PTI images
#	tapes.mk clean	# cleans: removes the PTI images
#	tapes.mk all	# crates the PTI images and frequent derivatives
#
SDIRS="dgreen lcm lh pf ss"

CPWD=`dirname $0`
ROOT=$CPWD/../tapes
TDIR=$ROOT/images

PTIS=0
CLEAN=0
FORMATS=0

if [ $# -eq 0 ] ; then
	PTIS=1
else
	while [ $# != 0 ] ; do
		case $1 in
		ptis)
			PTIS=1
			shift
			;;
		clean)
			CLEAN=1
			shift
			;;
		all)
			PTIS=1
			FORMATS=1
			shift
			;;
		esac
	done
fi


# first clean if requested
if [ $CLEAN = 1 ] ; then
	for dir in $SDIRS
	do+: " $dir
		cd $ROOT/src/$dir
		make clean
	done
	#
	rm -rf $TDIR
fi

# second generate PTI files
if [ $PTIS = 1 ] ; then
	if [ ! -e $TDIR ] ; then
		mkdir $TDIR
	fi
	#
	for dir in $SDIRS
	do
		cd $ROOT/src/$dir
		make
	done
fi

# third generate optional tape formats
if [ $FORMATS = 1 ] ; then
	echo "Create derivative formats"
	
	cd $TDIR
	for dir in *
	do
		cd $TDIR/$dir
		for file in *.pti
		do
			fileout=`echo $file | sed -e 's/pti/sum/'`
			echo $fileout
			pti2sum -i $file -o $fileout
			#
			fileout=`echo $file | sed -e 's/pti/ptr/'`
			echo $fileout
			pti2pt -r -i $file -o $fileout
		done
	done
fi

