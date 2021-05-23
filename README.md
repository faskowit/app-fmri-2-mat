[![Abcdspec-compliant](https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg)](https://github.com/brain-life/abcd-spec)
[![Run on Brainlife.io](https://img.shields.io/badge/Brainlife-brainlife.app.167-blue.svg)](https://doi.org/10.25663/brainlife.app.167)

# app-fmri-2-mat
fMRIPrep outputs that are nuisance regressed and then, in combination with a parcellation, made into timeseries and/or correlation matrix. 

So you've just preprocessed your fmri data... but you are now left wondering how you go from these preprocessed outputs to something ammenable for analysis, such as a nuisance-regressed image or bold timeseries from nodes of a parcellation or even an NxN connectivity matrix.   

These scripts will take a `bold.nii.gz`, `mask.nii.gz`, `confounds.tsv`, and `parcellation.nii.gz` and regress them (accoriding to a few nuisance strategies of your choice) and then create timeseries according to the nodes of your parc. 

These tools rely heavily on nilearn's functions-so much grattiude to them. Also many thanks to [fliem](https://github.com/fliem) whose code here: https://github.com/fliem/sea_zrh_rs I copied/adopted/written on top of to make these tools.

This code can be run within the [brainlife](https://brainlife.io/) environment, or your system directly, using either the command line interface or a `config.json` to mimic the brainlife functionality. 

### Authors 

- Josh Faskowitz (joshua.faskowitz@gmail.com) 

### Funding 

[![NSF-GRFP-1342962](https://img.shields.io/badge/NSF_GRFP-1342962-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1342962)
[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-1636893](https://img.shields.io/badge/NSF_BCS-1636893-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-ACI-1916518](https://img.shields.io/badge/NSF_ACI-1916518-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1916518)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NIH-NIBIB-R01EB029272](https://img.shields.io/badge/NIH_NIBIB-R01EB029272-green.svg)](https://grantome.com/grant/NIH/R01-EB029272-01)

### Citations 

Please cite the following articles when publishing papers that used data, code or other resources created by the brainlife.io community. Citing this repository will be good.

Avesani, P., McPherson, B., Hayashi, S. et al. The open diffusion data derivatives, brain data upcycling via integrated publishing of derivatives and reproducible open cloud services. Sci Data 6, 69 (2019). https://doi.org/10.1038/s41597-019-0073-y

### How to use
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

### Running Locally (on your machine) in the Brainlife.io manner

1. git clone this repo.
2. Inside the cloned directory, create `config.json` with something like the following content with paths to your input files.

```json
{
        "fmri": "/path/to/bold.nii.gz",
        "parc": "/path/to/parcellation.nii.gz",
        "confounds": "/path/to/confounds.tsv",
        "mask": "/path/to/mask.nii.gz",
        "confjson": "/path/to/config.json",
        "tr": "2.3",
        "savets": "true",
        "inspace": "data",
        "strategy" "36p"
}
```

3. Launch the App by executing `main`

```bash
./main
```

## Output

All output files will be generated under the current working directory (pwd), in directories called `output_makemat` and `output_regress`. 

### Dependencies

This App uses [singularity](https://www.sylabs.io/singularity/) to run. If you don't have singularity, you can run this script in a unix enviroment with:  

  - python3: https://www.python.org/downloads/
  - jq: https://stedolan.github.io/jq/
  
  #### MIT Copyright (c) Josh Faskowitz & brainlife.io

<sub> This material is based upon work supported by the National Science Foundation Graduate Research Fellowship under Grant No. 1342962. Any opinion, findings, and conclusions or recommendations expressed in this material are those of the authors(s) and do not necessarily reflect the views of the National Science Foundation. </sub>
