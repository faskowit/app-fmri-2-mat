#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Tue Oct 23 15:46:26 2018

@author: jfaskowi

copied/adapted from original code here: https://github.com/fliem/sea_zrh_rs

"""

import os
import argparse
import nibabel as nib
import numpy as np
from nilearn import input_data, connectome
import pandas as pd
import h5py


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
    assert np.allclose(raw_mat, raw_mat.T, atol=1e-04, equal_nan=True), "matrix not symmetrical"

    np.fill_diagonal(raw_mat, 0)
    con_df = pd.DataFrame(raw_mat, index=roi_names, columns=roi_names)
    return con_df


def extract_mat(rsimg, maskimg, labelimg, conntype='correlation', space='labels', savets=False, nomat=False):

    masker = input_data.NiftiLabelsMasker(labelimg,
                                          background_label=0,
                                          smoothing_fwhm=None,
                                          standardize=False, detrend=False,
                                          mask_img=maskimg,
                                          resampling_target=space,
                                          verbose=0)

    # get the unique labels list, other than 0, which will be first
    reginparc = np.unique(labelimg.get_fdata())[1:].astype(np.int)
    reglabs = list(reginparc.astype(np.str))

    # Extract time series
    time_series = masker.fit_transform(rsimg)

    if nomat:
        connmat = None
        conndf = None
    else:
        connobj = connectome.ConnectivityMeasure(kind=conntype)
        connmat = connobj.fit_transform([time_series])[0]
        conndf = get_con_df(connmat, reglabs)


    # if not saving time series, don't pass anything substantial, save mem
    if not savets:
        time_series = 42

    return conndf, connmat, time_series, reginparc


def main():

    parser = argparse.ArgumentParser(description='fmri -> adjacency matrix')
    parser.add_argument('fmri', type=str, help='input fmri to be denoised')
    parser.add_argument('mask', type=str, help='input mask in same space as fmri')
    parser.add_argument('-space', type=str, help='space that the connectivity is computed in',
                        choices=['labels', 'data'], default='labels')
    parser.add_argument('-type', type=str, help='type of connectivity',
                        choices=['correlation', 'partial correlation', 'covariance'],
                        default='correlation')
    parser.add_argument('-out', type=str, help='output base name',
                        default='output')
    parser.add_argument('-savetimeseries', help='also save average time series from each roi in parcellation',
                        action="store_true")
    parser.add_argument('-nomatrix', help='if you dont want to compute matix (because you just want time series)',
                        action="store_true")
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
    inputimg = nib.load(args.fmri)
    inputmask = nib.load(args.mask)

    # if args.savetimeseries:
    #    # initialize an hd5 group
    #    h5file = h5py.File(''.join([args.out, '_timeseries.hdf5']), "w")
    #    h5filegroup = h5file.create_group('timeseries')

    # loop over labels provided
    for parc in args.parcs:

        print("\nmaking conn matricies for {}".format(str(parc)))

        labimg = nib.load(parc)
        conndf, connmat, times, regions = extract_mat(inputimg, inputmask, labimg,
                                                      conntype=args.type, 
                                                      space=args.space,
                                                      savets=args.savetimeseries,
                                                      nomat=args.nomatrix)

        # format name
        baseoutname = (os.path.basename(parc)).rsplit('.nii', 1)[0]

        if conndf is not None:
            # write
            conndf.to_csv(''.join([args.out, '_', baseoutname, '_', ''.join(args.type.split()), '_connMatdf.csv']), float_format='%.3g')

        # # format name
        # with open(''.join([args.out, '_', baseoutname, '_connMat.csv']), "w") as f:
        #     writer = csv.writer(f)
        #     writer.writerows(connmat)

        # also write out time series if requested
        if args.savetimeseries:

            # this method closes file: https://stackoverflow.com/questions/29863342/close-an-open-h5py-data-file
            with h5py.File(''.join([args.out, '_', baseoutname, '_timeseries.hdf5']), "w")as h5f:
                h5f.create_dataset('timeseries',
                                   data=times,
                                   compression="gzip")
                h5f.create_dataset('regionids',
                                   data=np.array(regions))


if __name__ == '__main__':
    main()
