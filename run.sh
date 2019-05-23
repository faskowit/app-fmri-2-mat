#!/bin/bash

# TODO 
# give user more control over parameters

#set -e
#set -x

function checkisfile {

	inFile=$1
	if [[ ! -f ${inFile} ]] ; then
		echo "file does not exist: $inFile"
		exit 1
	fi
}

EXEDIR=$(dirname "$(readlink -f "$0")")/

echo "PWD: $(pwd)"
echo "ls pwd dir read--> "
ls -dl ${PWD}

###############################################################################

inFMRI="null"
inMASK="null"
# inPARC="null"
inCONF="null"
inOUTBASE="null"
inTR="null"
saveTS="null"
inDISCARD="null"
inSPACE="null"

# initialize this to be an array so we can add multiple parcs via cmd line
inPARC=()

###############################################################################
# read input from config.json
# starting off with basic options here

if [[ "$#" -lt 4 ]] ; then 
	echo "need at least 4 arguments: fmri, mask, parc, conf"
	echo "will hopefully find these in config.json."
	echo "or else I'll complain"
fi

if [[ -f config.json ]] ; then
	# roll with config.json
	echo "reading config.json"

	inFMRI=`jq -r '.fmri' config.json`
	inMASK=`jq -r '.mask' config.json`
	inPARC=`jq -r '.parc' config.json`
	inCONF=`jq -r '.confounds' config.json`
	inTR=`jq -r '.tr' config.json`
	saveTS=`jq -r '.savets' config.json`
	inDISCARD=`jq -r '.discardvols' config.json`
	inSPACE=`jq -r '.inspace' config.json`

else
	echo "reading command line args"

	while [ "$1" != "" ]; do
	    case $1 in
	        -f | -fmri ) shift
	                               	inFMRI=$1
	                          		checkisfile $1
	                               	;;
	        -m | -mask ) shift
									inMASK=$1
									checkisfile $1
	                                ;;
	        -p | -parc ) shift
									checkisfile $1
									# add to list
									inPARC[${#inPARC[@]}]=$1
	                                ;;
	        -c | -conf ) shift
									inCONF=$1
									checkisfile $1
	                                ;;
	        -o | -out ) shift
									inOUTBASE=$1
									#checkisfile $1
	                                ;;
	        -t | -tr ) shift
									inTR=$1
	                                ;;
	        -d | -discard ) shift
									inDISCARD=$1
	                    			;;
            -e | -space ) shift
									inSPACE=$1
	                    			;;
	       	-s | -savets )			saveTS="true"
	       							;;	
	        -h | --help )           echo "see script"
	                                exit 1
	                                ;;
            -regressextra )	shift
									REXTRA="${REXTRA} $1 $2" ; shift
									;;
			-makematextra )	shift
									MEXTRA="${MEXTRA} $1 $2" ; shift
            						;;	
	        * )                     echo "see script"
	                                exit 1
	    esac
	    shift #this shift "moves up" the arg in after each case
	done

fi

###############################################################################
# check the inputs

if [[ ${inFMRI} = "null" ]] ||
	[[ ${inMASK} = "null" ]] ||
	[[ ${inPARC} = "null" ]] ||
	[[ ${inCONF} = "null" ]] ; then
	echo "ERROR: need an fmri, mask, parc, and confounds file" >&2;
	exit 1
fi

if [[ ${inOUTBASE} = "null" ]] ; then
	inOUTBASE=${PWD}/
fi

if [[ ${inDISCARD} = "null" ]] ; then
	inDISCARD=4 
fi

# https://stackoverflow.com/questions/806906/how-do-i-test-if-a-variable-is-a-number-in-bash
re='^[0-9]+$'
if ! [[ ${inDISCARD} =~ $re ]] ; then
   echo "ERROR: discard vols not an integer" >&2; 
   exit 1
fi

if [[ ${inSPACE} = "null" ]] ; then
	inSPACE="data"
fi

if [[ ${inSPACE} != "data" ]] && [[ ${inSPACE} != "labels" ]] ; then
	echo "ERROR: space can only be 'data' or 'labels'" >&2; 
	exit 1
fi

###############################################################################
# try to get repeition time if not provided

if [[ ${inTR} = "null" ]] ; then

	blJson=$(dirname ${inFMRI})/.brainlife.json

	if [[ -f ${blJson} ]] ; then
		getTr=$(jq -r '.meta.RepetitionTime' ${blJson})
		if [[ ${getTr} != "null" ]] ; then
			inTR=${getTr}
		fi
	else
		echo "blJson not found, not reading TR from here"
	fi
fi

###############################################################################
# run it

mkdir -p ${inOUTBASE}/output_regress/

cmd="python3 ${EXEDIR}/src/regress.py \
		-strategy 36P \
		-fwhm 0 \
		-out ${inOUTBASE}/output_regress/out \
		-discardvols ${inDISCARD} \
		${REXTRA} \
		${inFMRI} \
		${inMASK} \
		${inCONF} \
	"
if [[ ${inTR} != "null" ]] ; then
	cmd="${cmd} -tr ${inTR}"
fi
echo $cmd
eval $cmd

regressFMRI=${inOUTBASE}/output_regress/out_nuisance.nii.gz

if [[ ! -f ${regressFMRI} ]] ; then
	echo "ERROR: something wrong with nusiance regression" >&2; 
	exit 1
fi

# loop through the pars provided. output is storred based on name of parc
for (( i=0; i<${#inPARC[@]}; i++ )) ; do

	mkdir -p ${inOUTBASE}/output_makemat/

	echo ; echo "making matrix $((i+1)) from parc: ${inPARC[i]}" ; echo

	cmd="python3 ${EXEDIR}/src/makemat.py \
			-space ${inSPACE} \
			-type correlation \
			-out ${inOUTBASE}/output_makemat/out \
			${MEXTRA}
			${regressFMRI} \
			${inMASK} \
			-parcs ${inPARC[i]} \
		"
	if [[ ${saveTS} = "true" ]] ; then
		cmd="${cmd} -savetimeseries"
	fi
	echo $cmd
	eval $cmd
done

###############################################################################
# map output for bl

mv ${inOUTBASE}/output_regress/out_nuisance.nii.gz \
	${inOUTBASE}/output_regress/bold.nii.gz 

