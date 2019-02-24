#!/usr/bin/env python3

"""
Created on Tue Oct 23 15:46:26 2018

@author: jfaskowi

copied/adapted from original code here: https://github.com/fliem/sea_zrh_rs

"""

import os
import csv
import nibabel as nib
import argparse
from nilearn import input_data, connectome
import numpy as np
import pandas as pd


def get_con_df(raw_mat, roi_names):
    """
    takes a symmetrical connectivity matrix (e.g., numpy array) and a list of roi_names (strings)
    returns data frame with roi_names as index and column names
    e.g.
         r1   r2   r3   r4
    r1  0.0  0.3  0.7  0.2
    r2  0.3  0.0  0.6  0.5
    r3  0.7  0.6  0.0  0.9
    r4  0.2  0.5  0.9  0.0
    """
    # sanity check if matrix is symmetrical
    assert np.allclose(raw_mat, raw_mat.T), "matrix not symmetrical"

    np.fill_diagonal(raw_mat, 0)
    con_df = pd.DataFrame(raw_mat, index=roi_names, columns=roi_names)
    return con_df


def extract_mat(rsimg, maskimg, labelimg, regnames=None, conntype='correlation', space='labels'):

    masker = input_data.NiftiLabelsMasker(labelimg,
                                          background_label=0,
                                          smoothing_fwhm=None,
                                          standardize=False, detrend=False,
                                          mask_img=maskimg,
                                          resampling_target=space,
                                          verbose=0)

    # Extract time series
    time_series = masker.fit_transform(rsimg)

    connobj = connectome.ConnectivityMeasure(kind=conntype)
    connmat = connobj.fit_transform([time_series])[0]

    if regnames is not None:
        reglabs = open(regnames).read().splitlines()
    else:
        # get the unique labels list, other than 0, which will be first
        reglabs = list(np.unique(labelimg.get_data())[1:].astype(np.int).astype(np.str))

    conndf = get_con_df(connmat, reglabs)

    return conndf, connmat


def main():

    parser = argparse.ArgumentParser(description='fmri -> adjacency matrix')
    parser.add_argument('fmri', type=str, help='input fmri to be denoised')
    parser.add_argument('mask', type=str, help='input mask in same space as fmri')
    parser.add_argument('-regionnames', type=str, help='single column file that contains region names')
    parser.add_argument('-space', type=str, help='space that the connectivity is computed in',
                        choices=['labels', 'data'], default='labels')
    parser.add_argument('-type', type=str, help='type of connectivity',
                        choices=['correlation', 'partial correlation', 'tangent', 'covariance', 'precision'],
                        default='correlation')
    parser.add_argument('-out', type=str, help='output base name',
                        default='output')
    parser.add_argument('-parcs', help='parcs to be used for makin\' matrices. make last arg',
                        nargs='+', required=True)

    # parse
    args = parser.parse_args()

    # print the args
    print("\nARGS: ")
    for arg in vars(args):
        print("{} {}".format(str(arg), str(getattr(args, arg))))
    print("END ARGS\n")

    # read in the data
    inputImg = nib.load(args.fmri)
    inputMask = nib.load(args.mask)

    # loop over labels provided
    for parc in args.parcs:

        print("\nmaking conn matricies for {}".format(str(parc)))

        labImg = nib.load(parc)
        conndf, connmat = extract_mat(inputImg, inputMask, labImg,
                                      conntype=args.type, space=args.space,
                                      regnames=args.regionnames)

        # format name
        baseoutname = (os.path.basename(parc)).rsplit('.nii', 1)[0]

        # write
        conndf.to_csv(''.join([args.out, '_', baseoutname, '_connMatdf.csv']))

        # format name
        baseoutname = (os.path.basename(parc)).rsplit('.nii', 1)[0]
        with open(''.join([args.out, '_', baseoutname, '_connMat.csv']), "w") as f:
            writer = csv.writer(f)
            writer.writerows(connmat)


if __name__ == '__main__':
    main()
