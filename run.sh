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
inPARC="null"
inCONF="null"
inOUTBASE="null"
inTR="null"
saveTS="null"

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

else
	echo "reading command line args"

	while [ "$1" != "" ]; do
	    case $1 in
	        -f | -fmri )           	shift
	                               	inFMRI=$1
	                          		checkisfile $1
	                               	;;
	        -m | -mask )    		shift
									inMASK=$1
									checkisfile $1
	                                ;;
	        -p | -parc )    		shift
									inPARC=$1
									checkisfile $1
	                                ;;
	        -c | -conf )			shift
									inCONF=$1
									checkisfile $1
	                                ;;
	        -o | -out )				shift
									inOUTBASE=$1
									checkisfile $1
	                                ;;
	        -t | -tr )				shift
									inTR=$1
	                                ;;
	       	-s | -savets )			saveTS="true"
	       							;;	
	        -h | --help )           echo "see script"
	                                exit 1
	                                ;;		
	        * )                     echo "see script"
	                                exit 1
	    esac
	    shift
	done

fi

###############################################################################
# check the inputs

if [[ ${inFMRI} = "null" ]] ||
	[[ ${inMASK} = "null" ]] ||
	[[ ${inPARC} = "null" ]] ||
	[[ ${inCONF} = "null" ]] ; then
	echo "need an fmri, mask, parc, and confounds file"
	exit 1
fi

if [[ ${inOUTBASE} = "null" ]] ; then
	inOUTBASE=${PWD}/
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

mkdir -p ${PWD}/output_regress/

cmd="python3 ${EXEDIR}/src/regress.py \
		-strategy 36P \
		-fwhm 0 \
		-out ${inOUTBASE}/output_regress/out \
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
	echo "something wrong with nusiance regression"
	exit 1
fi

mkdir -p ${PWD}/output_makemat/

cmd="python3 ${EXEDIR}/src/makemat.py \
		-space labels \
		-type correlation \
		-out ${inOUTBASE}/output_makemat/out \
		${regressFMRI} \
		${inMASK} \
		-parcs ${inPARC} \
	"
if [[ ${saveTS} = "true" ]] ; then
	cmd="${cmd} -savetimeseries"
fi
echo $cmd
eval $cmd

###############################################################################
# map output for bl

mv ${inOUTBASE}/output_regress/out_nuisance.nii.gz \
	${inOUTBASE}/output_regress/bold.nii.gz 

