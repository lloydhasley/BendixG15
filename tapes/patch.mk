#! /bin/sh
#
# some (several?) of the bendixg15 have patches that were applied
# in the field to them.  Each site was responsible for "upgrading"
# their software
#

# this file applies those patches - if we know about them.
# to tape files in our library.
#
# this file is expected to grow over time.
#
#
SDIR=images
TMPFILE=tmp.ptw

function create_derivatives {
	echo hello $1
	filebase=`echo $1 | sed -e 's/\..*//'`
	echo filebase $filebase
	
	pti2pt -r -i $1.pti -o $filebase.ptr
	pti2pt -r -p -i $1.pti -o ${filebase}_NT.ptr
	
	
}

# patch the 1000d tape obtained from David Green/Australia
function tape_1000d_dg {
	echo "in function"
	PRGMS="intercom_1000d_dg"
	for prgm in $PRGMS
	do
		sfile=$SDIR/$prgm.pti
		tfilebase=$SDIR/${prgm}_patched
		
		# convert to PTW
		pti2ptw -i $sfile -o $TMPFILE
		
		# edit PTW
		ed $TMPFILE <<%END
/08  42/
s/42.*/42 -0008u0/p
/08  50/
s/50.*/50 -v43635v/p
w
q
%END
		# convert back to PTI + derivatives
		ptw2pti -i $TMPFILE -o $tfilebase.pti
		create_derivatives $tfilebase
	done
	

}


# call the individual patches
tape_1000d_dg

