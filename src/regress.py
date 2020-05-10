#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Tue Oct 23 15:46:26 2018

@author: jfaskowi

copied/adapted from original code here: https://github.com/fliem/sea_zrh_rs

"""

import argparse
import json
import nibabel as nib
import numpy as np
from nilearn import input_data, image
import pandas as pd
# from scipy import signal

NUSCHOICES= ["36P", "9P", "6P", 
             "aCompCor", "24aCompCor", "24aCompCorGsr",
             "globalsig", "globalsig4", "linear" ]


# https://github.com/edickie/ciftify/blob/master/ciftify/bin/ciftify_clean_img.py#L301
# MIT License https://github.com/edickie/ciftify/blob/master/LICENSE
def image_drop_dummy_trs(nib_image, start_from_tr):
    # use nilearn to drop the number of trs from the image
    img_out = nib_image.slicer[:,:,:, start_from_tr:]
    return img_out


def nuisance_regress(inputimg, confoundsfile, inputmask, inputtr=0,
    conftype="36P", spikethr=0.25, smoothkern=6.0, discardvols=4,
    highpassval=0.008, lowpassval=0.08, confoundsjson='',
    addregressors=''):
    """
    
    returns a nibabel.nifti1.Nifti1Image that is cleaned in following ways:
        detrending, smoothed, motion parameter regress, spike regress, 
        bandpass filtered, and normalized
        
    options for motion paramter regress: 36P, 9P, 6P, or aCompCor
    
    signal cleaning params from:
        
        Parkes, L., Fulcher, B., Yücel, M., & Fornito, A. (2018). An evaluation 
        of the efficacy, reliability, and sensitivity of motion correction 
        strategies for resting-state functional MRI. NeuroImage, 171, 415-436.
        
        Ciric, R., Wolf, D. H., Power, J. D., Roalf, D. R., Baum, G. L., 
        Ruparel, K., ... & Gur, R. C. (2017). Benchmarking of participant-level
        confound regression strategies for the control of motion artifact in 
        studies of functional connectivity. Neuroimage, 154, 174-187.
    
    """

    dct = False
    if highpassval == 'cosine':
        print("using cosine basis for high pass")
        highpassval = None
        dct = True
    else:
        highpassval = float(highpassval)

    if lowpassval == 0:
        print("detected lowpassval 0, setting to None")
        lowpassval = None
    else:
        # check highpass versus low pass
        if highpassval:
            if highpassval >= lowpassval:
                print("high and low pass values dont make sense. exiting")
                exit(1)

    # extract confounds
    confounds, outlier_stats = get_confounds(confoundsfile,
                                             kind=conftype,
                                             spikereg_threshold=spikethr,
                                             confounds_json=confoundsjson,
                                             dctbasis=dct,
                                             addreg=addregressors)

    # check tr
    if inputtr == 0:
        # read the tr from the fourth dimension of zooms, this depends on the input
        # data being formatted to have the dim4 be the TR...
        tr = inputimg.header.get_zooms()[3]
        print("found that tr is: {}".format(str(tr)))

        if tr == 0:
            print("thats not a good tr. exiting")
            exit(1)

    else:
        tr = inputtr

    if inputmask is not None:
        print("cleaning image with masker")

        # masker params
        masker_params = {"mask_img": inputmask, "detrend": False,
                         "standardize": True, "low_pass": lowpassval,
                         "high_pass": highpassval, "t_r": tr,
                         "smoothing_fwhm": smoothkern, "verbose": 1, }

        # invoke masker
        masker = input_data.NiftiMasker(**masker_params)

        # perform the nuisance regression
        time_series = masker.fit_transform(inputimg, confounds=confounds.values)

        # inverse masker operation to get the nifti object, n.b. this returns a Nifti1Image!!!
        outimg = masker.inverse_transform(time_series)  # nus regress

    else:
        # no mask! so no masker
        print("cleaning image with no mask")

        clean_params = {"confounds": confounds.values,
                        "detrend": False, "standardize": True,
                        "low_pass": lowpassval, "high_pass": highpassval, 
                        "t_r": tr, }

        loadimg = image.load_img(inputimg)
        outimg = image.clean_img(loadimg, **clean_params)  # nus regress

    # get rid of the first N volumes
    # outimgtrim = image.index_img(outimg, np.arange(discardvols, outimg.shape[3]))
    if discardvols > 0:
        outimgtrim = image_drop_dummy_trs(outimg,discardvols)
    else:
        outimgtrim = outimg

    return outimgtrim, confounds, outlier_stats


def get_spikereg_confounds(motion_ts, threshold):
    """
    motion_ts = [0.1, 0.7, 0.2, 0.6, 0.3]
    threshold = 0.5
    get_spikereg_confounds(motion_ts, threshold)

    returns
    1.) a df with spikereg confound regressors (trs with motion > thershold)
       outlier_1  outlier_2
    0          0          0
    1          1          0
    2          0          0
    3          0          1
    4          0          0

    2.) a df with counts of outlier and non-outlier trs
       outlier  n_tr
    0    False     3
    1     True     2

    note, from Ciric et. al, "the conversion of FD to RMS displacement is approximately 2:1"...
    -> here we are using FD for spike thr, so a value of 0.5 is ~ to the 0.25mm RMS spike thr of 36P method

    """
    df = pd.DataFrame({"motion": motion_ts})
    df.fillna(value=0, inplace=True)  # first value is nan
    df["outlier"] = df["motion"] > threshold
    outlier_stats = df.groupby("outlier").count().reset_index().rename(columns={"motion": "n_tr"})

    df["outliers_num"] = 0
    df.loc[df.outlier, "outliers_num"] = range(1, df.outlier.sum() + 1)
    outliers = pd.get_dummies(df.outliers_num, dtype=int, drop_first=True, prefix="outlier")

    return outliers, outlier_stats


def get_confounds(confounds_file, kind="36P", spikereg_threshold=None, confounds_json='', dctbasis=False, addreg=''):
    """
    takes a fmriprep confounds file and creates data frame with regressors.
    kind == "36P" returns Satterthwaite's 36P confound regressors
    kind == "9P" returns CSF, WM, Global signal + 6 motion parameters (used in 
            Ng et al., 2016)
    kind == "aCompCor"* returns model no. 11 from Parkes
    kind == "24aCompCor"* returns model no. 7 from Parkes
    kind == "24aCompCorGsr"* returns model no. 9 from Parkes

    if spikereg_threshold=None, no spike regression is performed

    Satterthwaite, T. D., Elliott, M. A., Gerraty, R. T., Ruparel, K., 
    Loughead, J., Calkins, M. E., et al. (2013). An improved framework for 
    confound regression and filtering for control of motion artifact in the 
    preprocessing of resting-state functional connectivity data. NeuroImage, 
    64, 240?256. http://doi.org/10.1016/j.neuroimage.2012.08.052

    Parkes, L., Fulcher, B., Yücel, M., & Fornito, A. (2018). An evaluation
    of the efficacy, reliability, and sensitivity of motion correction
    strategies for resting-state functional MRI. NeuroImage, 171, 415-436.

    Ng et al. (2016). http://doi.org/10.1016/j.neuroimage.2016.03.029
    """
    if kind not in NUSCHOICES:
        raise Exception("Confound type unknown {}".format(kind))

    df = pd.read_csv(confounds_file, sep="\t")

    # check if old/new confound names
    p6cols = ''
    p9cols = ''
    if 'GlobalSignal' in df:
        print("detected old confounds names")
        # imgsignals = ['CSF', 'WhiteMatter', 'GlobalSignal']
        p6cols = ['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ']
        p9cols = ['CSF', 'WhiteMatter', 'GlobalSignal', 'X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ']
        globalsignalcol = ['GlobalSignal']
        compCorregex = 'aCompCor'
        framewisecol = 'FramewiseDisplacement'
        # de-trend the image signals
        # df['CSF'] = signal.detrend(df['CSF'])
        # df['WhiteMatter'] = signal.detrend(df['WhiteMatter'])
        # df['GlobalSignal'] = signal.detrend(df['GlobalSignal'])

    elif 'global_signal' in df:
        print("detected new confounds names")
        # imgsignals = ['csf', 'white_matter', 'global_signal']
        p6cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        p9cols = ['csf', 'white_matter', 'global_signal', 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        globalsignalcol = ['global_signal']
        compCorregex = 'a_comp_cor_'
        framewisecol = 'framewise_displacement'
        # de-trend the image signals
        # df['CSF'] = signal.detrend(df['csf'])
        # df['WhiteMatter'] = signal.detrend(df['white_matter'])
        # df['GlobalSignal'] = signal.detrend(df['global_signal'])

    else:
        print("trouble reading necessary columns from confounds file. exiting")
        exit(1)

    # extract nusiance regressors for movement + signal
    p6 = df[p6cols]
    p9 = df[p9cols]

    # 6Pder
    p6_der = p6.diff().fillna(0)
    p6_der.columns = [c + "_der" for c in p6_der.columns]
    
    # 9Pder
    p9_der = p9.diff().fillna(0)
    p9_der.columns = [c + "_der" for c in p9_der.columns]
    
    # 12P
    p12 = pd.concat((p6, p6_der), axis=1)
    p12_2 = p12 ** 2
    p12_2.columns = [c + "_2" for c in p12_2.columns]
    
    # 18P + 18P^2
    p18 = pd.concat((p9, p9_der), axis=1)
    p18_2 = p18 ** 2
    p18_2.columns = [c + "_2" for c in p18_2.columns]
    
    # 36P
    p36 = pd.concat((p18, p18_2), axis=1)

    # GSR4
    gsr = df[globalsignalcol]
    gsr2 = gsr ** 2
    gsr_der = gsr.diff().fillna(0)
    gsr_der2 = gsr_der ** 2
    gsr4 = pd.concat((gsr, gsr2, gsr_der, gsr_der2), axis=1)

    if kind == "globalsig":
        confounds = gsr
    elif kind == "globalsig4":
        confounds = gsr4
    elif kind == "36P":
        confounds = p36
    elif kind == "9P":
        confounds = p9
    elif kind == "6P":
        confounds = p6
    elif kind == "linear":
        pass
    else:
        # then we grab compcor stuff
        # get compcor nuisance regressors and combine with 12P
        aCompC = df.filter(regex=compCorregex)
        if aCompC.empty:
            print("could not find compcor columns. exiting")
            exit(1)
        elif aCompC.shape[1] > 10:

            # if the confounds json is available, read the variance explained
            # from the 'combined' 'Mask' components, and use top 5 of those
            if confounds_json:
                # read the confounds json
                with open(confounds_json, 'r') as json_file:
                    confjson = json.load(json_file)
                print('read confounds json')

                # initalize lists
                combokeys = []
                varex = []
                for key in confjson:
                    if 'Mask' in confjson[key].keys():
                        if confjson[key]['Mask'] == 'combined':
                            combokeys.append(key)
                            varex.append(confjson[key]['VarianceExplained'])

                # get the sort based on variance explained
                sortvar = np.argsort(varex)
                aCCcolnames = [combokeys[i] for i in sortvar[-5:]]
                aCompC = aCompC[aCCcolnames]

            else:
                # if there are more than 5 columns, take only the first five components
                aCCcolnames = [(''.join([compCorregex, "{:0>2}".format(n)])) for n in range(0, 5)]
                aCompC = aCompC[aCCcolnames]

        p12aCompC = pd.concat((p12, aCompC), axis=1)
        p24aCompC = pd.concat((p12, p12_2, aCompC), axis=1)

        if kind == "aCompCor":
            confounds = p12aCompC
        elif kind == "24aCompCor":
            confounds = p24aCompC
        elif kind == "24aCompCorGsr":
            confounds = pd.concat((p24aCompC, gsr4), axis=1)
        elif kind == "linear":
            pass
        else:
            # it will never get here, but assign confounds so my linter doesn't complain
            confounds = ''
            exit(1)

    if kind != "linear" :
        # add to all confounds df a linear trend
        confounds['lin'] = list(range(1, confounds.shape[0]+1))
    else : # it is "linear"
        confounds = pd.DataFrame(list(range(1, df.shape[0]+1)))

    if spikereg_threshold:
        threshold = spikereg_threshold
    else:
        # if no spike regression still call get_spikereg_confounds to get count
        # of available trs
        threshold = 99999

    # if using dctbasis, get these from confounds file and add it
    if dctbasis:
        cosconfounds = df.filter(regex='cosine')
        confounds = pd.concat((confounds, cosconfounds), axis=1)

    # any additional regressors to add?
    if addreg:
        addregtable = pd.read_csv(addreg, sep="\t")
        confounds = pd.concat([confounds, addregtable], axis=1) 

    outliers, outlier_stats = get_spikereg_confounds(df[framewisecol].values, threshold)

    if spikereg_threshold:
        confounds = pd.concat([confounds, outliers], axis=1)

    return confounds, outlier_stats


def main():

    parser = argparse.ArgumentParser(description='nusiance regression')
    parser.add_argument('fmri', type=str, help='input fmri to be denoised')
    parser.add_argument('confounds', type=str, help='input confounds file (from fmriprep)')
    parser.add_argument('-mask', type=str, help='input mask in same space as fmri',
                        default=None)
    parser.add_argument('-tr', type=float, help='tr of image (for bandpass filtering)', default=0)
    parser.add_argument('-strategy', type=str, help='confound strategy',
                        choices=NUSCHOICES,
                        default='36P')
    parser.add_argument('-spikethr', type=float, help='spike threshold value',
                        default=0.5)
    parser.add_argument('-fwhm', type=float, help='smoothing fwhm',
                        default=6.0)
    parser.add_argument('-discardvols', type=int, help='number of volumes to discard at beginning of func',
                        default=4)
    parser.add_argument('-highpass', type=str, help='high pass value, can be "cosine" for using DCT-basis',
                        default=0.008)
    parser.add_argument('-lowpass', type=float, help='low pass value',
                        default=0.08)
    parser.add_argument('-confjson', type=str, help='confound json file, output by newer version of fmriprep',
                        default=None)
    parser.add_argument('-out', type=str, help='ouput base name',
                        default='output')
    parser.add_argument('-add_regressors', type=str, help='add these regressors')

    # parse
    args = parser.parse_args()

    # print the args
    print("\nARGS: ")
    for arg in vars(args):
        print("{} {}".format(str(arg), str(getattr(args, arg))))
    print("END ARGS\n")

    # read in the data
    inputImg = nib.load(args.fmri)

    if args.mask is not None:
        inputMask = nib.load(args.mask)
    else:
        inputMask = None

    # call nuisance regress, get a nib Nifti1Image
    nrImg, outldf, outdfstat = nuisance_regress(inputImg, args.confounds,
                                                inputmask=inputMask, 
                                                inputtr=args.tr,
                                                conftype=args.strategy,
                                                spikethr=args.spikethr,
                                                smoothkern=args.fwhm,
                                                discardvols=args.discardvols,
                                                highpassval=args.highpass,
                                                lowpassval=args.lowpass,
                                                confoundsjson=args.confjson,
                                                addregressors=args.add_regressors)

    # write it
    nib.save(nrImg, ''.join([args.out, '_nuisance.nii.gz']))
    outldf.to_csv(''.join([args.out, '_outlierdf.csv']))
    outdfstat.to_csv(''.join([args.out, '_outlierstat.csv']))


if __name__ == '__main__':
    main()
