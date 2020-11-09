#!/bin/bash

# TODO 
# give user more control over parameters

#set -e
#set -x

# if py_bin not exported to script, use "python3"
if [[ -z ${py_bin} ]] ; then
	py_bin=python3
fi

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
inCONF="null"
inCONFJSON="null"
inOUTBASE="null"
inTR="null"
saveTS="null"
noMat="null"
inDISCARD="null"
inSPACE="null"
regStrategy="null"

# initialize this to be an array so we can add multiple parcs via cmd line
inPARC=()

###############################################################################
# read input from config.json
# starting off with basic options here

if [[ "$#" -lt 3 ]] ; then 
	echo "need at least 3 arguments: fmri, parc, conf"
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
  	inCONFJSON=`jq -r '.confjson' config.json`
	inTR=`jq -r '.tr' config.json`
	saveTS=`jq -r '.savets' config.json`
	inDISCARD=`jq -r '.discardvols' config.json`
	inSPACE=`jq -r '.inspace' config.json`
  	regStrategy=`jq -r '.strategy' config.json`

else
	echo "reading command line args"

	while [ "$1" != "" ]; do
	    case $1 in
	        -f | -fmri ) 	shift
							inFMRI=$1
							checkisfile $1
	        ;;
	        -m | -mask ) 	shift
							inMASK=$1
							checkisfile $1
	        ;;
	        -p | -parc ) 	shift
							# add to list
							inPARC[${#inPARC[@]}]=$1
	        ;;
	        -c | -conf ) 	shift
							inCONF=$1
							checkisfile $1
			;;
        	-j | -cjson ) 	shift
							inCONFJSON=$1
							checkisfile $1
			;;
	        -o | -out ) 	shift
							inOUTBASE=$1
			;;
	        -t | -tr ) 		shift
							inTR=$1
	        ;;
	        -d | -discard ) shift
							inDISCARD=$1
	        ;;
			-e | -space ) 	shift
							inSPACE=$1
	        ;;
	        -y | -strategy ) shift
							regStrategy=$1
	        ;;
	       	-s | -savets ) 
							saveTS="true"
	       	;;
	       	-n | -nomat )
							noMat="true"
			;;
	        -h | --help ) 	echo "see script"
							exit 1
	        ;;
          	-regressextra )	shift
							REXTRA="${REXTRA} $1 $2" ; shift
			;;
			-makematextra )	shift
							MEXTRA="${MEXTRA} $1 $2" ; shift
			;;
	        * ) echo "see script"
	            exit 1
	        ;;
	    esac
	    shift #this shift "moves up" the arg in after each case
	done

fi

###############################################################################
# check the inputs

if [[ ${inFMRI} = "null" ]] ||
	[[ ${inPARC[0]} = "null" ]] ||
	[[ ${inCONF} = "null" ]] ; then
	echo "ERROR: need an fmri, parc, and confounds file" >&2;
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

cmd="${py_bin} ${EXEDIR}/src/regress.py \
		-out ${inOUTBASE}/output_regress/out \
		-discardvols ${inDISCARD} \
		${REXTRA} \
		${inFMRI} \
		${inCONF} \
	"
if [[ ${inMASK} != "null" ]] ; then
	cmd="${cmd} -mask ${inMASK}"
fi
if [[ ${inTR} != "null" ]] ; then
	cmd="${cmd} -tr ${inTR}"
fi
if [[ ${regStrategy} != "null" ]] ; then
  cmd="${cmd} -strategy ${regStrategy}"
fi
if [[ ${inCONFJSON} != "null" ]] ; then
  cmd="${cmd} -confjson ${inCONFJSON}"
fi
echo $cmd
eval $cmd

regressFMRI=${inOUTBASE}/output_regress/out_nuisance.nii.gz

if [[ ! -f ${regressFMRI} ]] ; then
	echo "ERROR: something wrong with nusiance regression" >&2; 
	exit 1
fi

# EDIT: the python can handle the looping over parcs, save time by only having
# to call python once.
# loop through the pars provided. output is storred based on name of parc
# for (( i=0; i<${#inPARC[@]}; i++ )) ; do

mkdir -p ${inOUTBASE}/output_makemat/

# echo ; echo "making matrix $((i+1)) from parc: ${inPARC[i]}" ; echo

cmd="${py_bin} ${EXEDIR}/src/makemat.py \
    -space ${inSPACE} \
    -type correlation \
    -out ${inOUTBASE}/output_makemat/out \
    ${MEXTRA} \
    ${regressFMRI} \
    ${inMASK} \
    -parcs ${inPARC[*]} \
  "
if [[ ${saveTS} = "true" ]] ; then
  cmd="${cmd} -savetimeseries"
fi
if [[ ${noMat}  = "true" ]] ; then
  cmd="${cmd} -nomatrix"
fi
echo $cmd
eval $cmd

# done # for (( i=0; i<${#inPARC[@]}; i++ ))

# check if mat is made...
outFile=$(ls ${inOUTBASE}/output_makemat/out_*_connMatdf.csv)
if [[ ! -e $outFile ]] ; then
	echo "output csv file not created! error"
	exit 1
fi

###############################################################################
# map output for bl

mv ${inOUTBASE}/output_regress/out_nuisance.nii.gz \
	${inOUTBASE}/output_regress/bold.nii.gz 

# if we are running on brainlife, lets format!
if [[ -f config.json ]] ; then
		
	keyGrep=$(cat config.json | grep "key")

	if [[ ! -z ${keyGrep} ]] ; then
		# convert matcon output to brainlife neuro/cm
		${py_bin} ./generate_cm_datatype.py
		echo "generated bl cm data in ./cm"
	else
		echo "no key found in config.json, didn't do bl formatting"
	fi
fi
