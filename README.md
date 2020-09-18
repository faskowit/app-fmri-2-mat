# app-fmri-2-mat
fmriprep outputs to connectivity matrices 

So you've just preprocessed your fmri data... but you are now left wondering how you go from these preprocessed outputs to something ammenable for analysis, such as a nuisance-regressed image or bold timeseries from nodes of a parcellation or even an NxN connectivity matrix.   

These scripts will take a `bold.nii.gz`, `mask.nii.gz`, `confounds.tsv`, and `parcellation.nii.gz` and regress them (accoriding to a few nuisance strategies of your choice) and then create timeseries according to the nodes of your parc. 

These tools rely heavily on nilearn's functions-so much grattiude to them. Also many thanks to [fliem](https://github.com/fliem) whose code here: https://github.com/fliem/sea_zrh_rs I copied/adopted/written on top of to make these tools.

# How to use
Need python3 with nibable, pandas, nilearn, and h5py

```
  run.sh
    REQUIRED
    -fmri:      your bold.nii.gz image here
    -mask:      your mask.nii.gz image here
    -parc:      parcellation in same space as bold.nii.gz
    -conf:      confounds file (.tsv format, expecting it to be fmriprep's output)
    OPTIONAL **=default
    -out:       output prefix; **output_
    -tr:        repetition time, if not provided, scripts will try to guess (not a great move)
    -discard:   now many volumes (integer) to descard from beginning of bold; **0
    -space:     for parc to bold resampling, which space to use; choices **data, labels
    -strategy:  nuisance regression strategy; choices **36p, 9p, 6p, aCompCor, 24aCompCor
                                                        24aCompCorGsr, globalsig, globalsig4
    OPT FLAGS
    -savets:    flag to save timeseries as hd5 file
    -nomat:     flag to not make correlation matrix
    EXTRA OPTS
    -regressextra, -makematextra
                these args let advanced users have access to the python scripts in /src. 
                For example, to change the smoothing kernel in the regress.py script, 
                you can add `-regressextra -fwhm 2`. Other options are low and high pass 
                filter settings, and the spike threshold. Check out the python scripts 
                for all these extra options. 
                ***also*** please be aware of the default parameters being used in these
                python scripts; these parameters, which are set to reasonable values 
                based on literature, will surely affect your processed data. cheers. 
```

These scripts have also been made Brainlife.io compatible (re: cm datatype), but can be run outside of the brainlife platform.

<sub> This material is based upon work supported by the National Science Foundation Graduate Research Fellowship under Grant No. 1342962. Any opinion, findings, and conclusions or recommendations expressed in this material are those of the authors(s) and do not necessarily reflect the views of the National Science Foundation. </sub>
