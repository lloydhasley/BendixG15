#
# create tape images from raw source directories.
#
# syntax:
#   tapes.mk		# create the PTI images
#	tapes.mk clean	# cleans: removes the PTI images
#	tapes.mk all	# crates the PTI images and frequent derivatives
#

# define originating (scanned) tape images)
#SDIRS="dg lcm lh pf ss"

# locate tapes directory by locating this script
# and then looking relative
PDIR=`dirname $0`


function goto_top () {
    # go to top of G15 installation tree
    cd $(dirname "${BASH_SOURCE[0]}")
    while true
    do
        dir=`pwd`
        bdir=`basename $dir`
        if [ ${bdir:0:9} == "BendixG15" ] ; then
            # at top of user tree
            # determine if top of tape source tree is above
            cpwd=`pwd`
            cd ..
            if [ ${bdir:0:9} == "BendixG15" ] ; then
                # next level tree root exists
                echo "Sitting Tape Keeper mode"
                _DIR_TYPE_=1
            else
                _DIR_TYPE_=0            
            fi
            cd $cpwd
            break
        fi
        if [ $dir == "/" ] ; then
            break
        fi
        cd ..
    done
    echo "wd has been set to: " `pwd`
}



# change to top of g15 directory structure
cd $PDIR/..     
CPWD=`pwd`
goto_top        # go to top of g15 tree (two possible tops)

# tape directories
pwd=`pwd`
pwd1=`basename $pwd`
if [ $pwd1 == "BendixG15" ] ; then
    TAPES_DIR_SRC=../tapes/src      # if it exists
    TAPES_DIR_DEST="$pwd/tapes/images"
    TAPES_SRC_SUFFIX=".ptir"
else
    echo "Error: command not in BendixG15 directory, or below"
    exit 1
fi


TAPES_KNOWN=$CPWD/BendixG15/tapes/tapes.knowns

DERIVATIVES="ptr"
DERIVATIVES_ALL="pt ptw sum v ptr nt"

# set up handlers by name
# note: bash on Mac is version 2, ie no associated memory
#handlers="pt:pti2pt ptr:pti2ptS-r ptw:pti2ptw sum:pti2sum v:pti2v"

declare -a handlers
# note: use S to represent space
handlers[0]=pti:pti2pti
handlers[1]=pt:pti2pt
handlers[2]=ptir:ptir2pti
handlers[3]=ptw:pti2ptw
handlers[4]=sum:pti2sum 
handlers[5]=v:pti2v
handlers[6]=ptr:pti2ptS-r
handlers[7]=nt:pti2ptiS-p

function Usage () {
    echo "tapes.mk clean   --- cleans target directory"
    if [ $_DIR_TYPE_ == 1 ] ; then
        echo "tapes.mk pti     --- copies all ptir files to target directory"
    fi
    echo "tapes.mk all     --- generates all tapes types (suffixes)"
}

function find_handler () {
    OIFS=$IFS
    HANDLER=""
        
    for format in "${handlers[@]}"
    do
        IFS=":"
        
        unset sc
        declare -a sc
        read -ra sc <<< "$format"

        IFS=$OIFS

        if [ ${sc[0]} = "$1" ] ; then
            HANDLER=${sc[1]}
            # echo "handler=" ${sc[0]} ${sc[1]}
            break        
        fi
    done
    
    IFS=$OIFS
}


# removes derivative views from target directory
function do_clean () {
    echo "Note: Clean does NOT clean src directory"
    echo "      Clean does clean the target user directory"
    
    cpwd=`pwd`

    # clean target directory
    if [ -e $TAPES_DIR_DEST ] ; then
        cd $TAPES_DIR_DEST
        rm -f *NT*
        for suffix in $DERIVATIVES_ALL
        do
            rm -f *.$suffix
        done
    fi
    
    # insert other clean tasks here
    cd $cpwd
}


function do_pti () {
    if [ $_DIR_TYPE_ != 1 ] ; then
        return
    fi
    # see if target directory exists in submodule
    # (git does not create empty directories)
    if [ ! -e $TAPES_DIR_DEST ] ; then
        mkdir $TAPES_DIR_DEST
    fi
    
    # determine available src directories
    cpwd=`pwd`
    cd $TAPES_DIR_SRC
    SDIRS=`ls`
    cd $cpwd

    # for each source directory 
	for dir in $SDIRS
	do
	    dir_full=$CPWD/$TAPES_DIR_SRC/$dir
	    if [ ! -d "$dir_full" ] ; then
	        continue
	    fi

		cd $dir_full
		
		FOUND=0
		for suffix in ptir pt
		do
		    number=`ls -1 *.$suffix 2>/dev/null | wc -l 2>/dev/null`
            if [ $number -eq "0" ] ; then
                continue
            fi
		    if [ $number -eq "1" ] ; then
		        suf=`echo *.$suffix`
		        if [ $suf = "*.$suffix" ] ; then
		            continue
		        fi
		    fi
		    
		    FOUND=1
    		files=`ls *.$suffix`
    		for file in $files
    		do
    		    # file is source file
    		    # determine target file namd and directory
    		    tfilename=`echo $file | sed -e "s/.${suffix}/_${dir}.pti/"`
    		    tfile=$TAPES_DIR_DEST/$tfilename
                #
                # check if target is stale or does not exist
                if [ -f $tfile ]; then
                    if [ $tfile -nt $file ]; then
                        # target file exists and is newer
                        # do not copy
                        continue
                    fi
                fi
                
                handler=${suffix}"2pti"

                # copy and clean up the file                                                
#                find_handler $suffix
#                handler=`echo $HANDLER | sed -e 's/S/ /g'`
                
                echo $handler -i $file -o $tfile 
                $handler -i $file -o $tfile 
            done
            
            if [ $FOUND = 1 ] ; then
                break
            fi
        done
    done   
    
    cd $cpwd 
    echo "BASE PTI VIEWS COMPLETE ===="
}


function do_derivative_views () {
    # see if target directory exists in submodule
    # (git does not create empty directories)
    if [ ! -e $TAPES_DIR_DEST ] ; then
        echo "Error: Cannot locate target directory: $TAPES_DIR_DEST"
        return
    fi

    # go to target directory    
    cpwd=`pwd`
    cd $TAPES_DIR_DEST
    
    for file_pti in *.pti
    do
        # do not create double NT files
        if [[ $file_pti =~ "NT" ]] ; then
            continue
        fi
        # for creating an NT file, place in file name
        if [ "$1" = "nt" ] ; then
            file_der=`echo $file_pti | sed -e "s/.pti/_NT.pti/"`    
        else
            file_der=`echo $file_pti | sed -e "s/.pti/.$1/"`
        fi
        #
        find_handler $1
        handler=`echo $HANDLER | sed -e 's/S/ /g'`

        echo  $handler  -i $file_pti -o $file_der
        $handler  -i $file_pti -o $file_der
    done   
    
    cd $cpwd
}



if [ $# -eq 0 ] ; then
    Usage
    exit 1
fi


DERS=`echo $DERIVATIVES_ALL | sed -e 's/ / | /g'`

while [ $# != 0 ] ; do
    # check if base pti view
    if [ "$1" = pti ] ; then
        do_pti
        shift
        continue
    fi
    
    # check if DERIVATIVES_ALL
    for der in $DERIVATIVES_ALL
    do
        DONE=0
        if [ $der = $1 ] ; then
            do_derivative_views $1
            shift
            DONE=1
            break
        fi
    done
    if [ $DONE = "1" ] ; then
        continue    
    fi

    # not a derivative view
    case "$1" in
    clean)
        do_clean
        shift
        ;;
    all)
        do_pti
        for suffix in $DERIVATIVES_ALL
        do
            do_derivative_views $suffix    
        done
        shift
        ;;
    *)
        Usage
        exit 1
    esac
done



exit 0

