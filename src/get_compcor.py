#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function using nilearn to write tsv with compcor columns

@author: jfaskowi

"""

import argparse
import nibabel as nib
# import numpy as np
from nilearn import image
import pandas as pd


def runcompcor(inputimg, inputmask, prcntl, numc, detr):

    return image.high_variance_confounds(inputimg, mask_img=inputmask, percentile=prcntl,
                                         n_confounds=numc, detrend=detr)


def main():

    parser = argparse.ArgumentParser(description='nusiance regression')
    parser.add_argument('fmri', type=str, help='input fmri to extract high variance cofounds from')
    parser.add_argument('-mask', type=str, help='input mask in same space as fmri',
                        default=None)
    parser.add_argument('-prcnt', type=float, help='percentile threshold to determin highest variance voxels',
                        default=2.)
    parser.add_argument('-ncomponents', type=int, help='number of regressors to extract',
                        default=5)
    parser.add_argument('-nodetrend', help='number of regressors to extract',
                        action='store_false')
    parser.add_argument('-compcorstr', type=str, help='string to add to compcor column name',
                        default=None)
    parser.add_argument('-out', type=str, help='ouput base name', default='output')

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
    conf = runcompcor(inputImg, inputMask,
                      prcntl=args.prcnt,
                      numc=args.ncomponents,
                      detr=args.nodetrend)

    colstrbase = 'a_comp_cor_'
    if args.compcorstr is not None:
        colstrbase = ''.join([colstrbase, args.compcorstr, '_'])

    colnames = [(''.join([colstrbase, str(n)])) for n in range(1, args.ncomponents+1)]

    # write it
    conf_df = pd.DataFrame(conf, columns=colnames)
    conf_df.to_csv(''.join([args.out, 'acompcor.csv']), index=False)


if __name__ == '__main__':
    main()
